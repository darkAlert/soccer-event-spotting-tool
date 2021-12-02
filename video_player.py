import cv2
from multiprocessing import Process, Event, shared_memory, Lock, Value, Array
import numpy as np
import time


cv2.setNumThreads(0)      # disable multithreading


class SharedFrameBuffer:
    def __init__(self, shape):
        self._shape = shape                                          # batch, height, width, channels
        self._lock = Lock()
        self._num_frames = Value('i', 0)                             # ready frame counter
        self._batch_size = self._shape[0]
        self._writing_idx = 0
        self._reading_idx = 0

        # Create shared memory:
        self._info = np.ndarray((3), dtype=np.int32)                # frame_id, frame_width, frame_height
        self._bytes = np.ndarray((self._shape[1:]), dtype=np.uint8) # frame bytes
        self._elem_size = self._info.nbytes + self._bytes.nbytes
        self._buffer_size = self._elem_size * self._batch_size
        self._shm = shared_memory.SharedMemory(create=True, size=self._buffer_size)

    def __del__(self):
        self._shm.close()

    def clear(self):
        raise NotImplementedError

    def put(self, frame_id, frame, timeout=0.01):
        # Wait for the buffer to free up space:
        while True:
            self._lock.acquire()
            if self._num_frames.value < self._batch_size - 1: # subtract '1' because we don't copy the memory
                self._lock.release()                          # of the current frame in get() below
                break
            self._lock.release()
            time.sleep(timeout)

        # Prepare buffer element:
        offset = self._elem_size*self._writing_idx
        frame_info = np.ndarray((self._info.shape), dtype=self._info.dtype, buffer=self._shm.buf[offset:])
        offset += self._info.nbytes
        frame_shape = frame.shape if frame is not None else (1,1)
        frame_bytes = np.ndarray(frame_shape, dtype=self._bytes.dtype, buffer=self._shm.buf[offset:])

        # Write to buffer:
        self._lock.acquire()
        frame_info[:] = (frame_id, frame_shape[1], frame_shape[0])
        frame_bytes[:] = frame[:] if frame is not None else (0,0)
        self._num_frames.value += 1
        self._lock.release()

        self._writing_idx += 1
        if self._writing_idx >= self._batch_size:
            self._writing_idx = 0

    def get(self):
        # Try to pop frame from buffer:
        self._lock.acquire()
        if self._num_frames.value <= 0:
            self._lock.release()
            return None, None

        # Prepare buffer element:
        offset = self._elem_size*self._reading_idx
        frame_info = np.ndarray((self._info.shape), dtype=self._info.dtype, buffer=self._shm.buf[offset:])
        offset += self._info.nbytes
        frame_id = frame_info[0]
        shape = (frame_info[2], frame_info[1], 3)
        frame_bytes = np.ndarray(shape, dtype=self._bytes.dtype, buffer=self._shm.buf[offset:])

        # Read frame from buffer:
        frame = frame_bytes           # copy() will be needed here if we don't subtract '1' in put() above
        self._num_frames.value -= 1
        self._lock.release()

        self._reading_idx += 1
        if self._reading_idx >= self._batch_size:
            self._reading_idx = 0

        return frame_id, frame


class VideoPlayer:
    '''
    Video player with multiprocessing
    '''
    class Messages:
        NONE = 0
        REWIND = 1
        SET_RESOLUTION = 2
        TERMINATE = 3

    def __init__(self, buffer_size=300):
        self._buffer_size = buffer_size
        self._path = ''
        self._openned = False
        self._video_fps = 0
        self._num_frames = 0
        self._width = 0
        self._height = 0
        self._frame_id = -1
        self._buffer = None
        self._worker = None
        self._terminated = None
        self._messages = None
        self._resolution = None

    def open(self, video_path):
        assert video_path is not None and len(video_path)

        # Release current video if it is open:
        if self._openned:
            self._messages[:] = (self.Messages.TERMINATE, -1)
            # self._buffer.stop()
            self._terminated.wait()

        # Temporarily open the video to get some info:
        cap = cv2.VideoCapture(video_path)
        assert cap.isOpened()
        self._video_fps = int(round(cap.get(cv2.CAP_PROP_FPS)))
        self._num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        # Init variables:
        self._path = video_path
        self._terminated = Event()
        self._messages = Array('i', [self.Messages.NONE, -1])
        self._resolution = Array('i', [self._width, self._height])
        self._buffer = SharedFrameBuffer(shape=(self._buffer_size, self._height, self._width, 3))

        # Run capture worker:
        args = (self._path, self._buffer, self._resolution, self._messages, self._terminated)
        self._worker = Process(target=VideoPlayer.run_capture, args=args)
        self._worker.start()
        self._openned = True

    def release(self):
        # Release current video if it is open:
        if self._openned:
            self._messages[:] = (self.Messages.TERMINATE, -1)
            self._terminated.wait()

    def set_resolution(self, width, height):
        assert self._openned
        if width != self._width or height != self._height:
            self._width = width
            self._height = height
            self._resolution[:] = (width, height)

    def rewind(self, next_frame_id):
        assert self._openned
        self._messages[:] = (self.Messages.REWIND, next_frame_id)

    def get_frame(self, size):
        assert self._openned

        # Pop frame from buffer:
        frame_id, frame = self._buffer.get()

        if frame_id is not None:
            if frame_id >= 0:
                self._frame_id = frame_id

        # Resize frame if needed:
        if frame is not None and (size[0] != frame.shape[1] or size[1] != frame.shape[0]):
            frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)

        return True, frame

    def is_open(self):
        return self._openned

    @property
    def video_fps(self):
        return self._video_fps

    @property
    def num_frames(self):
        return self._num_frames

    @property
    def frame_id(self):
        return self._frame_id

    @property
    def path(self):
        return self._path

    @staticmethod
    def run_capture(path, buffer, resolution, messages, terminated):
        '''
        Runs worker to capture frames from video
        '''
        cap = cv2.VideoCapture(path)
        assert cap is not None and cap.isOpened()
        frame_id = -1

        while True:
            # Read message:
            mes = messages[:]
            if mes[0] == VideoPlayer.Messages.REWIND:
                buffer.clear()
                next_frame = mes[1]
                cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame)
                frame_id = next_frame - 1
                messages[0] = VideoPlayer.Messages.NONE
            elif mes[0] == VideoPlayer.Messages.TERMINATE:
                buffer.clear()
                cap.release()
                messages[0] = VideoPlayer.Messages.NONE
                break

            # Read next frame:
            _, frame = cap.read()
            frame_id = frame_id + 1 if frame is not None else -1

            # Resize frame if needed:
            res = resolution[:]
            if frame is not None and frame.shape[:2] != res[:2]:
                frame = cv2.resize(frame, res, interpolation=cv2.INTER_AREA)

            # Put frame in the buffer:
            buffer.put(frame_id, frame)

            if frame is None:
                time.sleep(0.01)

        terminated.set()
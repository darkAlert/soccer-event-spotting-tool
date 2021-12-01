import cv2
from multiprocessing import Process, Queue, Event, Manager, shared_memory, Lock, Value, managers, Array
from queue import Empty
import numpy as np
import time
from enum import Enum

cv2.setNumThreads(0)      # disable multithreading


class VideoPlayer:
    def __init__(self):
        self._cap = None
        self._path = ''
        self._video_fps = 0
        self._num_frames = 0
        self._frame_id = -1

    def open(self, video_path):
        assert video_path is not None and len(video_path)

        self._path = video_path
        if self._cap is not None:
            self.release()

        self._cap = cv2.VideoCapture(self.path)
        self._video_fps = 0
        self._num_frames = 0
        self._frame_id = -1
        if self._cap is not None and self._cap.isOpened():
            self._video_fps = int(round(self._cap.get(cv2.CAP_PROP_FPS)))
            self._num_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def is_open(self):
        return self._cap is not None and self._cap.isOpened()

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

    # @x.setter
    # def x(self, value):
    #     self._x = value

    def rewind(self, next_frame_id):
        assert self._cap is not None and self._cap.isOpened()
        if next_frame_id != self.frame_id + 1:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame_id)  # rewind
        self._frame_id = next_frame_id-1

    def capture(self, frame_size=(1280,720)):
        assert self._cap is not None and self._cap.isOpened()

        self._frame_id += 1

        if self._frame_id >= self.num_frames:
            self._frame_id = self.num_frames - 1
            return False, None

        _, img = self._cap.read()

        if img is not None and frame_size[0] != img.shape[1]:
            img = cv2.resize(img, frame_size, interpolation=cv2.INTER_AREA)

        return True, img

    def release(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None






class SharedFrameBuffer_old:
    def __init__(self, shape):
        self._shape = shape       # batch, height, width, channels
        data = np.empty(shape=self._shape, dtype=np.uint8)
        self._shm = shared_memory.SharedMemory(create=True, size=data.nbytes)
        self._buffer = np.ndarray(data.shape, dtype=np.uint8, buffer=self._shm.buf)
        self._lock = Lock()

        self._writing_idx = 0
        self._reading_idx = 0
        self._max_size = 300
        self._num_frames = Value('i', 0)
        self._n = self._shape[0]

    def __del__(self):
        self._shm.close()

    def put(self, frame):
        if frame is None:
            pass

        existing_shm = shared_memory.SharedMemory(name=self._shm.name)
        buffer = np.ndarray(self._shape, dtype=np.uint8, buffer=existing_shm.buf)

        while True:
            self._lock.acquire()
            if self._num_frames.value < self._max_size:
                self._lock.release()
                break
            self._lock.release()
            time.sleep(0.01)

        self._lock.acquire()
        # buffer[self._writing_idx, :, :, :] = frame
        buffer[self._writing_idx, :, :, :] = cv2.resize(frame, (self._shape[2], self._shape[1]), interpolation=cv2.INTER_AREA)
        self._num_frames.value += 1
        # print ('write', self._num_frames.value, self._writing_idx)
        self._lock.release()

        self._writing_idx += 1
        if self._writing_idx >= self._n:
            self._writing_idx = 0
        existing_shm.close()

    def get(self, size):
        self._lock.acquire()

        # print('read', self._num_frames.value, self._reading_idx)
        if self._num_frames.value <= 0:
            self._lock.release()
            return None
        frame = self._buffer[self._reading_idx, :, :, :]
        # frame = cv2.resize(self._buffer[self._reading_idx, :, :, :], (size[0], size[1]), interpolation=cv2.INTER_AREA)

        self._num_frames.value -= 1
        self._lock.release()

        self._reading_idx += 1
        if self._reading_idx >= self._n:
            self._reading_idx = 0

        return frame






class SharedFrameBuffer:
    def __init__(self, shape):
        self._shape = shape       # batch, height, width, channels
        data = np.empty(shape=self._shape, dtype=np.uint8)
        self._shm = shared_memory.SharedMemory(create=True, size=data.nbytes)
        self._buffer = np.ndarray(data.shape, dtype=np.uint8, buffer=self._shm.buf)
        self._lock = Lock()

        self._writing_idx = 0
        self._reading_idx = 0
        self._max_size = 300
        self._num_frames = Value('i', 0)
        self._n = self._shape[0]

    def __del__(self):
        self._shm.close()

    def put(self, frame):
        if frame is None:
            pass

        # existing_shm = shared_memory.SharedMemory(name=self._shm.name)
        buffer = np.ndarray(self._shape, dtype=np.uint8, buffer=self._shm.buf)

        while True:
            self._lock.acquire()
            if self._num_frames.value < self._max_size:
                self._lock.release()
                break
            self._lock.release()
            time.sleep(0.01)

        self._lock.acquire()
        # buffer[self._writing_idx, :, :, :] = frame
        buffer[self._writing_idx, :, :, :] = cv2.resize(frame, (self._shape[2], self._shape[1]), interpolation=cv2.INTER_AREA)
        self._num_frames.value += 1
        print ('write', self._num_frames.value, self._reading_idx, self._writing_idx)
        self._lock.release()

        self._writing_idx += 1
        if self._writing_idx >= self._n:
            self._writing_idx = 0
        # existing_shm.close()

    def get(self, size):
        self._lock.acquire()
        print('read', self._num_frames.value, self._reading_idx, self._writing_idx)
        if self._num_frames.value <= 0:
            self._lock.release()
            return None
        frame = self._buffer[self._reading_idx, :, :, :]
        # frame = cv2.resize(self._buffer[self._reading_idx, :, :, :], (size[0], size[1]), interpolation=cv2.INTER_AREA)

        self._num_frames.value -= 1
        self._lock.release()

        self._reading_idx += 1
        if self._reading_idx >= self._n:
            self._reading_idx = 0

        return frame



class ShareMemoryManager(managers.BaseManager):
    pass
ShareMemoryManager.register('VideoCapture', cv2.VideoCapture)

class SharedVideoCapture:
    def __init__(self):
        self.cap = cv2.VideoCapture()

    def open(self, path):
        self.cap.open(path)

    def isOpened(self):
        return self.cap.isOpened()

    def get(self, value):
        return self.cap.get(value)

    def read_batch(self, count=10):
        frames = []
        for i in range(count):
            _, img = self.cap.read()
            if img is None:
                break
            frames.append(img)

        return frames
ShareMemoryManager.register('SharedVideoCapture', SharedVideoCapture)


class VideoPlayerMP:
    def __init__(self):
        self._cap = None
        self._path = ''
        self._video_fps = 0
        self._num_frames = 0
        self._frame_id = -1
        self._buffer = None


    def open(self, video_path, buffer_shape=(300, 720, 1280, 3)):
        assert video_path is not None and len(video_path)

        self._path = video_path
        if self._cap is not None:
            self.release()

        # self._cap = cv2.VideoCapture(self.path)

        # shared_mem_manager = ShareMemoryManager()
        # shared_mem_manager.start()
        # self._cap = shared_mem_manager.VideoCapture()
        # self._cap.open(self.path)

        shared_mem_manager = ShareMemoryManager()
        shared_mem_manager.start()
        self._cap = shared_mem_manager.SharedVideoCapture()
        self._cap.open(self.path)




        self._video_fps = 0
        self._num_frames = 0
        self._frame_id = -1
        if self._cap is not None and self._cap.isOpened():
            self._video_fps = int(round(self._cap.get(cv2.CAP_PROP_FPS)))
            self._num_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Multi-threading:
        self._run_worker(buffer_shape)

    def is_open(self):
        return self._cap is not None and self._cap.isOpened()

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


    def _run_worker(self, buffer_shape):
        self._terminate = Event()
        self._terminated = Event()

        # Shared memory:
        self._buffer = SharedFrameBuffer(buffer_shape)

        args = (self._path, self._buffer, self._cap, self._terminate, self._terminated)
        self._worker = Process(target=VideoPlayerMP.capture, args=args)
        self._worker.start()


    def rewind(self, next_frame_id):
        assert self._cap is not None and self._cap.isOpened()

        self._terminate.set()
        self._terminated.wait()

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame_id)  # rewind
        self._frame_id = next_frame_id-1

        self._run_worker()


    def get_frame(self, size):
        if self._buffer is None:
            return False, None

        try:
            img = self._buffer.get(size)


            # img = self._frames.get()
            self._frame_id += 1

            # if img is not None and frame_size[0] != img.shape[1]:
            #     img = cv2.resize(img, frame_size, interpolation=cv2.INTER_AREA)

            return True, img

        except Empty:
            return False, None


    def release(self):
        self._terminate.set()
        self._terminated.wait()

        if self._cap is not None:
            self._cap.release()
            self._cap = None




    @staticmethod
    def capture(path, buffer, cap, terminate, terminated):
        # cap = cv2.VideoCapture(path)
        assert cap is not None and cap.isOpened()

        # existing_shm = shared_memory.SharedMemory(name=buffer_name)
        # np_array = np.ndarray(buffer_shape, dtype=np.uint8, buffer=existing_shm.buf)


        while not terminate.is_set():
            # _, img = cap.read()
            # buffer.put(img)
            frames = cap.read_batch()
            for img in frames:
                buffer.put(img)

            # if img is None:
            #     break

        terminated.set()





class SharedFrameBuffer_v2:
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
            if self._num_frames.value < self._batch_size-1:
                self._lock.release()
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
        frame = frame_bytes[:]
        self._num_frames.value -= 1
        self._lock.release()

        self._reading_idx += 1
        if self._reading_idx >= self._batch_size:
            self._reading_idx = 0

        return frame_id, frame


class VideoPlayerMP_v2:
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
        self._buffer = SharedFrameBuffer_v2(shape=(self._buffer_size, self._height, self._width, 3))

        # Run capture worker:
        args = (self._path, self._buffer, self._resolution, self._messages, self._terminated)
        self._worker = Process(target=VideoPlayerMP_v2.run_capture, args=args)
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
            if mes[0] == VideoPlayerMP_v2.Messages.REWIND:
                buffer.clear()
                next_frame = mes[1]
                cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame)
                frame_id = next_frame - 1
                messages[0] = VideoPlayerMP_v2.Messages.NONE
            elif mes[0] == VideoPlayerMP_v2.Messages.TERMINATE:
                buffer.clear()
                cap.release()
                messages[0] = VideoPlayerMP_v2.Messages.NONE
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
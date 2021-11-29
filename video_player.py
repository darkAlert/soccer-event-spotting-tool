import cv2
from multiprocessing import Process, Queue, Event, Manager, shared_memory, Lock
from queue import Empty
import numpy as np



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






class SharedFrameBuffer:
    def __init__(self, shape):
        self._shape = shape       # batch, height, width, channels
        data = np.empty(shape=self._shape, dtype=np.uint8)
        self._shm = shared_memory.SharedMemory(create=True, size=data.nbytes)
        self._buffer = np.ndarray(data.shape, dtype=np.uint8, buffer=self._shm.buf)
        self._lock = Lock()

    def __del__(self):
        self._shm.close()

    def put(self, frame):
        if frame is None:
            pass

        self._lock.acquire()
        self._buffer[0, :, :, :] = cv2.resize(frame, (self._shape[2], self._shape[1]), interpolation=cv2.INTER_AREA)
        self._lock.release()

    def get(self):
        self._lock.acquire()
        frame = self._buffer[0, :, :, :]
        self._lock.release()

        return frame





class VideoPlayerMP:
    def __init__(self):
        self._cap = None
        self._path = ''
        self._video_fps = 0
        self._num_frames = 0
        self._frame_id = -1
        self._buffer = None


    def open(self, video_path, buffer_shape=(100, 720, 1280, 3)):
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

        args = (self.path, self._buffer, self._terminate, self._terminated)
        self._worker = Process(target=VideoPlayerMP.capture, args=args)
        self._worker.start()


    def rewind(self, next_frame_id):
        assert self._cap is not None and self._cap.isOpened()

        self._terminate.set()
        self._terminated.wait()

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame_id)  # rewind
        self._frame_id = next_frame_id-1

        self._run_worker()


    @staticmethod
    def capture(path, buffer, terminate, terminated):
        cap = cv2.VideoCapture(path)
        assert cap is not None and cap.isOpened()

        while not terminate.is_set():
            _, img = cap.read()

            buffer.put(img)

            if img is None:
                break

            # img = cv2.resize(img, (1280,720), interpolation=cv2.INTER_AREA)

            # frames.put(img)

        terminated.set()


    def get_frame(self, frame_size=(1280,720)):
        if self._buffer is None:
            return False, None

        try:
            img = self._buffer.get()


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
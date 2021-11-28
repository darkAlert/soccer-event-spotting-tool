import cv2
from torch.multiprocessing import Process, Queue, Event, set_start_method
from queue import Empty


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




class VideoPlayerMP:
    def __init__(self):
        self._cap = None
        self._path = ''
        self._video_fps = 0
        self._num_frames = 0
        self._frame_id = -1
        self._frames = None


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

        # Multi-threading:
        self._run_worker(self.path)

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


    def _run_worker(self, path):
        if self._frames is not None:
            self._frames.close()
        self._frames = Queue(100)
        self._terminate = Event()
        self._terminated = Event()
        args = (path, self._cap, self._frames, self._terminate, self._terminated)
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
    def capture(path, cap, frames, terminate, terminated):
        cap = cv2.VideoCapture(path)
        assert cap is not None and cap.isOpened()
        print('Worker started!')

        while not terminate.is_set():
            print ('read')
            _, img = cap.read()
            print ('read done!')

            if img is None:
                break

            print ('frames',frames.qsize())
            frames.put(img)
            print ('capture', img is not None)

        terminated.set()
        print ('Worker terminated!')


    def get_frame(self, frame_size=(1280,720)):
        if self._frames is None:
            return False, None

        try:
            img = self._frames.get(timeout=0.005)
            self._frame_id += 1

            if img is not None and frame_size[0] != img.shape[1]:
                img = cv2.resize(img, frame_size, interpolation=cv2.INTER_AREA)

            return True, img

        except Empty:
            return False, None


    def release(self):
        self._terminate.set()
        self._terminated.wait()

        if self._cap is not None:
            self._cap.release()
            self._cap = None
import cv2


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

    def capture(self):
        assert self._cap is not None and self._cap.isOpened()

        self._frame_id += 1

        if self._frame_id >= self.num_frames:
            self._frame_id = self.num_frames - 1
            return False, None

        _, img = self._cap.read()

        return True, img

    def release(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None
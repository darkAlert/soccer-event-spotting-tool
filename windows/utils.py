import datetime
import cv2
from PIL import Image, ImageTk
import PySimpleGUI as sg


def image_np_to_pil(cv_img):
    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(cv_img)
    # window['image'](data=cv2.imencode('.png', cap.read()[1])[1].tobytes())

    return ImageTk.PhotoImage(img_pil)


def frame_id_to_time_stamp(frame_id, video_fps):
    return str(datetime.timedelta(seconds=frame_id / video_fps)).split('.')[0]


def show_conformation_window(header, message):
    confirmed = False

    # Create buttons:
    sg_button_list = [
        [sg.Button('Отмена', key='cancel', size=(20, 1)), sg.Button('OK', key='ok', size=(20, 1))]
    ]

    # Create a layout:
    layout = [
        [sg.Text(text=message, font=('Helvetica', 10))],
        [sg.Column(sg_button_list, justification='center')]
    ]

    # Create a window:
    window = sg.Window(header, layout, keep_on_top=True, modal=True, finalize=True)

    # Window events:
    while True:
        w_event, w_values = window.read(timeout=0)

        # Close:
        if w_event == sg.WIN_CLOSED or w_event == 'Exit' or w_event == 'cancel':
            break
        elif w_event == 'ok':
            confirmed = True
            break

    window.close()
    return confirmed
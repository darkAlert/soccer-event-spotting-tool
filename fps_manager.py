from datetime import datetime


class FPSManager:
    def __init__(self, target_fps=30):
        self.reset()
        self.set_target_fps(target_fps)

    def reset(self):
        self._delay = 0
        self.prev_time = datetime.now()
        self.start_time = datetime.now()
        self.tic = 0
        self.real_fps = 0.0

    def set_target_fps(self, target_fps):
        self.target_fps = target_fps
        target_frame_delta = 1.0 / self.target_fps
        self._delay = int(round(target_frame_delta * 1000))
        self.tic = 0
        self.start_time = datetime.now()

    def calulate_delay(self):
        target_frame_delta = 1.0 / self.target_fps
        new_time = datetime.now()
        frame_delta = (new_time - self.prev_time).total_seconds()
        self.prev_time = new_time
        if frame_delta < target_frame_delta:
            self._delay += 1
        elif frame_delta > target_frame_delta:
            self._delay = self._delay - 1 if self._delay > 0 else 0

        return self._delay

    def mesure_fps(self):
        self.tic += 1
        if self.tic >= self.target_fps:
            self.tic = 0
            stop_time = datetime.now()
            elapsed = (stop_time - self.start_time).total_seconds()
            self.start_time = stop_time
            self.real_fps = 1.0/(elapsed/self.target_fps)

        return self.real_fps
#
#
#
#
#
#
#
#
# import PySimpleGUI as sg
# #set the theme for the screen/window
# sg.theme('SystemDefault')
# menu_def=['&File', ['&New File', '&Open...','Open &Module','---', '!&Recent Files','C&lose']],['&Save',['&Save File', 'Save &As','Save &Copy'  ]],['&Edit', ['&Cut', '&Copy', '&Paste']]
# #define layout
# layout=[[sg.Menu(menu_def, background_color='lightsteelblue',text_color='navy', disabled_text_color='yellow', font='Verdana', pad=(10,10))],
#         [sg.ButtonMenu('', [['nf', 'op','om','---','rf','cl'],['New File', 'Open','Open Module','---','Recent Files','Close']],image_filename ='icon_biggrin.gif',border_width=5),sg.ButtonMenu('', [['rm', 'rc','sm','ps'],['Run', 'Run Module','Shell','Python module']],image_filename ='icon_cry.gif',background_color='teal'),sg.ButtonMenu('Terminate', [['ex', 'cl','---','ab'],['Exit', 'Close','---','About us...']])],
#         [sg.Multiline(size=(80,10),tooltip='Write your Text here')],
#         [sg.Text('File Name'),sg.Input(),sg.OptionMenu(values=['.txt','.pdf','.gif', '.jpg','.mp4','.gif','.dat','.sql'],size=(4,8),default_value='.doc',key='ftype')],
#         [sg.Button('SAVE', font=('Times New Roman',12)),sg.Button('CANCEL', font=('Times New Roman',12))]]
# #Define Window
# win =sg.Window('Your Custom Editor',layout)
# #Read  values entered by user
# events,values=win.read()
# #close first window
# win.close()

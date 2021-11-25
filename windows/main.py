import PySimpleGUI as sg

SPEED_VALUES = {'0.25': 0.25, '0.5': 0.5, 'Обычная': 1, '1.5': 1.5, '2.0': 2, '4.0': 4}
SPEED_DEFAULT = 'Обычная'


class WindowMain:
    def __init__(self, video_dir=''):
        self.window = self.create_window(video_dir)

    def create_window(self, video_dir):
        # Create GUI elements:
        sg.theme('DarkAmber')

        sg_canvas = sg.Image(key='image_canvas')

        menu_def = [['&File', ['&Открыть...', '&Сохранить', '---', '&Выход']], ['&Events', ['Панель ивентов']]]
        sg_menu = sg.Menu(
            menu_def,
            font=('Helvetica', 12),
            background_color=sg.theme_background_color(),
            text_color='white')

        sg_slider = sg.Slider(
            range=(0, 0),
            key='slider_frame_id',
            default_value=0,
            size=(117, 15),
            orientation='horizontal',
            font=('Helvetica', 12),
            enable_events=True,
            disable_number_display=True,
            disabled=True
        )
        sg_text_fps = sg.Text('FPS: 0', key='text_fps')
        sg_text_counter = sg.Text('{}/{}'.format(0, 0), key='text_counter')
        sg_combo_speed = sg.Combo(
            [str(speed) for speed in SPEED_VALUES.keys()],
            key='combo_speed',
            default_value=SPEED_DEFAULT,
            enable_events=True,
            readonly=True,
            disabled=True
        )
        sg_file_browse = sg.FileBrowse(key='file_browse',
                                       file_types=(("mp4", "*.mp4"), ("ALL Files", "*.* *"),),
                                       enable_events=True,
                                       change_submits=True,
                                       visible=False,
                                       initial_folder=video_dir)

        # All the stuff inside your window.
        layout = [
            [sg_menu],
            [sg.Column([[sg_canvas]])],
            [sg_slider],
            [sg_file_browse],
            [sg.Column([[sg_text_counter, sg_text_fps]], justification='left'),
             sg.Column([[sg.Button('Панель ивентов', key='Панель ивентов', size=(20, 1))]], justification='right')],
            [sg.Column([[sg.Button('◼️', key='button_play', size=(1, 1)), sg_combo_speed]], justification='center')]
        ]

        # Create the Window
        window = sg.Window(
            'Soccer Event Spotting Tool',
            layout,
            return_keyboard_events=True,
            location=(0, 0),
            resizable=False,
            use_default_focus=False,
            enable_close_attempted_event=True
        ).Finalize()
        # window.bind('<Configure>', 'Configure')
        # window.Maximize()

        return window


def show_team_setting_window():
    # Create buttons:
    sg_button_list = [
        [sg.Button('Отмена', key='cancel', size=(20, 1)), sg.Button('OK', key='ok', size=(20, 1))]
    ]

    column_left = sg.Column([
        [sg.Text('Хозяева:')],
        [sg.Text('Гости:')],
    ])
    column_right = sg.Column([
        [sg.Input(key='home')],
        [sg.Input(key='away')]
    ])

    # Create a layout:
    layout = [
        [sg.Text(text='Введите название команд', font=('Helvetica', 10))],
        [column_left, column_right],
        [sg.Text('Ошибка!', text_color='red', font=('Helvetica', 10), key='not_filled', visible=False)],
        [sg.Column(sg_button_list, justification='center')]
    ]

    # Create a window:
    window = sg.Window('Установка команд', layout, keep_on_top=True, modal=True, finalize=True)

    # Window events:
    while True:
        w_event, w_values = window.read(timeout=0)

        # Close:
        if w_event == sg.WIN_CLOSED or w_event == 'Exit' or w_event == 'cancel':
            break
        elif w_event == 'ok':
            home_team = w_values['home']
            away_team = w_values['away']
            if len(home_team) == 0 or len(away_team) == 0 or home_team == away_team:
                window['not_filled'].update(visible=True, value='Введите название команд!')
                continue

            window.close()
            return home_team, away_team

    window.close()
    return None, None

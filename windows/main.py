import PySimpleGUI as sg
from event_manager import EventTypes
from windows.utils import frame_id_to_time_stamp, show_conformation_window


SPEED_VALUES = {'0.25': 0.25, '0.5': 0.5, 'Обычная': 1, '1.5': 1.5, '2.0': 2, '4.0': 4}
SPEED_DEFAULT = 'Обычная'


class EventTableNames():
    START_TIME = 0
    END_TIME = 1
    NAME = 2
    TYPE = 3
    TEAM = 4
    FINISHED = 5
    # Invisible:
    START_IDX = 6
    END_IDX = 7


class WindowMain:
    def __init__(self, video_dir=''):
        self.window = self.create_window(video_dir)
        self.event_list = []
        self.event_start_frame = None
        self.event_end_frame = None
        self.selected_event = None


    def create_window(self, video_dir):
        # Create GUI elements:
        sg.theme('DarkAmber')

        # Menu:
        menu_def = [['&File', ['&Открыть...', '&Сохранить', '---', '&Выход']]]
        sg_menu = sg.Menu(
            menu_def,
            font=('Helvetica', 12),
            background_color=sg.theme_background_color(),
            text_color='white')

        # Open file:
        sg_file_browse = sg.FileBrowse(
            key='file_browse',
            file_types=(("mp4", "*.mp4"), ("ALL Files", "*.* *"),),
            enable_events=True,
            visible=False,
            initial_folder=video_dir
        )

        # Top column (video screen + event panel):
        event_panel = [
            [sg.Frame('Создание нового ивента', self.create_layout_event_creation(),
                      element_justification='center', vertical_alignment='top', expand_x=True)],
            [],
            [sg.Frame('Редактирование ивента', self.create_layout_edit_event(), key='-EDIT_EVENT_LAYOUT-',
                      element_justification='center', vertical_alignment='bottom', visible=False, expand_x=True)]
        ]
        sg_column_top = sg.Column([[
            sg.Column([[sg.Image(key='image_canvas')]]),
            sg.Column(event_panel, vertical_alignment='top', expand_x=True)
        ]])

        # Bottom column (slider + navigation + event table):
        slider = [
            sg.Slider(
                range=(0, 0),
                key='slider_frame_id',
                default_value=0,
                size=(117, 15),
                orientation='horizontal',
                font=('Helvetica', 12),
                enable_events=True,
                disable_number_display=True,
                disabled=True,
                expand_x=True
            )
        ]
        navigation_panel = [
            sg.Column([[
                sg.Button('◼️', key='button_play', size=(1, 1)),
                sg.Combo(
                    [str(speed) for speed in SPEED_VALUES.keys()],
                    key='combo_speed',
                    default_value=SPEED_DEFAULT,
                    enable_events=True,
                    readonly=True,
                    disabled=True
                )]
            ], justification='center'),
            sg.Column([[
                sg.Text('{}/{}'.format(0, 0), key='text_counter'),
                sg.Text('FPS: 0', key='text_fps')]
            ], justification='left')
        ]
        event_table = [
            sg.Table(
                values=[['','','','','','','']],
                headings=['Начало', 'Конец', 'Имя события', 'Тип события', 'Команда', 'Завершено'],
                max_col_width=35,
                auto_size_columns=True,
                vertical_scroll_only = True,
                justification='center',
                num_rows=5,
                key='-EVENT_TABLE-',
                row_height=25,
                def_col_width=10,
                enable_click_events=False,
                enable_events=True,
                expand_x=True,
                expand_y=True
            )
        ]
        sg_column_bottom = sg.Column([slider, navigation_panel, event_table], vertical_alignment='top', expand_x=True, expand_y=True)

        # All the stuff inside the window:
        layout = [
            [sg_menu],
            [sg_file_browse],
            [sg_column_top],
            [sg_column_bottom]
        ]

        # Create window:
        window = sg.Window(
            'Soccer Event Spotting Tool',
            layout,
            return_keyboard_events=True,
            location=(0, 0),
            resizable=True,
            use_default_focus=False,
            enable_close_attempted_event=True
        ).Finalize()
        window.Maximize()

        return window


    @staticmethod
    def create_layout_event_creation():
        layout = [
            [sg.Listbox(values=[t['alias'] for t in EventTypes.types()],
                       key='-SELECT_EVENT_ALIAS-', size=(34, 17), enable_events=True, expand_x=True)],
            [sg.Button('Создать ивент', key='-CREATE_EVENT-', size=(18, 1))]
        ]

        return layout


    def create_new_event(self, event_manager, frame_id):
        event_alias = self.window['-SELECT_EVENT_ALIAS-'].get()
        if len(event_alias) == 0:
            show_conformation_window('Ошибка', 'Выберите тип ивента!')
            return

        event_alias = event_alias[0]
        event_type = EventTypes.alias2type(event_alias)

        # Generate event name:
        base_name = event_alias.replace(' - ', '_').replace(' ', '_')
        event_name = 'unnamed'
        for i in range(1, 9999):
            name = base_name + '_{}'.format(str(i))
            if event_manager.get_event(event_type, name) is None:
                event_name = name
                break

        self.selected_event = event_manager.create_event(event_type, event_name, frame_id)

        # Clean selected event type:
        self.window['-SELECT_EVENT_ALIAS-'].update(set_to_index=-1)


    @staticmethod
    def create_layout_edit_event():
        # Create columns:
        sg_left_column = [
            [sg.Text('Тип ивента:')],
            [sg.Text('Имя ивента:')],
            [sg.Text('Команда:')],
            [sg.Text('Игроки команды:')],
            [sg.Text('Игроки противника:')],
            [sg.Text('Начало ивента:')],
            [sg.Text('Конец ивента:')]
        ]
        sg_right_column = [
            [sg.Text('не задано', key='-EDIT_EVENT_ALIAS-')],
            [sg.Text('не задано', key='-EDIT_EVENT_NAME-')],
            [sg.Combo([''], key='-EDIT_EVENT_TEAM-', expand_x=True, readonly=True)],
            [sg.Input(key='-EDIT_EVENT_PLAYERS-')],
            [sg.Input(key='-EDIT_EVENT_ENEMY_PLAYERS-')],
            [
                sg.Text('не задано', key='-EDIT_EVENT_START_TIME-'),
                sg.Button('Перейти', key='-EDIT_EVENT_MOVE_TO_START-'),
                sg.Button('Установить текущее', key='-EDIT_EVENT_SET_START_TIME-', button_color='green')
            ],
            [
                sg.Text('не задано', key='-EDIT_EVENT_END_TIME-'),
                sg.Button('Перейти', key='-EDIT_EVENT_MOVE_TO_END-'),
                sg.Button('Установить текущее', key='-EDIT_EVENT_SET_END_TIME-', button_color='green')
            ]
        ]
        sg_button_list = [
            [
                sg.Button('Сбросить', key='-EDIT_EVENT_RESET-', size=(20, 1)),
                sg.Button('Применить', key='-EDIT_EVENT_SAVE-', size=(20, 1))
            ],
            [sg.HorizontalSeparator()],
            [sg.Button('Удалить', key='-EDIT_EVENT_DELETE-', size=(20, 1))]
        ]

        # Create a layout:
        layout = [
            [sg.Column(sg_left_column), sg.Column(sg_right_column)],
            [sg.HorizontalSeparator()],
            [sg.Text('Ошибка!', text_color='red', font=('Helvetica', 10), key='not_filled', visible=False)],
            [sg.Column(sg_button_list, justification='center', element_justification='center')]
        ]

        return layout


    def refresh_edit_event_layout(self, event_manager, video_fps, selected_row):
        if len(selected_row) == 0:
            self.selected_event = None
            return

        # Find event:
        selected_row_id = int(selected_row[0])
        event_data = self.event_list[selected_row_id]
        self.selected_event = event_manager.get_event(event_data[EventTableNames.TYPE], event_data[EventTableNames.NAME])

        # Event start and end:
        self.event_start_frame = self.selected_event.start_idx
        self.event_end_frame = self.selected_event.end_idx

        # Refresh data in the panel:
        self.window['-EDIT_EVENT_ALIAS-'].update(EventTypes.type2alias(self.selected_event.type))
        self.window['-EDIT_EVENT_NAME-'].update(self.selected_event.name)
        self.window['-EDIT_EVENT_TEAM-'].update(
            values = [team_name for team_name in event_manager.teams.values()],
            value = event_manager.teams[self.selected_event.team_key]
        )
        self.window['-EDIT_EVENT_PLAYERS-'].update(self.selected_event.players)
        self.window['-EDIT_EVENT_ENEMY_PLAYERS-'].update(self.selected_event.enemy_players)
        self.window['-EDIT_EVENT_START_TIME-'].update(
            frame_id_to_time_stamp(self.event_start_frame, video_fps) if self.event_start_frame is not None else 'не задано'
        )
        self.window['-EDIT_EVENT_END_TIME-'].update(
            frame_id_to_time_stamp(self.event_end_frame, video_fps) if self.event_end_frame is not None else 'не задано'
        )


    def set_event_time(self, video_fps, start_frame=None, end_frame=None):
        if start_frame is not None:
            self.event_start_frame = start_frame
            self.window['-EDIT_EVENT_START_TIME-'].update(frame_id_to_time_stamp(start_frame, video_fps))
        if end_frame is not None:
            self.event_end_frame = end_frame
            self.window['-EDIT_EVENT_END_TIME-'].update(frame_id_to_time_stamp(end_frame, video_fps))


    def get_event_start_and_end(self):
        return self.event_start_frame, self.event_end_frame


    def get_selected_event(self):
        return self.selected_event


    def save_edited_event(self, event_manager):
        if self.selected_event is None:
            return None

        team_name = self.window['-EDIT_EVENT_TEAM-'].get()
        players = self.window['-EDIT_EVENT_PLAYERS-'].get()
        enemy_players = self.window['-EDIT_EVENT_ENEMY_PLAYERS-'].get()

        # Set updated values:
        self.selected_event.team_key = event_manager.team_name_to_key[team_name]
        self.selected_event.players = players
        self.selected_event.enemy_players = enemy_players
        self.selected_event.start_idx = self.event_start_frame
        self.selected_event.end_idx = self.event_end_frame


    def delete_edited_event(self, event_manager):
        deleted_rows = None

        if self.selected_event is None:
            return deleted_rows

        event_name = self.selected_event.name
        event_type = self.selected_event.type

        # Delete:
        header = 'Подтвереждение удаления ивента'
        message = 'Вы действительно хотите удалить событие:\n   {}  [{}]'.format(event_name, event_type)
        if show_conformation_window(header, message):
            if event_manager.delete_event(event_type, event_name):
                # Find raw index:
                for i, event in enumerate(self.event_list):
                    if event[EventTableNames.TYPE] == event_type and event[EventTableNames.NAME] == event_name:
                        deleted_rows = [i]
                        break

                return deleted_rows

        return None


    def set_event_layout_visibility(self, visible=True):
        self.window['-EDIT_EVENT_LAYOUT-'].update(visible=visible)
        self.selected_event = None
        self.event_end_frame = None
        self.event_start_frame = None


    def refresh_event_table(self, event_manager, video_fps, select_rows=None, select_event=None):
        # Update event list:
        self.event_list = []
        for event_type, events in event_manager.events.items():
            for event in events.values():
                start_time = frame_id_to_time_stamp(event.start_idx, video_fps)
                end_time = frame_id_to_time_stamp(event.end_idx, video_fps) if event.end_idx is not None else '-'
                team_name = event_manager.teams[event.team_key] if event.team_key is not None else '-'
                self.event_list.append(
                    [start_time, end_time, event.name, event.type, team_name, 'Нет', event.start_idx, event.end_idx]
                )
        self.event_list = sorted(self.event_list, key=lambda x: x[0], reverse=True)

        # Selet row:
        if select_event is not None:
            select_rows = (select_event.type, select_event.name)
        if select_rows is not None:
            if isinstance(select_rows, tuple):
                event_type, event_name = select_rows
                for i, event in enumerate(self.event_list):
                    if event[EventTableNames.TYPE] == event_type and event[EventTableNames.NAME] == event_name:
                        select_rows = [i]
                        break
            elif len(self.event_list) <= select_rows[0]:
                select_rows = [len(self.event_list)-1] if len(self.event_list) > 0 else None

        # Update table:
        self.window['-EVENT_TABLE-'].update(values=self.event_list, select_rows=select_rows)


    def clean_evant_table(self):
        self.event_list = []
        self.window['-EVENT_TABLE-'].update(values=self.event_list)


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

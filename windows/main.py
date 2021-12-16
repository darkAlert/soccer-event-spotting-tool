import platform
import PySimpleGUI as sg
from PySimpleGUI import TITLE_LOCATION_TOP

from event_manager import EventManager
from windows.utils import frame_id_to_time_stamp, show_conformation_window
from event_types import EventTypes


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
    def __init__(self, event_types : EventTypes, video_dir=''):
        self._new_events = {}
        self.event_list = []
        self.selected_event = None
        self.window = self.create_window(event_types, video_dir)
        print (platform.system())
        self._osx = False if 'Linux' in platform.system() or 'Windows' in in platform.system() else True


    def create_window(self, event_types : EventTypes, video_dir : str):
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

        # Create slider:
        sg_slider = sg.Slider(
            range=(0, 0),
            key='-SLIDER-',
            default_value=0,
            size=(40, 15),
            orientation='horizontal',
            font=('Helvetica', 12),
            enable_events=True,
            disable_number_display=True,
            disabled=True,
            expand_x=True
        )
        # Create navigation panel:
        navigation_panel = [
            sg.Column([[
                sg.Button('◼️', key='button_play', size=(2, 1)),
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
        # Create event table:
        sg_event_table = sg.Table(
            values=[['','','','','','','']],
            headings=['ID', 'Тип', 'Команда', 'Начало', 'Конец'],
            max_col_width=25,
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

        # Left column (screen + slider + event_table):
        sg_left_column = sg.Column([
            [sg.Image(key='image_canvas')],
            [sg_slider],
            navigation_panel,
            [sg_event_table]
            ], vertical_alignment = 'top', expand_x=False, expand_y=True
        )

        # Right column (event_creation + event_editing panels):
        event_creation_layout, self._new_events = self.create_layout_event_creation(event_types)
        sg_right_column = sg.Column([
            [sg.Frame('', event_creation_layout,
                      element_justification='center', vertical_alignment='top', expand_x=True, border_width=1)],
            [sg.Frame('', self.create_layout_edit_event(), key='-EDIT_EVENT_LAYOUT-',
                      element_justification='center', vertical_alignment='top', visible=True, expand_x=True, border_width=1)]
            ], vertical_alignment='top', expand_x=False, expand_y=True, vertical_scroll_only=True, scrollable=True
        )

        # All the stuff inside the window:
        layout = [
            [sg_menu],
            [sg_file_browse],
            [sg_left_column, sg_right_column]
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


    def press_event_creation_button(self, event_manager : EventManager, frame_id : int, button_key : str):
        assert button_key in self._new_events
        event_id = self._new_events[button_key]

        if event_id is None:
            # Create new event:
            e_supertype, e_type = button_key.split('=')[-1].split('+')[:]
            event = event_manager.create_event(supertype=e_supertype, type=e_type, start_idx=frame_id)
            self.selected_event = event
            self._new_events[button_key] = event.event_id
            self._recolor_button(self.window[button_key], highlight=True)
        else:
            # Finish current event:
            self.selected_event = event_manager.update_event(event_id, end_idx=frame_id)
            self._new_events[button_key] = None
            self._recolor_button(self.window[button_key], highlight=False)


    def refresh_edit_event_layout(self, event_manager, video_fps, selected_row):
        if len(selected_row) == 0:
            self.selected_event = None
            return

        # Find event:
        selected_row_id = int(selected_row[0])
        event_id = self.event_list[selected_row_id][0]
        self.selected_event = event_manager.get_event(event_id)

        # Event type:
        supertype = event_manager.event_types.supertypes[self.selected_event.supertype]
        event_type = '{} - {}'.format(supertype.alias, supertype.types[self.selected_event.type].alias)

        # Refresh data in the panel:
        self.window['-EDIT_EVENT_ID-'].update(self.selected_event.event_id)
        self.window['-EDIT_EVENT_TYPE-'].update(event_type)
        self.window['-EDIT_EVENT_TEAM-'].update(
            values = [team_name for team_name in event_manager.teams.values()],
            value = event_manager.teams[self.selected_event.team_key]
        )
        self.window['-EDIT_EVENT_PLAYERS-'].update(self.selected_event.players)
        self.window['-EDIT_EVENT_ENEMY_PLAYERS-'].update(self.selected_event.enemy_players)
        self.window['-EDIT_EVENT_START_ZONE-'].update(self.selected_event.start_zone if self.selected_event.start_zone is not None else '')
        self.window['-EDIT_EVENT_END_ZONE-'].update(self.selected_event.end_zone if self.selected_event.end_zone is not None else '')
        self.window['-EDIT_EVENT_START_CAUSE-'].update(self.selected_event.start_cause if self.selected_event.start_cause is not None else '')
        self.window['-EDIT_EVENT_END_CAUSE-'].update(self.selected_event.end_cause if self.selected_event.end_cause is not None else '')

        self.window['-EDIT_EVENT_MOVE_TO_START-'].update(
            frame_id_to_time_stamp(self.selected_event.start_idx, video_fps) if self.selected_event.start_idx is not None else 'не задано'
        )
        self.window['-EDIT_EVENT_MOVE_TO_END-'].update(
            frame_id_to_time_stamp(self.selected_event.end_idx, video_fps) if self.selected_event.end_idx is not None else 'не задано'
        )


    def refresh_event_table(self, event_manager, video_fps, select_rows=None):
        # Update event list:
        self.event_list = []
        for event_id, event in event_manager.events.items():
            start_time = frame_id_to_time_stamp(event.start_idx, video_fps)
            end_time = frame_id_to_time_stamp(event.end_idx, video_fps) if event.end_idx is not None else '-'
            team_name = event_manager.teams[event.team_key] if event.team_key is not None else '-'
            supertype = event_manager.event_types.supertypes[event.supertype]
            event_type = '{} - {}'.format(supertype.alias, supertype.types[event.type].alias)
            self.event_list.append(
                [event_id, event_type, team_name, start_time, end_time, event.start_idx, event.end_idx]
            )
        self.event_list = sorted(self.event_list, key=lambda x: x[3], reverse=True)

        # Find event in event table:
        if select_rows is None and self.selected_event is not None:
            for i, event in enumerate(self.event_list):
                if event[0] == self.selected_event.event_id:
                    select_rows = [i]
                    break

        # Selet row:
        if select_rows is not None and len(self.event_list) <= select_rows[0]:
            select_rows = [len(self.event_list)-1] if len(self.event_list) > 0 else None

        # Update table:
        self.window['-EVENT_TABLE-'].update(values=self.event_list, select_rows=select_rows)


    def clean_evant_table(self):
        self.event_list = []
        self.window['-EVENT_TABLE-'].update(values=self.event_list)


    def update_selected_event(self, event_manager, action):
        if self.selected_event is None:
            return False

        if action == '-EDIT_EVENT_TEAM-':
            team_name = self.window['-EDIT_EVENT_TEAM-'].get()
            self.selected_event.team_key = event_manager.team_name_to_key[team_name]
        elif action == '-EDIT_EVENT_PLAYERS-':
            self.selected_event.players = self.window[action].get()
        elif action == '-EDIT_EVENT_ENEMY_PLAYERS-':
            self.selected_event.enemy_players = self.window[action].get()
        elif action == '-EDIT_EVENT_START_ZONE-':
            self.selected_event.start_zone = self.window[action].get()
        elif action == '-EDIT_EVENT_END_ZONE-':
            self.selected_event.end_zone = self.window[action].get()
        elif action == '-EDIT_EVENT_START_CAUSE-':
            self.selected_event.start_cause = self.window[action].get()
        elif action == '-EDIT_EVENT_END_CAUSE-':
            self.selected_event.end_cause = self.window[action].get()

        return True


    def set_event_time(self, video_fps, start_frame=None, end_frame=None):
        if self.selected_event is None:
            return False

        if start_frame is not None:
            self.selected_event.start_idx = start_frame
            self.window['-EDIT_EVENT_MOVE_TO_START-'].update(frame_id_to_time_stamp(start_frame, video_fps))
        if end_frame is not None:
            self.selected_event.end_idx = end_frame
            self.window['-EDIT_EVENT_MOVE_TO_END-'].update(frame_id_to_time_stamp(end_frame, video_fps))

        return True


    def get_selected_event_start_and_end(self):
        if self.selected_event is None:
            return None, None

        return self.selected_event.start_idx, self.selected_event.end_idx


    def get_selected_event(self):
        return self.selected_event


    def delete_edited_event(self, event_manager):
        deleted_rows = None

        if self.selected_event is None:
            return deleted_rows

        event_id = self.selected_event.event_id
        event_type = '{}_{}'.format(self.selected_event.supertype, self.selected_event.type)

        # Delete:
        header = 'Подтвереждение удаления ивента'
        message = 'Вы действительно хотите удалить ивент ID:{} [{}]'.format(event_id, event_type)
        if show_conformation_window(header, message):
            if event_manager.delete_event(event_id):
                # Find row index:
                for i, event in enumerate(self.event_list):
                    if int(event[0]) == event_id:
                        deleted_rows = [i]
                        break
                # Delete event from new_events:
                for button_key, new_event_id in self._new_events.items():
                    if event_id == new_event_id:
                        self._new_events[button_key] = None
                        self._recolor_button(self.window[button_key], highlight=False)
                        break

                return deleted_rows

        return None


    def set_event_layout_visibility(self, visible=True):
        self.window['-EDIT_EVENT_LAYOUT-'].update(visible=visible)
        self.selected_event = None


    def _recolor_button(self, sg_button, highlight):
        if highlight:
            color = ('black', 'lime')
            if self._osx:
                sg_button.update(button_color=color)
            else:
                sg_button.ButtonColor = sg.button_color_to_tuple(color[:2], sg_button.ButtonColor)
                sg_button.TKButton.config(foreground=color[0], activeforeground=color[0])
                sg_button.TKButton.config(background=color[1], activebackground=color[1])
        else:
            color = ('black', '#fdcb52')
            if self._osx:
                sg_button.update(button_color=color)
            else:
                sg_button.ButtonColor = sg.button_color_to_tuple(color, sg_button.ButtonColor)
                sg_button.TKButton.config(foreground=color[0], activeforeground=color[1])
                sg_button.TKButton.config(background=color[1], activebackground=color[0])


    @staticmethod
    def create_layout_event_creation(event_types : EventTypes, buttons_per_raw=3):
        layout = []
        new_event_dict = {}

        for stype_name, stype in event_types.supertypes.items():
            buttons = []
            buttons_in_raw_counter = 0

            # Create event buttons:
            for type_name, type in stype.types.items():
                key = '-CREATE_EVENT={}+{}'.format(stype_name, type_name)
                if buttons_in_raw_counter == 0:
                    buttons.append([])
                buttons[-1].append(sg.Button(type.alias, key=key, auto_size_button=True, border_width=0, font=('',10)))
                buttons_in_raw_counter += 1
                if buttons_in_raw_counter >= buttons_per_raw:
                    buttons_in_raw_counter = 0
                new_event_dict[key] = None

            # Create event group (by supertype):
            layout.append([
                sg.Frame(stype.alias, buttons, element_justification='center',
                         vertical_alignment='top', expand_x=True, title_location=TITLE_LOCATION_TOP,
                         border_width=0, font=('bold',10), title_color='white')
            ])

        return layout, new_event_dict


    @staticmethod
    def create_layout_edit_event():
        # Create columns:
        sg_left_column = [
            [sg.Text('ID ивента:')],
            [sg.Text('Тип ивента:')],
            [sg.Text('Команда:')],
            [sg.Text('Игроки команды:')],
            [sg.Text('Игроки противника:')],
            [sg.Text('Квадрат начала:')],
            [sg.Text('Квадрат завершения:')],
            [sg.Text('Причина начала:')],
            [sg.Text('Причина завершения:')],
            [sg.Text('Время начала:')],
            [sg.Text('Время завершения:')],
        ]
        sg_right_column = [
            [sg.Text('-', key='-EDIT_EVENT_ID-')],
            [sg.Text('-', key='-EDIT_EVENT_TYPE-')],
            [sg.Combo([''], key='-EDIT_EVENT_TEAM-', expand_x=True, readonly=True, enable_events=True)],
            [sg.Input(key='-EDIT_EVENT_PLAYERS-', enable_events=True, border_width=0)],
            [sg.Input(key='-EDIT_EVENT_ENEMY_PLAYERS-', enable_events=True, border_width=0)],
            [sg.Input(key='-EDIT_EVENT_START_ZONE-', enable_events=True, border_width=0)],
            [sg.Input(key='-EDIT_EVENT_END_ZONE-', enable_events=True, border_width=0)],
            [sg.Input(key='-EDIT_EVENT_START_CAUSE-', enable_events=True, border_width=0)],
            [sg.Input(key='-EDIT_EVENT_END_CAUSE-', enable_events=True, border_width=0)],
            [
                sg.Button('Не задано', key='-EDIT_EVENT_MOVE_TO_START-', border_width=0, font=('',8)),
                sg.Button('Установить текущее', key='-EDIT_EVENT_SET_START_TIME-',
                          button_color='aquamarine', border_width=0, font=('',8))
            ],
            [
                sg.Button('Не задано', key='-EDIT_EVENT_MOVE_TO_END-',
                          border_width=0, font=('',8)),
                sg.Button('Установить текущее', key='-EDIT_EVENT_SET_END_TIME-',
                          button_color='aquamarine', border_width=0, font=('',8))
            ]
        ]
        sg_button_delete = [[sg.Button('Удалить', key='-EDIT_EVENT_DELETE-', size=(20, 1), border_width=0)]]

        # Create a layout:
        layout = [
            [sg.Column(sg_left_column), sg.Column(sg_right_column)],
            [sg.HorizontalSeparator()],
            [sg.Text('Ошибка!', text_color='red', font=('Helvetica', 8), key='not_filled', visible=False)],
            [sg.Column(sg_button_delete, justification='center', element_justification='center')]
        ]

        return layout


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

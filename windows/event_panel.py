import PySimpleGUI as sg

from event_manager import EventTypes
from windows.utils import frame_id_to_time_stamp, show_conformation_window


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



class WindowEventPanel:
    '''
    Event Panel Window
    '''
    def __init__(self, event_manager, video_fps):
        self.event_manager = event_manager
        self.video_fps = video_fps
        self.window = self.create_window()
        self.refresh_event_table()


    def close(self):
        self.window.close()

        return None


    def create_window(self):
        # Generate event list of the event table:
        headings = ['Начало', 'Конец', 'Имя события', 'Тип события', 'Команда', 'Завершено']
        self.event_list = [[''.zfill(7),''.zfill(7),''.zfill(30),''.zfill(30),''.zfill(12),''.zfill(6),'']]

        sg_table_event_list = sg.Table(
            values=self.event_list, headings=headings,
            max_col_width=35,
            auto_size_columns=True,
            vertical_scroll_only = True,
            justification='center',
            num_rows=10,
            key='event_table',
            row_height=30,
            def_col_width=10,
            enable_click_events=False,
            enable_events=True,
            right_click_menu=None#['&Right', ['Delete', 'Favourite', 'Reply', 'Copy', 'Edit']]
        )

        sg_button_create_event = [
            sg.Button('Создать новый ивент', key='create_event', size=(20, 1), border_width=5, font='bold')
        ]

        sg_button_list_left = [
            sg.Button('Перейти в начало', key='move_to_event_start', size=(20, 1)),
            sg.Button('Перети в конец', key='move_to_event_end', size=(20, 1)),
        ]
        sg_button_list_right = [
            sg.Button('Редактировать', key='edit_event', size=(20, 1)),
            sg.Button('Удалить', key='delete_event', size=(20, 1))
        ]

        # Create a layout:
        layout = [
            [sg.Column([sg_button_create_event], justification='center')],
            [sg.HorizontalSeparator()],
            [sg.Column([[sg.Text('или выберите ивент из списка:')]], justification='center')],
            [sg.Column([[sg_table_event_list]], justification='center')],
            [sg.Column([sg_button_list_left]), sg.VerticalSeparator(), sg.Column([sg_button_list_right], justification='center')]
        ]

        # Create a window:
        window = sg.Window('Панель ивентов', layout, modal=False, keep_on_top=True, finalize=True, location=(0,0))

        return window


    def refresh_event_table(self, select_rows=None):
        # Update event list:
        self.event_list = []
        for event_type, events in self.event_manager.events.items():
            for event in events.values():
                start_time = frame_id_to_time_stamp(event.start_idx, self.video_fps)
                end_time = frame_id_to_time_stamp(event.end_idx, self.video_fps) if event.end_idx is not None else '-'
                team_name = self.event_manager.teams[event.team_key]
                self.event_list.append(
                    [start_time, end_time, event.name, event.type, team_name, 'Нет', event.start_idx, event.end_idx]
                )
        self.event_list = sorted(self.event_list, key=lambda x: x[0], reverse=True)

        # Selet row:
        if select_rows is not None:
            if isinstance(select_rows, tuple):
                event_type, event_name = select_rows
                for i, event in enumerate(self.event_list):
                    if event[EventTableNames.TYPE] == event_type and event[EventTableNames.NAME] == event_name:
                        select_rows = [i]
                        break
            elif len(self.event_list) <= select_rows[0]:
                select_rows = [len(self.event_list)-1] if len(self.event_list) > 0 else None

        # if select_rows is not None and len(self.event_list) <= select_rows[0]:
        #         select_rows = [len(self.event_list)-1] if len(self.event_list) > 0 else None

        # Update table:
        self.window['event_table'].update(values=self.event_list, select_rows=select_rows)


    def read(self, frame_id):
        w_event, w_values = self.window.read(0)

        # Close:
        if w_event == sg.WIN_CLOSED or w_event == 'Exit':
            return ('close', None)
        # Create new event:
        elif w_event == 'create_event':
            created = self.create_new_event(frame_id)
            if created:
                self.refresh_event_table()
        # ????
        elif w_event == 'event_table':
            selected_row_id = w_values['event_table']
        # Edit event:
        elif w_event == 'edit_event':
            selected_row= w_values['event_table']
            if len(selected_row) > 0:
                selected_row_id = int(selected_row[0])
                event_data = self.event_list[selected_row_id]
                event = self.event_manager.get_event(event_data[EventTableNames.TYPE], event_data[EventTableNames.NAME])
                self.window.keep_on_top_clear()
                edited = self.edit_event(event, frame_id)
                if edited:
                    self.refresh_event_table((event_data[EventTableNames.TYPE], event_data[EventTableNames.NAME]))
                self.window.keep_on_top_set()
            else:
                print ('ВЫБЕРИТЕ СОБЫТИЕ')
        # Delete selected event:
        elif w_event == 'delete_event':
            selected_row = w_values['event_table']
            if len(selected_row) > 0:
                selected_row_id = int(selected_row[0])
                data = self.event_list[selected_row_id]
                event_name = data[EventTableNames.NAME]
                event_type = data[EventTableNames.TYPE]
                header = 'Подтвереждение удаления ивента'
                message = 'Вы действительно хотите удалить событие:\n   {}  [{}]'.format(event_name, event_type)
                self.window.keep_on_top_clear()
                if show_conformation_window(header, message):
                    if self.event_manager.delete_event(event_type, event_name):
                        self.refresh_event_table([selected_row_id])
                self.window.keep_on_top_set()
            else:
                print('ВЫБЕРИТЕ СОБЫТИЕ')
        # Move player to the start of the event:
        elif w_event == 'move_to_event_start':
            selected_row = w_values['event_table']
            if len(selected_row) > 0:
                selected_row_id = int(selected_row[0])
                data = self.event_list[selected_row_id]
                if data[EventTableNames.START_IDX] is not None:
                    return ('move_to', data[EventTableNames.START_IDX])
        # Move player to the end of the event:
        elif w_event == 'move_to_event_end':
            selected_row = w_values['event_table']
            if len(selected_row) > 0:
                selected_row_id = int(selected_row[0])
                data = self.event_list[selected_row_id]
                if data[EventTableNames.END_IDX] is not None:
                    return ('move_to', data[EventTableNames.END_IDX])

        return ('continue', None)


    def edit_event(self, event, frame_id):
        new_start_time_idx, new_end_time_idx = None, None
        event_start_time = \
            frame_id_to_time_stamp(event.start_idx, self.video_fps) if event.start_idx is not None else 'не задано'
        event_end_time = \
            frame_id_to_time_stamp(event.end_idx, self.video_fps) if event.end_idx is not None else 'не задано'

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
            [sg.Text(EventTypes.type2alias(event.type), key='event_type_alias')],
            [sg.Text(event.name)],
            [sg.Combo(
                [self.event_manager.teams['home_team'], self.event_manager.teams['away_team']],
                default_value=self.event_manager.teams[event.team_key], key='team_name')
            ],
            [sg.Input(default_text=event.players, key='players')],
            [sg.Input(default_text=event.enemy_players, key='enemy_players')],
            [
                sg.Text(event_start_time, key='start_time'),
                sg.Button('Установить текущее', key='set_current_start_time', size=(18, 1), button_color='green')
            ],
            [
                sg.Text(event_end_time, key='end_time'),
                sg.Button('Установить текущее', key='set_current_end_time', size=(18, 1), button_color='green')
            ]
        ]
        sg_button_list = [[
            sg.Button('Отмена', key='cancel', size=(20, 1)), sg.Button('Сохранить', key='save', size=(20, 1))
        ]]

        # Create a layout:
        layout = [
            [sg.Column(sg_left_column), sg.Column(sg_right_column)],
            [sg.HorizontalSeparator()],
            [sg.Text('Ошибка!', text_color='red', font=('Helvetica', 10), key='not_filled', visible=False)],
            [sg.Column(sg_button_list, justification='center')]
        ]

        # Create a window:
        window = sg.Window('Редактирование ивента', layout, keep_on_top=True, modal=True, finalize=True)

        # Window events:
        while True:
            w_event, w_values = window.read(timeout=0)

            # Close and exit:
            if w_event == sg.WIN_CLOSED or w_event == 'Exit' or w_event == 'cancel':
                break
            # Set start time on current one:
            elif w_event == 'set_current_start_time':
                new_start_time_idx = frame_id
                window['start_time'].update(frame_id_to_time_stamp(frame_id, self.video_fps))
                # Set start time on current one:
            elif w_event == 'set_current_end_time':
                new_end_time_idx = frame_id
                window['end_time'].update(frame_id_to_time_stamp(frame_id, self.video_fps))
            # Save changes:
            elif w_event == 'save':
                # Check start and stop time:
                cur_start_time_idx = new_start_time_idx if new_start_time_idx is not None else event.start_idx
                cur_end_time_idx = new_end_time_idx if new_end_time_idx is not None else event.end_idx
                if cur_start_time_idx is not None and cur_end_time_idx is not None \
                        and cur_end_time_idx < cur_start_time_idx is not None:
                    header = 'Несоответствие начала и конца события'
                    message = 'Время конца события меньше чем время его начала:\n{} > {}\n Хотите продолжить?'\
                        .format(window['start_time'].get(), window['end_time'].get())
                    window.keep_on_top_clear()
                    if show_conformation_window(header, message) == False:
                        window.keep_on_top_set()
                        continue
                    window.keep_on_top_set()

                team_name = w_values['team_name']
                players = w_values['players']
                enemy_players = w_values['enemy_players']

                event.team_key = self.event_manager.team_name_to_key[team_name]
                event.players = players
                event.enemy_players = enemy_players
                if new_start_time_idx is not None:
                    event.start_idx = new_start_time_idx
                if new_end_time_idx is not None:
                    event.end_idx = new_end_time_idx

                window.close()
                return True

        window.close()
        return False


    def create_new_event(self, frame_id):
        # Create a list of the event types:
        colum_event_alias_list = sg.Column([
            [sg.Listbox(values=[t['alias'] for t in EventTypes.types()], key='event_alias_list', size=(30, 14),
                        enable_events=True)]
        ], justification='center')

        # Create columns:
        column1 = sg.Column([
            [sg.Text('Тип ивента:')],
            [sg.Text('Имя ивента:')],
            [sg.Text('Команда:')],
            [sg.Text('Игроки команды:')],
            [sg.Text('Игроки противника:')],
            [sg.Text('Начало ивента:')],
            [sg.Text('Конец ивента:')]
        ])
        column2 = sg.Column([
            [sg.Text('', key='event_type_alias')],
            [sg.Input(key='event_name')],
            [sg.Combo([self.event_manager.teams['home_team'], self.event_manager.teams['away_team']], key='team_name')],
            [sg.Input(key='players')],
            [sg.Input(key='enemy_players')],
            [sg.Text(frame_id_to_time_stamp(frame_id, self.video_fps))],
            [sg.Text('Не задано')]
        ])

        # Create a layout:
        layout = [
            [colum_event_alias_list],
            [column1, column2],
            [sg.Text('Ошибка!', text_color='red', font=('Helvetica', 10), key='not_filled', visible=False)],
            [sg.Button('Отмена', key='cancel', size=(20, 1)), sg.Button('Создать', key='create', size=(20, 1))]
        ]

        # Create a window:
        window = sg.Window('Создание нового ивента', layout, keep_on_top=True, modal=True, finalize=True)

        # Window events:
        while True:
            w_event, w_values = window.read(timeout=0)

            # Close and exit:
            if w_event == sg.WIN_CLOSED or w_event == 'Exit' or w_event == 'cancel':
                break
            # Select event type (alias):
            elif w_event == 'event_alias_list':
                e_type_alias = w_values['event_alias_list'][0]
                window['event_type_alias'].update(e_type_alias)
                # Generate event name:
                e_type = EventTypes.alias2type(e_type_alias)
                base_name = e_type_alias.replace(' - ', '_').replace(' ', '_')
                e_name = ''
                for i in range(1, 9999):
                    name = base_name + '_{}'.format(str(i))
                    if self.event_manager.get_event(e_type, name) is None:
                        e_name = name
                        break
                window['event_name'].update(e_name)
            # Create new event:
            elif w_event == 'create':
                event_name = w_values['event_name']
                team_name = w_values['team_name']
                players = w_values['players']
                enemy_players = w_values['enemy_players']
                event_type = EventTypes.alias2type(window['event_type_alias'].get())

                if event_type is None:
                    window['not_filled'].update(visible=True, value='Выберите ивент!')
                    continue
                if self.event_manager.get_event(event_type, event_name) is not None:
                    window['not_filled'].update(visible=True, value='Ивент с таким именем уже существует!')
                    continue
                if len(event_name) == 0:
                    window['not_filled'].update(visible=True, value='Введите имя ивента!')
                    continue
                if len(team_name) == 0:
                    window['not_filled'].update(visible=True, value='Выберите команду!')
                    continue
                window['not_filled'].update(visible=False)

                self.event_manager.create_event(event_type, event_name, self.event_manager.team_name_to_key[team_name],
                                                frame_id, players=players, enemy_players=enemy_players)

                window.close()
                return True

        window.close()
        return False
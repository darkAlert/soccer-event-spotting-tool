import os
import argparse
import datetime
from pathlib import Path
from enum import Enum
import numpy as np
import PySimpleGUI as sg

from video_player import VideoPlayer
from fps_manager import FPSManager
from event_manager import EventManager
from windows.main import WindowMain, show_team_setting_window, SPEED_VALUES
from windows.utils import image_np_to_pil, show_conformation_window


class State(Enum):
    NOT_OPEN = 1,
    PLAY = 2,
    PLAY_ONCE = 3,
    PAUSE = 4,
    EXIT = 5


def calculate_frame_size(window_size, max_frame_size=(1280,720), max_ratio=0.7):
    '''
    :param window_size:
    :param max_video_size:
    :param max_ratio:       max ratio of video to window
    :return:
    '''
    target_frame_size = max_frame_size

    r = max_frame_size[0] / window_size[0]
    if r > max_ratio:
        target_frame_size = (int(round(window_size[0]*max_ratio)), int(round(window_size[1]*max_ratio)))

    return target_frame_size


def create_dummy_events(event_manager):
    # Create fake events FOR DEBUG:
    event_manager.create_event('ATTACK', 'Атака_1', 'Спартак', 1000)
    event_manager.create_event('STANDARD_FREEKICK', 'Стандарт_штрафной_удар_1', 'Спартак', 5000)
    event_manager.create_event('DEFENSE_LOW', 'Оборона_низкая_1', 'Динамо', 25000)
    event_manager.create_event('STANDARD_FREEKICK', 'Стандарт_штрафной_удар_2', 'Спартак', 57800)
    event_manager.create_event('PASS_TO_PENALTY_AREA', 'Передача_в_штрафную_соперника_1', 'Динамо', 100300)
    event_manager.create_event('PASS_TO_PENALTY_AREA', 'Передача_в_штрафную_соперника_2', 'Динамо', 130111)

    return event_manager


def get_events_path(video_path):
    p = Path(video_path)
    game_dir = p.parent.absolute()
    game_name = p.stem

    return os.path.join(game_dir, game_name + '_events.json')


def run_player(video_dir):
    # Create GUI windows:
    window_main = WindowMain(video_dir)

    # Instantiate:
    player = VideoPlayer(300)
    fps_manager = FPSManager()
    event_manager = None
    state = State.NOT_OPEN
    pil_img = image_np_to_pil(np.zeros((720,1280,3), dtype=np.uint8))


    # Playing loop:
    while state != State.EXIT:
        real_fps, delay = 0, 0
        if state == State.PLAY:
            real_fps = fps_manager.mesure_fps()
            delay = fps_manager.calulate_delay()

        # Count FPS:
        window_main.window['text_fps'].update(value='FPS: {:.1f}'.format(real_fps))

        # Window events:
        event, values = window_main.window.read(timeout=delay)

        # Close and exit:
        if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT or event == 'Выход':
            if player.is_open():
                header = 'Подтверждение выхода'
                message = 'Вы действительно хотите выйти из программы?'
                confirmed = show_conformation_window(header, message)
                if confirmed:
                    header = 'Подтверждение сохранения в файл'
                    message = 'Сохранить ивенты в файл\n{}'.format(get_events_path(player.path))
                    if show_conformation_window(header, message):
                        event_manager.save(get_events_path(player.path))
                else:
                    continue
            player.release()
            break

        # Open file_browse dialog:
        elif event == 'Открыть...':
            window_main.window.Element('file_browse').TKButton.invoke()
            continue

        # Open video file:
        elif event == 'file_browse':
            video_path = values['file_browse']
            if len(video_path) > 0 and video_path != player.path:
                # Check if need to save event file of the current video:
                if player.is_open():
                    header = 'Подтверждение сохранения в файл'
                    message = 'Сохранить ивенты в файл\n{}?'.format(get_events_path(player.path))
                    if show_conformation_window(header, message):
                        event_manager.save(get_events_path(player.path))
                    # Close current video:
                    player.release()
                    event_manager = None
                    window_main.clean_evant_table()
                    window_main.set_event_layout_visibility(False)
                    fps_manager = FPSManager()
                    pil_img = image_np_to_pil(np.zeros((720, 1280, 3), dtype=np.uint8))
                    window_main.window['image_canvas'].update(data=pil_img)
                    state = State.NOT_OPEN

                # Open new video:
                player.open(video_path)
                if player.is_open():
                    # Set resolution:
                    frame_size = calculate_frame_size(window_main.window.size)
                    player.set_resolution(frame_size[0], frame_size[1])
                    # Load events from file:
                    events_path = None
                    path = get_events_path(player.path)
                    if os.path.exists(path):
                        header = 'Подтверждение загрузки из файла'
                        message = 'Хотите загрузить ивенты из файла\n{}?'.format(path)
                        confirmed =show_conformation_window(header, message)
                        events_path = path if confirmed else None
                    # Create event manager:
                    home_team, away_team = None, None
                    if events_path is None:
                        home_team, away_team = show_team_setting_window()
                        if home_team is None or away_team is None:
                            player.release()
                            continue
                    event_manager = EventManager(home_team, away_team, path=events_path)
                    window_main.window.set_title(player.path)
                    window_main.window['slider_frame_id'].update(disabled=False, range=(0, player.num_frames-1), value=0)
                    window_main.window['combo_speed'].update(disabled=False)
                    fps_manager.reset()
                    fps_manager.set_target_fps(player.video_fps)
                    window_main.window['button_play'].update('⏸')
                    window_main.refresh_event_table(event_manager, player.video_fps)
                    state = State.PLAY_ONCE


        # Change playing speed:
        elif event == 'combo_speed':
            speed = float(SPEED_VALUES[values['combo_speed']])
            target_fps = int(round(player.video_fps*speed))
            fps_manager.set_target_fps(target_fps)

        # Play / Pause:
        elif event == 'button_play':
            if state == State.PLAY:
                state = State.PAUSE
                window_main.window['button_play'].update('▶')
            elif state == State.PAUSE:
                state = State.PLAY
                window_main.window['button_play'].update('⏸')
                fps_manager.reset()

        # Rewind (by slider):
        elif event == 'slider_frame_id':
            next_frame_id = int(values['slider_frame_id'])
            player.rewind(next_frame_id)
            fps_manager.reset()
            if state == State.PAUSE:
                state = State.PLAY_ONCE


        # Save events:
        elif event == 'Сохранить':
            if player.is_open():
                event_manager.save(get_events_path(player.path))

        # EVENT TABLE:
        elif event == '-EVENT_TABLE-' and player.is_open():
            window_main.set_event_layout_visibility(True)
            window_main.refresh_edit_event_layout(event_manager, player.video_fps, values['-EVENT_TABLE-'])

        # EVENT PANEL:
        elif event == '-EDIT_EVENT_SET_START_TIME-' and player.is_open():
            window_main.set_event_time(player.video_fps, start_frame=player.frame_id)
        elif event == '-EDIT_EVENT_SET_END_TIME-' and player.is_open():
            window_main.set_event_time(player.video_fps, end_frame=player.frame_id)
        elif event == '-EDIT_EVENT_MOVE_TO_START-' and player.is_open():
            start_frame, _ = window_main.get_event_start_and_end()
            if start_frame is not None:
                player.rewind(start_frame)
                if state == State.PAUSE:
                    state = State.PLAY_ONCE
        elif event == '-EDIT_EVENT_MOVE_TO_END-' and player.is_open():
            _, end_frame = window_main.get_event_start_and_end()
            if end_frame is not None:
                player.rewind(end_frame)
                if state == State.PAUSE:
                    state = State.PLAY_ONCE
        elif event == '-EDIT_EVENT_SAVE-' and player.is_open():
            window_main.save_edited_event(event_manager)
            selected_event = window_main.get_selected_event()
            window_main.refresh_event_table(event_manager, player.video_fps, select_event=selected_event)
        elif event == '-EDIT_EVENT_RESET-' and player.is_open():
            selected_event = window_main.get_selected_event()
            window_main.refresh_event_table(event_manager, player.video_fps, select_event=selected_event)
        elif event == '-EDIT_EVENT_DELETE-' and player.is_open():
            deleted_rows = window_main.delete_edited_event(event_manager)
            if deleted_rows is not None:
                window_main.refresh_event_table(event_manager, player.video_fps, deleted_rows)
                window_main.set_event_layout_visibility(False)
        elif event == '-CREATE_EVENT-' and player.is_open():
            window_main.create_new_event(event_manager, player.frame_id)
            selected_event = window_main.get_selected_event()
            window_main.refresh_event_table(event_manager, player.video_fps, select_event=selected_event)

        # Read next frame:
        if state == State.PLAY or state == State.PLAY_ONCE:
            frame_size = calculate_frame_size(window_main.window.size)
            stopped, img = player.get_frame(frame_size)
            if img is not None:
                pil_img = image_np_to_pil(img)
            time = str(datetime.timedelta(seconds=int(player.frame_id / player.video_fps)))
            total_time = str(datetime.timedelta(seconds=int(player.num_frames / player.video_fps)))
            window_main.window['text_counter'].update(
                value='{} / {}    {} / {}'.format(time, total_time, player.frame_id, player.num_frames-1)
            )
            if state == State.PLAY_ONCE or stopped:
                state = State.PAUSE
                window_main.window['button_play'].update('▶')

        # Update image on the screen:
        if pil_img is not None:
            window_main.window['image_canvas'].update(data=pil_img)

    window_main.window.close()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_dir", help="path to dir containing videos")

    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    run_player(args.video_dir)
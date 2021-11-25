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
from windows.event_panel import WindowEventPanel
from windows.utils import image_np_to_pil, show_conformation_window


class State(Enum):
    NOT_OPEN = 1,
    PLAY = 2,
    PLAY_ONCE = 3,
    PAUSE = 4,
    EXIT = 5


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
    window_event_panel = None

    # Instantiate:
    player = VideoPlayer()
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
            break

        # Open file_browse dialog:
        elif event == 'Открыть...':
            window_main.window.Element('file_browse').TKButton.invoke()
            continue

        # Open video file:
        elif event == 'file_browse':
            video_path = values['file_browse']
            if len(video_path) > 0:
                # Check if need to save event file of the current video:
                if player.is_open():
                    header = 'Подтверждение сохранения в файл'
                    message = 'Сохранить ивенты в файл\n{}?'.format(get_events_path(player.path))
                    if show_conformation_window(header, message):
                        event_manager.save(get_events_path(player.path))
                    if window_event_panel is not None:
                        window_event_panel = window_event_panel.close()
                # Open new video:
                player.open(video_path)
                if player.is_open():
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
                    state = State.PLAY_ONCE
                    # create_dummy_events(event_manager)       # Create fake events FOR DEBUG!!!!!!!!!!!!!

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

        # Rewind (by slider):
        elif event == 'slider_frame_id':
            next_frame_id = int(values['slider_frame_id'])
            player.rewind(next_frame_id)
            if state == State.PAUSE:
                state = State.PLAY_ONCE

        # Show Event Panel:
        elif event == 'Панель ивентов':
            if window_event_panel is None:
                if player.is_open():
                    window_event_panel = WindowEventPanel(event_manager, player.video_fps)
            else:
                window_event_panel = window_event_panel.close()

        # Save events:
        elif event == 'Сохранить':
            if player.is_open():
                event_manager.save(get_events_path(player.path))

        # elif event == 'Configure':
            # print(player.frame_id, window.size)

        # Read next frame:
        if state == State.PLAY or state == State.PLAY_ONCE:
            playing, img = player.capture()
            if img is not None:
                pil_img = image_np_to_pil(img)
            window_main.window['slider_frame_id'].update(value=player.frame_id)
            time = str(datetime.timedelta(seconds=int(player.frame_id / player.video_fps)))
            total_time = str(datetime.timedelta(seconds=int(player.num_frames / player.video_fps)))
            window_main.window['text_counter'].update(
                value='{} / {}    {} / {}'.format(time, total_time, player.frame_id, player.num_frames-1)
            )
            if state == State.PLAY_ONCE or playing == False:
                state = State.PAUSE
                window_main.window['button_play'].update('▶')

        # Update image on the screen:
        if pil_img is not None:
            window_main.window['image_canvas'].update(data=pil_img)

        # Event Panel events:
        if window_event_panel is not None:
            ret_state, ret_value = window_event_panel.read(player.frame_id)
            if ret_state == 'close':
                window_event_panel = None
            elif ret_state == 'move_to':
                player.rewind(ret_value)
                if state == State.PAUSE:
                    state = State.PLAY_ONCE

    window_main.window.close()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_dir", help="path to dir containing videos")

    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    run_player(args.video_dir)
import json

class EventTypes:
    _types = [
        {'type': 'ATTACK_START', 'alias': 'Атака - начало'},
        {'type': 'ATTACK_DEVELOPMENT', 'alias': 'Атака - развитие'},
        {'type': 'ATTACK_END', 'alias': 'Атака - завершение'},
        {'type': 'DEFENSE_HIGH', 'alias': 'Оборона - высокая'},
        {'type': 'DEFENSE_MEDIUM', 'alias': 'Оборона - в средней зоне'},
        {'type': 'DEFENSE_LOW', 'alias': 'Оборона - низкая'},
        {'type': 'TRANSITION', 'alias': 'Переключение'},
        {'type': 'STANDARD_CORNER', 'alias': 'Стандарт - угловой'},
        {'type': 'STANDARD_FREEKICK', 'alias': 'Стандарт - штрафной удар'},
        {'type': 'STANDARD_OUT', 'alias': 'Стандарт - аут'},
        {'type': 'PASS_FORWARD', 'alias': 'Передача - вперед'},
        {'type': 'PASS_LONG', 'alias': 'Передача - Длинная'},
        {'type': 'PASS_TO_FINAL_THIRD', 'alias': 'Передача - в финальную треть'},
        {'type': 'PASS_TO_PENALTY_AREA', 'alias': 'Передача - в штрафную соперника'},
        {'type': 'PASS_CROSS', 'alias': 'Передача - кросс'},
        {'type': 'LOSS_IN_OWN_HALF', 'alias': 'Потеря - на своей половине'},
        {'type': 'LOSS_IN_ENEMY_HALF', 'alias': 'Потеря - на чужой половине'},
    ]
    _type2alias = {t['type']: t['alias'] for t in _types}
    _alias2type = {t['alias']: t['type'] for t in _types}

    @classmethod
    def types(cls):
        return cls._types

    @classmethod
    def alias2type(cls, alias):
        return cls._alias2type.get(alias, None)

    @classmethod
    def type2alias(cls, type):
        return cls._type2alias.get(type, None)


class Event:
    def __init__(self, type, name, start_idx, team_key='none', end_idx=None, players=None, enemy_players=None):
        assert type is not None and name is not None and start_idx is not None
        self.type = type
        self.name = name
        self.team_key = team_key
        self.players = players if players is not None else []
        self.enemy_players = enemy_players if enemy_players is not None else []
        self.start_idx = start_idx
        self.end_idx = end_idx


class EventManager:
    def __init__(self, home_team=None, away_team=None, path=None):
        assert home_team is not None or away_team is not None or path is not None

        self.events = {event_type['type']: {} for event_type in EventTypes.types()}   # (event_type, (event_name, values))
        if path is not None:
            self.load(path)
        else:
            self.set_teams(home_team, away_team)


    def set_teams(self, home_team, away_team):
        self.teams = {'home_team': home_team, 'away_team': away_team, 'none': 'none'}
        self.team_name_to_key = {home_team: 'home_team', away_team: 'away_team', 'none': 'none'}


    def create_event(self, event_type, event_name, start_idx,
                     team_key='none', end_idx=None, players=None, enemy_players=None):
        if event_name in self.events[event_type]:
            return None
        else:
            event = Event(event_type, event_name, start_idx, team_key, end_idx, players, enemy_players)
            self.events[event_type][event_name] = event
            return event

    def get_event(self, event_type, event_name):
        return self.events[event_type].get(event_name, None)

    def delete_event(self, event_type, event_name):
        event = self.get_event(event_type, event_name)

        if event is None:
            return False
        else:
            del self.events[event_type][event_name]
            return True


    def load(self, path):
        with open(path, 'r') as f:
            data = json.load(f)

        for event in data['events']:
            self.create_event(
                event['type'],
                event['name'],
                event['start_frame'],
                event['team_key'],
                event['end_frame'],
                event['players'],
                event['enemy_players']
            )
        self.set_teams(data['home_team'], data['away_team'])


    def save(self, path):
        event_list = []

        for events in self.events.values():
            for e in events.values():
                event_list.append({
                    'type': e.type,
                    'name': e.name,
                    'team_key': e.team_key,
                    'start_frame': e.start_idx,
                    'end_frame': e.end_idx,
                    'players': e.players,
                    'enemy_players': e.enemy_players
                })

        data = {
            'home_team': self.teams['home_team'],
            'away_team': self.teams['away_team'],
            'events': event_list
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=3)

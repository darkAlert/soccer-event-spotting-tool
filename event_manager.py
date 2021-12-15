import json
from event_types import EventTypes


class Event:
    def __init__(self, event_id, supertype, type, start_idx, end_idx=None, team_key='none',
                 players=None, enemy_players=None, start_cause=None, end_cause=None, start_zone=None, end_zone=None):
        assert supertype is not None and type is not None
        assert event_id is not None and start_idx is not None
        self.event_id = event_id
        self.supertype = supertype
        self.type = type
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.team_key = team_key
        self.players = players if players is not None else []
        self.enemy_players = enemy_players if enemy_players is not None else []
        self.start_cause = start_cause
        self.end_cause = end_cause
        self.start_zone = start_zone
        self.end_zone = end_zone


class EventManager:
    def __init__(self, event_types : EventTypes, home_team=None, away_team=None, path=None):
        assert home_team is not None or away_team is not None or path is not None
        self.event_types = event_types
        self.events = {}
        self._event_counter = 1

        # Load:
        if path is not None:
            self.load(path)
        else:
            self._set_teams(home_team, away_team)


    def _set_teams(self, home_team, away_team):
        self.teams = {'home_team': home_team, 'away_team': away_team, 'none': 'none'}
        self.team_name_to_key = {home_team: 'home_team', away_team: 'away_team', 'none': 'none'}


    def _issue_event_id(self):
        while self._event_counter in self.events:
            self._event_counter += 1
        return self._event_counter


    def create_event(self, supertype, type, start_idx, event_id=None, end_idx=None,
                     team_key='none',players=None, enemy_players=None, start_cause=None,
                     end_cause=None, start_zone=None, end_zone=None):
        if event_id is None:
            event_id = self._issue_event_id()
        elif event_id in self.events:
            print ('[Warning] Event with the same ID{} already exists'.format(event_id))
            return None

        self.events[event_id] = Event(
            event_id=event_id,
            supertype=supertype,
            type=type,
            start_idx=start_idx,
            end_idx=end_idx,
            team_key=team_key,
            players=players,
            enemy_players=enemy_players,
            start_cause=start_cause,
            end_cause=end_cause,
            start_zone=start_zone,
            end_zone=end_zone
        )

        return self.events[event_id]


    def update_event(self, event_id, start_idx=None, end_idx=None, team_key=None, players=None, enemy_players=None,
                     start_cause=None, end_cause=None, start_zone=None, end_zone=None):
        event = self.get_event(event_id)
        assert event is not None

        if start_idx is not None:
            event.start_idx = start_idx
        if end_idx is not None:
            event.end_idx = end_idx
        if team_key is not None:
            event.team_key = team_key
        if players is not None:
            event.players = players
        if enemy_players is not None:
            event.enemy_players = enemy_players
        if start_cause is not None:
            event.start_cause = start_cause
        if end_cause is not None:
            event.end_cause = end_cause
        if start_zone is not None:
            event.start_zone = start_zone
        if end_zone is not None:
            event.end_zone = end_zone

        return event


    def get_event(self, event_id):
        return self.events.get(event_id, None)


    def delete_event(self, event_id):
        event = self.get_event(event_id)
        if event is None:
            return False
        else:
            del self.events[event_id]
            return True


    def load(self, path):
        self.events2 = {}

        # Load:
        with open(path, 'r') as f:
            data = json.load(f)

        if 'event_types_version' in data and data['event_types_version'] != self.event_types.version:
            print ('[Warning] Version mismatch between loaded events and current event_types ({}!={})!'.
                   format(data['event_types_version'], self.event_types.version))

        # Create events:
        for event_id, event in data['events'].items():
            self.create_event(
                event_id=int(event_id),
                supertype=event['supertype'],
                type=event['type'],
                start_idx=event['start_frame'],
                end_idx=event['end_frame'],
                team_key=event['team_key'],
                players=event['players'],
                enemy_players=event['enemy_players'],
                start_cause=event.get('start_cause', None),
                end_cause=event.get('end_cause', None),
                start_zone=event.get('start_zone', None),
                end_zone=event.get('end_zone', None),
            )

        # Set team names:
        self._set_teams(data['home_team'], data['away_team'])


    def save(self, path):
        # Create event dictionary:
        event_dict = {}
        for event_id, e in self.events.items():
            event = {
                'supertype': e.supertype,
                'type': e.type,
                'team_key': e.team_key,
                'start_frame': int(e.start_idx) if e.start_idx is not None else None,
                'end_frame': int(e.end_idx) if e.end_idx is not None else None,
                'players': e.players,
                'enemy_players': e.enemy_players
            }
            # Add optional values:
            if e.start_cause is not None:
                event['start_cause'] = e.start_cause
            if e.end_cause is not None:
                event['end_cause'] = e.end_cause
            if e.start_zone is not None:
                event['start_zone'] = e.start_zone
            if e.end_zone is not None:
                event['end_zone'] = e.end_zone

            event_dict[event_id] = event

        # Save:
        data = {
            'home_team': self.teams['home_team'],
            'away_team': self.teams['away_team'],
            'event_types_version': self.event_types.version,
            'events': event_dict
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=3)

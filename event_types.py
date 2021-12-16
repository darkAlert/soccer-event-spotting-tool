import json


class EventSupertype:
    def __init__(self, supertype, alias):
        self.supertype = supertype
        self.alias = alias
        self.types = {}


class EventSubtype:
    def __init__(self, supertype : str, type : str, alias : str,
                 start_causes : dict=None, end_causes : dict=None):
        self.supertype = supertype
        self.type = type
        self.alias = alias
        self.start_causes = start_causes
        self.end_causes = end_causes


class EventTypes:
    def __init__(self, types_path='./assets/event_types.json'):
        self.supertypes, self.version = self.open(types_path)

    @staticmethod
    def open(path):
        with open(path, 'r', encoding="utf8") as f:
            data = json.load(f)

        supertypes = {}
        for stype_name, stype in data['supertypes'].items():
            supertypes[stype_name] = EventSupertype(supertype=stype_name, alias=stype['alias'])

            for type_name, type in stype['types'].items():
                supertypes[stype_name].types[type_name] = EventSubtype(
                    supertype=stype_name,
                    type=type_name,
                    alias=type['alias'],
                    start_causes=type['start_causes'],
                    end_causes=type['end_causes']
                )

        return supertypes, data['version']
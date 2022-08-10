import dataclasses
import json

class EnhancedJSONEncoder(json.JSONEncoder):
    """https://stackoverflow.com/a/51286749/1779707
    """

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
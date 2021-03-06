from nbh_main.settings import logger

class Build:

    DEFAULTS = {
        'name': None,
        'script': None,
        'result_folder': '.',
        'mount_as': '{self.name}',
        'entry_point': 'index.html'
    }

    def __init__(self, yaml_d):
        for field in self.DEFAULTS:
            if field in yaml_d:
                setattr(self, field, yaml_d[field])
            elif self.DEFAULTS[field] is None:
                logger.error(f"ERROR: missing field {field} in Build")
            elif '{' in self.DEFAULTS[field]:
                # it's important that the DEFAULTS dict comes in order
                setattr(self, field, self.DEFAULTS[field].format(self=self))
            else:
                setattr(self, field, self.DEFAULTS[field])

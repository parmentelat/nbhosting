from nbh_main.settings import logger

class YamlRecord:

    # define for each subclass
    # DEFAULTS = dict(
    #    mandatory_field: None,
    #    optional_field: default_value,
    # }
    # a default may use a field defined previously
    # by referencing e.g. {self.name}
    def __init__(self, yaml_d):
        dup = dict()
        # accept keys with a - as if they were with a _
        for key in yaml_d:
            new_key = key.replace('-', '_')
            dup[new_key] = yaml_d[key]
        yaml_d = dup
        for key in yaml_d:
            if key not in self.DEFAULTS:
                raise ValueError(f"unexpected key {key} for class {type(self).__name__}")
        for field in self.DEFAULTS:
            if field in yaml_d:
                setattr(self, field, yaml_d[field])
            elif self.DEFAULTS[field] is None:
                raise ValueError(f"ERROR: missing field {field} in {type(self).__name__}")
            elif '{' in self.DEFAULTS[field]:
                # it's important that the DEFAULTS dict comes in order
                setattr(self, field, self.DEFAULTS[field].format(self=self))
            else:
                setattr(self, field, self.DEFAULTS[field])


class Build(YamlRecord):
    DEFAULTS = {
        'name': None,
        'script': None,
        'result_folder': '.',
        'mount_as': '{self.name}',
        'entry_point': 'index.html'
    }

from pathlib import Path

from nbh_main.settings import logger

class StaticMapping:

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], str):
            [line] = args
            self._init_from_line(line)
        elif len(args) == 2 and all(isinstance(x, str) for x in args):
            src, dest = args
            self._init_from_src_dest(src, dest)

    def _init_from_src_dest(self, src, dest):
        self.local, self.from_top = src, dest
        self.valid = True

    def _init_from_line(self, line):
        """
        each non-comment line in nbhosting/static-mappings
        results in one valid instance
        """
        try:
            line = line.strip()
            if '#' in line:
                self.valid = False
            else:
                left, right = line.split("->")
                self.local, self.from_top = left.strip(), right.strip()
                self.valid = True
        except:
            logger.exception(f"Could not read static mapping {line}")
            self.local = self.from_top = None
            self.valid = False

    def __repr__(self):
        return f"{self.local} -> {self.from_top}"

    # ignore the ones that are broken
    def __bool__(self):
        return self.valid

    # for displaying in a web page
    def html(self):
        return (f'<span class="mapping from">{self.local}</span>'
                f'<span class="mapping to">{self.from_top}</span>')

    # this is used in the nbh shell script
    def expose(self, coursedir):
        return f"{self.from_top}::{self.local}"

    @staticmethod
    def defaults():
        """
        returns the built-in defaults for when a course
        has no mapping defined, or it is broken
        """
        return [
            StaticMapping("media -> media"),
            StaticMapping("data -> data"),
        ]

    @staticmethod
    def static_toplevels(mappings):
        """
        given a list of mappings, computes the consolidated
        list of first-level directories involved at least once
        these will need to be exposed in the static/ directory
        """
        return {Path(mapping.from_top).parts[0] for mapping in mappings}

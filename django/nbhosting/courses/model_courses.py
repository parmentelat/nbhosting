from pathlib import Path
import subprocess

from nbh_main.settings import sitesettings

NBHROOT = Path(sitesettings.nbhroot)


class CoursesDir:

    def __init__(self):
        subdirs = (NBHROOT / "courses-git").glob("*")
        self._coursenames = sorted(
            subdir.name for subdir in subdirs)

    def coursenames(self):
        return self._coursenames

# pylint: disable=c0111

from pathlib import Path
from collections import defaultdict

import nbformat

from nbhosting.main.settings import logger, DEBUG


class Sections(list):

    def __init__(self, sections):
        super().__init__(sections)
        self.unknown_section = None

    def add_unknown(self, notebook):
        # we need at least one section instance
        # to figure the coursedir
        if not self:
            logger.error("need at least one section to call Sections.add_unknown")
            return
        coursedir = self[0].coursedir
        if not self.unknown_section:
            self.unknown_section = Section(coursedir, "Unknown", [])
            self.append(self.unknown_section)
        self.unknown_section.notebooks.append(notebook)

    def __repr__(self):
        result = f"{len(self)} sections"
        if self:
            result += f" on {self[0].coursedir}xs"
        return result

    def dump(self, logger):
        for section in self:
            logger.info(f"Section {section} has {len(section)} nbs")
            for notebook in section.notebooks:
                logger.info(f"{section} → {notebook}")


class Section:                                          # pylint: disable=r0903

    def __init__(self, name, coursedir, notebooks):
        """
        notebooks are relative paths from a common coursedir
        """
        self.name = name
        self.coursedir = coursedir
        self.notebooks = notebooks

    def __repr__(self):
        return (f"{self.coursedir}:{self.name}"
                f" ({len(self.notebooks)} nbs)")

    def __len__(self):
        return len(self.notebooks)

    # for templating
    def length(self):
        return len(self)

    def spot_notebook(self, path):
        # may be a Path instance
        path = str(path)
        for notebook in self.notebooks:
            if notebook.clean_path() == path:
                return notebook



class Notebook:                                         # pylint: disable=r0903

    """
    path is a relative path from coursedir
    """

    def __init__(self, coursedir, path):
        self.coursedir = coursedir
        self.path = path
        self.in_course = None
        self.in_student = None
        self._notebookname = None
        self._version = None

    def __repr__(self):
        result = ""
        result += f"{self.path} in {self.coursedir.coursename}"
        if self._notebookname:
            result += f" ({self.notebookname})"
        if self._version:
            result += f" [self.version]"
        return result


    def absolute(self):
        return (self.coursedir.notebooks_dir / self.path).absolute()


    # a Path instance does not seem
    # to please the templating engine
    def clean_path(self):
        clean = str(self.path).replace(".ipynb", "")
        return clean


    def _get_notebookname(self):
        if self._notebookname is None:
            self._read_embedded()
        return self._notebookname

    notebookname = property(_get_notebookname)


    def _read_embedded(self):
        try:
            with self.absolute().open() as feed:
                nb = nbformat.read(feed, nbformat.NO_CONVERT)
                self._notebookname = nb['metadata']['notebookname']
                self._version = nb['metadata']['version']
        except:
            self._notebookname = self.path
            self._version = "n/a"



##### helpers to build manual sectioning
def notebooks_by_pattern(coursedir, pattern):
    """
    return a sorted list of all notebooks (relative paths)
    matching some pattern from coursedir
    """
    logger.debug(
        f"notebooks_by_pattern in {coursedir} with {pattern}")
    root = Path(coursedir.notebooks_dir).absolute()
    absolutes = root.glob(pattern)
    probed = [path.relative_to(root) for path in absolutes]
    notebooks = [Notebook(coursedir, path) for path in probed]
    notebooks.sort(key=lambda n: n.path)
    return notebooks


def sections_by_directory(coursedir, notebooks):
    """
    from a list of relative paths, returns a list of
    Section objects corresponing to directories
    """
    logger.debug(f"sections_by_directory in {coursedir}")
    root = coursedir.notebooks_dir

    hash_per_dir = defaultdict(list)

    for notebook in notebooks:
        hash_per_dir[notebook.absolute().parent].append(notebook)

    result = []

    for absolute, notebooks_per_dir in hash_per_dir.items():
        result.append(
            Section(name=absolute.relative_to(root),
                    coursedir=coursedir,
                    notebooks=notebooks_per_dir))

    result.sort(key=lambda s: s.name)
    for section in result:
        section.notebooks.sort(key=lambda n: n.path)
    return Sections(result)

def default_sectioning(coursedir):
    """
    From a toplevel directory, this function scans for all subdirs that
    have at least one notebook; this is used to create a generic sectioning

    result will contain one Section instance per such directory,
    ordered alphabetically. similarly the notebooks in a Section instance
    are sorted alphabetically
    """
    return sections_by_directory(
        coursedir,
        notebooks_by_pattern(coursedir, "**/*.ipynb"))

# pylint: disable=c0111, w1203

from pathlib import Path
from collections import defaultdict

import nbformat

from nbhosting.main.settings import logger, DEBUG


DEFAULT_TRACK = "course"


class Sections(list):

    def __init__(self, coursedir, sections):
        self.coursedir = coursedir
        super().__init__(sections)
        #
        self.unknown_section = None
        self._marked = False

    # initial intention here was to be able to show student
    # notebooks that were not in the course
    # it needs more work obviously, so let's turn it off for now
    def add_unknown(self, notebook):
        logger.error("Sections.add_unknown needs more work - ignoring")
        return

        coursedir = self.coursedir
        if not self.unknown_section:
            self.unknown_section = Section(coursedir, "Unknown", [])
            self.append(self.unknown_section)
        self.unknown_section.notebooks.append(notebook)

    def __repr__(self):
        result = f"{len(self)} sections"
        # self is a list, this tests if we have at least one son
        if self:
            result += f" on {self[0].coursedir}"
        return result

    def spot_notebook(self, path):
        # may be a Path instance
        path = str(path)
        for section in self:
            spotted = section.spot_notebook(path)
            if spotted:
                return spotted
        return None

    def mark_notebooks(self, student):
        if self._marked:
            return
        coursedir = self.coursedir
        for section in self:
            for notebook in section.notebooks:
                notebook.in_course = True

        # read student dir
        read_notebook_paths = set(
            coursedir.probe_student_notebooks(student))

        # mark corresponding notebook instances as read
        for read_path in read_notebook_paths:
            spotted = self.spot_notebook(read_path)
            if spotted:
                spotted.in_student = True
            else:
                # existing in the student tree, but not in the track
                odd_notebook = Notebook(coursedir, read_path)
                odd_notebook.in_student = True
                # turn this off for now
                # self.add_unknown(odd_notebook)
        self._marked = True


    def dumps(self):
        """
        return a pure python object that can be json-stored,
        and that contain enough to rebuild the structure entirely
        """
        return dict(
            sections=[section.dumps() for section in self],
            )

    @staticmethod
    def loads(coursedir, d: dict):
        sections = [Section.loads(coursedir, s) for s in d['sections']]
        return Sections(coursedir, sections)


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
        for notebook in self.notebooks:
            if notebook.clean_path() == path:
                return notebook
        return None

    def dumps(self):
        return dict(
            name=str(self.name),
            notebooks=[notebook.dumps() for notebook in self.notebooks]
            )

    @staticmethod
    def loads(coursedir, d: dict):
        restored = Section(
            name=d['name'],
            coursedir=coursedir,
            notebooks=[])
        restored.notebooks = [
            Notebook.loads(coursedir, n) for n in d['notebooks']
        ]
        return restored


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


    def _get_notebookname(self):
        if self._notebookname is None:
            self._read_embedded()
        return self._notebookname
    notebookname = property(_get_notebookname)

    def _get_version(self):
        if self._version is None:
            self._read_embedded()
        return self._version
    version = property(_get_version)


    def absolute(self):
        return (self.coursedir.notebooks_dir / self.path).absolute()

    # a Path instance does not seem
    # to please the templating engine
    def clean_path(self):
        clean = str(self.path).replace(".ipynb", "")
        return clean

    def classes(self):
        classes = []
        if self.in_course:
            classes.append('in-course')
        if self.in_student:
            classes.append('in-student')
        return " ".join(classes)

    def _read_embedded(self):
        try:
            with self.absolute().open() as feed:
                nb = nbformat.read(feed, nbformat.NO_CONVERT)
                self._notebookname = nb['metadata']['notebookname']
                self._version = nb['metadata']['version']
        except:
            self._notebookname = self.clean_path()
            self._version = "n/a"


    def dumps(self):
        return dict(
            path=str(self.path),
            in_course=self.in_course,
            notebookname=self.notebookname,
            version=self.version
        )

    @staticmethod
    def loads(coursedir, d: dict):
        restored = Notebook(
            coursedir=coursedir,
            path=d['path'])
        if d['notebookname']:
            restored._notebookname = d['notebookname']
        if d['version']:
            restored._version = d['version']
        return restored



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


def sections_by_directory(coursedir, notebooks,
                          *, dir_labels=None):
    """
    from a list of relative paths, returns a list of
    Section objects corresponing to directories

    optional dir_labels allows to provide a mapping
    "dirname" -> "displayed name"
    """

    def mapped_name(dirname):
        dirname = str(dirname)
        if not dir_labels:
            return dirname
        return dir_labels.get(dirname, dirname)

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

    # sort *before* applying the name mapping
    result.sort(key=lambda s: s.name)
    for section in result:
        section.name = mapped_name(section.name)
        section.notebooks.sort(key=lambda n: n.path)
    return Sections(coursedir, result)

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

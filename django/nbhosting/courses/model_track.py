# pylint: disable=c0111, w1203

from pathlib import Path
from collections import defaultdict
from typing import List

import jsonpickle
import nbformat

from nbh_main.settings import logger

# as of 2019 aug, we don't worry at all about untracked notebooks
# that can be entirely managed through a regular jupyter app

class Notebook:                                         # pylint: disable=r0903

    """
    path is a relative path from coursedir
    """

    def __init__(self, coursedir, path):
        self.coursedir = coursedir
        self.path = path
        self.in_track = None
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


    # customize jsonpickle output
    def __getstate__(self):
        return dict(path=self.path,
                    _notebookname=self._notebookname,
                    _version=self._version)

    # coursedir restored by read_tracks
    def __setstate__(self, state):
        self.__dict__.update(state)
        # if it's saved it means it's in the course
        self.in_track = True
        self.in_student = None


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
        if self.in_track:
            classes.append('in-track')
        if self.in_student:
            classes.append('in-student')
        return " ".join(classes)

    def decorate_a(self, main_tooltip=None):
        """
        a convenience that decorates the inside of a <a> tag
        to point at that notebook
        """
        if main_tooltip is None:
            main_tooltip = self.notebookname

        result = ""
        result += f''' data-toggle="tooltip" data-html="true"'''
        result += f''' title="'''
        if main_tooltip:
            result +=  f'''{main_tooltip}<br/>'''
        result += f'''<span class='smaller'>{self.clean_path()}</span>"'''
        return result

    def _read_embedded(self):
        try:
            with self.absolute().open() as feed:
                nbo = nbformat.read(feed, nbformat.NO_CONVERT)
                self._notebookname = (
                    nbo['metadata'].get('notebookname', self.clean_path()))
                self._version = (
                    nbo['metadata'].get('version', '0.1'))
        except:
            logger.exception(
                f"failed to extract metadata for notebook {self.clean_path()} ")
            self._notebookname = self.clean_path()
            self._version = "n/a"


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

    # customize jsonpickle output
    def __getstate__(self):
        return dict(notebooks=self.notebooks,
                    name=self.name)

    # coursedir restored by read_tracks
    # so no need for setstate


    def first_notebook(self):
        return self.notebooks[0]

    # can't seem to use section.notebooks[0].decorate_a in template
    def decorate_a(self):
        return self.first_notebook().decorate_a("")

    def spot_notebook(self, path):
        for notebook in self.notebooks:
            if notebook.clean_path() == path:
                return notebook
        return None


class Track:

    def __init__(self, coursedir, sections: List['Section'],
                 *, name="default", description="no description"):
        self.coursedir = coursedir
        self.sections = sections
        self.name = name
        self.description = description
        # a flag that says if we've been through
        # mark_notebooks already or not
        self._marked = False


    # customize jsonpickle output
    def __getstate__(self):
        return dict(sections=self.sections,
                    name=self.name,
                    description=self.description)

    # coursedir restored by read_tracks
    def __setstate__(self, state):
        self.__dict__.update(state)
        # when restoring from the cache we need
        # to redo the marking process
        self._marked = False


    def __repr__(self):
        result = ""
        result += f"{len(self.sections)} sections,"
        result += f" {self.number_notebooks()} notebooks"
        result += f" in course {self.coursedir}"
        return result

    def number_sections(self):
        return len(self.sections)

    def number_notebooks(self):
        return sum((len(section) for section in self.sections), 0)
    
    def first_notebook(self):
        return self.sections[0].first_notebook()

    def spot_notebook(self, path):
        # may be a Path instance
        path = str(path)
        for section in self.sections:
            spotted = section.spot_notebook(path)
            if spotted:
                return spotted
        return None

    def mark_notebooks(self, student):
        if self._marked:
            return
        coursedir = self.coursedir
        for section in self.sections:
            for notebook in section.notebooks:
                notebook.in_track = True

        # read student dir
        read_notebook_paths = set(
            coursedir.probe_student_notebooks(student))

        # mark corresponding notebook instances as read
        for read_path in read_notebook_paths:
            spotted = self.spot_notebook(read_path)
            if spotted:
                spotted.in_student = True
            else:
                # turn this off for now
                # no longer try to incorporate notebooks
                # that are not on that track
                pass
        self._marked = True

##### helpers to build a track manually
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


def track_by_directory(coursedir, *,
                       name="", description,
                       notebooks, directory_labels=None):
    """
    from a list of relative paths, returns a list of
    Section objects corresponding to directories

    optional directory_labels allows to provide a mapping
    "dirname" -> "displayed name"
    """

    def mapped_name(dirname):
        dirname = str(dirname)
        if not directory_labels:
            return dirname
        return directory_labels.get(dirname, dirname)

    logger.debug(f"track_by_directory in {coursedir}")
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
    return Track(coursedir, result, name=name, description=description)

def generic_track(coursedir):
    """
    From a toplevel directory, this function scans for all subdirs that
    have at least one notebook; this is used to create a generic track

    result will contain one Section instance per such directory,
    ordered alphabetically. similarly the notebooks in a Section instance
    are sorted alphabetically
    """
    return track_by_directory(
        coursedir,
        name="generic",
        description="automatically generated track from full repo contents",
        notebooks=notebooks_by_pattern(coursedir, "**/*.ipynb"))


# storage for caching
def write_tracks(tracks:List[Track], output_path: Path):
    with output_path.open('w') as output_file:
        output_file.write(jsonpickle.encode(tracks))


def read_tracks(coursedir, input_path: Path) -> List[Track]:
    with input_path.open() as input_file:
        tracks = jsonpickle.decode(input_file.read())
    for track in tracks:
        track.coursedir = coursedir
        for section in track.sections:
            section.coursedir = coursedir
            for notebook in section.notebooks:
                notebook.coursedir = coursedir
                notebook.in_track = True
    return tracks

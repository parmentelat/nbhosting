# pylint: disable=c0111, w1203, f-string-without-interpolation

from pathlib import Path
from collections import defaultdict
from typing import List

import yaml
import jsonpickle
import jupytext

from nbh_main.settings import logger, sitesettings

# this is what we expect to find as the result of a course custom tracks.py
CourseTracks = List['Track']

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
        # historically the nbhosting.title metadata was named notebookname
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
        clean = str(self.path)
        for extension in sitesettings.notebook_extensions:
            clean = clean.replace(f".{extension}", "")
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

        full_tooltip = ""
        if main_tooltip:
            full_tooltip +=  f'''{main_tooltip}<br/>'''
        full_tooltip += f'''<span class='smaller'>{self.clean_path()}</span>'''

        result = ""
        result += f''' data-toggle="tooltip" data-html="true" data-placement="bottom"'''
        result += f''' title="{full_tooltip}"'''
        return result

    def onclick(self):
        return f'iframe_notebook("{self.clean_path()}");'

    def _read_embedded(self):
        try:
            nbo = jupytext.read(self.absolute())
            metadata = nbo['metadata']
            nbh_md = metadata.get('nbhosting', {})
            self._notebookname = (
                nbh_md.get('title', "")
                or metadata.get('notebookname', self.clean_path()))
            self._version = (
                nbh_md.get("version", "")
                or metadata.get('version', '0.1'))
        except Exception as exc:                # pylint: disable=broad-except
            logger.warning(
                f"failed to extract metadata for notebook {self.clean_path()}\n"
                f"because of exception {type(exc)}: {exc}")
            self._notebookname = self.clean_path()
            self._version = "n/a"

class DummyNotebook:
    """
    just a placeholder so that an empty section can do from the ninja template
    section.first_notebook.decorate_a
    """

    notebookname = "dummy notebook"

    def decorate_a(self):                                   # pylint: disable=no-self-use
        return ""

    def onclick(self):                                      # pylint: disable=no-self-use
        return ""

    def clean_path(self):                                   # pylint: disable=no-self-use
        return "dummy-notebook"


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
        return self.notebooks[0] if self.notebooks else DummyNotebook()

    def spot_notebook(self, path):
        for notebook in self.notebooks:
            if notebook.clean_path() == path:
                return notebook
        return None

    def sanitize(self):
        # sanitize it only about removing empty nodes
        # so, nothing to do
        pass

class Track:

    def __init__(self, coursedir, sections: List['Section'],
                 *, name="default", description="no description", id_=None):
        self.coursedir = coursedir
        self.sections = sections
        self.name = name
        self.description = description
        self.id = (                                        # pylint: disable=invalid-name
            id_ or self.name.replace(' ', '-').replace('&', 'and'))
        # a flag that says if we've been through
        # mark_notebooks already or not
        self._marked = False


    # customize jsonpickle output
    def __getstate__(self):
        return dict(sections=self.sections,
                    name=self.name,
                    description=self.description,
                    id=self.id)

    # coursedir restored by read_tracks
    def __setstate__(self, state):
        self.__dict__.update(state)
        # when restoring from the cache we need
        # to redo the marking process
        self._marked = False


    def __repr__(self):
        return f"{self.name}[{self.id}]"

    def describe(self):
        result = ""
        result += f"{len(self.sections)} sections,"
        result += f" {self.number_notebooks()} notebooks"
        return result

    def number_sections(self):
        return len(self.sections)

    def number_notebooks(self):
        return sum((len(section) for section in self.sections), 0)

    def first_notebook(self):
        return self.sections[0].first_notebook() if self.sections else DummyNotebook()

    def spot_notebook(self, path):
        # may be a Path instance
        path = str(path)
        for section in self.sections:
            spotted = section.spot_notebook(path)
            if spotted:
                return spotted
        return None

    def sanitize(self):
        for section in self.sections[:]:
            section.sanitize()
            if not section:
                self.sections.remove(section)

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
    root = Path(coursedir.notebooks_dir).absolute()
    absolutes = root.glob(pattern)
    probed = [path.relative_to(root) for path in absolutes]
    notebooks = [Notebook(coursedir, path) for path in probed]
    notebooks.sort(key=lambda n: n.path)
    logger.debug(f"{coursedir}: {pattern} -> {len(notebooks)} notebook(s)")
    return notebooks


def notebooks_by_patterns(coursedir, patterns):
    """
    return a concatenation of notebooks_by_pattern on
    all patterns
    each bunch is sorted internally, but the concatenation
    remains in the order specified in patterns
    Returns:
       list of all notebooks (relative paths)
    """
    result = []
    for pattern in patterns:
        result.extend(notebooks_by_pattern(coursedir, pattern))
    return result


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
        description="generated track from all ipynb's found in repo",
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

# for model_course; prune empty nodes in the structure
def sanitize_tracks(tracks: CourseTracks):
    # don't modify the iterable you iterate upon
    for track in tracks[:]:
        track.sanitize()
        if not track:
            tracks.remove(track)
    return tracks

# see test-data/ue22-web-intro.yaml for an example
# of a yaml-based tracks definition
# pylint: disable=invalid-name
def tracks_from_yaml_config(coursedir, tracks: dict, tracks_filter: list=None):
    tracks_filter = [] if tracks_filter is None else tracks_filter
    def get(D, key):
        return D.get(key, key)
    def build_track_from_dict(D):
        return Track(coursedir,
                     sections=[build_section_from_dict(subD) for subD in D['sections']],
                     name=get(D, 'name'),
                     description=get(D, 'description'),
                     id_=get(D, 'id'))
    def build_section_from_dict(D):
        return Section(
            name=get(D, 'name'),
            coursedir=coursedir,
            notebooks=notebooks_by_patterns(coursedir, D['notebooks']))
    unfiltered = [build_track_from_dict(track) for track in tracks]
    logger.debug(f"{unfiltered=}")
    logger.debug(f"{tracks_filter=}")
    if not tracks_filter:
        return unfiltered
    else:
        return [track for track in unfiltered if track.id in tracks_filter]

# input is a list of Track instances
def to_yaml(tracks):
    def section_dict(section):
        return dict(
            name=section.name,
            notebooks=[str(notebook.path) for notebook in section.notebooks],
        )
    def track_dict(track):
        return dict(
            name=track.name,
            description=track.description,
            id=track.id,
            sections = [section_dict(section) for section in track.sections],
        )
    pre_yaml = dict(tracks=[track_dict(track) for track in tracks])
    return yaml.dump(pre_yaml)

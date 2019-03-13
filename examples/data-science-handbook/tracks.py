# pylint: disable=c0111
from nbhosting.courses import (
    Track, Section, Notebook,
    notebooks_by_pattern, track_by_directory)

def tracks(coursedir):
    """
    coursedir is a CourseDir object that points
    at the root directory of the filesystem tree
    that holds notebooks

    result is a list of Track instances
    """

    # define a single track that has sections based on the first 2 digits in the filename
    # that is to say 7 sections 00 .. 06

    section_names = [
        "preface",
        "IPython",
        "numpy",
        "pandas",
        "matplotlib",
        "machine learning",
        "appendix",
        ]

    default_track =  Track(
        coursedir,
        [Section(coursedir=coursedir,
                 name=section_name,
                 notebooks=notebooks_by_pattern(
                     coursedir,
                     f"notebooks/{number:02}*.ipynb"))
         for number, section_name in enumerate(section_names)],
        name="book",
        description="complete book contents")

    return [default_track]

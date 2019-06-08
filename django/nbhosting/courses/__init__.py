# don't import the models that inherit django's models.Model
# as it causes django to complain with the infamous
# django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet
#
#from .model_course import CourseDir

from .model_track import (
    Track, Section, Notebook,
    notebooks_by_pattern, track_by_directory, generic_track)

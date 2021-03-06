# pylint: disable=c0111

from django.test import TestCase

from nbhosting.courses.model_course import CourseDir


from nbhosting.courses.model_track import (
    Track, Section, Notebook, generic_track, tracks_from_yaml_config)

class Tests(TestCase):

    def test_generic(self):
        track = generic_track(
            CourseDir.objects.get(coursename="python-mooc"))
        self.assertEqual(track.number_sections(), 9)
        self.assertIsInstance(track, Track)


    def _test_custom(self, coursename, expected, track):
        course = CourseDir.objects.get(coursename=coursename)
        track = course.track(track)
        self.assertEqual(track.number_sections(), expected)
        self.assertIsInstance(track, Track)

    def test_py_regular(self):
        self._test_custom("python-mooc", 9, 'mooc')
    def test_py_exos(self):
        self._test_custom("python-mooc", 7, 'exos')
    def test_py_manual(self):
        self._test_custom("python-mooc", 9, 'undefined')

    def test_notebookname(self):
        coursedir = CourseDir.objects.get(coursename="python-mooc")
        notebook = Notebook(coursedir, "w1/w1-s1-c1-versions-python.md")

        self.assertEqual(notebook.notebookname, "Versions de python")

    def test_yaml_tracks(self):
        coursedir = CourseDir.objects.get(coursename="ue22-web-intro")
        import yaml
        with open('test-data/config.yaml') as feed:
            yaml_config = yaml.safe_load(feed.read())
        yaml_tracks = yaml_config['tracks']
        tracks = tracks_from_yaml_config(yaml_tracks)
        # warning, this may change if the course gets pulled
        self.assertEqual(len(tracks), 5)

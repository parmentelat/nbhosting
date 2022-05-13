# pylint: disable=c0111

from django.test import TestCase

from nbhosting.courses.model_course import CourseDir


from nbhosting.courses.model_track import (
    Track, Section, Notebook, generic_track, tracks_from_yaml_config)

class Tests(TestCase):

    def test_generic(self):
        track = generic_track(
            CourseDir.objects.get(coursename="python-mooc"))
        # remember this will only look for ipynbs
        self.assertEqual(track.number_sections(), 4)
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


    def init_yaml(self, suffix=""):
        coursedir = CourseDir.objects.get(coursename="ue22-web-intro")
        import yaml
        with open(f'nbhosting/courses/test-data/ue22-web-intro{suffix}.yaml') as feed:
            return coursedir, yaml.safe_load(feed.read())

    def test_yaml_tracks(self):
        coursedir, yaml_config = self.init_yaml()
        yaml_tracks = yaml_config['tracks']
        tracks = tracks_from_yaml_config(coursedir, yaml_tracks)
        # warning, this may change if the course gets pulled
        self.assertEqual(len(tracks), 3)

    def test_yaml_tracks_local(self):
        """
        merge 2 files, local one having an addition
        """
        coursedir, yaml_config = self.init_yaml()
        # this one defines a new track
        coursedir, yaml_config2 = self.init_yaml("-local")
        # local stuff has precedence so it comes first when returned by customized_s
        settings = coursedir.merge_settings([yaml_config2, yaml_config])
        yaml_tracks = settings['tracks']
        tracks = tracks_from_yaml_config(coursedir, yaml_tracks)
        # warning, this may change if the course gets pulled
        self.assertEqual(len(tracks), 4)

    def test_yaml_tracks_filtered(self):
        """
        merge 2 files, local one having an addition
        """
        coursedir, yaml_config = self.init_yaml()
        # this one defines a new track
        coursedir, yaml_config2 = self.init_yaml("-local-filtered")
        # local stuff has precedence so it comes first when returned by customized_s
        settings = coursedir.merge_settings([yaml_config2, yaml_config])
        yaml_tracks = settings['tracks']
        tracks_filter = settings['tracks-filter']
        tracks = tracks_from_yaml_config(coursedir, yaml_tracks, tracks_filter)
        # warning, this may change if the course gets pulled
        self.assertEqual(len(tracks), 2)

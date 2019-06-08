# pylint: disable=c0111

from django.test import TestCase

from nbhosting.courses.model_course import CourseDir

from nbhosting.courses.model_track import Track, Section, Notebook, generic_track


class Tests(TestCase):

    def test_generic(self):
        track = generic_track(
            CourseDir.objects.get(coursename="python3-s2"))
        self.assertEqual(track.number_sections(), 9)
        self.assertIsInstance(track, Track)


    def _test_custom(self, coursename, expected, track):
        course = CourseDir.objects.get(coursename=coursename)
        track = course.track(track)
        self.assertEqual(track.number_sections(), expected)
        self.assertIsInstance(track, Track)

    def test_py_regular(self):
        self._test_custom("python3-s2", 9, 'mooc')
    def test_py_exos(self):
        self._test_custom("python3-s2", 7, 'exos')
    def test_py_manual(self):
        self._test_custom("python3-s2", 9, 'undefined')

    def test_notebookname(self):
        coursedir = CourseDir.objects.get(coursename="python3-s2")
        notebook = Notebook(coursedir, "w1/w1-s1-c1-versions-python.ipynb")

        self.assertEqual(notebook.notebookname, "Versions de python")

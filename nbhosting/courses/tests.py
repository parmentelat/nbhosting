# pylint: disable=c0111

from django.test import TestCase

from nbhosting.courses import CourseDir, default_sectioning

from nbhosting.courses import Sections, Section, Notebook

class Tests(TestCase):

    def test_generic(self):
        sections = default_sectioning(
            CourseDir("python3-s2"))
        self.assertEqual(len(sections), 10)
        self.assertIsInstance(sections, Sections)


    def _test_custom(self, coursename, expected, viewpoint="course"):
        course = CourseDir(coursename)
        sections = course.sections(viewpoint)
        self.assertEqual(len(sections), expected)
        self.assertIsInstance(sections, Sections)

    def test_py_regular(self):
        self._test_custom("python3-s2", 9)
    def test_py_exos(self):
        self._test_custom("python3-s2", 7, 'exos')
    def test_py_manual(self):
        self._test_custom("python3-s2", 9, 'default')

    def test_notebookname(self):
        course = CourseDir("python3-s2")
        notebook = Notebook(course, "w1/w1-s1-c1-versions-python.ipynb")

        self.assertEqual(notebook.notebookname, "Versions de python")

from django.test import TestCase

from courses import CourseDir, generic_sectioning

class Tests(TestCase):

    def test_generic(self):
        sections = generic_sectioning(
            "/Users/tparment/git/nbhosting/nbhosting/fake-root/courses/python3-s2")
        self.assertEqual(len(sections), 10)


    def test_custom(self):
        course = CourseDir("python3-s2")
        self.assertEqual(len(course.sections()), 9)
        self.assertEqual(len(course.sections("exos")), 7)

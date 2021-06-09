# pylint: disable=missing-function-docstring, logging-fstring-interpolation

"""
the Dropped object represent one item dropped into the course's droparea
"""

from typing import List

from pwd import getpwnam
from os import chown
from pathlib import Path

from nbh_main.settings import logger

from django.contrib.auth.models import User


class Dropped:
    """
    a file dropped in a course
    """
    def __init__(self, coursedir, droparea, relpath: Path, bytes_size=None):
        if not isinstance(relpath, Path):
            relpath = Path(relpath)
        self.coursedir = coursedir
        self.relpath = Path(relpath)
        self.droparea = Path(droparea)
        self._bytes_size = bytes_size

    def __repr__(self):
        return f"<Dropped {self.coursedir.coursename} / {self.droparea} / {self.relpath}>"

    @property
    def fullpath(self):
        return (self.coursedir.drop_dir()             # pylint: disable=protected-access
                / self.droparea / self.relpath)

    def exists(self):
        return self.fullpath.exists()

    def mkdir(self):
        self.fullpath.parent.mkdir(parents=True, exist_ok=True)

    @property
    def bytes_size(self):
        if self._bytes_size is None:
            try:
                self._bytes_size = self.fullpath.stat().st_size
            except:                                       # pylint: disable = bare-except
                self._bytes_size = 0
        return self._bytes_size

    def remove(self):
        self.fullpath.unlink()

    @staticmethod
    def scan_course_droparea(coursedir, droparea) -> List["Dropped"]:
        droproot = (coursedir.drop_dir()              # pylint: disable=protected-access
                    / droparea)
        raw = [
            Dropped(coursedir,
                    droparea,
                    subfile.relative_to(droproot),
                    subfile.stat().st_size)
            for subfile in droproot.glob("**/*")
            ]
        return sorted(raw, key=lambda dropped: dropped.relpath)

    # the incoming parameter here is created by
    # django's upload mechanism, and is of type
    # InMemoryUploadedFile
    @staticmethod
    def from_uploaded(coursedir, droparea, inmemory: "InMemoryUploadedFile"):
        logger.info(f"Uploaded {inmemory.name}")
        # save it in the course area
        dropped = Dropped(coursedir, droparea, inmemory.name, inmemory.size)
        dropped.mkdir()
        with inmemory.open() as reader:
            with open(dropped.fullpath, 'wb') as writer:
                writer.write(reader.read())
        return dropped

    def deploy_to_student(self, student, *, force=False, dry_run=False):
        """
        propagate this dropped file into a student space

        unless force is set, this won't override a pre-existing copy
        in the student's space

        Returns:
          a dict of bools
            - relevant: the student is relevant (exists, ...)
            - already: the file was already present
            - new: the file was copied
            - available: the file is now available to the student
        """
        if not self.exists():
            logger.error(f"cannot deploy unexisting dropped {self}")
            return dict(relevant=False, already=False, new=False, available=False)

        # check for student in /etc/passwd
        if isinstance(student, User):
            student = student.username
        try:
            pwdentry = getpwnam(student)
            uid, gid = pwdentry.pw_uid, pwdentry.pw_gid
        except KeyError:
            logger.error(f"Cannot deploy to inexisting student {student}")
            return dict(relevant=False, already=False, new=False, available=False)

        student_droparea = self.coursedir.student_dir(student) / "DROPPED" / self.droparea
        if not student_droparea.exists() and not dry_run:
            student_droparea.mkdir(parents=True)
        target = student_droparea / self.relpath
        already = target.exists()
        if dry_run:
            return dict(relevant=True, already=already, new=False, available=already)
        if already and not force:
            return dict(relevant=True, already=already, new=False, available=True)
        with self.fullpath.open('rb') as reader:
            with target.open('wb') as writer:
                writer.write(reader.read())
        chown(str(target), uid, gid)
        return dict(relevant=True, already=already, new=True, available=True)

    def deploy_to_students(self, *, force=False, dry_run=False):
        """
        dry_run: if set, reports current stats but does not deploy
        force: if set, overwrite the students area even if that the
            file is already present there

        returns a dict
        - total: number of students attempted
        - availables: number of students that now have the file
        - news: number of actual deploys
        """
        deploys = [self.deploy_to_student(s, force=force, dry_run=dry_run)
                  for s in self.coursedir.i_registered_users()]
        availables = sum(deploy['available'] for deploy in deploys)
        news = sum(deploy['new'] for deploy in deploys)
        return dict(total=len(deploys), availables=availables, news=news)

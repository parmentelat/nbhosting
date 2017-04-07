import os
from pathlib import Path

class Course:

    def __init__(self, name, top_directory):
        """
        name is expected to be a simple (with no /) name from an incoming url
        """
        self.name = name
        self.top_directory = Path(top_directory)
        self.course_dir = self.top_directory / name

    def rain_check(self):
        """
        a boolean that says if this course is usable
        for now we just check if the directory can be found
        """
        return self.course_dir.exists()

    def has_notebook(self, notebook):
        """
        check if this course contains a notebook of that name
        notebook can contain slashes if needed
        ".ipynb" gets added to the notebook name if that helps
        returns the path of an existing and readable filename,
        or False
        """
        full_path = (self.course_dir / notebook).with_suffix(".ipynb")
        try:
            with full_path.open() as f:
                for line in f.readlines():
                    break
            return full_path
        except IOError as e:
            return False
            

        
    

        
        

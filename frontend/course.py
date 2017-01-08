import os
import os.path

class Course:

    def __init__(self, name, top_directory):
        """
        name is expected to be a simple (aith no /) name from an incoming url
        """
        self.name = name
        self.top_directory

    def rain_check(self):
        """
        a boolean that says if this course is usable
        for now we just check if the directory can be found
        """
        if not os.path.exists(
                os.path.join(self.top_directory, self.name)):
            return False
        return True

    def has_notebook(self, notebook):
        """
        check if this course contains a notebook of that name
        notebook can contain slashes if needed
        ".ipynb" gets added to the notebook name if that helps
        returns the path of an existing and readable filename,
        or False
        """
        full_path = os.path.join(self.top_directory,
                                 self.name,
                                 notebook)
        if not os.path.exists(full_path) and os.path.exists(full_path + ".ipynb"):
            full_path = full_path + ".ipynb"
        try:
            with open(full_path) as f:
                for line in f.readlines():
                    break
            return full_path
        except IOError as e:
            return False
            

        
    

        
        

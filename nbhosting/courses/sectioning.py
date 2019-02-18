from pathlib import Path
from collections import defaultdict

# from nbhosting.main.settings import sitesettings, logger

class Section:

    def __init__(self, name, root, notebooks):
        """
        notebooks are relative paths from a common course root
        provided in root
        """
        self.name = name
        self.root = root
        self.notebooks = notebooks

    def __repr__(self):
        return (f"Section {self.name} from {self.root}"
                f" has {len(self.notebooks)}"
                f" starting with {self.notebooks[0]}")


##### helpers to build manual sectioning
def notebooks_by_pattern(root, pattern):
    """
    return a sorted list of all notebooks (relative paths)
    matching some pattern from root
    """
    root = Path(root).absolute()
    absolutes = root.glob(pattern)
    probed = [path.relative_to(root) for path in absolutes]
    probed.sort()
    return probed


def group_by_directories(root, relatives):
    """
    from a list of relative paths, returns a list of
    Section objects correponing to directories
    """
    paths = [(relative, Path(root/relative)) for relative in relatives]
    hash = defaultdict(list)

    for relative, full in paths:
        hash[full.absolute().parent].append(relative)

    result = []

    for absolute, paths in hash.items():
        result.append(
            Section(name=absolute.relative_to(root),
                    root=root,
                    notebooks=paths),
        )

    result.sort(key=lambda s: s.name)
    for section in result:
        section.notebooks.sort()
    return result

def generic_sectioning(root):
    """
    From a toplevel directory, this function scans for all subdirs that
    have at least one notebook; this is used to create a generic sectioning

    result will contain one Section instance per such directory,
    ordered alphabetically. similarly the notebooks in a Section instance
    are sorted alphabetically
    """
    root = Path(root).absolute()
    return group_by_directories(
        root,
        notebooks_by_pattern(root, "**/*.ipynb"))

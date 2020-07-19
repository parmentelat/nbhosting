#!/usr/bin/env python

"""
ad hoc utility to have a running MOOC transition from .ipynb notebooks 
to a jupytext-powered format

specifically from python3-s2 (i.e. flotpython/course@master)
to python-mooc (i.e. i.e. flotpython/course@jupytext)
"""

import os
import json
from pathlib import Path

def run(command, dry_run):
    if dry_run:
        print(f"DRY-RUN: would do {command}")
        return
    return os.system(command)

supported_targets = {
    'md': {
        'ext': '.md',
        'format': 'myst',
        'fullname': 'markdown',
    },
    'py': {
        'ext': '.py',
        'format': 'percent',
        'fullname': 'python',
    },
}


def migrate_one_notebook(ipynb, target, 
                         *, dstdir=None, force=False,
                         git_move=False, dry_run=True):
    """
    manage one notebook
    """

    assert target in supported_targets
    details = supported_targets[target]
    extension = details['ext']

    old = Path(ipynb)
    if not old.exists():
        #raise ValueError(f"{old} not found")
        return

    if dstdir is None:
        dstdir = old.parent

    stem = old.stem
    newdir = Path(dstdir)
    new = (newdir / stem).with_suffix(extension)
    new_abs = new.absolute()

    needs_update = None
    
    if force:
        needs_update = True
    elif not new.exists():
        needs_update = True
    else:
        needs_update = old.stat().st_mtime >= new.stat().st_mtime
    if needs_update:
        format = supported_targets[target]['format']
        run(f"jupytext --to {target}:{format} -o {new_abs} {old}", dry_run)
        settings = {'jupytext' : {
            'cell_metadata_filter': 'all',
            'notebook_metadata_filter': 
                "all,-language_info,-toc,-jupytext.text_representation.jupytext_version,"
                "-jupytext.text_representation.format_version"
        }}
        run(f"jupytext {new} --update-metadata '{json.dumps(settings)}'",
            dry_run)
    else:
        print(f"target {new} up-to-date")
    if git_move:
        run(f"git rm -f {old}", dry_run)
        run(f"git add {new}", dry_run)


def migrate_student_notebook(student_home, course1, course2, rel_ipynb, target,
                             *, dry_run=True):
    student_home = Path(student_home)
    ipynb = student_home / course1 / rel_ipynb
    dstdir = (student_home / course2 / rel_ipynb).parent
    if not dstdir.exists():
        if dry_run:
            print(f"would create dir {dstdir}")
        else:
            dstdir.mkdir(parents=True)
    migrate_one_notebook(ipynb, target, dstdir=dstdir, dry_run=dry_run)



# provide for 2 environments
# . in the git repo of the course, need to translate notebooks in place
# . on the nbhosting infra, we need to populate course2 from course1

from argparse import ArgumentParser

# when running in a git repo (not a nbhosting box, no /nbhosting)
def main_in_git():
    parser = ArgumentParser()
    parser.add_argument("-n", "--dry-run", action='store_true', default=False)
    parser.add_argument("-d", "--directory", default=None)
    parser.add_argument("-t", "--target", 
                        choices=list(supported_targets.keys()), default='md')
    parser.add_argument("--force", action="store_true", default=False)
    parser.add_argument("--git", action="store_true", default=False)
    parser.add_argument("ipynbs", nargs='+')
    args = parser.parse_args()
    extras = {}
    if args.force:
        extras['force'] = True
    if args.git:
        extras['git_move'] = True
    for ipynb in args.ipynbs:
        migrate_one_notebook(ipynb, args.target, dry_run=args.dry_run, **extras)
    

# on a deployment
def main_in_nbhosting():
    parser = ArgumentParser()
    parser.add_argument("-n", "--dry-run", action='store_true', default=False)
    parser.add_argument("-l", "--list-notebooks", dest="ipynbs_filename",
                        help="provide the name of the file that contains "
                        "the relative paths to ipynbs in the course")
    parser.add_argument("-p", "--path", dest='raw_ipynbs',
                        action='append', default=[],
                        help="mention relative ipynb paths in the CLI (additive)")
    parser.add_argument("-t", "--target", 
                        choices=list(supported_targets.keys()), default='md')
    parser.add_argument("course1")
    parser.add_argument("course2")
    parser.add_argument("student_homes", nargs='+')
    args = parser.parse_args()
    ipynbs = []
    ipynbs += args.raw_ipynbs
    if args.ipynbs_filename:
        with open(args.ipynbs_filename) as feed:
            ipynbs += [line.strip() for line in feed]
    print(f"ipynbs={ipynbs}")
    for ipynb in ipynbs:
        print(f"==== dealing with notebook {ipynb}")
        for student_home in args.student_homes:
            migrate_student_notebook(
                student_home, args.course1, args.course2, 
                ipynb, args.target,
                dry_run=args.dry_run)
    
if __name__ == '__main__':
    if Path("/nbhosting").exists():
        print("** nbhosting mode (found /nbhosting/)**")
        main_in_nbhosting()
    else:
        print("** git mode (could not find /nbhosting/)**")
        main_in_git()
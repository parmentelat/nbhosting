#!/usr/bin/env python

"""
a utility to update a nbhosting config file - specifically tracks definition -
from a jupyter-book toc file

you need to specify
- the input _toc.yml
- the output nbhosting.yaml
- the track id to update
- optionally, a path replacement specification

"""

from pathlib import Path
from argparse import ArgumentParser

# import yaml
# we want to preserve comments in the nbhosting yaml file
import ruamel.yaml as yaml


def strip(filename):
    """
    remove extension
    """
    return str(Path(filename).with_suffix(""))


def inject_toc_into_track(
        jbtoc: dict, track: dict, path) -> dict:

    def cleansed(notebook):
        if path is None:
            return notebook
        else:
            return path + "/" + notebook

    # we assume the jupyter book TOC is primarily a 'parts' list
    #  each being a dict that has
    # caption: str
    # chapters: list of records that have
    # {file: str,
    #  glob: str,   (possibly replacing file:)
    #  sections: list of records that have again a 'file' or 'glob' key

    def notebooks(chapter):
        match chapter:
            # sections should be attached to a specific notebook, not a group...
            case {'glob': glob, 'sections': sections}:
                raise ValueError(f"unexpected glob+sections in {chapter}")
            # this corresponds to a notebook that has sub-notebooks
            case {'file': file, 'sections': sections}:
                return [strip(cleansed(file))] + [notebook for section in sections for notebook in notebooks(section)]
            case {'file': file}:
                return [strip(cleansed(file))]
            case {'glob': glob}:
                return [strip(cleansed(glob))]

    def section(part):
        match part:
            case {'caption': caption, 'chapters': chapters}:
                return dict(name=caption,
                            # append all notebooks from all chapters
                            notebooks=[notebook for chapter in chapters for notebook in notebooks(chapter)])
            case _:
                raise ValueError(f"unexpected part {part}")

    track['sections'] = [section(part) for part in jbtoc['parts']]


def update_nbh_from_jb(
    jupyter_book_yaml,
    nbhosting_yaml,
    trackname,
    path,
    dry_run,
):
    yaml_loader = yaml.YAML()
    try:
        with open(jupyter_book_yaml) as jb:
            jb_data = yaml_loader.load(jb.read())

        try:
            with open(nbhosting_yaml) as nbh:
                # yaml_loader2 = yaml.YAML()
                nbh_data = yaml_loader.load(nbh.read())
                if not nbh_data:
                    raise ValueError("empty jb toc")
        except FileNotFoundError:
            print(f"it is unsafe to start from an empty {nbhosting_yaml}")
            return False

        tracks = nbh_data["tracks"]
        if trackname is None:
            track = tracks[0]
        else:
            track = next(track for track in tracks if track["id"] == trackname)

        # print(f"track: {track}")

        inject_toc_into_track(jb_data, track, path)

        if dry_run:
            nbhosting_yaml += ".dry"
        with open(nbhosting_yaml, "w") as output:
            yaml_loader.dump(nbh_data, output)
            return nbhosting_yaml
    except Exception as exc:
        print(f"OOPS, no can do, {type(exc)}: {exc}")
        raise
        return False


def main():
    parser = ArgumentParser()
    parser.add_argument("-t", "--track", default=None, help="nbhosting track id")
    parser.add_argument(
        "-n",
        "--dry-run",
        default=False,
        action="store_true",
        help="append .dry to the written filename",
    )
    parser.add_argument(
        "-p",
        "--path",
        default=None,
        dest="path",
        help="provide relative path of notebooks starting from repo top"
    )
    parser.add_argument("jupyter_book_yaml")
    parser.add_argument("nbhosting_yaml")
    args = parser.parse_args()

    result = update_nbh_from_jb(
        args.jupyter_book_yaml,
        args.nbhosting_yaml,
        args.track,
        args.path,
        args.dry_run,
    )
    if result:
        print(f"(over)wrote {result}")
        return 0
    else:
        return 1


main()

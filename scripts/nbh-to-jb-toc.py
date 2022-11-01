#!/usr/bin/env python

from pathlib import Path
from argparse import ArgumentParser

import yaml

def strip(filename):
    """
    remove extension
    """
    return str(Path(filename).with_suffix(""))

def inject_track_into_toc(track: dict, toc: dict) -> dict:
    def chapter(notebook):
        if '*' in notebook:
            return {'glob': strip(notebook)}
        else:
            return {'file': strip(notebook)}
    def chapters(notebooks):
        return [chapter(notebook) for notebook in notebooks]
    new_parts = [dict(
                    caption=section['name'],
                    chapters=chapters(section['notebooks']))
                 for section in track['sections']]
    toc['parts'] = new_parts
    return toc

def update_jb_from_nbh(jupyter_book_yaml, nbhosting_yaml, trackname, dry_run):
    try:
        with (open(jupyter_book_yaml) as jb,
              open(nbhosting_yaml) as nbh):
            nbh_data = yaml.load(nbh, yaml.FullLoader)
            jb_data = yaml.load(jb, yaml.FullLoader)

        tracks = nbh_data['tracks']
        if trackname is None:
            track = tracks[0]
        else:
            track = next(track for track in tracks if track['id'] == trackname)

        inject_track_into_toc(track, jb_data)

        if dry_run:
            jupyter_book_yaml += ".dry"
        with open(jupyter_book_yaml, 'w') as output:
            yaml.dump(jb_data, output)
            return jupyter_book_yaml
    except Exception as exc:
        print(f"OOPS, no can do, {type(exc)}: {exc}")
        return False


def main():
    parser = ArgumentParser()
    parser.add_argument("-t", "--track", default=None, help="nbhosting track id")
    parser.add_argument("-n", "--dry-run", default=False, action='store_true',
                        help="append .dry to the written filename")
    parser.add_argument("nbhosting_yaml")
    parser.add_argument("jupyter_book_yaml")
    args = parser.parse_args()

    result = update_jb_from_nbh(args.jupyter_book_yaml,
                                args.nbhosting_yaml,
                                args.track,
                                args.dry_run)
    if result:
        print(f"(over)wrote {result}")
        return 0
    else:
        return 1

main()

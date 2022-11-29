#!/usr/bin/env python

import sys
from argparse import ArgumentParser
from pathlib import Path

from datetime import date as Date, timedelta as TimeDelta, datetime as DateTime

#
DEFAULT_AGE_YEARS = 3
DEFAULT_CUT = Date.today() - TimeDelta(days=DEFAULT_AGE_YEARS*365)

def most_recent_change(path) -> (Path, Date):
    epoch = 0
    most_recent = ""
    for file in path.glob("**/*"):
        if file.is_dir():
            continue
        if not file.exists():
            continue
        file_changed = file.stat().st_mtime
        if file_changed > epoch:
            most_recent = file
            epoch = file_changed
    return most_recent, DateTime.fromtimestamp(epoch)

# examples of use
#
# for c in 0 1 2 3 4 5 6 7 8 9 a b c d e f; do
# find-old-students.py /nbhosting/prod/students/${c}??????????????????????????????? > /tmp/obso-${c}
# done
#
# and then
#
# cat /tmp/obso-? | xargs rm -rf


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--cut",
        type=lambda s: DateTime.strptime(s, '%Y/%m/%d'),
        default=DEFAULT_CUT,
        help="the cutting date; folders whose contents is entirely"
            " older than that date get trashed; expected format is YYYY/MM/DD",
    )
    parser.add_argument("-v", "--verbose", default=False, action='store_true')
    parser.add_argument("folders", nargs="+")
    args = parser.parse_args()

    cut = args.cut.date()

    total = 0
    counter = 0

    if args.verbose:
        print(f"{cut=}")

    for folder in args.folders:
        path = Path(folder)
        if not path.exists():
            print(f"{path} not found")
            continue
        if not path.is_dir():
            print(f"{path} not a folder")
            continue
        total += 1
        most_recent, changes = most_recent_change(path)
        if args.verbose:
            print(
                f"{10*'='} {folder}\n"
                f"  last modified on {changes}\n"
                f"  on {most_recent}")
        if changes.date() <= cut:
            print(path)
            counter += 1
        elif args.verbose:
            print(f"  NOT OLD ENOUGH")

    # this line on stderr so the raw output on stdout
    # can be used down the line to xargs or anything else
    print(
        f"Found {counter} old folders out of {total}, i.e. {100*counter/total:.2f}%",
        file=sys.stderr)

main()
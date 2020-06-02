#!/usr/bin/env python

from collections import defaultdict
from pathlib import Path
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import datetime, timedelta

def average(dir, criteria):
    txt_filenames = Path(dir).glob("*.txt")
    number = 0
    total = 0
    for txt_filename in txt_filenames:
        with open(txt_filename) as feed:
            for line in feed:
                if criteria in line:
                    try:
                        _, itemstr = line.strip().split(":")
                        total += float(itemstr)
                        number +=1 
                    except Exception as exc:
                        print(f"warning: skipping line {line}", end="")
                        
    average = total / number if number else 0
    print(f"the average of {criteria} in {dir} (on {number} items) is {average} ")
                 
                 
def count_booms(dir):
    by_size = defaultdict(list)
    counter = 0
    for boom in Path(dir).glob("*boom*"):
        counter += 1
        size = boom.stat().st_size
        by_size[size].append(boom)
    if not counter:
        print("no boom")
        return
    print(f"boom happened {counter} times")
    for s, fs in by_size.items():
        print(f"   {s} -> {len(fs)} booms", end="")
        if (len(fs) == 1):
            print(f" {fs[0]}")
        else:
            print()
            
def duration(dir):
    FORMAT = "%H-%M-%S"
    def has_time(line):
        try:
            timestamp, rest = line.split(":", 1)
            return datetime.strptime(timestamp, FORMAT)
        except:
            pass
    beg = None
    try:
        with (dir / "LOG").open() as feed:
            for line in feed:
                the_time = has_time(line)
                if not the_time:
                    continue
                if beg is None:
                    beg = the_time
                    continue
                end = the_time
            delta = end - beg
            if delta <= timedelta(0):
                delta += timedelta(hour=24)
            print(f"duration was {delta}")
    except:
        pass
            
                   
def summary(dir):
    dir = Path(dir)
    print(f"{10*'-'} {dir}")
    duration(dir)
    for criteria in ('get', 'clear', 'trigger', 'save'):
        average(dir, criteria)
    count_booms(dir)

def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("dirs", default=None, type=str, nargs="*",
                        help="""
                        the artefacts directory where to search the .txt files.
                        By default all subdirs named in 'artefacts*'""")
    args = parser.parse_args()
    
    dirs = args.dirs
    if not dirs:
        dirs = Path(".").glob("artefacts*")
        dirs = [dir for dir in dirs if dir.is_dir()]
    for dir in dirs:
        summary(dir)
    
if __name__ == '__main__':
    main()
                        
    
#!/usr/bin/env python

from pathlib import Path
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


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
                    

def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c",  "--criteria", default="get duration",
                        help="the data to average")
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
        average(dir, args.criteria)
    
if __name__ == '__main__':
    main()
                        
    
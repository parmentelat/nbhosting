#!/usr/bin/env python

from datetime import datetime
from argparse import ArgumentParser

def get_time(line):
    timestamp, rest = line.split(' ', 1)
    try:
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    except:
        return datetime.fromordinal(1)

def next_line(file):
    try:
        return next(file)
    except StopIteration:
        return None

def merge_filenames(filename1, filename2):
    with open(filename1) as f1, open(filename2) as f2:
        merge_files(f1, f2)
        
def merge_files(f1, f2):
    line1 = next_line(f1)
    line2 = next_line(f2)
    
    while line1 and line2:
        time1, time2 = get_time(line1), get_time(line2)
        if time1 < time2:
            print(line1, end="")
            line1 = next_line(f1)
        else:
            print(line2, end="")
            line2 = next_line(f2)
    
    while line1:
        print(line1, end="")
        line1 = next_line(f1)
    while line2:
        print(line2, end="")
        line2 = next_line(f2)

        
def main():
    parser = ArgumentParser()
    parser.add_argument("file1")
    parser.add_argument("file2")
    args = parser.parse_args()
    merge_filenames(args.file1, args.file2)
    
if __name__ == '__main__':
    main()

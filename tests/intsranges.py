#!/usr/bin/env python3

"""
This is an extension to the argparse ecosystem

Purpose is to enable the description of integers ranges; typically with

parser.add_argument("-l", "--list-integers", action=IntsRanges, default=[1, 5, 7])

main.py
would yield 1, 5, 7

and main.py -l 10-15 -l 20-30-2 
would yield 10, 11, 12, 13, 14, 15, 20, 22, 24, 26, 28, 30

"""

import argparse

class IntsRanges(argparse.Action):

    """
    We cannot support choices here because choices is checked before 
    action is even called
    e.g.
    parser.add_argument(default=[1, 2], action=IntsRanges)
    """

    def __init__(self, *args, **kwds):
        self.result = []
        super().__init__(*args, **kwds)

    def __call__(self, parser, namespace, value, option_string=None):
        pieces = value.split('-')
        if not (0 < len(pieces) <= 3):
            raise argparse.ArgumentError("wrong syntax in IntsRange with {}"
                                         .format(value))
        try:
            if len(pieces) == 1:
                self.result.append(int(pieces[0]))
            elif len(pieces) == 2:
                a, b = (int(x) for x in pieces)
                self.result += list(range(a, b+1))
            else:
                a, b, c = (int(x) for x in pieces)
                self.result += list(range(a, b+1, c))
            self.result = sorted(set(self.result))
        except ValueError as e:
            raise argparse.ArgumentTypeError(value, "IntsRange requires integers")
        setattr(namespace, self.dest, self.result)

#################### unit test
if __name__ == '__main__':
    def test1():
        """
        IntsRanges micro-test
        """
        def new_parser():
            parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
            parser.add_argument("-r", "--ranges", default=[1, 3, 5],
                                action=IntsRanges,
                                help="specify inclusive integer ranges")
            return parser

        a = new_parser().parse_args([])
        assert a.ranges == [1, 3, 5]
        a = new_parser().parse_args(['-r', '1'])
        assert a.ranges == [1]
        a = new_parser().parse_args(['-r', '1', '-r', '3-5'])
        assert a.ranges == [1, 3, 4, 5]
        a = new_parser().parse_args(['-r', '1-5-2', '-r', '5-7'])
        assert a.ranges == [1, 3, 5, 6, 7]
        a = new_parser().parse_args(['-r', '0-100-5'])
        assert a.ranges == list(range(0, 101, 5))

    test1()

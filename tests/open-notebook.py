#!/usr/bin/env python3

# NOTE about installing phantomjs
# I first installed phantomjs from a binary distrib in
# ~/git/nbhosting/tests/phantomjs-2.1.1-macosx/bin/phantomjs
# then I created a symlink in ~/bin
# a mere alias would not be good enough, or we'd need to specify the
# full path of phantomjs to the webdriver.PhantomJS constructor

"""
Testing utility for nbhosting

This script uses selenium/phantomjs to actually open one notebook
and **run all cells** 
"""


import time
from pathlib import Path
from itertools import chain
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

# pip3 install 
from selenium import webdriver


def list_bioinfo_notebooks():
    from pathlib import Path
    bioinfo = Path.home() / "git" / "flotbioinfo"
    paths = chain((bioinfo / "w1").glob("fr*nb"), (bioinfo / "w1").glob("en*nb"))
    return [x.stem for x in paths]

bioinfo_notebooks = list_bioinfo_notebooks()


js_clear_all_on_document_load = "$(function() { Jupyter.notebook.clear_all_output(); })"
js_run_all = "Jupyter.notebook.execute_all_cells()"
js_save = "Jupyter.notebook.save_checkpoint()"


def pause(message, delay):
    print("{} - waiting for an extra {}s"
          .format(message, delay))
    time.sleep(delay)


class Artefact:
    def __init__(self, user, index, kind):
        self.user = user
        self.kind = kind
        self.index = index

    def mkdir(self):
        path = self.path = Path('artefacts')
        if not path.is_dir():
            print("Creating {}".format(path))
            path.mkdir()

    def filename(self, msg):
        self.mkdir()
        ext = "png"if self.kind == "screenshot" else "txt"
        return str(self.path / "{user}-{index}-{kind}-{msg}.{ext}"\
                   .format(**locals(), **self.__dict__))

def run(user, index, delay):
    """
    fetch bioinfo notebook of that index as this user
    and click the 'run-all-cells' button
    """
    nb = bioinfo_notebooks[index]
    url = "https://nbhosting.inria.fr/ipythonExercice/flotbioinfo/w1/{nb}/{user}"\
          .format(**locals())

    print("fetching URL {url}".format(url=url))
    driver = webdriver.PhantomJS() # or add to your PATH
    try:
        scr = Artefact(user, index, 'screenshot')
        driver.set_window_size(1024, 2048) # optional
        driver.get(url)
        print("GET OK")
        driver.save_screenshot(scr.filename('0bare'))
        #
        pause("cleared all", delay)
        driver.execute_script(js_clear_all_on_document_load)
        driver.save_screenshot(scr.filename('1cleared'))
        #
        pause("executing all ", delay)
        driver.execute_script(js_run_all)
        driver.save_screenshot(scr.filename('2trigger'))
        #
        pause("executed all", 10)
        driver.execute_script(js_save)
        driver.save_screenshot(scr.filename("3evaled"))
        #
        res = Artefact(user, index, 'contents')
        with open(res.filename('4contents'), 'w') as out_file:
            kernel_area = driver.execute_script(
                "return $('#notification_kernel>span').html()")
            number_cells = driver.execute_script(
                "return Jupyter.notebook.get_cells().length")
            out_file.write("kernel area:[{kernel_area}]\n"
                           "number of cells: {number_cells}\n"
                           .format(**locals()))
        driver.quit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        driver.save_screenshot(scr.filename('4boom'))


def list():
    """List found notebooks in bioinfo with their index"""
    for i, n in enumerate(bioinfo_notebooks):
        print(i, n)


def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-l", "--list", default=False, action='store_true',
                        help="when given, lists known notebooks and does *not* open anything")
    parser.add_argument("-i", "--index", default=0, type=int,
                        help="index in the list of known notebooks - run with -l to see list")
    parser.add_argument("-u", "--user", default='student-0001',
                        help="username for opening that notebook")
    parser.add_argument("-s", "--sleep", default=3, type=int,
                        help="delay in seconds to sleep between actions")
    args = parser.parse_args()
    if args.list:
        list()
    else:
        run(args.user, args.index, args.sleep)

if __name__ == '__main__':
    main()

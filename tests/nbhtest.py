#!/usr/bin/python3 -u

# NOTE about installing phantomjs
# I first installed phantomjs from a binary distrib in
# ~/git/nbhosting/tests/phantomjs-2.1.1-macosx/bin/phantomjs
# then I created a symlink in ~/bin
# a mere alias would not be good enough, or we'd need to specify the
# full path of phantomjs to the webdriver.PhantomJS constructor
#
# ditto on linux from
# https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2

"""
Testing utility for nbhosting

This script uses selenium/phantomjs to
* open one notebook
* run all cells
* save output in student space
"""

import time
from pathlib import Path
from itertools import chain
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


# default location where to look for test notebooks
default_course_gitdir = Path.home() / "git" / "flotpython3" 
default_topurl = "https://nbhosting-dev.inria.fr/"
default_sleep_internal = 1

# for testing we need a local (git) copy of one of the courses
def list_notebooks(course_gitdir):
    course_gitdir = Path(course_gitdir)
    if not course_gitdir.is_dir():
        print("Could not browse for test notebooks in {}"
              .format(course_gitdir))
        exit(1)
    paths = chain(course_gitdir.glob("w?/w*.ipynb"),
                  course_gitdir.glob("w?/fr*.ipynb"),
                  course_gitdir.glob("w?/en*.ipynb"),
                  course_gitdir.glob("notebooks/*.ipynb"),
    )
    notebooks = sorted(['/'.join([p.parts[-2], p.stem]) for p in paths])
    course = course_gitdir.parts[-1]
    return course, notebooks


js_clear_all_on_document_load = "$(function() { Jupyter.notebook.clear_all_output(); })"
js_run_all = "Jupyter.notebook.execute_all_cells()"
js_save = "Jupyter.notebook.save_checkpoint()"


def pause(message, delay, previous_duration=None):
    line = "{} - waiting for an extra {}s".format(message, delay)
    if previous_duration:
        line += " (previous op took {d:.02f})".format(d=previous_duration)
    print(line)
    time.sleep(delay)


class Artefact:
    def __init__(self, user, course, index, kind):
        self.user = user
        self.course = course
        self.kind = kind
        self.index = index
        # keep track of the last meaningful file in this category
        # and move all others under details/
        self.last = None

    def mkdir(self):
        self.path = Path('artefacts')
        self.details = self.path / "details"
        for path in self.path, self.details:
            if not path.is_dir():
                print("Creating {}".format(path))
                path.mkdir()

    def filename(self, msg):
        self.mkdir()
        ext = "png" if self.kind == "screenshot" else "txt"
        latest = self.path / "{user}-{course}-{index}-{msg}.{ext}"\
                     .format(**locals(), **self.__dict__)
        # keep only the last file in one series
        if self.last is not None:
            details_last = self.details / self.last.name
            self.last.rename(details_last)
        self.last = latest
        return str(latest)


def run(topurl, user, course, notebooks, index, delay):
    """
    fetch - as this user - 
    notebook indexed by index relative to that course dir
    then perform additional tasks (exec, save, etc..)
    """

    # import here so we can get to run --help on a
    # regular non-selenium box
    # pip3 install 
    from selenium import webdriver

    
    nb = notebooks[index]
    # be extra-safe
    if topurl.endswith("/"):
        topurl = topurl[:-1]
    
    url = "{topurl}/notebookLazyCopy/{course}/{nb}/{user}"\
          .format(**locals())

    print("fetching URL {url}".format(url=url))
    driver = webdriver.PhantomJS() # or add to your PATH
    try:
        begin = time.time()
        scr = Artefact(user, course, index, 'screenshot')
        driver.set_window_size(1024, 2048) # optional
        # xxx unfortunately this returns None and there seems to be no way
        # to retrive the http header code
        driver.get(url)
        get_duration = time.time() - begin
        driver.save_screenshot(scr.filename('0get'))
        #
        pause("about to clear", delay, get_duration)
        begin = time.time()
        driver.execute_script(js_clear_all_on_document_load)
        clear_duration = time.time() - begin
        driver.save_screenshot(scr.filename('1clear'))
        #
        pause("about to execute ", delay, clear_duration)
        begin = time.time()
        driver.execute_script(js_run_all)
        exec_duration = time.time() - begin
        driver.save_screenshot(scr.filename('2exec'))
        #
        pause("about to save", delay, exec_duration)
        begin = time.time()
        driver.execute_script(js_save)
        save_duration = time.time() - begin
        driver.save_screenshot(scr.filename("3save"))
        #
        res = Artefact(user, course, index, 'contents')
        with open(res.filename('4contents'), 'w') as out_file:
            kernel_area = driver.execute_script(
                "return $('#notification_kernel>span').html()")
            number_cells = driver.execute_script(
                "return Jupyter.notebook.get_cells().length")
            out_file.write("kernel area:[{kernel_area}]\n"
                           "number of cells: {number_cells}\n"
                           "get duration: {get_duration:.2f}\n"
                           "clear duration: {clear_duration:.2f}\n"
                           "trigger duration: {exec_duration:.2f}\n"
                           "exec duration: {save_duration:.2f}\n"
                           .format(**locals()))
        driver.quit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        driver.save_screenshot(scr.filename('4boom'))


def list(notebooks):
    """List found notebooks in bioinfo with their index"""
    for i, n in enumerate(notebooks):
        print(i, n)


def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-U", "--url", default=default_topurl,
                        dest='topurl',
                        help="url to reach nbhosting server")
    parser.add_argument("-l", "--list", default=False, action='store_true',
                        help="when given, lists known notebooks and does *not* open anything")
    parser.add_argument("-c", "--course-gitdir", default=default_course_gitdir,
                        help="""location of a git repo where to fetch notebooks;
                                needed in order to generate relevant URLs""")
    parser.add_argument("-i", "--index", default=0, type=int,
                        help="index in the list of known notebooks - run with -l to see list")
    parser.add_argument("-u", "--user", default='student-0001',
                        help="username for opening that notebook")
    parser.add_argument("-s", "--sleep", default=default_sleep_internal, type=float,
                        help="delay in seconds to sleep between actions inside nbhtest")
    args = parser.parse_args()

    course, notebooks = list_notebooks(args.course_gitdir)
    if args.list:
        list(notebooks)
    else:
        run(args.topurl, args.user, course, notebooks, args.index, args.sleep)

if __name__ == '__main__':
    main()

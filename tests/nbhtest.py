#!/usr/bin/env python3

# NOTE about installing phantomjs
# I first installed phantomjs from a binary distrib in
# ~/git/nbhosting/tests/phantomjs-2.1.1-macosx/bin/phantomjs
# then I created a symlink in ~/bin
# a mere alias would not be good enough, or we'd need to specify the
# full path of phantomjs to the webdriver.PhantomJS constructor
#
# ditto on linux from
# https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
#
# UPDATE 2019 Nov
# we now use chromium instead of phantomjs
# see install. instruction in AA-readme-tests.md

"""
Testing utility for nbhosting

This script uses chromium to
* open one notebook
* run all cells
* save output in student space
"""

import sys, os
import time
from pathlib import Path
import json
import random
from itertools import chain
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


# default location where to look for test notebooks
default_course_gitdir = Path.home() / "git" / "python3-s2" 
default_topurl = "https://nbhosting-dev.inria.fr/"
default_sleep_internal = 1


class Contents:
    """
    models a coursedir that we scan so we can reference notebooks by their index
    """
    
    def __init__(self, dir):
        self.dir = dir
        self.coursename = Path(dir).stem
        self._load()


    def print(self):
        """List found notebooks in bioinfo with their index"""
        for i, n in enumerate(self.notebooks):
            print(i, n)


    @property 
    def filename(self):
        return f"{self.coursename}.nbs.json"


    # for testing we need a local (git) copy of one of the courses
    def _load(self):
        try:
            with Path(self.filename).open() as f:
                self.notebooks = json.loads(f.read())
        except IOError:
            # print(f"OOPS {type(exc)} {exc}")
            path = Path(self.dir)
            if not path.is_dir():
                print(f"Could not browse for test notebooks in {self.dir}")
                exit(1)
            paths = path.glob("**/*.ipynb")
            notebooks = sorted(['/'.join([p.parts[-2], p.stem]) for p in paths
                                if 'test' not in str(p)])
            with Path(self.filename).open("w") as writer:
                writer.write(json.dumps(notebooks))
            print(f"saved notebooks list for {self.coursename} in {self.filename}")
            self.notebooks = notebooks


js_clear_all_on_document_load = "$(function() { Jupyter.notebook.clear_all_output(); })"
js_run_all = "Jupyter.notebook.execute_all_cells()"
js_save = "Jupyter.notebook.save_checkpoint()"


def pause(mark, message, *, sleep=0, duration=None, skip=0):
    line = f"{mark}:{message}"
    if sleep: 
        line += f" - waiting for {sleep}s"
    if duration:
        line += f" (since beg. {duration - skip*sleep:.02f})s"
    print(line)
    if sleep:
        time.sleep(sleep)


class Notebook:
    def __init__(self, notebook_arg):
        coursedir, index = notebook_arg.split(':')
        contents = Contents(coursedir)  
        course = contents.coursename
        notebooks = contents.notebooks
        self.course = course
        self.index = int(index)
        try:
            self.nb_path = notebooks[self.index]
        except IndexError:
            self.nb_path = "unexisting-notebook"
            print(f"Using {self.nb_path} for dangling index {index}")
        
    
    @property
    def url_path(self):
        return f"{self.course}/{self.nb_path}"
    


class Artefact:
    def __init__(self, user, notebook, kind):
        self.user = user
        self.notebook = notebook
        self.kind = kind
        # keep track of the last meaningful file in this category
        # and move all others under details/
        self.last = None

    def mkdir(self):
        self.path = Path('artefacts')
        self.details = self.path / "details"
        for path in self.path, self.details:
            if not path.is_dir():
                print(f"Creating {path}")
                path.mkdir()

    def filename(self, msg):
        self.mkdir()
        ext = "png" if self.kind == "screenshot" else "txt"
        latest = self.path / f"{self.user}-{self.notebook.course}-{self.notebook.index}-{msg}.{ext}"
        # keep only the last file in one series
        if self.last is not None:
            details_last = self.details / self.last.name
            self.last.rename(details_last)
        self.last = latest
        return str(latest)


def run(topurl, user, notebooks, sleep, cut):
    """
    fetch - as this user - 
    notebook indexed by index relative to that course dir
    then perform additional tasks (exec, save, etc..)
    """

    # import here so we can get to run --help on a
    # regular non-selenium box

    # from selenium import webdriver
    print("driver creation")
    import selenium.webdriver
    options = selenium.webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('no-sandbox')
    options.add_argument(f'window-size=1920,{2*1080}')
    # rpm -ql chromedriver
    # -> /usr/bin/chromedriver
    chrome_driver_binary = "/usr/bin/chromedriver"
    driver = selenium.webdriver.Chrome(chrome_driver_binary, options=options)

    print("driver ready")
    
    def fetch_one_notebook(notebook, need_new_window):
        nonlocal topurl
        nb = notebook.nb_path
        # be extra-safe
        if topurl.endswith("/"):
            topurl = topurl[:-1]
        
        url  = f"{topurl}/notebookLazyCopy/{notebook.url_path}/{user}"
        mark = f"{nb}/{user}"

        print(f"fetching URL {url} need_new_window={need_new_window}")
        try:
            begin = time.time()
            scr = Artefact(user, notebook, 'screenshot')
            # xxx unfortunately this returns None and there seems to be no way
            # to retrive the http header code
            if not need_new_window:
                driver.get(url)
                #print(f"after initial page, handles={driver.window_handles}")
            else:
                javascript_command = f'$(window.open("{url}"))'
                driver.execute_script(javascript_command)
                # move to the newly created window
                driver.switch_to.window(driver.window_handles[-1])
                # print(f"after other page, handles={driver.window_handles}")
            get_duration = time.time() - begin
            driver.save_screenshot(scr.filename('0get'))
            if cut:
                pause(mark, "loaded", sleep=0, duration=get_duration, skip=0)
                return
            #
            pause(mark, "loaded", sleep=sleep, duration=get_duration, skip=0)
            driver.execute_script(js_clear_all_on_document_load)
            clear_duration = time.time() - begin
            driver.save_screenshot(scr.filename('1clear'))
            #
            pause(mark, "cleared ", sleep=sleep, duration=clear_duration, skip=1)
            driver.execute_script(js_run_all)
            exec_duration = time.time() - begin
            driver.save_screenshot(scr.filename('2exec'))
            #
            pause(mark, "executed", sleep=sleep, duration=exec_duration, skip=2)
            driver.execute_script(js_save)
            driver.save_screenshot(scr.filename("3save"))
            #
            res = Artefact(user, notebook, 'contents')
            with open(res.filename('4contents'), 'w') as out_file:
                kernel_area = driver.execute_script(
                    "return $('#notification_kernel>span').html()")
                number_cells = driver.execute_script(
                    "return Jupyter.notebook.get_cells().length")
                save_duration = time.time() - begin
                out_file.write(f"kernel area:[{kernel_area}]\n"
                            f"number of cells: {number_cells}\n"
                            f"sleep between ops: {sleep}\n"
                            f"get duration: {get_duration:.2f}\n"
                            f"clear duration: {clear_duration:.2f}\n"
                            f"trigger duration: {exec_duration:.2f}\n"
                            f"exec&save duration: {save_duration:.2f}\n")
            pause(mark, "exec&saved", duration=save_duration, skip=3)
#            driver.quit()
        except Exception:
            import traceback
            traceback.print_exc()
            driver.save_screenshot(scr.filename('4boom'))

    # the first one is different, it receives its window 
    # in a natural way; other windows need to be open from there
    notebook0, *others = notebooks
    
    fetch_one_notebook(notebook0, False)
    for other in others:
        fetch_one_notebook(other, True)
    driver.quit()


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def main():
    # unfuffer standard output
    sys.stdout = Unbuffered(sys.stdout)

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-U", "--url", default=default_topurl,
                        dest='topurl',
                        help="url to reach nbhosting server")
    parser.add_argument("-l", "--list", default=False, action='store_true',
                        help="when given, lists known notebooks and does *not* open anything")
    parser.add_argument("-u", "--user", default='student-0001',
                        help="username for opening that notebook")
    parser.add_argument("-s", "--sleep", default=default_sleep_internal, type=float,
                        help="delay in seconds to sleep between actions inside nbhtest")
    parser.add_argument("-c", "--cut", default=False, 
                        help="""just load the urls, don't do any further processing""")
    parser.add_argument("notebooks", default=[f"{default_course_gitdir}:0"],
                        nargs='*',
                        help="""define the notebook to open; this is ':'-separated
                                with its first part a git repo, and the second part 
                                an index in the list of known notebooks
                                - run with -l to see list""")
    args = parser.parse_args()
    
    if args.list:
        for notebook_arg in args.notebooks:
            coursedir = notebook_arg.split(':')[0]
            contents = Contents(coursedir)
            coursename = contents.coursename
            notebooks = contents.notebooks
            print(f"{20*'-'} {len(notebooks)} notebooks in course {coursename}")
            contents.print()
    else:
        notebook_objs = [Notebook(notebook_arg) for notebook_arg in args.notebooks]
        run(args.topurl, args.user, notebook_objs, args.sleep, args.cut)

if __name__ == '__main__':
    main()

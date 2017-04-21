#!/usr/bin/env python3
import time
from itertools import chain

# pip3 install 
from selenium import webdriver


# NOTE about installing phantomjs
# I first installed phantomjs from a binary distrib in
# ~/git/nbhosting/tests/phantomjs-2.1.1-macosx/bin/phantomjs
# then I created a symlink in ~/bin
# a mere alias would not be good enough, or we'd need to specify the
# full path of phantomjs to the webdriver.PhantomJS constructor


def list_bioinfo_notebooks():
    from pathlib import Path
    bioinfo = Path.home() / "git" / "flotbioinfo"
    paths = chain((bioinfo / "w1").glob("fr*nb"), (bioinfo / "w1").glob("en*nb"))
    return [x.stem for x in paths]

bioinfo_notebooks = list_bioinfo_notebooks()


clear_all_on_document_load = "$(function() { Jupyter.notebook.clear_all_output(); })"
run_all = "Jupyter.notebook.execute_all_cells()"


def pause(message, delay):
    print("{} - waiting for an extra {}s"
          .format(message, delay))
    time.sleep(delay)


def screenshot(name, index):
    return "screenshot-{name}-{index}.png"\
        .format(**locals())

def run(index, user, delay):
    """
    fetch bioinfo notebook of that index as this user
    and click the 'run-all-cells' button
    """
    nb = bioinfo_notebooks[index]
    url = "https://nbhosting.inria.fr/ipythonExercice/flotbioinfo/w1/{nb}/{user}"\
          .format(**locals())

    print("fetching URL {url}".format(url=url))
    driver = webdriver.PhantomJS() # or add to your PATH
    driver.set_window_size(1024, 768) # optional
    driver.get(url)
    print("GET OK")
    driver.save_screenshot(screenshot('0bare', index))
    driver.execute_script(clear_all_on_document_load)
    pause("cleared all", delay)
    driver.save_screenshot(screenshot('1clear', index))
    driver.execute_script(run_all)
    pause("executing all all", delay)
    driver.save_screenshot(screenshot('2eval', index))
    driver.quit()


def list():
    """List found notebooks in bioinfo with their index"""
    for i, n in enumerate(bioinfo_notebooks):
        print(i, n)


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-i", "--index", default=0, type=int)
    parser.add_argument("-u", "--user", default='phantom')
    parser.add_argument("-d", "--delay", default=3, type=int)
    parser.add_argument("-l", "--list", default=False, action='store_true')
    args = parser.parse_args()
    if args.list:
        list()
    else:
        run(args.index, args.user, args.delay)

if __name__ == '__main__':
    main()

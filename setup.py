#!/usr/bin/env python3

from setuptools import setup, find_packages

from nbhosting import __version__

try:
    with open("README.md") as readme:
        long_description = readme.read()
except Exception as e:
    long_description = "no description could be found"

setup(
    name = 'nbhosting',
    version = __version__,
    author = "Thierry Parmentelat",
    author_email = "thierry.parmentelat@inria.fr",
    packages = find_packages(),
    url = "https://github.com/parmentelat/nbhosting",
    license = "See LICENSE",
    description = "An infrastructure for hosting notebooks beind an open-edX MOOC platform",
    long_description = long_description,
    install_requires = [
        'Django',
    ],
    setup_requires = [],
    tests_require = [],

    # see https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.5', 
    ],
)

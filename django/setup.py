#!/usr/bin/env python

from setuptools import setup, find_packages

# to allow for relative import in an entry point
__package__ = 'nbhosting'
from .version import __version__


try:
    with open("README.md") as readme:
        long_description = readme.read()
except Exception as exc:
    long_description = "no description could be found"

setup(
    name='nbhosting',
    version=__version__,
    author="Thierry Parmentelat",
    author_email="thierry.parmentelat@inria.fr",
    packages=find_packages(),
    url="https://github.com/parmentelat/nbhosting",
    license="See LICENSE",
    description=(
        "An infrastructure for hosting notebooks behind an open-edX"
        " MOOC platform, or for registered students like in a classroom"
    ),
    long_description=long_description,
    install_requires=[
        'pip',
        'setuptools',
        'wheel',
        'django',
        'django_extensions',
        'jsonpickle',
        'nbformat',
        'jupytext',
        'aiohttp',
        'podman',
        'rich',        # this is for podman, should not be needed, see also
                       # https://github.com/containers/podman/issues/20964
        'redis',
        'nbstripout',  # for course-pull
        'pandas',      # for mass-register
    ],
    setup_requires=[],
    tests_require=[],

    # see https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
from pgup import __version__

setup(
    name="pgup",
    version=__version__,
    url="http://pythonhosted.org/pgup",
    description="pgup - util for build postgresql structure",
    license='MIT',
    author="Stepan Perlov",
    author_email="stepanperlov@gmail.com",
    install_requires=["PyYAML", "jinja2", "pyparsing"],
    packages=["pgup"],
    package_data={'pgup': ['templates/*.j2']},
    data_files=[('/etc', ['etc/pgup.yaml'])],
    platforms=["linux"]
)

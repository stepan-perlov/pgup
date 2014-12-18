#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
from pgup import __version__

setup(
    name="pgup",
    version=__version__,
    url="http://pythonhosted.org/pgup",
    description="pgup - util for postgresql update",
    license='MIT',
    author="Stepan Perlov",
    author_email="stepanperlov@gmail.com",
    install_requires=["PyYAML", "jinja2", "python-make"],
    packages=["pgup"],
    package_data={'pgup': ['templates/*.j2']},
    scripts=["bin/pgup"],
    data_files=[('/etc', ['etc/pgup.yaml'])],
    platforms=["linux"]
)

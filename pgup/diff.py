# -*- coding: utf-8 -*-
from pake.shell import git


def diff(commit, config):
    pipe = git("diff --name-only {} HEAD".format(commit), pipe=True)
    diff = pipe.grep("\\\\|".join(config.databases)).split()

"""miscellany pgctl functions"""
from __future__ import absolute_import
from __future__ import unicode_literals

import json
import os

from frozendict import frozendict


def exec_(argv, env=None):  # pragma: no cover
    """Wrapper to os.execv which runs any atexit handlers (for coverage's sake).
    Like os.execv, this function never returns.
    """
    if env is None:
        env = os.environ

    # in python3, sys.exitfunc has gone away, and atexit._run_exitfuncs seems to be the only pubic-ish interface
    #   https://hg.python.org/cpython/file/3.4/Modules/atexitmodule.c#l289
    import atexit
    atexit._run_exitfuncs()  # pylint:disable=protected-access
    os.execvpe(argv[0], argv, env)  # never returns


def uniq(iterable):
    """remove duplicates while preserving ordering -- first one wins"""
    return tuple(_uniq(iterable))


def _uniq(iterable):
    seen = set()
    for i in iterable:
        if i in seen:
            pass
        else:
            yield i
            seen.add(i)


class JSONEncoder(json.JSONEncoder):
    """knows that frozendict is like dict"""

    def default(self, obj):  # pylint:disable=method-hidden
        if isinstance(obj, frozendict):
            return dict(obj)
        else:
            # Let the base class default method raise the TypeError
            return json.JSONEncoder.default(self, obj)
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os

import pytest
from py._path.local import LocalPath as Path
from testing import norm
from testing.assertions import assert_svstat
from testing.assertions import wait_for
from testing.subprocess import assert_command

from pgctl.daemontools import SvStat


pytestmark = pytest.mark.usefixtures('in_example_dir')
SLOW_STARTUP_TIME = 6


@pytest.yield_fixture
def service_name():
    yield 'slow-startup'


def it_times_out():
    assert_command(
        ('pgctl-2015', 'start'),
        '''\
''',
        '''\
[pgctl] Starting: slow-startup
[pgctl] ERROR: service 'slow-startup' failed to start after {TIME} seconds, its status is up (pid {PID}) {TIME} seconds
==> playground/slow-startup/log <==
[pgctl] Stopping: slow-startup
[pgctl] Stopped: slow-startup
[pgctl] ERROR: Some services failed to start: slow-startup
''',
        1,
        norm=norm.pgctl,
    )
    assert_svstat('playground/slow-startup', state=SvStat.UNSUPERVISED)

    assert_command(
        ('pgctl-2015', 'log'),
        '''\
==> playground/slow-startup/log <==
{TIMESTAMP} pgctl-poll-ready: service is stopping -- quitting the poll
''',
        '',
        0,
        norm=norm.pgctl,
    )


def it_can_succeed():
    from mock import patch, ANY
    with patch.dict(os.environ, [('PGCTL_TIMEOUT', str(SLOW_STARTUP_TIME))]):
        assert_command(
            ('pgctl-2015', 'start'),
            '',
            #'[pgctl] Starting: slow-startup\n[pgctl] Started: slow-startup\n',
            ANY,
            0
        )
    assert_svstat('playground/slow-startup', state='ready')


def it_restarts_on_unready():

    def it_is_ready():
        assert_svstat('playground/slow-startup', state='ready')

    def it_becomes_unready():
        from testfixtures import Comparison as C
        from pgctl.daemontools import svstat
        assert svstat('playground/slow-startup') != C(SvStat, {'state': 'ready'}, strict=False)

    it_can_succeed()
    os.remove('playground/slow-startup/readyfile')
    wait_for(it_becomes_unready)
    wait_for(it_is_ready)

    assert_command(
        ('pgctl-2015', 'log'),
        '''\
==> playground/slow-startup/log <==
{TIMESTAMP} pgctl-poll-ready: service's ready check succeeded
{TIMESTAMP} pgctl-poll-ready: service's ready check failed -- we are restarting it for you
{TIMESTAMP} [pgctl] Stopping: slow-startup
{TIMESTAMP} [pgctl] Stopped: slow-startup
{TIMESTAMP} [pgctl] Starting: slow-startup
{TIMESTAMP} pgctl-poll-ready: service's ready check succeeded
{TIMESTAMP} [pgctl] Started: slow-startup
''',
        '',
        0,
        norm=norm.pgctl,
    )


def it_removes_down_file():
    path = Path(os.getcwd()).join('playground/slow-startup/down')
    path.ensure()
    assert path.check()
    it_can_succeed()
    assert not path.check()

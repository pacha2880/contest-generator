"""Shared cancellation signal for long-running flows (app.py/atcoder.py/
gym.py). A should_stop() callback returning True at a loop checkpoint raises
this; callers that want "Stop" support (the GUI) catch it to tell a
cancelled run apart from an actual error."""


class StoppedByUser(Exception):
    pass

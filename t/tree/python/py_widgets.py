"""Module docstring mentions py_make_widget but is not a reference."""

import os

PY_WIDGET_LIMIT = 3

class PyWidget:
    """Class docstring mentions py_make_widget."""

    def __init__(self, label):
        self.label = label  # comment mentions py_make_widget

    def render(self):
        return "py_make_widget"

def py_make_widget(label):
    # py_make_widget in a comment should not count
    text = "py_make_widget inside a string"
    return PyWidget(label)

def py_use_widget():
    made = py_make_widget("demo")
    return made.render()

async def py_async_widget():
    return py_make_widget("async")

# t/tree/python/py_widgets.py
# SPDX-License-Identifier: CC0-1.0

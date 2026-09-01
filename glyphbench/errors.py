"""VELD error types.

Errors reveal syntax and constraints, never semantics/purpose.
"""


class VeldError(Exception):
    """An op call was refused. The message is shown verbatim to the agent."""


class VeldWarning:
    """A non-fatal advisory attached to an observation."""

    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return self.text

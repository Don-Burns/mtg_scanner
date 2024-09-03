from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.config.argparsing import Parser
    from _pytest.nodes import Item


def pytest_addoption(parser: Parser):
    """
    parse for run options
    """
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--runint", action="store_true", default=False, help="run integration tests"
    )
    parser.addoption(
        "--runall", action="store_true", default=False, help="run all tests"
    )


def pytest_runtest_setup(item: Item):
    """
    What to do when certain markers are encountered.
    Ref: https://stackoverflow.com/questions/47559524/pytest-how-to-skip-tests-unless-you-declare-an-option-flag

    """
    if item.config.getoption("--runall"):
        return
    markers = [mark.name for mark in item.iter_markers()]
    if "slow" in markers and not item.config.getoption("--runslow"):
        pytest.skip("need --runslow option to run slow tests")
    if "integration" in markers and not item.config.getoption("--runint"):
        pytest.skip("need --runint option to run integration tests")

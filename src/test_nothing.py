import pytest

from .nothing import add_numbers


@pytest.mark.unit
def test_add_numbers():
    assert add_numbers(1, 2) == 3
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0
    assert add_numbers(-5, -5) == -10
    assert add_numbers(100, 200) == 300

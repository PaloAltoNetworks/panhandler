import pytest
import os


@pytest.mark.docker_env
def test_terraform():
    rv = os.system('which terraform')
    assert rv == 0


@pytest.mark.docker_env
def test_bash():
    rv = os.system('which bash')
    assert rv == 0


@pytest.mark.docker_env
def test_az():
    rv = os.system('which az')
    assert rv == 0



from pathlib import Path

import pytest


@pytest.fixture
def server_widget():
    from SlicerTrameServer import Widget

    return Widget()


@pytest.fixture
def bootstrap(tmpdir, server_widget):
    dest_file = Path(tmpdir) / "slicer_trame_bootstrap.py"

    # Create the bootstrap file
    server_widget.createBootstrapFile(dest_file, "EXAMPLE_COMMAND")

    # Check that the bootstrap exists and is not empty
    assert dest_file.exists()
    assert dest_file.read_text()
    return dest_file


def get_fixture(request, name):
    return request.getfixturevalue(name)


def get_server_widget(request):
    return get_fixture(request, server_widget.__name__)


def get_bootstrap(request) -> Path:
    return get_fixture(request, bootstrap.__name__)

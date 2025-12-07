import os


def test_backend_folder_exists():
    assert os.path.isdir(os.path.join(os.path.dirname(__file__), '..'))

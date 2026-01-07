import importlib


def test_import_package():
    """Basic smoke test ensuring package is importable and exposes a version."""
    mod = importlib.import_module("big_data_rag")
    assert hasattr(mod, "__version__")
    assert isinstance(mod.__version__, str)

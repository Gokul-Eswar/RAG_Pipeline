import importlib


def test_import_package():
    """Basic smoke test ensuring src package is importable and exposes a version."""
    mod = importlib.import_module("src")
    assert hasattr(mod, "__version__")
    assert isinstance(mod.__version__, str)
    assert mod.__version__ == "0.1.0"

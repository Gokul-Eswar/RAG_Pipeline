# Developer quickstart

Use the steps below for local development and quick verification.

- Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

- Run the tiny launcher to verify the package imports:

```bash
python run.py
```

- Run tests (uses `pytest`):

```bash
pytest -q
```

If you prefer a `src` layout or CI config, tell me and I will scaffold it.

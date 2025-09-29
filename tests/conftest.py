import os
import sys
from pathlib import Path
import pytest

# Make sure project root is on sys.path so `import api` works under pytest
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure Flask uses the production DB bundled in repo
# No special setup needed; api.index resolves DB_PATH relative to file location.

@pytest.fixture(scope="session")
def app():
    from api.index import create_app
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    return app


@pytest.fixture()
def client(app):
    return app.test_client()

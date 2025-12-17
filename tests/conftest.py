import os
import pytest

from app import create_app
from extensions import mongo


@pytest.fixture(scope='module')
def app():
    # Create app using testing config; allow override with MONGO_URI_TEST env var
    test_uri = os.environ.get('MONGO_URI_TEST') or os.environ.get('MONGO_URI')
    app = create_app('testing')
    if test_uri:
        app.config['MONGO_URI'] = test_uri
    with app.app_context():
        # ensure extensions initialized
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()

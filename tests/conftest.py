import os
import tempfile

import pytest

from app import create_app, db, Sala


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
    })

    with application.app_context():
        db.create_all()
        db.session.add(Sala(nome="Sala Teste", capacidade=10))
        db.session.add(Sala(nome="Sala Grande", capacidade=50))
        db.session.commit()

    yield application

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sala_id(app):
    with app.app_context():
        return Sala.query.filter_by(nome="Sala Teste").first().id

from datetime import datetime

import pytest

from yap import create_app, db
from yap.models import Paste


@pytest.fixture
def app(tmpdir):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmpdir.join('db')}"})

    with app.app_context():
        db.create_all()
        some_paste = Paste(
            uuid="foo_uuid",
            filename="foo.txt",
            contents="some contents",
            created_at=datetime.fromisoformat("2020-07-01 10:30:50"),
            visibility=Paste.Visibility.public,
            expire_at=datetime.fromisoformat("2320-09-01 10:30:50"),
            author_ip="192.168.42.2",
        )
        db.session.add(some_paste)
        db.session.commit()

    return app


@pytest.fixture
def client(app):
    return app.test_client()

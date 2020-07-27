import datetime
import http

import pytest

from yap import db
from yap.models import Paste
from yap.paste import UNTITLED_FILE, get_latest_pastes


def make_paste(
    uuid, filename="foo", contents="bar", visibility="public", created_at=None, expire_at=None, author_ip="baz",
):
    return Paste(
        uuid=uuid,
        filename=filename,
        contents=contents,
        visibility=visibility,
        created_at=created_at or datetime.datetime.utcnow(),
        expire_at=expire_at or datetime.datetime.utcnow() + datetime.timedelta(days=1),
        author_ip=author_ip,
    )


def test_create(client, app):
    assert client.get("/").status_code == 200

    response = client.post(
        "/", data=dict(filename="foo", contents="some\ncontents", visibility="hidden", expire_in="7 days",)
    )
    assert response.status_code == 302

    with app.app_context():
        paste = Paste.query.order_by(Paste.created_at.desc()).first()
        assert paste.filename == "foo"
        assert paste.contents == "some\ncontents"
        assert paste.visibility == Paste.Visibility.hidden
        assert paste.author_ip == "127.0.0.1"


FILL_REQUIRED_FIELDS = "Please fill all the required fields."


@pytest.mark.parametrize(
    ("data", "expected_error"),
    [
        (dict(filename="", contents="", visibility="", expire_in=""), FILL_REQUIRED_FIELDS),
        (dict(filename="foo", contents="", visibility="baz", expire_in="qux"), FILL_REQUIRED_FIELDS),
        (dict(filename="foo", contents="bar", visibility="", expire_in="qux"), FILL_REQUIRED_FIELDS),
        (dict(filename="foo", contents="bar", visibility="baz", expire_in=""), FILL_REQUIRED_FIELDS),
        (
            dict(filename="foo", contents="bar", visibility="hidden", expire_in="invalid value"),
            "Expiration date is not in a valid range.",
        ),
        (
            dict(filename="foo", contents="bar", visibility="invalid_value", expire_in="7 days"),
            "Invalid visibility level.",
        ),
    ],
)
def test_create_validation(client, data, expected_error):
    response = client.post("/", data=data)
    assert expected_error in response.get_data(as_text=True)


def test_create_with_default_filename(client, app):
    response = client.post("/", data=dict(filename="", contents="bar", visibility="hidden", expire_in="7 days"))
    assert response.status_code == 302

    with app.app_context():
        paste = Paste.query.order_by(Paste.created_at.desc()).first()
        assert paste.filename == UNTITLED_FILE


def test_show(client):
    response = client.get("/paste/foo_uuid")
    response_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "foo.txt" in response_text
    assert "some contents" in response_text


def test_raw_show(client):
    response = client.get("/paste/foo_uuid/raw")

    assert response.status_code == 200
    assert response.content_type == "application/octet-stream"
    assert "some contents".encode() == response.get_data()


def test_expiration_date_is_respected(client, app):
    with app.app_context():
        paste = make_paste("expired_paste", expire_at=datetime.datetime.utcnow() - datetime.timedelta(milliseconds=1))
        db.session.add(paste)
        db.session.commit()

    assert client.get("/paste/expired_paste").status_code == 404
    assert client.get("/paste/expired_paste/raw").status_code == 404


def test_get_latest_pastes(app):
    with app.app_context():
        db.session.add(make_paste(uuid="over_limit"))
        db.session.add(make_paste(uuid="older"))
        db.session.add(make_paste(uuid="hidden", visibility="hidden"))
        db.session.add(make_paste(uuid="expired", expire_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=1)))
        db.session.add(make_paste(uuid="newer"))
        db.session.commit()

        assert [paste.uuid for paste in get_latest_pastes(2)] == ["newer", "older"]


def test_paste_flood_is_prevented(client, app):
    rate_limit = datetime.timedelta(seconds=420)
    epsilon = datetime.timedelta(seconds=2)
    app.config["YAP_PASTE_RATE_LIMIT"] = rate_limit

    response = client.post("/", data=dict(filename="", contents="foo", visibility="hidden", expire_in="7 days"))
    assert response.status_code == http.HTTPStatus.FOUND
    response = client.post("/", data=dict(filename="", contents="bar", visibility="hidden", expire_in="7 days"))
    assert response.status_code == http.HTTPStatus.TOO_MANY_REQUESTS
    assert "Retry-After" in response.headers
    assert rate_limit - epsilon <= response.retry_after - datetime.datetime.utcnow() <= rate_limit

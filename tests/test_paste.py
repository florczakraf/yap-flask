import pytest

from yap.models import Paste


def test_create(client, app):
    assert client.get("/").status_code == 200

    response = client.post(
        "/", data=dict(filename="Untitled", contents="some\ncontents", visibility="hidden", expire_in="7 days",)
    )
    assert response.status_code == 302

    with app.app_context():
        paste = Paste.query.order_by(Paste.created_at.desc()).first()
        assert paste.filename == "Untitled"
        assert paste.contents == "some\ncontents"
        assert paste.visibility == Paste.Visibility.hidden
        assert paste.author_ip == "127.0.0.1"


FILL_REQUIRED_FIELDS = "Please fill all the required fields."


@pytest.mark.parametrize(
    ("data", "expected_error"),
    [
        (dict(filename="", contents="", visibility="", expire_in=""), FILL_REQUIRED_FIELDS),
        (dict(filename="", contents="bar", visibility="baz", expire_in="qux"), FILL_REQUIRED_FIELDS),
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


def test_show(client):
    response = client.get("/paste/foo_uuid")
    response_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "foo.txt" in response_text
    assert "some contents" in response_text

import pytest

from flaskr import db
from flaskr.models import User


def test_register(client, app):
    # test that viewing the page renders without template errors
    assert client.get("/auth/register").status_code == 200

    # test that successful registration redirects to the login page
    response = client.post("/auth/register",
                           data={"username": "a", "password": "a"})
    assert response.headers["Location"].endswith("/auth/login")

    # test that the user was inserted into the database
    with app.app_context():
        query = User.select().where(User.username == "a")
        assert db.session.scalar(query) is not None


def test_user_password(app):
    user = User(username="a", password="a")
    assert user.password_hash != "a"
    assert user.check_password("a")


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("", "", b"Username is required."),
        ("a", "", b"Password is required."),
        ("test", "test", b"already registered"),
    ),
)
def test_register_validate_input(client, username, password, message):
    response = client.post(
        "/auth/register", data={"username": username, "password": password}
    )
    assert message in response.data


def test_login(client, auth):
    # test that viewing the page renders without template errors
    assert client.get("/auth/login").status_code == 200

    # test that successful login redirects to the index page
    response = auth.login()
    assert response.headers["Location"] in ["http://localhost/", "/"]

    # login request set the user_id in the session
    # check that the user is loaded from the session
    with client:
        response = client.get("/")
        assert b"<span>test</span>" in response.data


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (("a", "test", b"Incorrect username."),
     ("test", "a", b"Incorrect password.")),
)
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        response = client.get("/")
        assert b"Log In" in response.data

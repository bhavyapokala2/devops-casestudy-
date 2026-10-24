import os
import unittest
from unittest.mock import MagicMock, patch

# Set a test URI before importing app.py. The tests mock DB calls,
# so MongoDB does not need to be running.
os.environ["MONGO_URI"] = "mongodb://localhost:27017/"
os.environ["DATABASE_NAME"] = "url_shortener"
os.environ["FLASK_SECRET_KEY"] = "test-secret"

import app as url_app


class URLShortenerTests(unittest.TestCase):
    def setUp(self):
        self.client = url_app.app.test_client()
        url_app.app.config["TESTING"] = True
        self.urls = url_app.urls
        self.patches = [
            patch.object(self.urls, "find"),
            patch.object(self.urls, "find_one"),
            patch.object(self.urls, "insert_one"),
            patch.object(self.urls, "find_one_and_update"),
        ]
        self.mocks = [p.start() for p in self.patches]
        self.find_mock, self.find_one_mock, self.insert_mock, self.update_mock = self.mocks

        cursor = MagicMock()
        cursor.sort.return_value.limit.return_value = []
        self.find_mock.return_value = cursor
        self.find_one_mock.return_value = None

    def login_user(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "user-123"
            session["username"] = "testuser"

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def test_home_page_requires_login(self):
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")

    def test_home_page_loads_for_logged_in_user(self):
        self.login_user()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Shorten your links", response.data)

    def test_user_sees_how_many_urls_they_created(self):
        self.login_user()
        cursor = MagicMock()
        cursor.sort.return_value.limit.return_value = [
            {"short_code": "abc123", "original_url": "https://example.com", "clicks": 2},
            {"short_code": "def456", "original_url": "https://example.org", "clicks": 1},
        ]
        self.find_mock.return_value = cursor
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"2 urls created", response.data)

    def test_logout_ends_session(self):
        self.login_user()
        response = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")

    def test_valid_url_is_accepted(self):
        self.assertTrue(url_app.is_valid_url("https://www.example.com/page"))

    def test_invalid_url_is_rejected(self):
        self.assertFalse(url_app.is_valid_url("not-a-url"))

    def test_short_url_is_created(self):
        self.login_user()
        with patch.object(url_app, "generate_short_code", return_value="abc123"):
            response = self.client.post(
                "/",
                data={"original_url": "https://www.example.com"},
                follow_redirects=True,
            )

        self.assertEqual(response.status_code, 200)
        self.insert_mock.assert_called_once()
        saved = self.insert_mock.call_args.args[0]
        self.assertEqual(saved["short_code"], "abc123")
        self.assertEqual(saved["original_url"], "https://www.example.com")
        self.assertEqual(saved["clicks"], 0)
        self.assertEqual(saved["created_by"], "user-123")
        self.assertIn(b"abc123", response.data)

    def test_invalid_url_is_not_saved(self):
        self.login_user()
        response = self.client.post(
            "/",
            data={"original_url": "not-a-url"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.insert_mock.assert_not_called()
        self.assertIn(b"valid URL", response.data)

    def test_short_url_redirects_to_original(self):
        self.update_mock.return_value = {
            "short_code": "abc123",
            "original_url": "https://www.example.com",
            "clicks": 1,
        }
        response = self.client.get("/abc123")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "https://www.example.com")
        self.update_mock.assert_called_once_with(
            {"short_code": "abc123"}, {"$inc": {"clicks": 1}}
        )

    def test_unknown_short_code_returns_404(self):
        self.update_mock.return_value = None
        response = self.client.get("/unknown123")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Short URL not found", response.data)

    def test_signup_saves_user_to_mongodb(self):
        with patch.object(url_app.users, "find_one", return_value=None), patch.object(url_app.users, "insert_one") as insert_mock:
            response = self.client.post(
                "/signup",
                data={
                    "email": "user@example.com",
                    "username": "user1",
                    "password": "secret123",
                    "domain": "example.com",
                },
                follow_redirects=True,
            )

        self.assertEqual(response.status_code, 200)
        insert_mock.assert_called_once()
        saved = insert_mock.call_args.args[0]
        self.assertEqual(saved["email"], "user@example.com")
        self.assertEqual(saved["username"], "user1")
        self.assertEqual(saved["domain"], "example.com")
        self.assertNotEqual(saved["password"], "secret123")

    def test_login_accepts_email_or_username(self):
        user_doc = {
            "email": "user@example.com",
            "username": "user1",
            "password": url_app.generate_password_hash("secret123"),
        }
        with patch.object(url_app.users, "find_one", return_value=user_doc):
            response = self.client.post(
                "/login",
                data={"email_or_username": "user1", "password": "secret123"},
                follow_redirects=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back", response.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)

import sqlite3
import unittest

import reset_password
import server
from testsupport import ServerTestCase, TEST_USER, TEST_PASSWORD


class ResetPasswordTests(ServerTestCase):

    def test_reset_changes_login_keeps_patients_and_ends_sessions(self):
        count = lambda: sqlite3.connect(server.DB_PATH).execute('SELECT COUNT(*) FROM patient').fetchone()[0]
        before = count()
        name = reset_password.reset_password(server.DB_PATH, TEST_USER.upper(), "brand-new-pass-1")
        self.assertEqual(name, TEST_USER)
        self.assertEqual(count(), before)
        status, _ = self.call("GET", "/api/patients", headers=self.auth)
        self.assertEqual(status, 401)                       # old token is gone
        status, _ = self.call("POST", "/api/auth/login", {"username": TEST_USER, "password": TEST_PASSWORD})
        self.assertEqual(status, 401)                       # old password no longer works
        status, body = self.call("POST", "/api/auth/login", {"username": TEST_USER, "password": "brand-new-pass-1"})
        self.assertEqual(status, 200, body)

    def test_short_password_and_unknown_login_are_refused(self):
        with self.assertRaises(ValueError):
            reset_password.reset_password(server.DB_PATH, TEST_USER, "short")
        with self.assertRaises(ValueError):
            reset_password.reset_password(server.DB_PATH, "nobody", "long-enough-pass")


if __name__ == "__main__":
    unittest.main()

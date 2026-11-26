"""
The Therapist app must never reuse a server that uses a different copy of the database
(e.g. "python server.py" on the Microsoft Store Python, whose writes under %LOCALAPPDATA% go to a private copy).
Each database file carries a random ID; the server reports it and the app compares it with its own.
"""
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

import app
import server
from testsupport import ServerTestCase


class DatabaseIdRouteTests(ServerTestCase):

    def test_setup_reports_a_stable_database_id(self):
        status, first = self.call("GET", "/api/auth/setup")
        self.assertEqual(status, 200)
        self.assertRegex(first["databaseId"], r"^[0-9a-f]{32}$")
        _, second = self.call("GET", "/api/auth/setup")
        self.assertEqual(first["databaseId"], second["databaseId"])

    def test_id_matches_the_file_the_server_uses(self):
        _, body = self.call("GET", "/api/auth/setup")
        self.assertEqual(body["databaseId"], server.database_id_of(server.DB_PATH))


class DatabaseIdTests(unittest.TestCase):

    def test_two_files_get_different_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            ids = []
            for name in ("a.db", "b.db"):
                path = os.path.join(tmp, name)
                sqlite3.connect(path).close()
                ids.append(server.database_id_of(path))
            self.assertNotEqual(ids[0], ids[1])
            self.assertEqual(ids[0], server.database_id_of(os.path.join(tmp, "a.db")))   # kept once created

    def test_missing_file_has_no_id_and_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "none.db")
            self.assertIsNone(server.database_id_of(path))
            self.assertFalse(os.path.exists(path))

    def test_app_reuses_a_server_only_with_the_same_database(self):
        self.assertTrue(app.same_database("abc", "abc"))
        self.assertFalse(app.same_database("abc", "def"))
        self.assertFalse(app.same_database(None, "abc"))     # older server without databaseId
        self.assertFalse(app.same_database(None, None))


class StorePythonWarningTests(unittest.TestCase):

    def test_warns_for_store_python_on_the_real_database(self):
        with mock.patch.object(server, "is_store_python", return_value=True), \
             mock.patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\x\AppData\Local"}):
            self.assertIn("DIFFERENT database",
                          server.store_python_warning(r"C:\Users\x\AppData\Local\TheraQuest\theraquest.db"))
            self.assertEqual(server.store_python_warning(r"C:\tests\scratch.db"), "")   # test database elsewhere

    def test_no_warning_for_other_pythons(self):
        with mock.patch.object(server, "is_store_python", return_value=False), \
             mock.patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\x\AppData\Local"}):
            self.assertEqual(server.store_python_warning(r"C:\Users\x\AppData\Local\TheraQuest\theraquest.db"), "")


if __name__ == "__main__":
    unittest.main()

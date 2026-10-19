"""
Shared test harness: runs the real server on a throwaway database and makes HTTP calls to it.
Used by test_authorization.py and test_backend.py.
"""
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import server

TEST_USER, TEST_PASSWORD = "clinician", "correct-horse-42"


class ServerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="tq_test_")
        cls._real_db = server.DB_PATH
        server.DB_PATH = os.path.join(cls.tmp, "test.db")
        server.init_db()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

        status, body = cls.call("POST", "/api/auth/setup", {"username": TEST_USER, "password": TEST_PASSWORD})
        assert status == 201, body
        cls.token = body["token"]
        cls.auth = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        server.DB_PATH = cls._real_db
        server._login_failures.clear()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def call(cls, method, path, body=None, headers=None, raw=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(cls.base + path, data=data, method=method, headers=dict(headers or {}))
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                payload, status = r.read(), r.status
        except urllib.error.HTTPError as e:
            payload, status = e.read(), e.code
        try:
            return status, json.loads(payload or b"null")
        except ValueError:
            return status, payload

    @classmethod
    def patient_ids(cls):
        _, patients = cls.call("GET", "/api/patients", headers=cls.auth)
        return {p["code"]: p["id"] for p in patients}

    @staticmethod
    def session_body(patient_id, exercises=(), **extra):
        body = {"patient_id": patient_id, "ended_early": False, "input_source": "webcam", "points": 0,
                "started_at": "2026-10-20T09:00:00", "ended_at": "2026-10-20T09:20:00", "exercises": list(exercises)}
        body.update(extra)
        return body

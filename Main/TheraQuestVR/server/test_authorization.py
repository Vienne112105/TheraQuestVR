"""
Authorization tests for M3.2 (DEC-009): therapist-only clinical routes and
patient-code-scoped VR routes. Runs the real server on a throwaway database.

Run:   python test_authorization.py
"""
import unittest

import server
from testsupport import ServerTestCase, TEST_USER, TEST_PASSWORD


class AuthorizationTests(ServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        status, body = cls.call("POST", "/api/patients", {"code": "P-900", "name": "Isolation test"}, cls.auth)
        assert status == 201, body
        ids = cls.patient_ids()
        cls.p1, cls.p900 = ids["P-001"], ids["P-900"]

    def session_body(self, patient_id):
        return {"patient_id": patient_id, "ended_early": True, "input_source": "simulated", "points": 0, "exercises": []}

    # ------------------------------------------------ therapist routes
    def protected_routes(self):
        p = self.p1
        return [
            ("GET", "/api/patients", None),
            ("POST", "/api/patients", {"code": "P-999"}),
            ("GET", f"/api/patients/{p}/program", None),
            ("PUT", f"/api/patients/{p}/program", {}),
            ("GET", f"/api/patients/{p}/dashboard", None),
            ("POST", f"/api/patients/{p}/exercises", {"code": "slr"}),
            ("DELETE", f"/api/patients/{p}/exercises/1", None),
            ("POST", f"/api/patients/{p}/phase", {"phase_id": 1}),
            ("DELETE", f"/api/patients/{p}/protocol", None),
            ("GET", "/api/protocols", None),
            ("POST", "/api/protocols", {"name": "x"}),
            ("DELETE", "/api/protocols/1", None),
            ("POST", "/api/protocols/1/phases", {"name": "x"}),
            ("PUT", "/api/protocols/1/phases/1", {"goals": "x"}),
            ("PUT", f"/api/patients/{p}", {"name": "x"}),
            ("POST", f"/api/patients/{p}/archive", {"archived": True}),
            ("GET", "/api/library", None),
            ("PUT", "/api/sessions/1/clinical", {"pain_pre": 1}),
            ("GET", "/api/export?format=json", None),
            ("GET", f"/api/patients/{p}/export?format=json", None),
            ("POST", "/api/sessions", self.session_body(p)),   # removed legacy upload route
        ]

    def test_protected_routes_reject_missing_token(self):
        for method, path, body in self.protected_routes():
            with self.subTest(method=method, path=path):
                status, _ = self.call(method, path, body)
                self.assertEqual(status, 401)

    def test_protected_routes_reject_bad_token(self):
        bad = {"Authorization": "Bearer " + "0" * 64}
        for method, path, body in self.protected_routes():
            with self.subTest(method=method, path=path):
                status, _ = self.call(method, path, body, bad)
                self.assertEqual(status, 401)

    def test_patient_code_does_not_unlock_therapist_routes(self):
        status, _ = self.call("GET", f"/api/patients/{self.p1}/program", headers={"X-Patient-Code": "P-001"})
        self.assertEqual(status, 401)

    def test_valid_token_is_accepted(self):
        status, body = self.call("GET", f"/api/patients/{self.p1}/program", headers=self.auth)
        self.assertEqual(status, 200)
        self.assertEqual(body["patient"]["code"], "P-001")

    def test_query_token_only_on_export(self):
        status, _ = self.call("GET", f"/api/export?format=json&token={self.token}")
        self.assertEqual(status, 200)
        status, _ = self.call("GET", f"/api/patients?token={self.token}")
        self.assertEqual(status, 401)

    def test_logged_out_token_is_rejected(self):
        _, body = self.call("POST", "/api/auth/login", {"username": TEST_USER, "password": TEST_PASSWORD})
        temp = {"Authorization": f"Bearer {body['token']}"}
        self.assertEqual(self.call("GET", "/api/patients", headers=temp)[0], 200)
        self.call("POST", "/api/auth/logout", headers=temp)
        self.assertEqual(self.call("GET", "/api/patients", headers=temp)[0], 401)

    # ------------------------------------------------ VR routes
    def test_vr_program_requires_patient_code(self):
        self.assertEqual(self.call("GET", "/api/vr/program")[0], 401)
        self.assertEqual(self.call("GET", "/api/vr/program", headers={"X-Patient-Code": "P-404"})[0], 401)

    def test_vr_program_is_scoped_to_code(self):
        status, body = self.call("GET", "/api/vr/program", headers={"X-Patient-Code": "p-900"})
        self.assertEqual(status, 200)
        self.assertEqual(body["patient"]["id"], self.p900)
        self.assertEqual(body["patient"]["code"], "P-900")

    def test_vr_session_upload_with_own_code(self):
        status, body = self.call("POST", "/api/vr/sessions", self.session_body(self.p900), {"X-Patient-Code": "P-900"})
        self.assertEqual(status, 201)
        self.assertIn("session_id", body)

    def test_vr_session_offline_id_uses_code(self):
        status, _ = self.call("POST", "/api/vr/sessions", self.session_body(0), {"X-Patient-Code": "P-900"})
        self.assertEqual(status, 201)

    def test_vr_session_cannot_write_other_patient(self):
        status, _ = self.call("POST", "/api/vr/sessions", self.session_body(self.p1), {"X-Patient-Code": "P-900"})
        self.assertEqual(status, 403)

    def test_vr_session_requires_code(self):
        self.assertEqual(self.call("POST", "/api/vr/sessions", self.session_body(self.p1))[0], 401)

    def test_vr_routes_reject_non_loopback(self):
        real = server.Handler._client_is_loopback
        server.Handler._client_is_loopback = lambda self: False
        try:
            self.assertEqual(self.call("GET", "/api/vr/program", headers={"X-Patient-Code": "P-001"})[0], 403)
            status, _ = self.call("POST", "/api/vr/sessions", self.session_body(self.p1), {"X-Patient-Code": "P-001"})
            self.assertEqual(status, 403)
        finally:
            server.Handler._client_is_loopback = real


if __name__ == "__main__":
    unittest.main(verbosity=2)

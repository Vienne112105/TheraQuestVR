"""
Backend security and data-integrity tests for M4.2: static file containment, no CORS, input validation,
server-side completion rules, idempotent uploads, protocol replacement, prescription bounds, error codes,
migration of old databases, password change and login throttling.

Run:   python test_backend.py
"""
import http.client
import os
import shutil
import sqlite3
import tempfile
import unittest

import server
from testsupport import ServerTestCase, TEST_USER, TEST_PASSWORD


class BackendTests(ServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.p1 = cls.patient_ids()["P-001"]
        cls.vr = {"X-Patient-Code": "P-001"}

    def raw_get(self, path, headers=None):
        """GET without any URL clean-up, like `curl --path-as-is`."""
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=10)
        conn.request("GET", path, headers=headers or {})
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, dict(resp.getheaders()), body

    def vr_program(self, code="P-001"):
        status, body = self.call("GET", "/api/vr/program", headers={"X-Patient-Code": code})
        self.assertEqual(status, 200, body)
        return body

    def full_results(self, program, **overrides):
        out = []
        for e in program["exercises"]:
            need = e["reps"] * max(1, e["sets"])
            r = {"exercise_id": e["id"], "target_reps": need, "valid_reps": need, "attempts": need,
                 "avg_accuracy": 90, "mean_angle_error": 3, "unsafe_reps": 0}
            r.update(overrides)
            out.append(r)
        return out

    # ------------------------------------------------ static files and CORS
    def test_static_traversal_is_refused(self):
        for path in ("/static/../server.py", "/static/../theraquest.db", "/static/vendor/../../server.py",
                     "/static/C:/Windows/win.ini"):
            with self.subTest(path=path):
                status, _, body = self.raw_get(path)
                self.assertIn(status, (403, 404))
                self.assertNotIn(b"import", body)

    def test_static_vendor_file_served(self):
        status, headers, _ = self.raw_get("/static/vendor/chart.umd.min.js")
        self.assertEqual(status, 200)
        self.assertIn("javascript", headers.get("Content-Type", ""))

    def test_no_cors_headers(self):
        for path in ("/api/auth/setup", "/api/patients", "/"):
            with self.subTest(path=path):
                _, headers, _ = self.raw_get(path, {"Origin": "http://evil.example"})
                self.assertFalse(any(h.lower().startswith("access-control-") for h in headers))

    def test_vr_route_refuses_browser_origin(self):
        status, _ = self.call("POST", "/api/vr/sessions", self.session_body(self.p1),
                              {"X-Patient-Code": "P-001", "Origin": "http://evil.example"})
        self.assertEqual(status, 403)

    # ------------------------------------------------ input validation (stored script)
    def test_script_in_session_time_rejected(self):
        body = self.session_body(self.p1, started_at="<img src=x onerror=alert(1)>")
        status, _ = self.call("POST", "/api/vr/sessions", body, self.vr)
        self.assertEqual(status, 400)
        _, dash = self.call("GET", f"/api/patients/{self.p1}/dashboard", headers=self.auth)
        self.assertFalse(any("<" in s["started_at"] for s in dash["sessions"]))

    def test_dashboard_session_paging(self):
        for _ in range(2):
            self.call("POST", "/api/vr/sessions", self.session_body(self.p1), self.vr)
        con = sqlite3.connect(server.DB_PATH)
        total = con.execute("SELECT COUNT(*) FROM session WHERE patient_id=?", (self.p1,)).fetchone()[0]
        con.close()
        # A limit below one page still returns a full page (the 14-day KPIs come from these rows)
        _, dash = self.call("GET", f"/api/patients/{self.p1}/dashboard?sessions=1", headers=self.auth)
        self.assertEqual(dash["sessionsTotal"], total)
        self.assertEqual(len(dash["sessions"]), min(total, server.SESSION_PAGE))
        status, _ = self.call("GET", f"/api/patients/{self.p1}/dashboard?sessions=abc", headers=self.auth)
        self.assertEqual(status, 400)

    def test_unknown_input_source_rejected(self):
        status, _ = self.call("POST", "/api/vr/sessions", self.session_body(self.p1, input_source="<b>x</b>"), self.vr)
        self.assertEqual(status, 400)

    # ------------------------------------------------ completion and progression rules
    def test_complete_uses_server_prescription(self):
        prog = self.vr_program()
        # Client claims a target of 0 and does nothing: must not count as complete
        lazy = self.full_results(prog, target_reps=0, valid_reps=0, attempts=0)
        status, body = self.call("POST", "/api/vr/sessions", self.session_body(self.p1, lazy), self.vr)
        self.assertEqual(status, 201, body)
        self.assertEqual(body["status"], "incomplete")
        status, body = self.call("POST", "/api/vr/sessions", self.session_body(self.p1, self.full_results(prog)), self.vr)
        self.assertEqual(body["status"], "complete")

    def test_duplicate_exercise_ids_count_once(self):
        prog = self.vr_program()
        results = self.full_results(prog)
        results += [dict(results[0])]
        _, body = self.call("POST", "/api/vr/sessions", self.session_body(self.p1, results), self.vr)
        con = sqlite3.connect(server.DB_PATH)
        n = con.execute("SELECT COUNT(*) FROM performance_record WHERE session_id=?", (body["session_id"],)).fetchone()[0]
        con.close()
        self.assertEqual(n, len(prog["exercises"]))

    def test_empty_program_is_never_complete(self):
        status, _ = self.call("POST", "/api/patients", {"code": "P-950"}, self.auth)
        self.assertEqual(status, 201)
        prog = self.vr_program("P-950")
        for e in prog["exercises"]:
            self.call("DELETE", f"/api/patients/{prog['patient']['id']}/exercises/{e['id']}", headers=self.auth)
        self.assertEqual(self.vr_program("P-950")["exercises"], [])
        status, body = self.call("POST", "/api/vr/sessions", self.session_body(prog["patient"]["id"]),
                                 {"X-Patient-Code": "P-950"})
        self.assertEqual(status, 201, body)
        self.assertEqual(body["status"], "incomplete")
        self.assertNotIn("first", body["new_badges"])

    def test_results_for_other_patients_exercises_ignored(self):
        status, _ = self.call("POST", "/api/patients", {"code": "P-951"}, self.auth)
        other = self.vr_program("P-951")["exercises"][0]["id"]
        body = self.session_body(self.p1, [{"exercise_id": other, "target_reps": 1, "valid_reps": 1, "attempts": 1}])
        status, res = self.call("POST", "/api/vr/sessions", body, self.vr)
        self.assertEqual(status, 201)
        self.assertTrue(any("ignored" in n for n in res["notes"]))

    def test_session_uuid_is_idempotent(self):
        body = self.session_body(self.p1, session_uuid="7a1d1c1e-0000-4000-8000-000000000001", points=40)
        s1, first = self.call("POST", "/api/vr/sessions", body, self.vr)
        xp1 = first["patient"]["xp"]
        s2, second = self.call("POST", "/api/vr/sessions", body, self.vr)
        self.assertEqual((s1, s2), (201, 201))
        self.assertEqual(first["session_id"], second["session_id"])
        self.assertTrue(second.get("duplicate"))
        self.assertEqual(second["patient"]["xp"], xp1)

    # ------------------------------------------------ prescription bounds
    def test_add_exercise_clamps_prescription(self):
        status, prog = self.call("POST", f"/api/patients/{self.p1}/exercises",
                                 {"code": "elbowFlex", "rx": {"reps": 500, "targetAngle": 900, "tolerance": -4}}, self.auth)
        self.assertEqual(status, 201)
        e = prog["exercises"][-1]
        self.assertEqual(e["baseReps"], 50)
        self.assertEqual(e["targetAngle"], 175)
        self.assertEqual(e["tolerance"], 1)

    def test_add_protocol_clamps_prescription(self):
        status, prot = self.call("POST", "/api/protocols", {"name": "Bounds test", "phases": [
            {"name": "P1", "exercises": [{"code": "slr", "reps": 0, "sets": 99, "targetAngle": 1}]}]}, self.auth)
        self.assertEqual(status, 201, prot)
        ex = prot["phases"][0]["exerciseDetails"][0]
        self.assertEqual((ex["reps"], ex["sets"], ex["targetAngle"]), (1, 10, 5))

    # ------------------------------------------------ error codes
    def test_error_status_codes(self):
        cases = [
            ("GET", "/api/patients/abc/dashboard", None, 400),
            ("GET", "/api/patients/999999/dashboard", None, 404),
            ("DELETE", "/api/protocols/999999", None, 404),
            ("POST", "/api/patients", {"code": "P-001"}, 409),
            ("POST", "/api/patients", {}, 400),
            ("POST", f"/api/patients/{self.p1}/exercises", {"code": "noSuchExercise"}, 400),
            ("PUT", f"/api/patients/{self.p1}/program", {"maxReps": "lots"}, 400),
        ]
        for method, path, body, want in cases:
            with self.subTest(method=method, path=path):
                status, res = self.call(method, path, body, self.auth)
                self.assertEqual(status, want, res)
                self.assertNotIn("Traceback", str(res))

    def test_bad_json_is_400(self):
        status, _ = self.call("POST", "/api/patients", headers=self.auth, raw=b"{not json")
        self.assertEqual(status, 400)
        status, _ = self.call("POST", "/api/vr/sessions", headers=self.vr, raw=b"[1,2,3]")
        self.assertEqual(status, 400)

    # ------------------------------------------------ credentials
    def test_setup_only_once(self):
        _, body = self.call("GET", "/api/auth/setup")
        self.assertFalse(body["needsSetup"])
        status, _ = self.call("POST", "/api/auth/setup", {"username": "intruder", "password": "whatever-123"})
        self.assertEqual(status, 409)

    def test_tokens_stored_hashed(self):
        con = sqlite3.connect(server.DB_PATH)
        stored = [r[0] for r in con.execute("SELECT token FROM therapist_session")]
        con.close()
        self.assertTrue(stored)
        self.assertNotIn(self.token, stored)

    def test_change_password(self):
        bad = self.call("POST", "/api/auth/password", {"current_password": "wrong", "new_password": "another-pass-1"}, self.auth)
        self.assertEqual(bad[0], 400)
        short = self.call("POST", "/api/auth/password", {"current_password": TEST_PASSWORD, "new_password": "short"}, self.auth)
        self.assertEqual(short[0], 400)
        demo = self.call("POST", "/api/auth/password", {"current_password": TEST_PASSWORD, "new_password": "password123"}, self.auth)
        self.assertEqual(demo[0], 400)
        ok = self.call("POST", "/api/auth/password", {"current_password": TEST_PASSWORD, "new_password": "another-pass-1"}, self.auth)
        self.assertEqual(ok[0], 200)
        try:
            self.assertEqual(self.call("POST", "/api/auth/login", {"username": TEST_USER, "password": "another-pass-1"})[0], 200)
            self.assertEqual(self.call("POST", "/api/auth/login", {"username": TEST_USER, "password": TEST_PASSWORD})[0], 401)
        finally:
            self.call("POST", "/api/auth/password", {"current_password": "another-pass-1", "new_password": TEST_PASSWORD}, self.auth)
            server._login_failures.clear()

    def test_login_throttled_after_failures(self):
        try:
            for _ in range(server.LOGIN_MAX_FAILURES):
                self.assertEqual(self.call("POST", "/api/auth/login", {"username": "nobody", "password": "guess-1234"})[0], 401)
            self.assertEqual(self.call("POST", "/api/auth/login", {"username": "nobody", "password": "guess-1234"})[0], 429)
        finally:
            server._login_failures.clear()

    def test_old_demo_password_must_be_changed(self):
        h, s = server.hash_password("password123")
        con = sqlite3.connect(server.DB_PATH)
        con.execute("INSERT INTO physical_therapist(name, username, password_hash, salt) VALUES ('Old', 'legacy', ?, ?)", (h, s))
        con.commit()
        con.close()
        status, body = self.call("POST", "/api/auth/login", {"username": "legacy", "password": "password123"})
        self.assertEqual(status, 200)
        self.assertTrue(body["mustChangePassword"])

    # ------------------------------------------------ export
    def test_csv_export_neutralises_formulas(self):
        status, _ = self.call("POST", "/api/patients", {"code": "P-952", "name": "=HYPERLINK(\"http://x\")"}, self.auth)
        self.assertEqual(status, 201)
        pid = self.patient_ids()["P-952"]
        prog = self.vr_program("P-952")
        self.call("POST", "/api/vr/sessions", self.session_body(pid, self.full_results(prog)), {"X-Patient-Code": "P-952"})
        status, _, body = self.raw_get(f"/api/patients/{pid}/export?format=csv&token={self.token}")
        self.assertEqual(status, 200)
        self.assertIn(b"'=HYPERLINK", body)
        self.assertNotIn(b",=HYPERLINK", body)

    # ------------------------------------------------ exercise rules (M4.6, DEC-012)
    def test_every_library_entry_has_valid_rules(self):
        for code, entry in server.LIBRARY.items():
            with self.subTest(code=code):
                self.assertEqual(len(entry), 14)
                rules = entry[13]
                self.assertIn(rules["posture"], server.POSTURES)
                self.assertIn(rules["pose"], server.POSES)
                self.assertIn(rules["direction"], server.DIRECTIONS)
                if rules["direction"] in ("flex", "ext"):
                    self.assertIn(entry[2], ("shoulderElev", "hipElev"))   # only these have a signed angle
                for check in rules["checks"]:
                    self.assertIn(check["metric"], server.CHECK_METRICS)
                    self.assertGreater(check["max"], 0)
                    self.assertTrue(check["message"])

    def test_vr_program_carries_rules(self):
        for e in self.vr_program()["exercises"]:
            with self.subTest(code=e["code"]):
                rules = server.LIBRARY[e["code"]][13]
                self.assertEqual(e["pose"], rules["pose"])
                self.assertEqual(e["posture"], rules["posture"])
                self.assertEqual(e["direction"], rules["direction"] or "")
                self.assertEqual(e["checks"], rules["checks"])

    def test_rules_fallback_for_codes_no_longer_in_library(self):
        r = server.exercise_rules("retiredCode", "hipElev", "front")
        self.assertEqual((r["pose"], r["posture"], r["checks"]), ("hipAbd", "standing", []))

    # ------------------------------------------------ per-rep events (M4.5)
    def rep(self, eid, attempt, **extra):
        r = {"exercise_id": eid, "attempt": attempt, "set": 1, "side": "", "t": attempt * 3.0, "peak": 88.5,
             "error": 1.5, "accuracy": 97, "valid": True, "fault": "", "past_safety_max": False, "too_fast": False,
             "held": True}
        r.update(extra)
        return r

    def test_rep_events_stored_once_and_exported(self):
        status, _ = self.call("POST", "/api/patients", {"code": "P-953", "name": "Reps"}, self.auth)
        self.assertEqual(status, 201)
        pid = self.patient_ids()["P-953"]
        prog = self.vr_program("P-953")
        eid = prog["exercises"][0]["id"]
        reps = [self.rep(eid, 1), self.rep(eid, 2, valid=False, fault="Keep your trunk upright"),
                self.rep(eid, 3, past_safety_max=True, valid=False), self.rep(999999, 1)]
        body = self.session_body(pid, self.full_results(prog), session_uuid="reps-uuid-1", rep_events=reps)
        hdr = {"X-Patient-Code": "P-953"}
        status, res = self.call("POST", "/api/vr/sessions", body, hdr)
        self.assertEqual(status, 201, res)
        self.assertTrue(any("rep event" in n for n in res["notes"]))      # the unknown exercise is ignored
        self.call("POST", "/api/vr/sessions", body, hdr)                   # retry: same uuid, no new rows
        status, rows = self.call("GET", f"/api/patients/{pid}/export?format=json&kind=reps", headers=self.auth)
        self.assertEqual(status, 200)
        self.assertEqual([r["attempt"] for r in rows], [1, 2, 3])
        self.assertEqual([r["valid"] for r in rows], [1, 0, 0])
        self.assertEqual(rows[1]["fault"], "Keep your trunk upright")
        self.assertEqual(rows[2]["unsafe"], 1)
        self.assertEqual(rows[0]["session_uuid"], "reps-uuid-1")
        self.assertEqual(rows[0]["input_source"], "webcam")
        status, _, csv_body = self.raw_get(f"/api/patients/{pid}/export?format=csv&kind=reps&token={self.token}")
        self.assertEqual(status, 200)
        self.assertTrue(csv_body.startswith(b"patient_code,session_id,session_uuid"))

    def test_bad_rep_events_rejected(self):
        eid = self.vr_program()["exercises"][0]["id"]
        for bad in ("nope", [1, 2], [{"attempt": 1}], [self.rep(eid, 1)] * (server.MAX_REP_EVENTS + 1)):
            with self.subTest(bad=str(bad)[:40]):
                status, _ = self.call("POST", "/api/vr/sessions", self.session_body(self.p1, rep_events=bad), self.vr)
                self.assertEqual(status, 400)

    def test_missing_input_source_stored_as_unknown(self):
        body = self.session_body(self.p1, session_uuid="no-source-1")
        del body["input_source"]
        status, res = self.call("POST", "/api/vr/sessions", body, self.vr)
        self.assertEqual(status, 201, res)
        con = sqlite3.connect(server.DB_PATH)
        src = con.execute("SELECT input_source FROM session WHERE session_uuid='no-source-1'").fetchone()[0]
        con.close()
        self.assertEqual(src, "unknown")


class ProtocolReplaceTests(ServerTestCase):

    def test_version_bump_keeps_custom_protocols(self):
        status, prot = self.call("POST", "/api/protocols", {"name": "Clinic custom knee"}, self.auth)
        self.assertEqual(status, 201)
        con = sqlite3.connect(server.DB_PATH)
        con.execute("UPDATE app_meta SET value='old' WHERE key='protocol_version'")
        con.commit()
        con.close()
        server.init_db()   # sees the old version and reloads the built-in protocols
        _, protocols = self.call("GET", "/api/protocols", headers=self.auth)
        names = [p["name"] for p in protocols]
        self.assertIn("Clinic custom knee", names)
        self.assertEqual(sum(1 for n in names if n in {p[0] for p in server.PROTOCOLS}), len(server.PROTOCOLS))

    def builtin(self, name):
        _, protocols = self.call("GET", "/api/protocols", headers=self.auth)
        return next(p for p in protocols if p["name"] == name)

    def bump_version(self):
        con = sqlite3.connect(server.DB_PATH)
        con.execute("UPDATE app_meta SET value='old' WHERE key='protocol_version'")
        con.commit()
        con.close()
        server.init_db()

    def test_unchanged_builtin_keeps_patients_on_their_phase(self):
        prot = self.builtin(server.PROTOCOLS[0][0])
        phase_id = prot["phases"][1]["id"]
        pid = self.patient_ids()["P-001"]
        self.assertEqual(self.call("POST", f"/api/patients/{pid}/phase", {"phase_id": phase_id}, self.auth)[0], 200)
        self.bump_version()
        _, prog = self.call("GET", f"/api/patients/{pid}/program", headers=self.auth)
        self.assertEqual(prog["phase"]["id"], phase_id)
        self.assertEqual(self.builtin(server.PROTOCOLS[0][0])["id"], prot["id"])

    def test_changed_builtin_is_replaced(self):
        name = server.PROTOCOLS[1][0]
        old = self.builtin(name)
        con = sqlite3.connect(server.DB_PATH)
        con.execute("UPDATE protocol_phase SET goals='edited outside the app' WHERE phase_id=?", (old["phases"][0]["id"],))
        con.commit()
        con.close()
        self.bump_version()
        new = self.builtin(name)
        self.assertNotEqual(new["id"], old["id"])
        self.assertEqual(new["phases"][0]["goals"], server.PROTOCOLS[1][3][0][3])

    def test_every_builtin_protocol_is_well_formed(self):
        for name, condition, source, phases in server.PROTOCOLS:
            for ph in phases:
                with self.subTest(protocol=name, phase=ph[0]):
                    self.assertTrue(source and condition)
                    if ph[2]:
                        self.assertTrue(ph[10], "a VR phase needs at least one camera exercise")
                    for code, target, tol, safety, hold, sets, reps, rest in ph[10]:
                        self.assertIn(code, server.LIBRARY)
                        self.assertLessEqual(target, server.NORMAL_ROM[code][1])
                        if safety:
                            self.assertLessEqual(target, safety)


class PatientManagementTests(ServerTestCase):
    """M5.2: edit patient details, archive instead of delete (DEC-014)."""

    def new_patient(self, code):
        status, body = self.call("POST", "/api/patients", {"code": code, "condition": "Test"}, self.auth)
        self.assertEqual(status, 201, body)
        return body["id"]

    def test_edit_name_and_condition(self):
        pid = self.new_patient("P-510")
        status, body = self.call("PUT", f"/api/patients/{pid}", {"name": "Alias A", "condition": "Rotator cuff"}, self.auth)
        self.assertEqual(status, 200, body)
        _, dash = self.call("GET", f"/api/patients/{pid}/dashboard", headers=self.auth)
        self.assertEqual(dash["patient"]["name"], "Alias A")

    def test_edit_rejects_code_change_and_long_text(self):
        pid = self.new_patient("P-511")
        self.assertEqual(self.call("PUT", f"/api/patients/{pid}", {"code": "P-999"}, self.auth)[0], 400)
        self.assertEqual(self.call("PUT", f"/api/patients/{pid}", {"code": "p-511", "name": "ok"}, self.auth)[0], 200)
        self.assertEqual(self.call("PUT", f"/api/patients/{pid}", {"name": "x" * 201}, self.auth)[0], 400)
        self.assertEqual(self.call("PUT", "/api/patients/999999", {"name": "x"}, self.auth)[0], 404)

    def test_archive_hides_patient_and_keeps_records(self):
        pid = self.new_patient("P-512")
        vr = {"X-Patient-Code": "P-512"}
        self.assertEqual(self.call("POST", "/api/vr/sessions", self.session_body(pid), vr)[0], 201)
        status, body = self.call("POST", f"/api/patients/{pid}/archive", {"archived": True}, self.auth)
        self.assertEqual(status, 200, body)
        self.assertTrue(body["archivedAt"])
        self.assertNotIn("P-512", self.patient_ids())
        _, everyone = self.call("GET", "/api/patients?include_archived=1", headers=self.auth)
        self.assertTrue(next(p for p in everyone if p["code"] == "P-512")["archived_at"])
        # The chart and its sessions are still there
        _, dash = self.call("GET", f"/api/patients/{pid}/dashboard", headers=self.auth)
        self.assertTrue(dash["archivedAt"])
        self.assertEqual(dash["sessionsTotal"], 1)
        # No new sessions from the VR app, but sessions already recorded (offline queue) still upload
        self.assertEqual(self.call("GET", "/api/vr/program", headers=vr)[0], 403)
        later = self.session_body(pid, started_at="2026-10-21T09:00:00", ended_at="2026-10-21T09:20:00")
        self.assertEqual(self.call("POST", "/api/vr/sessions", later, vr)[0], 201)
        # Archiving again keeps the first date; unarchiving brings the patient back
        _, again = self.call("POST", f"/api/patients/{pid}/archive", {"archived": True}, self.auth)
        self.assertEqual(again["archivedAt"], body["archivedAt"])
        self.call("POST", f"/api/patients/{pid}/archive", {"archived": False}, self.auth)
        self.assertIn("P-512", self.patient_ids())
        self.assertEqual(self.call("GET", "/api/vr/program", headers=vr)[0], 200)

    def test_archive_needs_boolean(self):
        pid = self.new_patient("P-513")
        for body in ({}, {"archived": "yes"}, {"archived": 1}):
            with self.subTest(body=body):
                self.assertEqual(self.call("POST", f"/api/patients/{pid}/archive", body, self.auth)[0], 400)


class ProtocolPhaseEditTests(ServerTestCase):
    """M5.2: therapists edit and add phases of their own protocols; built-in protocols are read-only."""

    def custom_protocol(self, name="Clinic ACL"):
        status, prot = self.call("POST", "/api/protocols", {"name": name, "phases": [
            {"name": "Phase I", "exercises": [{"code": "slr"}]}]}, self.auth)
        self.assertEqual(status, 201, prot)
        return prot

    def test_builtin_protocols_are_read_only(self):
        _, protocols = self.call("GET", "/api/protocols", headers=self.auth)
        builtin = next(p for p in protocols if p["builtin"])
        ph = builtin["phases"][0]
        self.assertEqual(self.call("PUT", f"/api/protocols/{builtin['id']}/phases/{ph['id']}", {"goals": "x"}, self.auth)[0], 403)
        self.assertEqual(self.call("POST", f"/api/protocols/{builtin['id']}/phases", {"name": "Extra"}, self.auth)[0], 403)

    def test_add_phase_appends(self):
        prot = self.custom_protocol("Clinic add phase")
        self.assertFalse(prot["builtin"])
        status, prot = self.call("POST", f"/api/protocols/{prot['id']}/phases",
                                 {"name": "Phase II", "weeks": "Weeks 5-8", "exercises": ["heelSlide", "nope"]}, self.auth)
        self.assertEqual(status, 201, prot)
        self.assertEqual([p["phaseNo"] for p in prot["phases"]], [1, 2])
        self.assertEqual([e["code"] for e in prot["phases"][1]["exerciseDetails"]], ["heelSlide"])
        self.assertEqual(self.call("POST", f"/api/protocols/{prot['id']}/phases", {"name": " "}, self.auth)[0], 400)

    def test_update_phase_fields_and_bounds(self):
        prot = self.custom_protocol("Clinic update")
        ph = prot["phases"][0]
        status, prot = self.call("PUT", f"/api/protocols/{prot['id']}/phases/{ph['id']}", {
            "goals": "Full extension", "minAccuracy": 150, "minSessions": 0, "maxPainIncrease": 3,
            "maxSwellingCm": "", "exercises": [{"code": "heelSlide", "targetAngle": 999}]}, self.auth)
        self.assertEqual(status, 200, prot)
        ph = prot["phases"][0]
        self.assertEqual(ph["name"], "Phase I")              # left out = unchanged
        self.assertEqual(ph["goals"], "Full extension")
        self.assertEqual(ph["minAccuracy"], 100)
        self.assertEqual(ph["minSessions"], 1)
        self.assertEqual(ph["maxPainIncrease"], 3)
        self.assertIsNone(ph["maxSwellingCm"])
        self.assertEqual([e["code"] for e in ph["exerciseDetails"]], ["heelSlide"])
        self.assertLessEqual(ph["exerciseDetails"][0]["targetAngle"], 180)

    def test_update_phase_wrong_protocol_or_name(self):
        a, b = self.custom_protocol("Clinic A"), self.custom_protocol("Clinic B")
        ph_b = b["phases"][0]["id"]
        self.assertEqual(self.call("PUT", f"/api/protocols/{a['id']}/phases/{ph_b}", {"goals": "x"}, self.auth)[0], 404)
        self.assertEqual(self.call("PUT", f"/api/protocols/{b['id']}/phases/{ph_b}", {"name": ""}, self.auth)[0], 400)
        self.assertEqual(self.call("PUT", "/api/protocols/999999/phases/1", {"goals": "x"}, self.auth)[0], 404)

    def test_patient_on_phase_keeps_prescription(self):
        prot = self.custom_protocol("Clinic keep rx")
        ph = prot["phases"][0]
        pid = self.patient_ids()["P-001"]
        self.assertEqual(self.call("POST", f"/api/patients/{pid}/phase", {"phase_id": ph["id"]}, self.auth)[0], 200)
        self.call("PUT", f"/api/protocols/{prot['id']}/phases/{ph['id']}", {"exercises": ["heelSlide"]}, self.auth)
        _, prog = self.call("GET", f"/api/patients/{pid}/program", headers=self.auth)
        self.assertEqual([e["code"] for e in prog["exercises"]], ["slr"])


OLD_SCHEMA = """
CREATE TABLE physical_therapist (therapist_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, license_no TEXT, email TEXT);
CREATE TABLE rehabilitation_program (program_id INTEGER PRIMARY KEY AUTOINCREMENT, therapist_id INTEGER NOT NULL,
  name TEXT NOT NULL, description TEXT, schedule_days TEXT NOT NULL DEFAULT '1,3,5', max_reps INTEGER NOT NULL DEFAULT 14);
CREATE TABLE protocol (protocol_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, condition TEXT, source TEXT);
CREATE TABLE patient (patient_id INTEGER PRIMARY KEY AUTOINCREMENT, therapist_id INTEGER NOT NULL, program_id INTEGER,
  code TEXT UNIQUE NOT NULL, name TEXT, condition TEXT, xp INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')));
CREATE TABLE exercise (exercise_id INTEGER PRIMARY KEY AUTOINCREMENT, program_id INTEGER NOT NULL, code TEXT NOT NULL,
  name TEXT NOT NULL, joint TEXT NOT NULL, target_angle REAL NOT NULL, tolerance REAL NOT NULL DEFAULT 10,
  reps INTEGER NOT NULL DEFAULT 8, stage INTEGER NOT NULL DEFAULT 1, cue TEXT, sort_order INTEGER NOT NULL DEFAULT 0);
CREATE TABLE session (session_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL, program_id INTEGER,
  started_at TEXT NOT NULL, ended_at TEXT NOT NULL, input_source TEXT, points INTEGER NOT NULL DEFAULT 0,
  stars INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL);
"""


class MigrationTests(unittest.TestCase):

    def test_old_database_starts(self):
        tmp = tempfile.mkdtemp(prefix="tq_migrate_")
        real = server.DB_PATH
        try:
            server.DB_PATH = os.path.join(tmp, "old.db")
            con = sqlite3.connect(server.DB_PATH)
            con.executescript(OLD_SCHEMA)
            con.execute("INSERT INTO protocol(name) VALUES (?)", (server.PROTOCOLS[0][0],))   # an old built-in copy
            con.execute("INSERT INTO protocol(name) VALUES ('Custom from 2025')")
            con.commit()
            con.close()
            server.init_db()
            con = sqlite3.connect(server.DB_PATH)
            cols = {r[1] for r in con.execute("PRAGMA table_info(exercise)")}
            self.assertIn("active", cols)
            names = [r[0] for r in con.execute("SELECT name FROM protocol")]
            idx = {r[1] for r in con.execute("PRAGMA index_list(patient)")}
            con.close()
            self.assertIn("Custom from 2025", names)
            self.assertEqual(names.count(server.PROTOCOLS[0][0]), 1)
            self.assertIn("idx_patient_phase", idx)
            con = sqlite3.connect(server.DB_PATH)
            self.assertIn("archived_at", {r[1] for r in con.execute("PRAGMA table_info(patient)")})
            con.close()
        finally:
            server.DB_PATH = real
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)

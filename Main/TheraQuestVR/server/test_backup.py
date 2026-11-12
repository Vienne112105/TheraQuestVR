"""
M7.3 tests: encrypted backup and restore round trip, wrong password, tampering, version, no overwrite,
and a consistent copy while a write transaction is open.

Run:   python test_backup.py
"""
import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime

import backup

PW = "correct horse battery"
FAST = 12      # scrypt cost for tests only


def make_db(path):
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE patient(id INTEGER PRIMARY KEY, code TEXT, name TEXT)")
    con.executemany("INSERT INTO patient(code, name) VALUES (?,?)", [("P-001", "A"), ("P-002", "B")])
    con.commit()
    return con


def rows(path):
    con = sqlite3.connect(path)
    try:
        return con.execute("SELECT id, code, name FROM patient ORDER BY id").fetchall()
    finally:
        con.close()


class BackupTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tq_bak_")
        self.db = os.path.join(self.tmp, "live.db")
        self.con = make_db(self.db)
        self.out = os.path.join(self.tmp, "backups")

    def tearDown(self):
        self.con.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make(self, **kw):
        return backup.backup(self.out, PW, db_path=self.db, log2n=FAST, **kw)

    def test_round_trip_gives_identical_contents(self):
        path = self.make(now=datetime(2026, 11, 12, 10, 30, 5))
        self.assertTrue(path.endswith("theraquest-20261112-103005.tqbak"))
        restored = backup.restore(path, os.path.join(self.tmp, "restored.db"), PW)
        self.assertEqual(rows(restored), rows(self.db))
        con = sqlite3.connect(restored)
        self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        con.close()

    def test_file_does_not_contain_plain_data(self):
        with open(self.make(), "rb") as f:
            blob = f.read()
        self.assertNotIn(b"P-001", blob)
        self.assertNotIn(b"SQLite format", blob)

    def test_wrong_password_fails_cleanly(self):
        path = self.make()
        out = os.path.join(self.tmp, "r.db")
        with self.assertRaisesRegex(backup.BackupError, "Wrong password"):
            backup.restore(path, out, "not the right password")
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(out + ".part"))

    def test_tampered_file_fails(self):
        path = self.make()
        for pos in (-1, backup.HEADER_LEN + 3, 7):          # tag, ciphertext, salt in the header
            with self.subTest(pos=pos):
                with open(path, "rb") as f:
                    blob = bytearray(f.read())
                blob[pos] ^= 0x01
                bad = os.path.join(self.tmp, f"bad{pos}.tqbak")
                with open(bad, "wb") as f:
                    f.write(blob)
                with self.assertRaises(backup.BackupError):
                    backup.restore(bad, os.path.join(self.tmp, f"r{pos}.db"), PW)

    def test_not_a_backup_and_truncated_files_fail(self):
        junk = os.path.join(self.tmp, "junk.tqbak")
        with open(junk, "wb") as f:
            f.write(b"hello world, this is not a backup file at all")
        with self.assertRaisesRegex(backup.BackupError, "not a TheraQuest backup"):
            backup.restore(junk, os.path.join(self.tmp, "r.db"), PW)
        path = self.make()
        with open(path, "rb") as f:
            cut = f.read()[:backup.HEADER_LEN + 10]
        short = os.path.join(self.tmp, "short.tqbak")
        with open(short, "wb") as f:
            f.write(cut)
        with self.assertRaises(backup.BackupError):
            backup.restore(short, os.path.join(self.tmp, "r2.db"), PW)

    def test_header_version_is_checked(self):
        path = self.make()
        with open(path, "rb") as f:
            blob = bytearray(f.read())
        blob[len(backup.MAGIC)] = backup.VERSION + 1
        newer = os.path.join(self.tmp, "newer.tqbak")
        with open(newer, "wb") as f:
            f.write(blob)
        with self.assertRaisesRegex(backup.BackupError, "version"):
            backup.restore(newer, os.path.join(self.tmp, "r.db"), PW)

    def test_restore_refuses_an_existing_output(self):
        path = self.make()
        with self.assertRaisesRegex(backup.BackupError, "already exists"):
            backup.restore(path, self.db, PW)
        self.assertEqual(len(rows(self.db)), 2)             # the live file is untouched

    def test_short_password_refused(self):
        with self.assertRaisesRegex(backup.BackupError, "at least"):
            backup.backup(self.out, "short", db_path=self.db, log2n=FAST)

    def test_two_backups_in_one_second_do_not_overwrite(self):
        now = datetime(2026, 11, 12, 10, 30, 5)
        self.make(now=now)
        with self.assertRaises(FileExistsError):
            self.make(now=now)

    def test_open_write_transaction_gives_a_consistent_copy(self):
        writer = sqlite3.connect(self.db, isolation_level=None)
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("INSERT INTO patient(code, name) VALUES ('P-003', 'half-written')")
        try:
            path = self.make()
        finally:
            writer.execute("ROLLBACK")
            writer.close()
        restored = backup.restore(path, os.path.join(self.tmp, "r.db"), PW)
        self.assertEqual([r[1] for r in rows(restored)], ["P-001", "P-002"])

    def test_committed_wal_content_is_included(self):
        self.con.execute("INSERT INTO patient(code, name) VALUES ('P-003', 'C')")
        self.con.commit()                                    # still in the WAL file, not checkpointed
        restored = backup.restore(self.make(), os.path.join(self.tmp, "r.db"), PW)
        self.assertEqual(len(rows(restored)), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)

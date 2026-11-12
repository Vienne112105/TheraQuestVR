"""
Encrypted backup and restore of the TheraQuest database (M7.3, TASK-005, DEC-027).

  python backup.py backup <folder>            writes theraquest-YYYYMMDD-HHMMSS.tqbak into <folder>
  python backup.py restore <file> <out.db>    decrypts to a NEW file and checks it; never touches the live database

The backup is a consistent snapshot (SQLite backup API: safe while the server runs, WAL included), encrypted
with AES-256-GCM under a key derived from a password with scrypt. The password is asked for with getpass,
is never stored or logged, and a lost password cannot be recovered.

File layout: MAGIC(5) | version(1) | log2(scrypt N)(1) | salt(16) | nonce(12) | ciphertext+tag.
The whole header is authenticated, so a changed header or ciphertext fails to decrypt.

Only this tool needs the `cryptography` package; the server itself stays standard-library only.
"""
import getpass
import os
import sqlite3
import sys
import tempfile
from datetime import datetime

MAGIC = b"TQBAK"
VERSION = 1
SALT_LEN, NONCE_LEN = 16, 12
HEADER_LEN = len(MAGIC) + 1 + 1 + SALT_LEN + NONCE_LEN
SCRYPT_LOG2N = 15            # N = 32768, r = 8, p = 1: about 0.1 s and 32 MiB
MIN_PASSWORD = 12


class BackupError(Exception):
    """A problem the user can act on (wrong password, damaged file, existing output)."""


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    except ImportError:
        raise BackupError("The 'cryptography' package is missing. Run:  pip install -r requirements.txt")
    return AESGCM, Scrypt


def _key(password, salt, log2n):
    _, Scrypt = _crypto()
    return Scrypt(salt=salt, length=32, n=1 << log2n, r=8, p=1).derive(password.encode("utf-8"))


def _default_db():
    import server                       # imported late: the tool must work on its own for restore
    return server.DB_PATH


def _snapshot_bytes(db_path):
    """A consistent copy of the database as bytes."""
    if not os.path.exists(db_path):
        raise BackupError(f"Database not found: {db_path}")
    with tempfile.TemporaryDirectory(prefix="tq_snap_") as tmp:
        snap = os.path.join(tmp, "snap.db")
        src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=15.0)
        dst = sqlite3.connect(snap)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        with open(snap, "rb") as f:
            return f.read()


def backup(folder, password, db_path=None, now=None, log2n=SCRYPT_LOG2N):
    """Write an encrypted snapshot into `folder`; returns the new file's path."""
    if len(password) < MIN_PASSWORD:
        raise BackupError(f"The password must be at least {MIN_PASSWORD} characters.")
    AESGCM, _ = _crypto()
    data = _snapshot_bytes(db_path or _default_db())
    os.makedirs(folder, exist_ok=True)
    salt, nonce = os.urandom(SALT_LEN), os.urandom(NONCE_LEN)
    header = MAGIC + bytes([VERSION, log2n]) + salt + nonce
    blob = header + AESGCM(_key(password, salt, log2n)).encrypt(nonce, data, header)
    name = f"theraquest-{(now or datetime.now()).strftime('%Y%m%d-%H%M%S')}.tqbak"
    path = os.path.join(folder, name)
    with open(path, "xb") as f:         # never overwrite an earlier backup
        f.write(blob)
    return path


def restore(file, out, password):
    """Decrypt `file` into the NEW database file `out` and check it. Never overwrites anything."""
    if os.path.exists(out):
        raise BackupError(f"{out} already exists. Restore writes a new file only; choose another name.")
    AESGCM, _ = _crypto()
    with open(file, "rb") as f:
        blob = f.read()
    if len(blob) <= HEADER_LEN or blob[:len(MAGIC)] != MAGIC:
        raise BackupError("This is not a TheraQuest backup file.")
    version, log2n = blob[len(MAGIC)], blob[len(MAGIC) + 1]
    if version != VERSION:
        raise BackupError(f"Backup format version {version} is not supported (this tool reads version {VERSION}).")
    if not 10 <= log2n <= 20:
        raise BackupError("The backup header is damaged.")
    header = blob[:HEADER_LEN]
    salt = header[len(MAGIC) + 2:len(MAGIC) + 2 + SALT_LEN]
    nonce = header[-NONCE_LEN:]
    try:
        data = AESGCM(_key(password, salt, log2n)).decrypt(nonce, blob[HEADER_LEN:], header)
    except Exception:
        raise BackupError("Wrong password, or the backup file is damaged.")
    tmp = out + ".part"
    try:
        with open(tmp, "xb") as f:
            f.write(data)
        con = sqlite3.connect(tmp)
        try:
            result = con.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            con.close()
        if result != "ok":
            raise BackupError(f"The restored database failed its integrity check: {result}")
        os.rename(tmp, out)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return out


def _ask_password(confirm):
    pw = getpass.getpass("Backup password: ")
    if confirm:
        if len(pw) < MIN_PASSWORD:
            raise BackupError(f"The password must be at least {MIN_PASSWORD} characters.")
        if getpass.getpass("Type it again: ") != pw:
            raise BackupError("The two passwords differ.")
    return pw


def main(argv):
    try:
        if len(argv) == 3 and argv[1] == "backup":
            path = backup(argv[2], _ask_password(True))
            print(f"Backup written: {path}\nKeep the password safe: without it this file cannot be opened.")
        elif len(argv) == 4 and argv[1] == "restore":
            out = restore(argv[2], argv[3], _ask_password(False))
            print(f"Restored to {out}. Stop the server before swapping it in (see README, Backup and restore).")
        else:
            print(__doc__)
            return 2
    except (BackupError, OSError) as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

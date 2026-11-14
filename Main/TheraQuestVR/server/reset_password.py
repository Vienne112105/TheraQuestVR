"""
Set a new password for a clinician login without touching any patient data.

Run on the PC that holds the database, with the Therapist app closed. On Windows use Reset_Password.ps1
instead of this file directly: the Microsoft Store Python redirects writes under %LOCALAPPDATA% to a private
copy, so a direct run changes the wrong database. (Plain python.org installs are fine.)
    python reset_password.py                 (only one clinician: uses that login)
    python reset_password.py therapist       (name the login)

Anyone who can run this can already read and copy the database file, so it adds no new access.
The new password is typed at a hidden prompt; it is never printed or stored in plain text.
All signed-in sessions for that login are ended.
"""
import getpass
import sqlite3
import sys

import server


def reset_password(db_path, username, new_password):
    """Returns the login name that was changed. Raises ValueError with a readable message on bad input."""
    if len(new_password) < server.MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {server.MIN_PASSWORD_LENGTH} characters")
    con = sqlite3.connect(db_path, timeout=15.0)
    try:
        rows = con.execute("SELECT therapist_id, username FROM physical_therapist WHERE username IS NOT NULL "
                           "AND password_hash IS NOT NULL").fetchall()
        names = ", ".join(r[1] for r in rows) or "none"
        if username:
            rows = [r for r in rows if r[1].lower() == username.lower()]
        if len(rows) != 1:
            raise ValueError(f"Expected exactly one matching login, found {len(rows)} (logins in this database: {names})")
        tid, name = rows[0]
        h, s = server.hash_password(new_password)
        con.execute("UPDATE physical_therapist SET password_hash=?, salt=? WHERE therapist_id=?", (h, s, tid))
        con.execute("DELETE FROM therapist_session WHERE therapist_id=?", (tid,))
        con.commit()
        return name
    finally:
        con.close()


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"Database: {server.DB_PATH}")
    pw = getpass.getpass("New password: ")
    if pw != getpass.getpass("Repeat new password: "):
        sys.exit("The two passwords do not match. Nothing was changed.")
    try:
        name = reset_password(server.DB_PATH, username, pw)
    except ValueError as e:
        sys.exit(f"{e}. Nothing was changed.")
    print(f"Password for '{name}' updated. Patient data was not touched.")


if __name__ == "__main__":
    main()

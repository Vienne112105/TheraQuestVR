"""
TheraQuest VR - Native Desktop Application for Therapists
Launches the Therapist Command Center as a standalone desktop window (via WebView2 / pywebview).
No browser address bars, navigation buttons, or tabs — behaves as an authentic desktop software application.
"""
import os
import sys
import threading
import time
import socket
from urllib.request import urlopen

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from server import init_db, migrate_legacy_db, Handler, ThreadingHTTPServer

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def is_theraquest(url: str) -> bool:
    """True when the program on the port is a TheraQuest server (it answers /api/auth/setup)."""
    try:
        with urlopen(url + "/api/auth/setup", timeout=2) as resp:
            return resp.headers.get("Server", "").startswith("TheraQuest")
    except Exception:
        return False


def start_server_thread(port: int):
    migrate_legacy_db()
    init_db()
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def keep_serving(message):
    """Keep the backend up for the VR app after the therapist window is gone."""
    print(message)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


def main():
    port = 8000
    url = f"http://127.0.0.1:{port}"
    started_here = False
    if not is_port_in_use(port):
        print(f"Starting TheraQuest local database & clinical backend on port {port}...")
        start_server_thread(port)
        started_here = True
    elif is_theraquest(url):
        print(f"TheraQuest clinical backend is already running on port {port}.")
    else:
        print(f"Port {port} is used by another program, so TheraQuest can't start.")
        print("Close that program (or restart the computer) and run this again.")
        sys.exit(1)

    # Wait for server readiness
    for _ in range(30):
        try:
            with urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.1)

    # Launch native desktop application window
    try:
        import webview
        print("Launching native Windows desktop application window (WebView2)...")
        webview.create_window(
            title="TheraQuest VR — Therapist Command Center",
            url=url,
            width=1360,
            height=880,
            min_size=(980, 640),
            text_select=True,
            confirm_close=False
        )
        webview.start()
        if started_here:
            answer = input("Therapist window closed. Keep the server running for VR sessions? [Y/n] ").strip().lower()
            if answer in ("", "y", "yes"):
                keep_serving("Server still running for VR. Press Ctrl+C or close this window to stop it.")
    except Exception as e:   # pywebview not installed, or no WebView2 runtime
        print(f"Notice: native window unavailable ({e}). Opening the dashboard in an Edge app window instead...")
        import subprocess
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if os.path.exists(edge_path):
            subprocess.Popen([edge_path, f"--app={url}", "--window-size=1360,880"])
        else:
            import webbrowser
            webbrowser.open(url)
        if started_here:
            keep_serving("Server running. Keep this window open while you use the dashboard or VR; Ctrl+C stops it.")


if __name__ == "__main__":
    main()

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

from server import db, init_db, Handler, ThreadingHTTPServer

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_server_thread(port: int):
    init_db()
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def main():
    port = 8000
    if not is_port_in_use(port):
        print(f"Starting TheraQuest local database & clinical backend on port {port}...")
        start_server_thread(port)
    else:
        print(f"TheraQuest clinical backend is already running on port {port}.")

    # Wait for server readiness
    url = f"http://127.0.0.1:{port}"
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
        window = webview.create_window(
            title="TheraQuest VR — Therapist Command Center",
            url=url,
            width=1360,
            height=880,
            min_size=(980, 640),
            text_select=True,
            confirm_close=False
        )
        webview.start()
    except Exception as e:
        print(f"Notice: pywebview fallback ({e}). Launching dedicated Windows App Shell...")
        import subprocess
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if os.path.exists(edge_path):
            subprocess.run([edge_path, f"--app={url}", "--window-size=1360,880"])
        else:
            import webbrowser
            webbrowser.open(url)

if __name__ == "__main__":
    main()

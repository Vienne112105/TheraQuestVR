"""Build the therapist dashboard as a Windows program: dist/TheraQuest Therapist/TheraQuest Therapist.exe

    python -m pip install -r build-requirements.txt
    python build_app.py

The program is app.py with Python, pywebview and the dashboard files bundled (DEC-013): it opens the
dashboard in its own window, with no console. The database stays in %LOCALAPPDATA%\\TheraQuest (DEC-010).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "TheraQuest Therapist"
TEAL, WHITE = (13, 148, 136, 255), (255, 255, 255, 255)   # dashboard --teal


def make_icon(path):
    """Teal rounded square with a white medical cross, drawn at 256 px and saved at the usual icon sizes."""
    from PIL import Image, ImageDraw
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, size - 8, size - 8), radius=56, fill=TEAL)
    arm, c = 40, size // 2
    d.rounded_rectangle((c - arm, 52, c + arm, size - 52), radius=14, fill=WHITE)
    d.rounded_rectangle((52, c - arm, size - 52, c + arm), radius=14, fill=WHITE)
    img.save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def main():
    import PyInstaller.__main__
    build = os.path.join(HERE, "build")
    os.makedirs(build, exist_ok=True)
    icon = os.path.join(build, "theraquest.ico")
    make_icon(icon)
    sep = os.pathsep
    PyInstaller.__main__.run([
        os.path.join(HERE, "app.py"),
        "--name", NAME,
        "--onedir", "--windowed", "--noconfirm", "--clean",
        "--icon", icon,
        "--distpath", os.path.join(HERE, "dist"),
        "--workpath", build,
        "--specpath", build,
        "--add-data", f"{os.path.join(HERE, 'dashboard.html')}{sep}.",
        "--add-data", f"{os.path.join(HERE, 'schema.sql')}{sep}.",
        "--add-data", f"{os.path.join(HERE, 'static')}{sep}static",
    ])
    print(f"\nBuilt: {os.path.join(HERE, 'dist', NAME, NAME + '.exe')}")


if __name__ == "__main__":
    sys.exit(main())

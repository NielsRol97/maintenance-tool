import sys
import ctypes
import platform

from ui.main_window import MainWindow


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():
    params = " ".join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params,
        None,
        1
    )


if platform.system() != "Windows":
    raise SystemExit("Windows only")

if not is_admin():
    relaunch_as_admin()
    sys.exit(0)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()

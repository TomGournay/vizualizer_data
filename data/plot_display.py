import base64
from pathlib import Path
import platform
import subprocess
import webbrowser


def open_plot(path):
    path = Path(path).resolve()
    if "microsoft" in platform.release().lower():
        target = subprocess.check_output(["wslpath", "-w", str(path)], text=True).strip()
        script = "$ErrorActionPreference = 'Stop'; Start-Process -FilePath '" + target.replace("'", "''") + "'"
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive",
                        "-EncodedCommand", encoded], check=True, timeout=10)
    else:
        webbrowser.open(path.as_uri())

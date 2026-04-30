from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import time
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
LOGDIR = ROOT / "report" / "swanlog_hw2"
SAVEDIR = ROOT / "report" / "swanlab_home"
ASSETS = ROOT / "report" / "assets"
PROFILE = ROOT / "report" / "chrome-profile"
PORT = 5092


def find_chrome() -> str:
    candidates = [
        pathlib.Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        pathlib.Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        pathlib.Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    exe = shutil.which("chrome") or shutil.which("msedge")
    if exe:
        return exe
    raise RuntimeError("Chrome or Edge executable not found")


def wait_for_server(url: str, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(1)
    raise TimeoutError(f"SwanLab dashboard did not become ready: {url}")


def capture(chrome: str, url: str, output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    PROFILE.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            f"--user-data-dir={PROFILE}",
            "--window-size=1600,1100",
            "--hide-scrollbars",
            "--virtual-time-budget=6000",
            f"--screenshot={output}",
            url,
        ],
        check=True,
    )


def main() -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["SWANLAB_SAVE_DIR"] = str(SAVEDIR)
    env["SWANLAB_LOG_DIR"] = str(LOGDIR)

    swanlab_cmd = shutil.which("swanlab")
    if not swanlab_cmd:
        raise RuntimeError("swanlab command not found; install with: pip install \"swanlab[dashboard]\"")

    out = open(ROOT / "report" / "swanboard.log", "w", encoding="utf-8")
    err = open(ROOT / "report" / "swanboard.err.log", "w", encoding="utf-8")
    server = subprocess.Popen(
        [
            swanlab_cmd,
            "watch",
            str(LOGDIR),
            "-h",
            "127.0.0.1",
            "-p",
            str(PORT),
        ],
        cwd=str(ROOT),
        env=env,
        stdout=out,
        stderr=err,
    )

    try:
        base_url = f"http://127.0.0.1:{PORT}"
        wait_for_server(base_url)
        chrome = find_chrome()

        capture(chrome, base_url, ASSETS / "swanlab_dashboard_overview.png")
        capture(chrome, f"{base_url}/charts", ASSETS / "swanlab_dashboard_charts.png")
        capture(chrome, f"{base_url}/experiment/1/chart", ASSETS / "swanlab_dashboard_task1_chart.png")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        out.close()
        err.close()

    print("SwanLab screenshots saved to report/assets")


if __name__ == "__main__":
    main()

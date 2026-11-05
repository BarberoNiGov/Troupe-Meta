"""Start the studio (8030) and the isolated preview origin (8031)."""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    ("studio ", [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8030"]),
    ("preview", [sys.executable, "-m", "uvicorn", "app.preview:app", "--host", "127.0.0.1", "--port", "8031"]),
]


def main() -> int:
    procs = []
    try:
        for name, command in COMMANDS:
            print(f"starting {name}: {' '.join(command)}", flush=True)
            procs.append(subprocess.Popen(command, cwd=ROOT))
        print("\nstudio  -> http://127.0.0.1:8030", flush=True)
        print("preview -> http://127.0.0.1:8031\n", flush=True)
        while all(proc.poll() is None for proc in procs):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nstopping…", flush=True)
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

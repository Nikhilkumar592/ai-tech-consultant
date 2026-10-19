"""Runner script for Task 3: Meeting-to-Scope Agent Team."""
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TASK3_DIR = ROOT_DIR / "task3-meeting-to-scope"

if __name__ == "__main__":
    print("Starting Meeting-to-Scope Agent Team API on http://localhost:8002...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"],
        cwd=str(TASK3_DIR),
    )

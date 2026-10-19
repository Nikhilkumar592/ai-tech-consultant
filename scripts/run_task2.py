"""Runner script for Task 2: Intelligent Inbox Agent service."""
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TASK2_DIR = ROOT_DIR / "task2-inbox-agent" / "backend"

if __name__ == "__main__":
    print("Starting Intelligent Inbox Agent API & UI on http://localhost:8001...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
        cwd=str(TASK2_DIR),
    )

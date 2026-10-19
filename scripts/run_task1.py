"""Runner script for Task 1: Knowledge Brain RAG service."""
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TASK1_DIR = ROOT_DIR / "task1-knowledge-brain"

if __name__ == "__main__":
    print("Starting Knowledge Brain API on http://localhost:8000...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(TASK1_DIR),
    )

"""Unified test runner for all 3 AI Tech Consultant tasks."""
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

SUITES = [
    ("Task 1: Knowledge Brain RAG", ROOT_DIR / "task1-knowledge-brain"),
    ("Task 2: Intelligent Inbox Agent", ROOT_DIR / "task2-inbox-agent" / "backend"),
    ("Task 3: Meeting-to-Scope Agent Team", ROOT_DIR / "task3-meeting-to-scope"),
]


def run_all():
    print("=" * 70)
    print("AI TECH CONSULTANT CAPSTONE — UNIFIED TEST RUNNER")
    print("=" * 70)

    total_passed = 0
    total_failed = 0
    suite_results = []

    for name, path in SUITES:
        print(f"\n[RUNNING] {name} in {path.name}...")
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "--tb=short"],
            cwd=str(path),
            capture_output=True,
            text=True,
        )

        output = res.stdout + res.stderr
        passed = 0
        failed = 0

        import re
        m_pass = re.search(r"(\d+)\s+passed", output)
        m_fail = re.search(r"(\d+)\s+failed", output)
        if m_pass:
            passed = int(m_pass.group(1))
        if m_fail:
            failed = int(m_fail.group(1))

        total_passed += passed
        total_failed += failed
        suite_results.append((name, passed, failed, res.returncode == 0))
        print(f"Result: {passed} passed, {failed} failed (Exit: {res.returncode})")

    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    for name, p, f, ok in suite_results:
        status_str = "PASS" if ok else "FAIL"
        print(f"{name:<45} | {p} Passed | {f} Failed | {status_str}")
    print("-" * 70)
    print(f"Total Tests Passed: {total_passed} | Total Failed: {total_failed}")
    print("=" * 70)

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all()

import subprocess
import sys


def run_stage(name: str, module: str, *args: str, success_codes: tuple[int, ...] = (0,)) -> bool:
    result = subprocess.run([sys.executable, "-m", module, *args], check=False)
    passed = result.returncode in success_codes
    print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return passed


def main() -> int:
    ruff_passed = run_stage("ruff check", "ruff", "check")
    pytest_passed = run_stage("pytest", "pytest", success_codes=(0, 5))
    return 0 if ruff_passed and pytest_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_python() -> dict[str, str]:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info.major == 3 and sys.version_info.minor == 11
    return {
        "name": "python",
        "status": "pass" if ok else "warn",
        "details": f"detected {version}; expected 3.11.x",
    }


def check_command(name: str, help_arg: str = "--version") -> dict[str, str]:
    cmd = shutil.which(name)
    if not cmd:
        return {"name": name, "status": "fail", "details": "not found in PATH"}

    try:
        output = subprocess.check_output([cmd, help_arg], stderr=subprocess.STDOUT, text=True, timeout=5)
        first_line = output.splitlines()[0] if output else "version check completed"
        return {"name": name, "status": "pass", "details": first_line}
    except Exception as exc:  # pragma: no cover
        return {"name": name, "status": "warn", "details": f"found but version probe failed: {exc}"}


def check_port(host: str, port: int, service: str) -> dict[str, str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        sock.connect((host, port))
        return {
            "name": service,
            "status": "pass",
            "details": f"{host}:{port} reachable",
        }
    except OSError:
        return {
            "name": service,
            "status": "warn",
            "details": f"{host}:{port} not reachable",
        }
    finally:
        sock.close()


def check_model_assets() -> dict[str, str]:
    deepseek = ROOT / "DeepSeek-V4-Pro"
    csm = ROOT / "csm"
    missing = [str(path.name) for path in (deepseek, csm) if not path.exists()]
    if missing:
        return {
            "name": "model-assets",
            "status": "warn",
            "details": f"missing directories: {', '.join(missing)}",
        }
    return {"name": "model-assets", "status": "pass", "details": "DeepSeek and CSM folders present"}


def summarize(results: list[dict[str, str]], allow_warn: bool) -> int:
    status_order = {"pass": 0, "warn": 1, "fail": 2}
    worst = max(results, key=lambda item: status_order[item["status"]])["status"]

    print(json.dumps({"platform": platform.platform(), "checks": results}, indent=2))

    if worst == "fail":
        return 2
    if worst == "warn" and not allow_warn:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local Lockd'In development prerequisites.")
    parser.add_argument(
        "--allow-warn",
        action="store_true",
        help="return success even when checks are warn-level",
    )
    args = parser.parse_args()

    checks: list[dict[str, str]] = []
    checks.append(check_python())
    checks.append(check_command("node"))
    checks.append(check_command("npm"))
    checks.append(check_command("git"))
    checks.append(check_port("127.0.0.1", 5432, "postgres"))
    checks.append(check_port("127.0.0.1", 6379, "redis"))
    checks.append(check_model_assets())
    checks.append(check_port("127.0.0.1", 8000, "lockdin-api"))
    checks.append(check_port("127.0.0.1", 3000, "lockdin-web"))

    return summarize(checks, allow_warn=args.allow_warn)


if __name__ == "__main__":
    raise SystemExit(main())

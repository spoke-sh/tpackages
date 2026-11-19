#!/usr/bin/env python3
"""Repository checks and command dispatch, never a Transit compiler/resolver."""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = {
    "oauth": set(),
    "oauth-facebook": {"oauth"},
    "oauth-google": {"oauth"},
    "oauth-github": {"oauth"},
    "oidc": {"oauth"},
    "saml": set(),
    "scim": set(),
    "webauthn": set(),
    "carddav": {"vcard", "webdav"},
    "caldav": {"icalendar", "webdav"},
    "vcard": set(),
    "icalendar": set(),
    "webdav": set(),
    "websub": set(),
    "json-rpc": set(),
    "tus": set(),
    "standard-webhooks": set(),
    "cloudevents": set(),
}


def command(action, entry):
    result = ["transit", action, "-f", str(entry), "--format", "json", "--color", "off"]
    if action == "build":
        result.append("--check")
    else:
        result.extend(["--target", "tests"])
    return result


def diagnostic_fingerprint(result):
    """Only an ordinary pre-submission compiler refusal can match a gap."""
    if result.returncode != 1 or result.stderr.strip():
        raise ValueError(f"expected exit 1 and a JSON diagnostic, got exit {result.returncode}")
    diagnostic = json.loads(result.stdout)
    if not isinstance(diagnostic, dict):
        raise ValueError("expected one diagnostic object")
    if diagnostic.get("outcome") != "not_submitted" or diagnostic.get("evidence") != "local_before_dispatch":
        raise ValueError("runtime failures are not compiler gaps")
    facts = [fact for fact in diagnostic.get("facts", []) if fact and fact.get("field") == "native_cause"]
    if len(facts) != 1:
        raise ValueError("expected one native cause")
    location = diagnostic.get("location") or {}
    return {
        "definition": diagnostic["definition"],
        "code": diagnostic["code"],
        "category": diagnostic["category"],
        "stage": diagnostic["stage"],
        "native_cause": facts[0]["value"]["text"],
        "source": location.get("source"),
        "line": location.get("line"),
        "byte_column": location.get("byte_column"),
    }


def matches_gap(result, expected):
    try:
        actual = diagnostic_fingerprint(result)
    except (ValueError, KeyError, TypeError) as error:
        return False, str(error)
    if actual != expected:
        return False, f"diagnostic changed: {json.dumps(actual, sort_keys=True)}"
    return True, "recorded compiler gap; downstream stages not run"


def inventory():
    found = {path.name for path in (ROOT / "packages").iterdir() if path.is_dir()}
    if found != set(PACKAGES):
        raise ValueError(f"package inventory changed: {sorted(found)}")
    workspace = (ROOT / "build.transit").read_text()
    registered = set(re.findall(r"PACKAGE\s+\w+\s+AT\s+'\./packages/([^']+)'", workspace))
    if registered != found:
        raise ValueError("workspace registrations do not match package roots")
    for name, expected_dependencies in PACKAGES.items():
        package = ROOT / "packages" / name
        for required in ["README.md", "build.transit", "src", "tests/build.transit", "examples/build.transit"]:
            if not (package / required).exists():
                raise ValueError(f"{name}: missing {required}")
        declarations = re.findall(r"DEPENDENCY\s+(\w+)\s+FROM WORKSPACE\s+'([^']+)'", (package / "build.transit").read_text())
        if {target for _, target in declarations} != expected_dependencies:
            raise ValueError(f"{name}: unexpected declared dependencies")
        aliases = {alias for alias, _ in declarations}
        for source in package.rglob("*.transit"):
            if not source.is_file() or any(part in {".transit", ".git", ".direnv"} for part in source.relative_to(package).parts):
                continue
            text = source.read_text()
            if re.search(r"\b(?:TODO|FIXME|NOT_IMPLEMENTED)\b", text):
                raise ValueError(f"unfinished implementation marker in {source.relative_to(ROOT)}")
            for relative in re.findall(r"'((?:\./|\.\./)[^']+\.transit)'", text):
                resolved = (source.parent / relative).resolve()
                if not resolved.is_relative_to(package.resolve()) or not resolved.is_file():
                    raise ValueError(f"{source.relative_to(ROOT)}: missing or escaping source {relative}")
            for alias, path in re.findall(r"FROM PACKAGE\s+(\w+)\s+FILE\s+'([^']+)'", text):
                if alias not in aliases or path != "build.transit":
                    raise ValueError(f"{source.relative_to(ROOT)}: dependency must use its declared public entry")
        if not any((package / "tests").glob("*.test.transit")):
            raise ValueError(f"{name}: no protocol test cases")
    return len(found)


def snapshot_fixture(directory):
    """An isolated Git test input; no changes to this repository's Git history."""
    snapshot = directory / "snapshot"
    snapshot.mkdir()
    shutil.copy2(ROOT / "build.transit", snapshot / "build.transit")
    shutil.copytree(ROOT / "packages", snapshot / "packages", ignore=shutil.ignore_patterns(".transit", "__pycache__"))
    for args in [
        ["git", "init", "--quiet", str(snapshot)],
        ["git", "-C", str(snapshot), "add", "."],
        ["git", "-C", str(snapshot), "-c", "user.name=Transit fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "commit", "--quiet", "-m", "Fixture snapshot"],
    ]:
        subprocess.run(args, check=True, capture_output=True, timeout=30)
    revision = subprocess.check_output(["git", "-C", str(snapshot), "rev-parse", "HEAD"], text=True).strip()
    consumer = directory / "consumer"
    consumer.mkdir()
    template = (ROOT / "tests/consumers/external/build.transit.in").read_text()
    (consumer / "build.transit").write_text(template.replace("@REPOSITORY@", str(snapshot)).replace("@REVISION@", revision))
    return consumer


def run_case(case, reports):
    if case["entry"] == "@external":
        with tempfile.TemporaryDirectory(prefix="tpackages-consumer-") as temporary:
            consumer = snapshot_fixture(Path(temporary))
            invocation = ["transit", "build", "-f", "build.transit", "--format", "json", "--color", "off", "--fetch"]
            result = subprocess.run(invocation, cwd=consumer, capture_output=True, text=True, timeout=60)
            # The snapshot/consumer are temporary. Redact their nondeterministic
            # paths in stored transcripts, never in the matching fields.
            result.stdout = result.stdout.replace(temporary, "<fixture>")
            result.stderr = result.stderr.replace(temporary, "<fixture>")
    else:
        invocation = command(case["action"], case["entry"]) + case.get("arguments", [])
        result = subprocess.run(invocation, cwd=ROOT, capture_output=True, text=True, timeout=60)
    matched, reason = matches_gap(result, case["expected"])
    report = {
        "case": case["id"], "command": invocation, "requirement": case["requirement"],
        "status": "blocked" if matched else "unexpected", "reason": reason,
        "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
        "sql_emission": "not_run", "installation": "not_run", "protocol_tests": "not_run",
    }
    (reports / f"{case['id']}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{'BLOCKED' if matched else 'UNEXPECTED'} {case['id']}: {reason}", flush=True)
    return matched


def check():
    count = inventory()
    print(f"Package inventory and public-import boundaries: {count} packages", flush=True)
    ledger = json.loads((ROOT / "tooling/support.json").read_text())
    lock = json.loads((ROOT / "flake.lock").read_text())
    for name, revision in ledger["pins"].items():
        if lock["nodes"][name]["locked"]["rev"] != revision:
            raise ValueError(f"{name} pin changed; re-audit compiler gaps")
    entries = [
        ROOT / "build.transit",
        *sorted((ROOT / "packages").glob("*/build.transit")),
        *sorted((ROOT / "tests/consumers").glob("*/build.transit")),
    ]
    expected_cases = {
        (str(path.relative_to(ROOT)), action)
        for path in entries for action in ["build", "test"]
    }
    expected_cases.update(
        (str(path.relative_to(ROOT)), "test" if path.parent.name == "testing" else "build")
        for path in (ROOT / "tests/compiler").glob("*/build.transit")
    )
    recorded = {(case["entry"], case["action"]) for case in ledger["cases"]}
    if not expected_cases.issubset(recorded):
        raise ValueError("missing package/workspace/consumer/probe command gap records")
    ids = [case["id"] for case in ledger["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate gap record ID")
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tooling/tests", "-q"], cwd=ROOT, check=True)
    subprocess.run(["transitc", "--help"], check=True, capture_output=True)
    subprocess.run(["transitc", "--version"], check=True, capture_output=True)
    subprocess.run(["transit", "build", "-f", "tests/bootstrap/build.transit", "--check"], cwd=ROOT, check=True)
    subprocess.run(["transit", "test", "-f", "tests/bootstrap/build.transit"], cwd=ROOT, check=True)
    reports = ROOT / ".transit/reports"
    reports.mkdir(parents=True, exist_ok=True)
    results = [run_case(case, reports) for case in ledger["cases"]]
    if not all(results):
        raise ValueError("unexpected compiler result; inspect .transit/reports and update code or reviewed gap record")
    print(f"Tooling/bootstrap checks passed; {len(results)} compiler attempts remain blocked. No protocol suite has executed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "test", "check"])
    parser.add_argument("package", nargs="?", default="all", choices=["all", "bootstrap", *PACKAGES])
    args = parser.parse_args()
    try:
        if args.action == "check":
            check()
            return 0
        entry = {"all": "build.transit", "bootstrap": "tests/bootstrap/build.transit"}.get(
            args.package, f"packages/{args.package}/build.transit")
        invocation = ["transit", args.action, "-f", entry]
        if args.action == "test":
            invocation.extend(["--target", "tests"])
        return subprocess.run(invocation, cwd=ROOT).returncode
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"Repository check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

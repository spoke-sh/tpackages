set shell := ["bash", "-euo", "pipefail", "-c"]

# List tasks. Build/test accept a package name, all (default), or bootstrap.
default:
    @just --list

# Compile a selected package or the workspace; compiler gaps remain failures.
build package="all":
    python3 tooling/repo.py build {{ quote(package) }}

# Check boundaries, bootstrap, and exact recorded compiler gaps.
check:
    nixfmt --check flake.nix
    just --fmt --check
    python3 tooling/repo.py check
    nix flake check --no-build --no-update-lock-file

# Format repository tooling; upstream does not expose a Transit formatter yet.
fmt:
    nixfmt flake.nix
    just --fmt

# Run selected Transit tests; unsupported execution is never a passing test.
test package="all":
    python3 tooling/repo.py test {{ quote(package) }}

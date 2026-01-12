"""Simple script to create a user in Redis-backed auth store.

Usage:
    python scripts/create_user.py --username alice --password secret
"""
import argparse
import sys

# Ensure project root is on path for imports when running as script
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api import security


def main():
    parser = argparse.ArgumentParser(description="Create a user for the API (Redis-backed)")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--disabled", action="store_true")
    args = parser.parse_args()

    ok = security.create_user(args.username, args.password, disabled=args.disabled)
    if ok:
        print(f"User '{args.username}' created or updated successfully.")
    else:
        print("Failed to create user. Is Redis available?", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()

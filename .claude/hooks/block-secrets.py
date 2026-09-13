#!/usr/bin/env python3
"""PreToolUse hook (Read|Grep): refuse to open files that hold real secrets."""
import json
import re
import sys

BLOCKED = re.compile(
    r"(^|/)\.env$"
    r"|(^|/)config/master\.key$"
    r"|(^|/)config/credentials/.*\.key$"
    r"|(^|/)config/credentials\.yml\.enc$"
    r"|\.pem$"
    r"|(^|/)id_rsa[^/]*$"
    r"|\.p12$"
)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = data.get("tool_input", {})
    candidates = [
        tool_input.get("file_path"),
        tool_input.get("path"),
        tool_input.get("notebook_path"),
    ]

    for candidate in candidates:
        if candidate and BLOCKED.search(candidate):
            print(
                f"Blocked: '{candidate}' looks like a secrets file "
                "(.env, config/master.key, credentials.yml.enc, a key/cert). "
                "Ask the human to paste the specific value you need instead.",
                file=sys.stderr,
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())

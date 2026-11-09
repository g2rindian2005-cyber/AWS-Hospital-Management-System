#!/usr/bin/env python3
"""Validate frontend JavaScript syntax for CI.

Checks every standalone .js file and every inline <script> block in the
HTML pages with `node --check`. The application code is never executed;
Node only parses the source, so this catches syntax errors safely.
"""

from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

SCRIPT_RE = re.compile(
    r"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
SRC_RE = re.compile(r"\bsrc\s*=", re.IGNORECASE)
TYPE_RE = re.compile(r"\btype\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
JS_TYPES = {
    "",
    "text/javascript",
    "application/javascript",
    "text/ecmascript",
    "application/ecmascript",
    "module",
}


def node_check(source: str, label: str, module: bool = False) -> bool:
    suffix = ".mjs" if module else ".js"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, encoding="utf-8", delete=False
    ) as handle:
        handle.write(source)
        temp_path = handle.name

    try:
        result = subprocess.run(
            ["node", "--check", temp_path],
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        Path(temp_path).unlink(missing_ok=True)

    if result.returncode:
        print(f"\nJavaScript syntax error in {label}", file=sys.stderr)
        print((result.stderr or result.stdout).strip(), file=sys.stderr)
        return False
    return True


def main() -> int:
    failures = 0
    checked = 0

    for path in sorted(FRONTEND.rglob("*.js")):
        checked += 1
        if not node_check(
            path.read_text(encoding="utf-8"),
            str(path.relative_to(ROOT)),
            module=path.suffix == ".mjs",
        ):
            failures += 1

    for path in sorted(FRONTEND.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        for index, match in enumerate(SCRIPT_RE.finditer(text), start=1):
            attrs = match.group("attrs")
            if SRC_RE.search(attrs):
                continue

            type_match = TYPE_RE.search(attrs)
            script_type = type_match.group(1).lower() if type_match else ""
            if script_type not in JS_TYPES:
                continue

            body = match.group("body").strip()
            if not body:
                continue

            checked += 1
            label = f"{path.relative_to(ROOT)} inline script #{index}"
            if not node_check(body, label, module=script_type == "module"):
                failures += 1

    if failures:
        print(f"\nFrontend validation failed: {failures} syntax error(s).", file=sys.stderr)
        return 1

    print(f"Frontend validation passed: {checked} JavaScript blocks/files checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

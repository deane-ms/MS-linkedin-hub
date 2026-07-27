"""Regenerates index.html from the canonical dashboard source (the Claude Artifact's
content-hub.html), wrapping it with the DOCTYPE/head/body structure GitHub Pages needs
and the Mediashock favicon link -- the Artifact host adds an equivalent wrapper itself,
but raw GitHub Pages serving does not.

Also stamps a build version (current UTC timestamp) into index.html and writes it to
version.txt, so the running app can detect a new deploy and reload itself -- see the
"live update" block in content-hub-firebase.html for the client side of this.

Usage: python sync_from_scratchpad.py <path-to-content-hub.html>
"""
import sys
from datetime import datetime, timezone

SOURCE_TITLE = '<title>MediaShock APAC - LinkedIn Content Hub</title>'
BUILD_VERSION_PLACEHOLDER = "__BUILD_VERSION__"
HEAD_OPEN = (
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    + SOURCE_TITLE + '\n'
    '<link rel="icon" type="image/png" href="favicon.png">\n'
    '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
    '<link rel="manifest" href="manifest.json">\n'
    '<meta name="theme-color" content="#ff4e20">\n'
)
BODY_MARKER = '.modal-backdrop, .modal, .chart-tooltip { transition: none; }\n  }\n</style>\n'
BODY_OPEN = BODY_MARKER + '</head>\n<body>\n'

def main():
    if len(sys.argv) != 2:
        print("Usage: python sync_from_scratchpad.py <path-to-content-hub.html>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        content = f.read()

    build_version = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content = content.replace(SOURCE_TITLE, HEAD_OPEN, 1)
    content = content.replace(BODY_MARKER, BODY_OPEN, 1)
    content = content.replace(BUILD_VERSION_PLACEHOLDER, build_version)
    content = content.rstrip() + "\n</body>\n</html>"

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    with open("version.txt", "w", encoding="utf-8") as f:
        f.write(build_version)
    print("Wrote index.html,", len(content), "bytes -- build", build_version)

if __name__ == "__main__":
    main()

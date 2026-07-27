"""Regenerates index.html from the canonical dashboard source (the Claude Artifact's
content-hub.html), wrapping it with the DOCTYPE/head/body structure GitHub Pages needs
and the Mediashock favicon link -- the Artifact host adds an equivalent wrapper itself,
but raw GitHub Pages serving does not.

Usage: python sync_from_scratchpad.py <path-to-content-hub.html>
"""
import sys

SOURCE_TITLE = '<title>MediaShock APAC - LinkedIn Content Hub</title>'
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

    content = content.replace(SOURCE_TITLE, HEAD_OPEN, 1)
    content = content.replace(BODY_MARKER, BODY_OPEN, 1)
    content = content.rstrip() + "\n</body>\n</html>"

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote index.html,", len(content), "bytes")

if __name__ == "__main__":
    main()

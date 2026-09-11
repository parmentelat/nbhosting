#!/usr/bin/env python3
"""
for each top-level folder under <root> (typically /nbhosting/prod/students),
report the most recent mtime found recursively, the number of regular files,
and their total size

unlike a find+awk pipeline, this never round-trips filenames through a
text/line format, so it is immune to filenames containing spaces, commas,
apostrophes, unicode, or even embedded newlines - all of which are legal
in a Linux filename
"""

import sys
from datetime import datetime
from pathlib import Path
from stat import S_ISREG

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

max_mtime = {}
count = {}
size = {}

for path in root.rglob("*"):
    top = path.relative_to(root).parts[0]
    try:
        st = path.stat(follow_symlinks=False)
    except OSError as exc:
        print(f"warning: skip {path}: {exc}", file=sys.stderr)
        continue
    if not S_ISREG(st.st_mode):
        continue
    max_mtime[top] = max(max_mtime.get(top, 0), st.st_mtime)
    count[top] = count.get(top, 0) + 1
    size[top] = size.get(top, 0) + st.st_size

for folder in sorted(max_mtime, key=lambda f: max_mtime[f]):
    dt = datetime.fromtimestamp(max_mtime[folder]).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{dt}\t{count[folder]}\t{size[folder] / 1024 / 1024:.1f}\t{folder}")

#!/usr/bin/env python3
"""Fix server.py corruption by removing garbled duplicate lines.

The corruption pattern is: every garbled line is followed by its clean twin.
Strategy: remove lines that are prefixes/superset duplicates of the next line.
Then restore from git HEAD if clean, otherwise apply de-duplication filter.
"""
import subprocess
import py_compile
import tempfile
import os
import sys

SERVER_PY = os.path.join(os.path.dirname(__file__), "../../backend/api/server.py")
SERVER_PY = os.path.abspath(SERVER_PY)

def check_syntax(content: str) -> bool:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(content)
        fname = f.name
    try:
        py_compile.compile(fname, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  Syntax error: {e}", file=sys.stderr)
        return False
    finally:
        os.unlink(fname)

# --- Strategy 1: Restore from git HEAD ---
print("Strategy 1: Trying git HEAD restore...")
result = subprocess.run(
    ["git", "show", "HEAD:backend/api/server.py"],
    capture_output=True, text=True,
    cwd=os.path.dirname(os.path.dirname(SERVER_PY))
)
if result.returncode == 0 and check_syntax(result.stdout):
    head_lines = len(result.stdout.splitlines())
    print(f"  HEAD version: {head_lines} lines, syntax OK!")
    with open(SERVER_PY, 'w', encoding='utf-8') as f:
        f.write(result.stdout)
    print("  ✔ Restored from git HEAD")
    sys.exit(0)
else:
    print(f"  HEAD has syntax errors too — trying deduplication...")

# --- Strategy 2: De-duplication filter ---
print("Strategy 2: Applying deduplication filter...")
with open(SERVER_PY, 'r', encoding='utf-8') as f:
    lines = f.readlines()

CORRUPT_START = 4228  # 0-indexed (line 4229 in 1-indexed)
clean_head = lines[:CORRUPT_START]
corrupted = lines[CORRUPT_START:]

clean_tail = []
i = 0
removed = 0
while i < len(corrupted):
    line = corrupted[i]
    stripped = line.rstrip('\n').rstrip()

    if i + 1 < len(corrupted):
        next_line = corrupted[i + 1]
        next_stripped = next_line.rstrip('\n').rstrip()

        # Detect garbled line: next line starts with 10+ chars of this line
        # AND this line has extra garbage appended after those chars
        prefix_check = min(12, len(stripped), len(next_stripped))
        if (prefix_check >= 8
                and stripped[:prefix_check] == next_stripped[:prefix_check]
                and len(stripped) > len(next_stripped)):
            # This line is the garbled version — skip it
            removed += 1
            i += 1
            continue

        # Detect exact duplicate (same content)
        if stripped and stripped == next_stripped:
            removed += 1
            i += 1
            continue

        # Detect garbled inline comment / separator lines (═══ duplicated)
        if '═' in stripped and '═' in next_stripped and i + 1 < len(corrupted):
            # Keep only one
            next2 = corrupted[i + 2].rstrip('\n').rstrip() if i + 2 < len(corrupted) else ''
            if next2 == next_stripped:
                removed += 1
                i += 1
                continue

    clean_tail.append(line)
    i += 1

all_clean = clean_head + clean_tail
content = ''.join(all_clean)
print(f"  Removed {removed} garbled/duplicate lines")
print(f"  New total: {len(all_clean)} lines")

if check_syntax(content):
    with open(SERVER_PY, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✔ server.py fixed and syntax verified!")
    sys.exit(0)
else:
    print("  ✖ de-duplication result still has syntax errors")
    print("  Trying broader git restore from parent commit...")

# --- Strategy 3: Try parent commits ---
for ref in ["HEAD~1", "HEAD~2", "1d19c42"]:
    print(f"Strategy 3: Trying {ref}...")
    result = subprocess.run(
        ["git", "show", f"{ref}:backend/api/server.py"],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(SERVER_PY))
    )
    if result.returncode == 0 and check_syntax(result.stdout):
        head_lines = len(result.stdout.splitlines())
        print(f"  {ref} version: {head_lines} lines, syntax OK!")
        with open(SERVER_PY, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        print(f"  ✔ Restored from {ref}")
        sys.exit(0)

print("ERROR: Could not fix server.py automatically.", file=sys.stderr)
sys.exit(1)

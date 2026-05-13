"""
Transcript'teki tüm Write/Edit tool çağrılarını ana proje dizinine uygular.
- Write: dosyayı doğrudan yazar (yeni dosyalar)
- Edit: mevcut dosya üzerinde patch uygular (zaten var olan dosyalar)
"""
import json, os, sys

TRANSCRIPT = r'C:/Users/himmo/.claude/projects/C--Users-himmo-Desktop-e-student-course-selection-and-academic-management-program--claude-worktrees-upbeat-varahamihira-7480c0/ba255155-a47a-430c-99ab-95e2b53cdbd1.jsonl'

SEP = os.sep
WORKTREE = SEP.join(['C:', 'Users', 'himmo', 'Desktop', 'e',
    'student course selection and academic management program',
    '.claude', 'worktrees', 'upbeat-varahamihira-7480c0'])
MAIN = SEP.join(['C:', 'Users', 'himmo', 'Desktop', 'e',
    'student course selection and academic management program'])

# Files to SKIP (we don't want to touch these)
SKIP_PATTERNS = [
    'recover_transcript.py',
    'recover_and_apply.py',
    'seed_demo_users.py',      # management commands — keep existing
    'seed_student_profiles.py',
]

# In-memory virtual filesystem: path -> content
vfs = {}

def normalize(fp):
    fp = fp.replace('/', SEP)
    if fp.startswith(WORKTREE):
        return MAIN + fp[len(WORKTREE):]
    return fp

def get_content(fp):
    """Get current content: from vfs if tracked, else from disk."""
    if fp in vfs:
        return vfs[fp]
    if os.path.exists(fp):
        with open(fp, encoding='utf-8') as fh:
            return fh.read()
    return None

# Process all tool calls in order
ops = []
with open(TRANSCRIPT, encoding='utf-8') as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        for block in obj.get('message', {}).get('content', []):
            if not isinstance(block, dict) or block.get('type') != 'tool_use':
                continue
            name = block['name']
            if name not in ('Write', 'Edit'):
                continue
            inp = block.get('input', {})
            fp  = normalize(inp.get('file_path', ''))
            if not fp or any(pat in fp for pat in SKIP_PATTERNS):
                continue
            ops.append((name, fp, inp))

print(f"Total operations: {len(ops)}")

write_count = 0
edit_ok = 0
edit_fail = 0
edit_skip = 0

for name, fp, inp in ops:
    if name == 'Write':
        vfs[fp] = inp.get('content', '')
        write_count += 1
    elif name == 'Edit':
        current = get_content(fp)
        if current is None:
            edit_skip += 1
            print(f"  SKIP (not found): {fp[len(MAIN)+1:]}")
            continue
        old = inp.get('old_string', '')
        new = inp.get('new_string', '')
        if inp.get('replace_all'):
            updated = current.replace(old, new)
        else:
            updated = current.replace(old, new, 1)
        if updated == current and old:
            edit_fail += 1
            print(f"  MISS (patch not applied): {fp[len(MAIN)+1:]}  old_len={len(old)}")
        else:
            vfs[fp] = updated
            edit_ok += 1

print(f"\nWrites: {write_count}, Edits OK: {edit_ok}, Edits missed: {edit_fail}, Skipped: {edit_skip}")

# Write everything to disk
written = 0
skipped_existing = 0
for fp, content in vfs.items():
    rel = fp[len(MAIN)+1:]
    # Check if file already has this exact content
    if os.path.exists(fp):
        with open(fp, encoding='utf-8') as fh:
            existing = fh.read()
        if existing == content:
            skipped_existing += 1
            continue
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as fh:
        fh.write(content)
    print(f"  wrote: {rel}")
    written += 1

print(f"\nWrote {written} files to disk ({skipped_existing} already up-to-date).")

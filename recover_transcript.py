import json, os

TRANSCRIPT = r'C:/Users/himmo/.claude/projects/C--Users-himmo-Desktop-e-student-course-selection-and-academic-management-program--claude-worktrees-upbeat-varahamihira-7480c0/ba255155-a47a-430c-99ab-95e2b53cdbd1.jsonl'

SEP = os.sep
WORKTREE = SEP.join(['C:', 'Users', 'himmo', 'Desktop', 'e',
    'student course selection and academic management program',
    '.claude', 'worktrees', 'upbeat-varahamihira-7480c0'])
MAIN = SEP.join(['C:', 'Users', 'himmo', 'Desktop', 'e',
    'student course selection and academic management program'])

files = {}

def normalize(fp):
    fp = fp.replace('/', SEP)
    if fp.startswith(WORKTREE):
        return MAIN + fp[len(WORKTREE):]
    return fp

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
            inp  = block.get('input', {})
            fp   = normalize(inp.get('file_path', ''))
            if not fp:
                continue

            if name == 'Write':
                files[fp] = inp.get('content', '')
            elif name == 'Edit':
                old = inp.get('old_string', '')
                new = inp.get('new_string', '')
                if fp in files:
                    if inp.get('replace_all'):
                        files[fp] = files[fp].replace(old, new)
                    else:
                        files[fp] = files[fp].replace(old, new, 1)

print(f"Recovered {len(files)} files:")
for fp, content in sorted(files.items()):
    rel = fp[len(MAIN)+1:]
    print(f"  {len(content):6d} chars  {rel}")

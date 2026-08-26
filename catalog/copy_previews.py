"""Copy each pack's preview image into catalog/previews/ so the repo can show
the art without shipping it. Kenney previews only - CC0, redistributable.
Re-runnable and idempotent."""
import json, os, re, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = 'D:/Claude/Games/assets'
OUT = ROOT + '/catalog/previews'
packs = json.load(open(ROOT + '/catalog/packs.json', encoding='utf-8'))

def slug(s):
    s = re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-').lower()
    return re.sub(r'-+', '-', s)

copied = skipped_nopreview = 0
failures = []
for p in packs:
    if not p.get('preview'):
        skipped_nopreview += 1
        continue
    src = ROOT + '/' + p['preview']
    dst_dir = OUT + '/' + slug(p['section'])
    dst = dst_dir + '/' + slug(p['pack']) + '.png'
    try:
        if not os.path.isfile(src):
            failures.append('MISSING SOURCE: ' + src)
            continue
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copyfile(src, dst)
        p['preview_local'] = os.path.relpath(dst, ROOT).replace(os.sep, '/')
        copied += 1
    except Exception as e:
        failures.append(repr(e) + ' :: ' + src)

with open(ROOT + '/catalog/packs.json', 'w', encoding='utf-8', newline='\n') as f:
    json.dump(packs, f, indent=1, ensure_ascii=True)

total_bytes = sum(os.path.getsize(os.path.join(d, fn))
                  for d, _, fns in os.walk(OUT) for fn in fns)
print('packs                :', len(packs))
print('previews copied      :', copied)
print('packs with no preview:', skipped_nopreview)
print('failures             :', len(failures))
for f in failures[:10]:
    print('   FAIL', f)
print('previews total MB    : %.2f' % (total_bytes / 1048576))

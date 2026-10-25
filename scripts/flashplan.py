# Maps the HOS 4.2 images (NAME_k.img extracted from the UPDATE.APP files) to the partitions of the NEW GPT,
# checks that every image fits, and writes a PowerShell flash script for bootloader fastboot.
# It sends nothing to the device.
# Usage: python flashplan.py <img_root> <gpt_dir> <out.ps1>
#   img_root: folder with base/ cust/ preload/ subfolders (one per UPDATE.APP)
#   gpt_dir:  primary GPT of every LUN 0..5: lunN_primary.bin (from gptmake.py) or gpt_mainN.bin (unchanged LUNs)
import sys, os, struct, glob, hashlib

SS = 4096
img_root, gpt_dir, out_ps1 = sys.argv[1:4]

# Not written: table/version records (not partitions) and ABL (the unlocked ABL must stay)
SKIP = {'ABL': 'keep the unlocked ABL, never flash the stock one',
        'EFI': 'GPT template; the GPT is written separately in EDL', 'FI': 'GPT template',
        'PTABLE_CUST': 'table record', 'PTABLE_PRELOAD': 'table record',
        'CRC': 'package record', 'SHA256RSA': 'package signature', 'PACKAGE_TYPE': 'package record',
        'BASE_VER': 'version record', 'BASE_VERLIST': 'version record', 'CUST_VER': 'version record',
        'CUST_VERLIST': 'version record', 'PRELOAD_VER': 'version record', 'PRELOAD_VERLIST': 'version record'}


def parts_of(path):
    d = open(path, 'rb').read()
    el, n, es = struct.unpack_from('<QII', d, SS + 72)
    res = {}
    for i in range(n):
        e = d[el * SS + i * es: el * SS + (i + 1) * es]
        if len(e) < es or e[:16] == b'\0' * 16:
            continue
        f, l = struct.unpack_from('<QQ', e, 32)
        res[e[56:128].decode('utf-16le').rstrip('\0').lower()] = (l - f + 1) * SS
    return res


parts = {}
for lun in range(6):
    cand = [p for p in (f'{gpt_dir}/lun{lun}_primary.bin', f'{gpt_dir}/gpt_main{lun}.bin') if os.path.exists(p)]
    for k, v in parts_of(cand[0]).items():
        parts[k] = (lun, v)


def img_size(p):
    with open(p, 'rb') as f:
        h = f.read(28)
    if struct.unpack_from('<I', h)[0] == 0xED26FF3A:
        bsz, tblk = struct.unpack_from('<II', h, 12)
        return bsz * tblk, 'sparse'
    return os.path.getsize(p), 'raw'


plan, skipped, problems = [], [], []
for pkg in ('base', 'cust', 'preload'):
    for p in sorted(glob.glob(f'{img_root}/{pkg}/*_[0-9].img')):
        stem = os.path.basename(p).rsplit('_', 1)[0]
        if stem in SKIP:
            skipped.append((pkg, stem, SKIP[stem]))
            continue
        low = stem.lower()
        # UPDATE.APP names are cut at 16 characters (ERECOVERY_RAMDIS, VBMETA_HW_PRODUC)
        match = [k for k in parts if k == low] or [k for k in parts if len(low) == 16 and k.startswith(low)]
        if len(match) != 1:
            problems.append(f'{pkg}/{stem}: partition match {match}')
            continue
        part = match[0]
        size, kind = img_size(p)
        lun, psize = parts[part]
        if size > psize:
            problems.append(f'{pkg}/{stem}: {size} bytes > {part} {psize} bytes')
            continue
        plan.append((pkg, stem, part, lun, size, psize, kind, p))

print(f'{"package":8} {"image":20} {"partition":20} LUN {"image":>12} {"partition":>12} type')
for pkg, stem, part, lun, size, psize, kind, _ in plan:
    print(f'{pkg:8} {stem:20} {part:20} {lun:3} {size:12} {psize:12} {kind}')
print(f'\nto write: {len(plan)} partitions')
for s in skipped:
    print('skipped:', *s)
for pr in problems:
    print('PROBLEM:', pr)
# SUPER comes as two sparse parts (SUPER_0, SUPER_1); they don't overlap and are written one after the other.
dup = {x[2] for x in plan if [y[2] for y in plan].count(x[2]) > 1} - {'super'}
if dup:
    print('PROBLEM: more than one image for the same partition:', dup)
if problems or dup:
    sys.exit(1)

# The script checks before EVERY write that it is in bootloader fastboot (not fastbootd) and stops at the first error.
# PowerShell 5.1: fastboot writes to stderr; "Stop" + 2>&1 would treat that as an error, so "Continue" is used and
# success is judged by the exit code and by "FAILED" in the output.
L = ['$ErrorActionPreference = "Continue"',
     r'$fb = (Get-Command fastboot -ErrorAction SilentlyContinue).Source',
     r'if (-not $fb) { $fb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\fastboot.exe" }',
     'function FB { $o = (& $fb @args 2>&1 | ForEach-Object { "$_" }) -join "`n"; return @($LASTEXITCODE, $o) }',
     'function Check-Bootloader { $r = FB getvar is-userspace; '
     r'if ($r[1] -notmatch "is-userspace:\s*no") { Write-Host "STOP: not in bootloader fastboot: $($r[1])"; exit 2 } }',
     'function Flash($part, $img) { Check-Bootloader; Write-Host "== $part <- $img"; $r = FB flash $part $img; '
     'Write-Host $r[1]; if ($r[0] -ne 0 -or $r[1] -match "FAILED") { Write-Host "STOP: write failed: $part"; exit 3 } }',
     r'$u = FB getvar unlocked; if ($u[1] -notmatch "unlocked:\s*yes") { Write-Host "STOP: bootloader not unlocked: $($u[1])"; exit 4 }']
for pkg, stem, part, lun, size, psize, kind, p in plan:
    L.append(f'Flash "{part}" "{os.path.abspath(p)}"')
L.append('Write-Host "All partitions written. ABL untouched. Next: fastboot getvar unlocked, then fastboot reboot."')
open(out_ps1, 'w', encoding='utf-8-sig').write('\r\n'.join(L) + '\r\n')
print('script:', out_ps1, hashlib.sha256(open(out_ps1, 'rb').read()).hexdigest())

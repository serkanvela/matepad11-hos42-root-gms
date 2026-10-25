# Huawei oeminfo region/model record converter (the same 9-byte change other tools make, done transparently).
# Usage: python oeminfo_region.py in.bin out.bin      -> lists the records, converts to all/cn and DBY-W09
# Record layout (observed): "OEM_INFO" | version u32 | id u32 | type u32 | length u32 | age u32 ... data @ +0x200, empty = 0xFF
import sys, struct

src, dst = sys.argv[1], sys.argv[2]
d = bytearray(open(src, 'rb').read())
EDIT = {0x12: b'all/cn', 0x61: b'DBY-W09'}   # 0x12: vendor/country, 0x61: product model
found = {}
for off in range(0, len(d), 0x1000):
    if d[off:off+8] != b'OEM_INFO': continue
    ver, oid, typ, ln, age = struct.unpack_from('<5I', d, off + 8)
    if oid in EDIT:
        old = bytes(d[off+0x200: off+0x200+ln])
        print(f'record id=0x{oid:02x} @0x{off:x} age={age} old={old!r}')
        found.setdefault(oid, []).append((age, off, ln))
for oid, lst in found.items():
    for age, off, ln in lst:   # update every copy of the id (the newest by age is the one that is read)
        new = EDIT[oid]
        d[off+0x200: off+0x200+max(ln, len(new))] = new + b'\xff' * (max(ln, len(new)) - len(new))
        struct.pack_into('<I', d, off + 20, len(new))
missing = set(EDIT) - set(found)
if missing: sys.exit(f'ERROR: record not found: {missing}')
open(dst, 'wb').write(d)
a = open(src, 'rb').read(); print('changed bytes:', sum(1 for x, y in zip(a, d) if x != y))

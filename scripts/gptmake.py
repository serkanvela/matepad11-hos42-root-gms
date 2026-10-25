# Builds a device-specific GPT for one LUN from the HOS 4.2 GPT template (EFI_0.img from the base package:
# 11 sectors per LUN = protective MBR + header + 4 entry sectors | 4 entry sectors + backup header).
# Taken from the device's CURRENT GPT: disk GUID, unique GUIDs of partitions with the same name, backup header LBA
# and last usable LBA. Huawei rule (seen on all 6 LUNs of the device): the last partition is grown to the end of
# the disk. New partitions get random GUIDs.
# Usage: python gptmake.py EFI_0.img LUN device_gpt_mainN.bin out_prefix [--selftest] [--backup-entries-lba=N]
#   device_gpt_mainN.bin: the gpt_mainN.bin that "edl rl ... --genxml" (or "edl gpt") saved for that LUN
#   --selftest: compare the result with the device GPT instead of writing (use on an unchanged LUN: 1, 2, 3, 5)
#   --backup-entries-lba: read it from YOUR backup header (offset 72 of the last sector). On LUN0 it is NOT backup-4.
import sys, struct, zlib, uuid

SS = 4096
tmpl_path, lun, dev_path, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
selftest = '--selftest' in sys.argv
bel = next((int(a.split('=')[1]) for a in sys.argv if a.startswith('--backup-entries-lba=')), None)

t = open(tmpl_path, 'rb').read()[lun * 11 * SS:(lun + 1) * 11 * SS]
d = open(dev_path, 'rb').read()
assert t[SS:SS + 8] == b'EFI PART' and d[SS:SS + 8] == b'EFI PART'


def hdr(b):
    cur, bak, fu, lu = struct.unpack_from('<QQQQ', b, 24)
    el, n, es = struct.unpack_from('<QII', b, 72)
    return cur, bak, fu, lu, b[56:72], el, n, es


_, dbak, dfu, dlu, dguid, del_, dn, des = hdr(d[SS:])
_, _, tfu, _, _, tel, tn, tes = hdr(t[SS:])
assert (tfu, tel, tn, tes) == (dfu, del_, dn, des), 'header geometry differs'


def entries(b, el, n, es):
    return [b[el * SS + i * es: el * SS + (i + 1) * es] for i in range(n)]


def name(e):
    return e[56:128].decode('utf-16le').rstrip('\0')


# The "last_parti" sentinel entry (zero type GUID, but has a name) keeps its own GUID on the device too.
dev_guid = {name(e): e[16:32] for e in entries(d, del_, dn, des) if name(e)}
tents = entries(t, tel, tn, tes)
used = [i for i, e in enumerate(tents) if e[:16] != b'\0' * 16]
last = max(used, key=lambda i: struct.unpack_from('<Q', tents[i], 32)[0])

new, report = [], []
for i, e in enumerate(tents):
    e = bytearray(e)
    nm = name(e)
    if nm:
        if nm in dev_guid:
            e[16:32] = dev_guid[nm]
        else:
            e[16:32] = uuid.uuid4().bytes_le
            report.append(f'new entry: {nm} (random GUID)')
    if i in used:
        if i == last:
            first, end = struct.unpack_from('<QQ', e, 32)
            struct.pack_into('<Q', e, 40, dlu)
            report.append(f'last partition grown: {nm} {first}..{end} -> {first}..{dlu}')
        f, l = struct.unpack_from('<QQ', e, 32)
        assert dfu <= f <= l <= dlu, f'{nm} out of bounds'
    new.append(bytes(e))

# overlap check
spans = sorted(struct.unpack_from('<QQ', e, 32) + (name(e),) for e in new if e[:16] != b'\0' * 16)
for (f1, l1, n1), (f2, l2, n2) in zip(spans, spans[1:]):
    assert l1 < f2, f'overlap: {n1} / {n2}'

ent_bytes = b''.join(new)
ent_area = ent_bytes + b'\0' * (4 * SS - len(ent_bytes))  # 4-sector entry area
ecrc = zlib.crc32(ent_bytes) & 0xffffffff


def mkhdr(cur, alt, el):
    h = bytearray(t[SS:SS + 92])
    struct.pack_into('<QQQQ', h, 24, cur, alt, dfu, dlu)
    h[56:72] = dguid
    struct.pack_into('<Q', h, 72, el)
    struct.pack_into('<I', h, 88, ecrc)
    struct.pack_into('<I', h, 16, 0)
    struct.pack_into('<I', h, 16, zlib.crc32(h) & 0xffffffff)
    return bytes(h) + b'\0' * (SS - 92)


mbr = t[:SS]
primary = mbr + mkhdr(1, dbak, 2) + ent_area                 # LBA 0..5
bel = dbak - 4 if bel is None else bel
assert dlu < bel and bel + 4 <= dbak
bakent, bakhdr = ent_area, mkhdr(dbak, 1, bel)                # entries at LBA bel..bel+3, header at LBA dbak
assert len(primary) == 6 * SS

for r in report:
    print(r)
print(f'LUN{lun}: backup header LBA {dbak}, backup entries LBA {bel}, last usable {dlu}, entries CRC {ecrc:08x}')

if selftest:
    same = primary[:len(d)] == d
    print('SELFTEST (byte-for-byte against the device primary GPT):', 'SAME' if same else 'DIFFERENT')
    if not same:
        diff = [i for i in range(len(d)) if primary[i] != d[i]]
        print('  differing bytes', len(diff), 'first', diff[:10])
    sys.exit(0 if same else 1)

open(out + '_primary.bin', 'wb').write(primary)
open(out + '_bakent.bin', 'wb').write(bakent)
open(out + '_bakhdr.bin', 'wb').write(bakhdr)
print('written:', out + '_primary.bin (LBA 0)', out + f'_bakent.bin (LBA {bel})', out + f'_bakhdr.bin (LBA {dbak})')

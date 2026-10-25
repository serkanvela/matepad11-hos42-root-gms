# Huawei UPDATE.APP extractor.
#   python updateapp.py UPDATE.APP                  -> list the images only
#   python updateapp.py UPDATE.APP out_dir [NAME..]  -> extract all (or only the named) images as NAME_k.img
# Names are cut at 16 characters (e.g. ERECOVERY_RAMDIS). Repeated names get _0, _1 ... (SUPER comes as SUPER_0, SUPER_1).
import struct, sys, os

src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None; want = set(sys.argv[3:])
f = open(src, 'rb'); size = os.path.getsize(src)
buf = f.read(4096); pos = buf.find(struct.pack('<I', 0xA55AAA55)); seen = {}   # file may start with padding
if out: os.makedirs(out, exist_ok=True)
while 0 <= pos < size:
    f.seek(pos); h = f.read(98)
    if len(h) < 98 or struct.unpack('<I', h[:4])[0] != 0xA55AAA55: break
    hlen = struct.unpack('<I', h[4:8])[0]; fsize = struct.unpack('<I', h[24:28])[0]
    name = h[60:76].split(b'\0')[0].decode(errors='replace'); dpos = pos + hlen
    k = seen.get(name, 0); seen[name] = k + 1
    if not out:
        print(f'{name}_{k}  {fsize}')
    elif not want or name in want:
        fn = os.path.join(out, f'{name}_{k}.img'); f.seek(dpos)
        with open(fn, 'wb') as o:
            left = fsize
            while left: c = f.read(min(left, 8 << 20)); o.write(c); left -= len(c)
        print('written', fn, fsize)
    pos = dpos + fsize; pos += (-pos) % 4

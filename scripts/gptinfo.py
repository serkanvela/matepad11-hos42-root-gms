# Prints a GPT header and its partition list from a dump with 4096-byte sectors.
#   python gptinfo.py gpt_main0.bin          -> primary GPT (header in sector 1, entries follow)
#   python gptinfo.py bakhdr0.bin            -> a single backup-header sector (header only)
import sys, struct

SS = 4096
d = open(sys.argv[1], 'rb').read()
off = SS if d[SS:SS + 8] == b'EFI PART' else 0
assert d[off:off + 8] == b'EFI PART', 'no GPT header found'
cur, alt, fu, lu = struct.unpack_from('<QQQQ', d, off + 24)
el, n, es = struct.unpack_from('<QII', d, off + 72)
print(f'header LBA {cur}, other header LBA {alt}, usable LBA {fu}..{lu}, entries at LBA {el} ({n} x {es} bytes)')
if off == SS and len(d) >= (el + 1) * SS:
    for i in range(n):
        e = d[el * SS + i * es: el * SS + (i + 1) * es]
        if len(e) < es or e[:16] == b'\0' * 16:
            continue
        f, l = struct.unpack_from('<QQ', e, 32)
        name = e[56:128].decode('utf-16le').rstrip('\0')
        print(f'{name:24} first {f:10}  last {l:10}  sectors {l - f + 1:10}  ({(l - f + 1) * SS / 2**20:.0f} MiB)')

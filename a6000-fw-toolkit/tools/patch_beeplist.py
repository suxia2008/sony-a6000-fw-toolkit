import struct, sys, zlib

IMG = r'D:\edge下载\a6000_unpacked\firmware.tar_unpacked\0700_part_image\dev\nflasha15_unpacked'
TPZL = r'D:\edge下载\a6000_unpacked\firmware.tar_unpacked\0700_part_image\dev\nflasha15'
OUT_TPZL = r'D:\edge下载\nflasha15_mod'

# ext2 layout from analysis
BLOCK = 1024
BEEPLIST_BLOCKS = [82956, 82957, 82958, 82959]
BEEPLIST_SIZE = 3443

img = bytearray(open(IMG, 'rb').read())
data = bytearray()
for b in BEEPLIST_BLOCKS:
    data += img[b*BLOCK:(b+1)*BLOCK]
data = data[:BEEPLIST_SIZE]

old = b'Dslr_Emnt_FocusLock.bin'
new = b'Dslr_Emnt_T_Select.bin'.ljust(len(old), b' ')
assert len(new) == len(old)
i = data.find(old)
assert i >= 0, 'token not found'
data[i:i+len(old)] = new
print('patched at file offset', i, data[max(0,i-40):i+40])

# write back into image blocks
full = bytes(data).ljust(len(BEEPLIST_BLOCKS)*BLOCK, b'\x00')
for k, b in enumerate(BEEPLIST_BLOCKS):
    img[b*BLOCK:(b+1)*BLOCK] = full[k*BLOCK:(k+1)*BLOCK]

# recompress affected TPZL blocks
sys.path.insert(0, r'D:\edge下载')
from tpzl_encode import lz77_compress

t = open(TPZL, 'rb').read()
magic, bslog, tocOff, tocSize = struct.unpack_from('<4sIII', t, 0)
bs = 1 << bslog
n = tocSize // 8
entries = [list(struct.unpack_from('<II', t, tocOff + i*8)) for i in range(n)]

changed = {1296, 1297}
payload = bytearray()
new_entries = []
for idx in range(n):
    if idx in changed:
        raw = bytes(img[idx*bs:(idx+1)*bs])
        enc = lz77_compress(raw)
        new_entries.append([24 + len(payload), len(enc)])
        payload += enc
        print('block', idx, 'new size', len(enc))
    else:
        off, size = entries[idx]
        new_entries.append([24 + len(payload), size])
        payload += t[off:off+size]

# header + toc at end
out = bytearray(24)
# blocks start after 24-byte header
out += payload
toc_off = len(out)
toc = b''.join(struct.pack('<II', o, s) for o, s in new_entries)
out += toc
struct.pack_into('<4sIII', out, 0, b'TPZL', bslog, toc_off, len(toc))
# pad to original size
orig_size = len(t)
if len(out) < orig_size:
    out += b'\x00' * (orig_size - len(out))
elif len(out) > orig_size:
    raise SystemExit('new tpack too big: %d > %d' % (len(out), orig_size))
open(OUT_TPZL, 'wb').write(out)
print('wrote', OUT_TPZL, len(out), 'crc32', hex(zlib.crc32(out) & 0xffffffff))

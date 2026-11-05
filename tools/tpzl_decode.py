import struct, io, sys

def inflate_block(data):
    f = io.BytesIO(data)
    t = f.read(1)[0]
    if t == 0x0f:
        f.read(1)
        l = struct.unpack('<H', f.read(2))[0]
        return f.read(l)
    if t != 0xf0:
        raise Exception('unknown type %02x' % t)
    out = bytearray()
    lengths = list(range(3, 17)) + [32, 64]
    while True:
        fb = f.read(1)
        if not fb:
            break
        flags = fb[0]
        if flags == 0:
            chunk = f.read(8)
            out += chunk
        else:
            for i in range(8):
                if (flags >> i) & 1:
                    d = f.read(2)
                    if len(d) < 2:
                        return bytes(out)
                    b0, b1 = d[0], d[1]
                    l = lengths[b0 >> 4]
                    bd = ((b0 & 0xf) << 8) | b1
                    if bd == 0:
                        return bytes(out)
                    seg = out[-bd:]
                    rep = l // len(seg) + 1
                    out += (seg * rep)[:l]
                else:
                    c = f.read(1)
                    if not c:
                        return bytes(out)
                    out += c
    return bytes(out)

def decode(path, outpath):
    data = open(path, 'rb').read()
    magic, blockSize, tocOffset, tocSize = struct.unpack_from('<4sIII', data, 0)
    assert magic == b'TPZL', magic
    block = 1 << blockSize
    entries = []
    for off in range(0, tocSize, 8):
        eo, es = struct.unpack_from('<II', data, tocOffset + off)
        entries.append((eo, es))
    out = bytearray()
    for i, (eo, es) in enumerate(entries):
        dec = inflate_block(data[eo:eo+es])
        out += dec
        if i % 50 == 0:
            print('block', i, 'out', len(out), flush=True)
    open(outpath, 'wb').write(out)
    print('done', len(out), 'blocks', len(entries))

if __name__ == '__main__':
    decode(sys.argv[1], sys.argv[2])

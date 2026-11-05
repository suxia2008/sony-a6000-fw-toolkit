import sys

def lz77_compress(data):
    """Encode data in the camera LZ77 format (0xf0), terminator in final group."""
    out = bytearray([0xf0])
    n = len(data)
    i = 0
    table = {}
    done = False
    while i < n and not done:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                # terminator backref (distance 0) in this group
                flags |= (1 << bit)
                out.append(0)
                out.append(0)
                done = True
                break
            if i + 3 <= n:
                key = data[i:i+3]
                cand = table.get(key, -1)
                table[key] = i
                best_len = 0
                best_dist = 0
                if cand >= 0 and 0 < i - cand <= 4095:
                    maxl = min(16, n - i)
                    l = 3
                    while l < maxl and data[cand + l] == data[i + l]:
                        l += 1
                    if 3 <= l <= 16:
                        best_len = l
                        best_dist = i - cand
                if best_len >= 3:
                    b0 = ((best_len - 3) << 4) | ((best_dist >> 8) & 0xf)
                    out.append(b0)
                    out.append(best_dist & 0xff)
                    flags |= (1 << bit)
                    for k in range(1, best_len):
                        if i + k + 3 <= n:
                            table[data[i+k:i+k+3]] = i + k
                    i += best_len
                    continue
            out.append(data[i])
            i += 1
        out[flag_pos] = flags
    return bytes(out)

if __name__ == '__main__':
    img = open(sys.argv[1], 'rb').read()
    bs = 1 << int(sys.argv[2])
    idx = int(sys.argv[3])
    block = img[idx*bs:(idx+1)*bs]
    enc = lz77_compress(block)
    print('block', idx, 'raw', len(block), 'enc', len(enc), 'ratio', round(len(enc)/len(block), 3))

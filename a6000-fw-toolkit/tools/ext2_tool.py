import struct, sys

class Ext2:
    def __init__(self, path):
        self.data = bytearray(open(path, 'rb').read())
        sb = self.data[1024:2048]
        self.block_size = 1024 << struct.unpack_from('<I', sb, 24)[0]
        self.inode_size = struct.unpack_from('<H', sb, 88)[0] or 128
        self.inodes_count = struct.unpack_from('<I', sb, 0)[0]
        self.first_data_block = struct.unpack_from('<I', sb, 20)[0]
        self.inodes_per_group = struct.unpack_from('<I', sb, 40)[0] or 1
        self.bgd_off = (self.first_data_block + 1) * self.block_size
        self.inode_table = struct.unpack_from('<I', self.data, self.bgd_off + 8)[0]

    def inode_offset(self, ino):
        g = (ino - 1) // self.inodes_per_group
        idx = (ino - 1) % self.inodes_per_group
        table = struct.unpack_from('<I', self.data, self.bgd_off + g * 32 + 8)[0]
        return table * self.block_size + idx * self.inode_size

    def inode(self, ino):
        off = self.inode_offset(ino)
        d = self.data[off:off + self.inode_size]
        mode = struct.unpack_from('<H', d, 0)[0]
        size = struct.unpack_from('<I', d, 4)[0]
        blocks = list(struct.unpack_from('<15I', d, 40))
        return {'mode': mode, 'size': size, 'blocks': blocks}

    def read_block(self, b):
        return bytes(self.data[b * self.block_size:(b + 1) * self.block_size])

    def file_data(self, ino):
        ino_d = self.inode(ino)
        out = bytearray()
        for b in ino_d['blocks'][:12]:
            if b == 0:
                break
            out += self.read_block(b)
        return bytes(out[:ino_d['size']])

    def list_dir(self, ino):
        d = self.file_data(ino)
        i = 0
        res = []
        while i + 8 <= len(d):
            inum, rec_len, name_len, ftype = struct.unpack_from('<IHBB', d, i)
            if rec_len < 8:
                break
            name = d[i + 8:i + 8 + name_len].decode('latin1', 'ignore')
            if inum and name not in ('.', '..'):
                res.append((name, inum, ftype))
            i += rec_len
        return res

    def lookup(self, path):
        ino = 2
        for part in [p for p in path.split('/') if p]:
            found = None
            for name, i, t in self.list_dir(ino):
                if name == part:
                    found = i
                    break
            if not found:
                return None
            ino = found
        return ino

if __name__ == '__main__':
    img = sys.argv[1]
    e = Ext2(img)
    print('block_size', e.block_size, 'inode_size', e.inode_size, 'inodes', e.inodes_count)
    for p in ['usr', 'usr/share', 'usr/share/avsystemsound']:
        ino = e.lookup(p)
        print(p, 'inode', ino, e.inode(ino) if ino else None)
    ino = e.lookup('usr/share/avsystemsound/beeplist.txt')
    print('beeplist inode', ino)
    if ino:
        d = e.file_data(ino)
        print('size', len(d))
        print(d[:200])

# 02 — TPZL / LZ77 格式与重压缩

## 头部

```c
struct LzptHeader {
    char magic[4];      // "TPZL"
    uint32_t blockSize; // log2，A6000 为 16（64KB）
    uint32_t tocOffset; // 绝对文件偏移
    uint32_t tocSize;   // 条目数 × 8
};
struct Entry { uint32_t offset; uint32_t size; };
```

## LZ77 流

每个 TOC 条目指向一个压缩块，解压后恰好 `2^blockSize` 字节。流格式：

- 首字节：`0x0f`（raw）或 `0xf0`（LZ77）
- `0xf0`：每 8 个 item 前有 1 字节 flags
  - bit=0：1 字节 literal
  - bit=1：2 字节 backref
    - 高 4 位：长度码（3..16）
    - 低 12 位：距离（1..4095）
    - 距离 0 表示块结束

## 重压缩要点

1. 只有被修改的块需要重压；其余块可原样复制，避免整体尺寸膨胀；
2. 编码器必须在**当前 flags 组内**写终止符（距离 0），不能另起一组；
3. 重压后总大小必须 ≤ 原分区大小（分区在 NAND 上位置固定）；
4. 更新 `part_image.sum`：`CRC32,长度,偏移,...`，CRC32 用 zlib 计算。

脚本：`tools/tpzl_decode.py`、`tools/tpzl_encode.py`。

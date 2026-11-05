# 01 — 官方升级包解包

## 1. 运行 EXE 取 `.dat`

`Update_ILCE6000V321.exe` 是 Sony 的 PackmanExtractor：主程序约 0.6MB，其余是加密 overlay。
直接运行（无需相机）会自解压到：

```
%TEMP%\SPackTool\{GUID}\Package\Resource\FirmwareData_ILCE6000V321.dat
```

复制出来即可，无需管理员权限（manifest `asInvoker`）。

## 2. 校验

```
SHA-256 = 29aef21ab9b5c2e98388974ac9749c2cbfb1815273b444e62f2e41398aa8892f
```

与公开研究（CliffVale）的 `.dat` 一致。

## 3. 解密

```bash
python fwtool.py unpack -f FirmwareData_ILCE6000V321.dat -o unpacked
```

crypter：`CXD90014`（A6000 不强制签名，才能离线解密）。

产物：

```
firmware.tar_unpacked/
├── 0100_config … 0800_appli
├── 0700_part_image/dev/nflasha3/5/7/15/16   ← TPZL 分区
└── updater.img
```

## 4. 分区

| 分区 | 压缩大小 | 解压后 | 内容 |
|---|---|---|---|
| nflasha3 | 11.0 MB | 23.1 MB | 系统 |
| nflasha5 | 40.3 MB | 约 42 MB | 系统 |
| nflasha7 | 3.2 MB | 6.1 MB | 系统 |
| nflasha15 | 80.1 MB | 148.3 MB | 主系统（ext2，含 `/share/avsystemsound`） |
| nflasha16 | 56.3 MB | 106.8 MB | Android 系统（17 个 APK） |

# 06 — 实验与刷写日志（2026-11-05）

> 时间线按实际操作记录，错误信息为原文。

## 阶段 1：升级到 3.21

- 相机 3.20 → 官方 `Update_ILCE6000V321.exe` → 3.21 ✅
- 官方流程：安全弹出（不拔线）→ 相机按 OK → 下一步 → 写入 100%

## 阶段 2：dump 3.20 NAND

- `pmca-console updatershell -m ILCE-6000` → `pull /dev/nflasha nflasha` → **483MB** ✅
- SHA-256：`bddf55fa75c48337c361ee0b3517e379bd498f74c29f600408e1ba05103ff1aa`
- bootloader pull 失败（`Unknown error`），未取得 boot1

## 阶段 3：TPZL/ext2 改动

- 解出 `nflasha15`（148.3MB ext2），定位 `/share/avsystemsound/beeplist.txt`
- 把 `BEEP_ID_FORCUSLOCK` 的 `FileName` 从 `Dslr_Emnt_FocusLock.bin` 改为 `Dslr_Emnt_T_Select.bin`（长度相同，13 字节差异）
- 重压缩受影响的两个 64KB 块，重建 TPZL（总大小不变）
- 更新 `part_image.sum` 的 CRC32 与长度
- 重打 `firmware.tar` → `fwtool pack` → 3.23 版 `.dat`

## 阶段 4：刷写尝试

| 尝试 | 通道 | 结果 |
|---|---|---|
| 3.23 改内容包 | PMCA native（MSC） | `Firmware update error: Invalid data` |
| 官方内容 + 3.22 | PMCA native | 写到 55% USB 掉线（`DeviceIoControl：指定不存在的设备`） |
| 官方内容 + 3.22（重试） | PMCA libusb | ✅ 100%，相机启动 3.22 |
| 3.23 改内容包 | PMCA libusb | ❌ `Invalid data`（写入前 guard 阶段） |
| 官方内容 + 3.24 恢复 | PMCA libusb | ✅ 100%，相机启动 3.24 |

## 阶段 5：结论

- 官方内容重打包可以通过；
- 任意内容修改被拒 → Sony 签名/内容摘要校验；
- 私有签名不可得，改固件路线终止。

## 关键错误原文

```
Firmware update error: Invalid data
pywintypes.error: (433, 'DeviceIoControl', '指定不存在的设备。')
usb.core.USBError: [Errno 32] Pipe error
usb.core.USBTimeoutError: [Errno 10060] Operation timed out
```

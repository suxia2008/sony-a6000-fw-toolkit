# 04 — 刷写通道与踩坑

## 工具

- `fwtool.py pack`：`config.yaml` + `updater.img` + `firmware.tar` → `.dat`
- `pmca-console.py firmware -f <dat> -d native|libusb`
- `pmca-console.py updatershell`：进更新模式、dump NAND

## 进更新模式

```bash
pmca-console.py updatershell -m ILCE-6000 -d native
```

相机屏幕出现 **Reset device OK** 时按机身 OK（几十秒窗口）。

## 驱动（Windows）

- 更新模式设备：`054C 03E2`
- 官方升级程序/PMCA native：Windows 自带 USBSTOR 即可
- PMCA libusb 通道：需 Zadig 把 `054C 03E2` 换成 **libusb-win32**（不是 libusb0/WinUSB）
- 换错设备会改掉键鼠接收器驱动，务必核对 USB ID

## 踩坑记录

1. **版本检查**：目标版本 ≤ 相机版本时，官方程序提示“无需更新”；PMCA 也需更高版本号；
2. **写入中断**：MSC 通道在 55% 左右可能短暂掉线；**不要拔线**，等它自己恢复；
3. **USB 卡死**：反复中断后会出现 `Pipe error` / 超时；拔电池 10 分钟 + 换线换口再试；
4. **黑屏**：更新模式下黑屏/镜头不动是正常现象，USB 枚举存在就还活着；
5. **恢复**：用官方内容 + 更高版本号重打包，可把卡住的相机救回。

## 恢复命令（官方内容）

```bash
pmca-console.py firmware -f firmware_recover.dat -d libusb
```

前提：设备在 `054C 03E2` 且 libusb 驱动正常。

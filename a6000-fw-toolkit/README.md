# Sony ILCE-6000 (A6000) 固件逆向与安全改机研究

> 个人研究记录：官方固件解包、TPZL 重打包、分区校验、刷写实验与失败复盘。
>
> **这个仓库不包含任何 Sony 固件、Sony 工具或相机备份**，只放方法、脚本与结论。

## 结论（TL;DR）

| 项目 | 结果 |
|---|---|
| 官方升级包解包 | ✅ `Update_ILCE6000V321.exe` → `FirmwareData_ILCE6000V321.dat`（SHA-256 `29aef21a…8892f`，与公开研究一致） |
| `.dat` 解密 | ✅ `fwtool.py`（crypter CXD90014） |
| 分区格式 | TPZL（LZ77）→ 内部 ext2 文件系统 |
| 重打包 | ✅ 可重建 TPZL，并用 fwtool `pack` 生成 `.dat` |
| **修改内容后刷入** | ❌ 相机返回 `Invalid data`：**内容有 Sony 签名/完整性校验**，改 `beeplist.txt` 或 daemon 都会被拒 |
| 官方内容 + 改版本号 | ✅ 可刷入（用于恢复/升级），相机正常启动 |

**一句话**：能拆、能重打包、能刷**官方内容**；但改任何字节都会被签名校验拦下，改 AF 提示音这条路走不通。

## 目录

```
docs/
├── 01-unpack.md        官方升级包 → .dat → 固件树
├── 02-tpzl.md          TPZL/LZ77 格式与重压缩
├── 03-ext2.md          固件内 ext2 文件系统读写
├── 04-flash.md         PMCA 刷写通道与踩坑
├── 05-conclusion.md    校验层分析与最终结论
└── 06-experiment-log.md 实验与刷写日志（含错误原文）
reports/
└── firmware-research-report.md  完整研究报告（含 BEEP_ID 枚举、调用链）
tools/
├── tpzl_decode.py      TPZL 解码（LZ77）
├── tpzl_encode.py      TPZL 重压缩（LZ77 编码器，含终止符）
├── ext2_tool.py        最小 ext2 读写（定位/读取/回写文件）
└── patch_beeplist.py   示例：改 beep 映射并重建 TPZL
samples/
└── beeplist.excerpt.txt  提示音映射表片段（仅示例文本）
```

## 硬件/软件环境

- 相机：Sony ILCE-6000（CXD90014）
- 固件：3.20 / 3.21 / 3.22（3.22 为本文实验中的临时版本号）
- 工具：Python 3.12、`fwtool.py`、Sony-PMCA-RE、Zadig、Ghidra 12.1.4（可选）

## 警告

- 刷写有**变砖风险**；本文的实验相机在多次中断后曾黑屏，靠官方包恢复；
- 请先做 **NAND 备份**（`pmca-console updatershell` + `pull /dev/nflasha`）；
- 不要用本仓库去改别人机器；仅供个人研究。

## License

- 脚本：MIT
- 文档：CC BY-NC 4.0
- 不包含任何 Sony 版权素材。

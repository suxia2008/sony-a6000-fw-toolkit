# Sony ILCE-6000（A6000）固件逆向分析报告

- 日期：2026-11-04
- 对象：`D:\edge下载\Update_ILCE6000V321.exe`（Sony 官方固件升级程序，Windows，207 MiB）
- 目的：评估“改固件自定义功能（如自定义快门声）”的可行性
- 结论级别：**离线解包成功；自定义快门声不可行（A6000 为机械快门）；改固件刷写风险高，不建议**

---

## 1. 结论摘要

| 问题 | 结论 |
|---|---|
| a7c2-fl23-research 能否直接用 | **不能**。该项目仅支持 ILCE-7CM2 固件 2.01，新平台（FL2/FL3），与 A6000 完全不同 |
| 能否离线解包官方固件 | **能**。已拿到 `FirmwareData_ILCE6000V321.dat`（SHA-256 与公开研究一致），并用 `fwtool.py` 解出完整固件树 |
| 能否自定义快门声 | **不能**。A6000 是纯机械快门，固件里没有任何“快门音效文件”；只有提示音（Beep）的音量/开关设置 |
| 能否改其他功能 | 可以走 **PMCA-RE + OpenMemories-Tweak**：解锁语言、去掉 30 分钟录像限制、开 telnet/adb、装老 PMCA 应用；**不需要改固件** |
| 刷改固件风险 | 高：可能变砖、无法恢复、失去保修；A6000 没有公开的“改固件成功”案例 |

---

## 2. 升级包结构

`Update_ILCE6000V321.exe` 不是普通安装包，而是 Sony 自研的 **PackmanExtractor**：

| 项 | 值 |
|---|---|
| PE 名称 | `PackmanExtractor.exe`（ATL 对话框程序） |
| 代码大小 | 约 0.6 MB |
| 覆盖数据（overlay） | 约 206 MB，**熵 7.01**，无 LZH/gzip/zip 头 → 加密/压缩容器 |
| Authenticode | **有效**（Sony 官方签名） |
| 7-Zip | 只能识别 PE，打不开 overlay |

**关键发现**：直接运行官方升级器时，它会自解压到：

```
%TEMP%\SPackTool\{GUID}\Package\Resource\FirmwareData_ILCE6000V321.dat
```

这一步不需要连接相机，也不需要管理员权限（清单为 `asInvoker`）。

---

## 3. 提取与解包结果

### 3.1 固件数据文件

| 项 | 值 |
|---|---|
| 路径 | `D:\edge下载\a6000_dat\FirmwareData_ILCE6000V321.dat` |
| 大小 | 203.1 MiB |
| SHA-256 | `29aef21ab9b5c2e98388974ac9749c2cbfb1815273b444e62f2e41398aa8892f` |
| 对照 | 与 CliffVale《sony-a6000-firmware-research》公布的 `.dat` 哈希**完全一致** |

### 3.2 解密

使用 `ma1co/fwtool.py`（crypter **CXD90014**）离线解包：

```bash
python fwtool.py unpack -f FirmwareData_ILCE6000V321.dat -o a6000_unpacked
```

输出目录：`D:\edge下载\a6000_unpacked`

| 项 | 值 |
|---|---|
| 总大小 | 约 **1.1 GB** |
| 文件数 | 1388 |
| 关键产物 | `firmware.tar`（202.2 MB）、`firmware.fdat`、`updater.img`、`config.yaml` |

### 3.3 固件树

```
firmware.tar_unpacked/
├── 0100_config / 0110_backup / 0300_partconf
├── 0600_gps / 0630_ca / 0640_darwin / 0650_prfile
├── 0700_part_image/dev/        ← 分区镜像
│   ├── nflasha3   11.0 MB  → 解包 23.1 MB
│   ├── nflasha5   40.3 MB
│   ├── nflasha7    3.2 MB  → 解包 6.1 MB
│   ├── nflasha15  80.1 MB  → 解包 148.3 MB（相机主系统）
│   └── nflasha16  56.3 MB  → 解包 106.8 MB（Android 系统）
└── 0800_appli/                android / lens / setting
```

**nflasha16 = Android 系统分区**，解包后含 17 个系统 APK：

```
app/
├── ApplicationsProvider.apk
├── AvindexProvider.apk
├── CertInstaller.apk
├── DefaultContainerService.apk
├── MediaProvider.apk
├── ScalarAAppManager.apk
├── ScalarADisclaimer.apk
├── ScalarAHotspot.apk
├── ScalarAInstaller.apk
├── ScalarALauncher.apk
├── SmartRemote.apk
├── WifiSettings.apk
└── ...
```

这与公开研究“A6000 内部运行 Android”一致。

---

## 4. 关于“自定义快门声”的核查

### 4.1 固件里有没有音频文件？

扫描整个 1.1 GB 固件树（含所有分区、APK）：

| 检查 | 结果 |
|---|---|
| `RIFF/WAVE`、`OggS`、`ID3/MP3` 魔数文件 | **0 个** |
| APK 内 `res/raw`、`assets` 音频条目（.ogg/.mp3/.wav） | **0 个** |
| 文件名含 `shutter` / `beep` / `click` 的音频资源 | **0 个** |

### 4.2 能找到的相关证据

- UI 文案：`Set beep sound`、`You can adjust (or mute) the volume of shutter/button`
  → 说明“快门/按键提示音”只有**音量与开关**，没有“换音效”；
- 原生符号：`AppWidgetBase::beepPlay(int)`、`UserGetKeyBeepMode5Way`、`SYS_MODEL_BEEP`
  → 提示音由**代码/硬件发声**产生，不是播放音频文件；
- `libScalarDaemon.so`、`viewUnified*.so` 等负责快门速度、按键提示音控制。

### 4.3 对焦提示音（AF Beep）单独核查

对焦声音分两部分：

| 来源 | 能否改 |
|---|---|
| **镜头对焦马达声** | 纯机械/电磁，固件无法改 |
| **AF 锁定提示音（Beep）** | 与快门/按键提示音**同一套 Beep 系统**，只能开关/调音量，不能换音色 |

证据（`libObj.so` / `orb-server` / `libScalarDaemon.so`）：

- 反汇编 `AppWidgetBase::beepPlay(int)`（Thumb，0x120078）：
  - 参数是 **beep ID**（`cmp r1,#-1` 为空则直接返回），随后尾调用 `0x11e224` 的 Beep 服务；
  - 不涉及音频解码/播放，属于“发一个 ID 给发声服务”。
- `LkmBeepIF::ModelExecute(...)`、`LkmBeepIF::Create(...)`：Beep 接口层，按 ID 执行。
- `orb-server` 暴露的是 **`SetBeepMode` / `GetBeepMode` / `GetSupportedBeepMode` / `GetAvailableBeepMode`**：
  - 说明提示音是**枚举模式**（开/关、可能的几种组合），不是“任意音色/频率”；
  - 没有 `SetBeepFrequency` / `SetBeepWaveform` 之类的接口。
- `libncurses` 里的 `beep` 是终端库函数，与相机提示音无关（排除）。

**结论**：对焦提示音也只能“开/关/调音量”，没有可替换的音频资源；想换成别的音色，必须改 Beep 服务的原生代码并重新刷写固件——属于高风险改机，且没有公开成功案例。

### 4.4 Beep 调用链深挖（2026-11-04 追加）

继续沿 `beepPlay` 往下追，得到完整链路与“为什么没有音效文件”的答案：

```
AppWidgetBase::beepPlay(beepId)
  └─ LkmBeepIF::ModelExecute / Create      （libObj.so，Beep 接口层）
       └─ Beep 服务（libScalarDaemon.so）
            └─ AbstractSequenceFactory::CreateSystemsoundSequence(soundId)
                 └─ CreateSystemsoundSequenceParam(soundId, ObjMsg, ParamList)
                      └─ [ObjActiveBaseAvbbc] CreateSequence [CATEID_SYSTEMSOUND]
                           └─ ADF 音频通道（Audio Processor / AudioOutpin）
```

关键证据：

- `libBizFw.so` 中存在 `AbstractSequenceFactory::CreateSystemsoundSequence(uint)` 和
  `CreateSystemsoundSequenceParam(...)`，日志字符串为
  `[ObjActiveBaseAvbbc] CreateSequence [CATEID_SYSTEMSOUND]`；
- 也就是说：**提示音是“系统音序列（SystemSound Sequence）”合成的**，走 ADF 音频通道，
  不是从文件系统读 wav/ogg 播放；
- 扫描 50 多个内核模块（`kmod/*.ko`）：**没有 buzzer/beep/pwm 驱动**，
  说明发声不靠独立蜂鸣器驱动，而是走音频子系统；
- `orb-server` 只暴露 `SetBeepMode` / `GetBeepMode` / `GetSupportedBeepMode` /
  `GetAvailableBeepMode`，**没有**频率、波形、音效文件相关接口。

**这意味着**：

1. “换一个对焦提示音”本质是**改 `CreateSystemsoundSequence` 的 soundId 或序列参数**，
   属于改原生代码 + 重刷固件；
2. 即使改了，也只能发出**内置音序列**里的另一种“滴”，不能导入自定义音频；
3. 没有公开的 A6000 改 Beep 案例，刷写失败就是变砖。

### 4.5 Beep 守护进程接口（2026-11-04 二次深挖）

在 `libScalarDaemon.so` 中找到实际执行提示音的接口：

| 符号 | 说明 |
|---|---|
| `SCALARDAEMON::SystemEventIssuerSystemSound::beepPlayStart(int,int,int)` | 启动一次提示音（3 个整型参数） |
| `...::setBeepType(int)` | 设置提示音类型 |
| `...::beepPlayStop()` | 停止提示音 |
| `CommandProcessorBeepPlayStart::SyncProcessor::mappingBeepId(const char*)` | 把**字符串名字**映射成 beep ID |
| `CommandProcessorBeepPlayStop::SyncProcessor::execute()` | 停止命令处理 |

`beepPlayStart` 反汇编显示它构造一条 SDCom 消息，依次写入三个参数：

```
param 0x100 = arg0   （beep ID）
param 0x101 = arg1   （第二参数，推测为音量/强度）
param 0x102 = arg2   （第三参数，推测为时长/重复）
然后发送 command id = 6, sub = 2
```

`setBeepType` 写 `param 0x103`，发送 command id = 6, sub = 4。

`mappingBeepId(const char*)` 的实现是：

- 运行时动态构建一张 `std::map<int, const char*>` / 数组表（`.data` 里初值为 0，
  启动后填充），条目为 `{name_ptr, id}`，按名字线性/二分查找；
- 说明提示音是**按名字索引的固定 ID**，不是频率/波形参数。

**进一步结论**：

1. Beep 是**枚举 ID**（名字 → ID → 固定 SystemSound 序列），没有“频率/波形/自定义音频”入口；
2. `arg1/arg2` 可能控制音量/时长，但音色由 ID 决定；
3. 想换 AF 提示音音色 = 改 daemon 的 ID→序列映射或 SystemSound 序列本身，必须改原生库并重刷固件；
4. 这张映射表是**运行时动态构建**的，静态提取不到完整 ID 表，需要在 Ghidra 里继续跟初始化代码（或上机 dump 内存）才能枚举全部 ID。

### 4.6 BEEP_ID 枚举（47 个，2026-11-04 三次深挖）

在 `libScalarDaemon.so` 的 `.rodata` 中找到完整的 BEEP_ID 枚举（字符串表），并确认
`mappingBeepId(const char*)` 就是拿外部名字在这张表里查 ID：

```
 0 BEEP_ID_UNKNOWN            16 BEEP_ID_MENU_OFF          32 BEEP_ID_EVENT_ANIME_2LINE
 1 BEEP_ID_STARTUP            17 BEEP_ID_OPTION_ON         33 BEEP_ID_EVENT_ANIME_3LINE
 2 BEEP_ID_KA                 18 BEEP_ID_OPTION_OFF        34 BEEP_ID_EVENT_ANIME_4LINE
 3 BEEP_ID_SHA                19 BEEP_ID_JET_TOUCH         35 BEEP_ID_PULL_DOWN_ON
 4 BEEP_ID_KASHA              20 BEEP_ID_JET_SENT          36 BEEP_ID_PULL_DOWN_OFF
 5 BEEP_ID_FORCUSLOCK         21 BEEP_ID_JET_ERROR         37 BEEP_ID_SCROLL
 6 BEEP_ID_RECSTART           22 BEEP_ID_GESTURE           38 BEEP_ID_HOLD_ENTER
 7 BEEP_ID_RECSTOP            23 BEEP_ID_AIR_ZOOM          39 BEEP_ID_BACK_CANCEL
 8 BEEP_ID_CAUTION            24 BEEP_ID_AIR_FOCUS         40 BEEP_ID_BACK_CANCEL_TP
 9 BEEP_ID_SELECT             25 BEEP_ID_TAP               41 BEEP_ID_ON
10 BEEP_ID_MOVE_DOWN          26 BEEP_ID_MEDIA_CHANGE      42 BEEP_ID_OFF
11 BEEP_ID_MOVE_UP            27 BEEP_ID_HELP_ON           43 BEEP_ID_WHEEL_UP
12 BEEP_ID_MOVE_LEFT          28 BEEP_ID_HELP_OFF          44 BEEP_ID_WHEEL_DOWN
13 BEEP_ID_MOVE_RIGHT         29 BEEP_ID_SWITCH_MODE       45 BEEP_ID_SELFTIMER_2SEC
14 BEEP_ID_SELFTIMER          30 BEEP_ID_DISABLE           46 BEEP_ID_CLEANING
15 BEEP_ID_MENU_ON            31 BEEP_ID_EVENT_ANIME_1LINE
```

**对焦相关**：

- `BEEP_ID_FORCUSLOCK`（第 5 个，拼写是 Sony 原样的 FORCUS）＝ **AF 合焦提示音**；
- `BEEP_ID_AIR_FOCUS`＝触摸/空中对焦相关提示音。

**这意味着什么**：

1. AF 提示音不是“音频文件”，而是 47 个固定 ID 之一，每个 ID 对应内置 SystemSound 序列；
2. 想换“那个滴声”，理论上有两条路：
   - **换 ID**：把 AF 事件映射到另一个 BEEP_ID（例如 SELECT/TAP），音色会变，但仍是内置音；
   - **改序列**：改 SystemSound 序列参数（需要改音频子系统，难度更高）；
3. 两条路都要**改 daemon/音频库并重刷固件**，没有运行时配置入口，也没有导入自定义音频的通道。

### 4.7 ID → 音色表为什么静态抓不到（2026-11-04 四次深挖）

用 PyGhidra（Ghidra 12.1.4 headless）对 `libObj.so` 的 SystemSound 相关函数做了反编译，
结果如下：

- `ObjSystemSound_Create(size_t, int*)`：`operator_new(0x224)` 创建 SystemSound 对象，
  随后调用内部构造函数 `FUN_00344590`；
- `AbstractSequenceFactory` 的构造/析构、`AddPin` 等全是**通过函数指针表转发**的薄壳
  （`(*(code *)PTR_...)(...)`），真正的序列参数在 ADF/音频子系统内部；
- `AppWidgetBase::beepPlay(int)` 也是取一个全局单例、虚调用 `vtable+8`；
- `HighlightManager::playDirectionBeep` 在反编译里是空函数（被优化/内联）。

**结论**：

1. “beep ID → 具体音序列（频率、时长、音数）”的映射**不在这些 .so 的静态数据里**，
   而是构造对象时由代码/硬件音频子系统生成；
2. 想拿到完整映射，需要**运行时 dump 相机内存**（例如通过 telnet 读 daemon 进程内存），
   或继续逆向 ADF 音频层（工作量很大）；
3. 即便拿到，也只能证明“每个 ID 对应哪个内置音”，**不能导入自定义音频**。

### 4.8 物理事实

A6000 是**机械快门**（帘幕 + 马达），快门声来自机械动作，不是扬声器播放的音频。
真正能“换快门音效”的是 A7C II 这类**电子快门 + 扬声器**的机型——这也是 a7c2 项目只支持它的原因。

**因此：改固件也无法给 A6000 加“自定义快门声”，因为没有可替换的音效文件，也没有电子快门发声通道。**

---

## 5. 可行的替代路线（不刷固件）

1. **OpenMemories-Tweak**（通过 PMCA-RE 安装）
   - 去掉 30 分钟录像限制
   - 解锁全部语言菜单
   - 关闭 NTSC 提示
   - 开启 telnet / adb
2. **PMCA 老应用**（延时摄影、Smart Remote、HDMI Cam 等）
   - 通过 PMCA-RE 侧载 APK（Internet Archive 有备份）
3. **固件 dump（研究用）**
   - `pmca-console updatershell` → `pull /dev/nflasha`，可做离线分析
4. **提示音设置**
   - 相机菜单里调音量/关闭，属于原生功能，不需要改固件

---

## 6. 风险与边界

| 风险 | 说明 |
|---|---|
| 变砖 | 改分区/刷写失败可能导致无法开机，且无公开救砖方案 |
| 签名/校验 | CXD90014 不强制签名是研究结论，但不等于随便改都能启动 |
| 保修/合规 | 拆机、改固件、刷非官方包会失去保修，可能涉及版权/反规避问题 |
| 收益 | 即使成功改提示音，也只是“滴”声，不是快门音效；性价比极低 |

**本报告只做离线分析与可行性判断，不提供“改好直接刷”的成品固件。**

---

## 7. 产物清单

| 文件 | 路径 |
|---|---|
| 原始升级包 | `D:\edge下载\Update_ILCE6000V321.exe` |
| 提取的固件数据 | `D:\edge下载\a6000_dat\FirmwareData_ILCE6000V321.dat` |
| 解包固件树 | `D:\edge下载\a6000_unpacked\`（1.1 GB） |
| 解包工具 | `D:\edge下载\fwtool\fwtool.py-master` + venv `D:\edge下载\fwtool-venv` |
| 参考研究 | `D:\edge下载\a6000-fw-research\sony-a6000-firmware-research-main` |
| 本报告 | `D:\edge下载\A6000_firmware_research_report.md` |

## 8. 下一步（B，明天中午）

- 装 **Sony-PMCA-RE**（Windows 版）、Zadig 驱动；
- 用 PMCA-RE 连相机：先 `pmca-console list` 确认识别，再装 **OpenMemories-Tweak**；
- 目标：解锁语言 / 去 30 分钟限制 / 开 telnet-adb；
- 全程不刷固件；操作前确认相机电量 >50%，USB 直连、别用集线器。

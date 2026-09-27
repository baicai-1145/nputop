# Ascend 950PR 适配档案（nputop）

适配目标：让 `nputop` 在本机 **Ascend950PR_9579 / NpuArch 3510 / CANN 9.1.0 / npu-smi 25.7.rc1.6** 上正确解析并显示（本机 1 卡）。

采集环境（2026-09-27，本机实测）：

| 项目 | 值 | 来源 |
| --- | --- | --- |
| 板卡 Product Name | `A310-50-C00MM304A1`（Atlas 350 标卡） | `npu-smi info -t board -i 0` |
| NPU Name / Chip Name | `9579` / `Ascend950PR`（Chip Version V100） | 同上 |
| SKU / NpuArch | `Ascend950PR_9579`，Short SoC `Ascend950` | 平台配置 ini |
| AI Core | 28AIC + 56AIV, AI CPU 7 | `npu-smi info -t common -i 0`（Aicore Count 28）+ ini |
| HBM | 131072 MB（npu-smi 口径），HBM Clock 3200 MHz | `-t usages` / `-t memory -i 0` |
| L2 | 134217728 B (128 MiB)，`memory_size=137438953472` (128 GiB) | 平台配置 ini |
| npu-smi / 固件 | npu-smi 25.7.rc1.6 / firmware 9.0.0.105.229 | `npu-smi info` / `-t board -i 0` |
| PCIe | 0000:01:00.0，PCI Device ID 0xD806，PCIe 5.0 x16 | `-t board -i 0` |
| 卡数 | 1（`npu-smi info -l`: Total Count 1；`/dev/davinci0`） | `-t l` / `/dev` |
| 额定功耗 | **600 W**（Atlas 350 标卡公开参数） | 华为 2026-03 中国合作伙伴大会公开数据（Atlas 350 产品页 / 上证报、IT之家等报道）；本机 `npu-smi set` 在容器内被拒绝、DCMI/DSMI 无可用 power-cap 查询，故取官方板卡额定值 |
| CANN | 9.1.0 | `/usr/local/Ascend/ascend-toolkit/latest/x86_64-linux/ascend_toolkit_install.info`（现有代码读取该文件，实测可用） |

---

## 1. `npu-smi info` 主表真实格式（本次适配的解析对象）

`npu-smi info`（本机 25.7.rc1.6）原始输出，逐字节存档于 `.tmp/adapt-950pr/npusmi_info_950pr.txt`：

```
+-------------------------------------------------------------------------------------------------+
| npu-smi 25.7.rc1.6                               Version: 25.7.rc1.6                            |
+--------+------------------+---------------+-----------------------------------------------------+
| NPU ID | Name             | Health        | Power(W)    Temp(C)           Hugepages-Usage(page) |
|        |                  | Bus-Id        | NPU Util(%) Memory-Usage(MB)  HBM-Usage(MB)         |
+========+==================+===============+=====================================================+
| 0      | Ascend950PR      | OK            | 209.1       63                0     / 0             |
|        |                  | 0000:01:00.0  | 0           0    / 0          121576/ 131072        |
+========+==================+===============+=====================================================+
+---------------------------+---------------+-----------------------------------------------------+
| NPU ID                    | Process id    | Process name             | Process memory(MB)       |
+===========================+===============+=====================================================+
| 0                         | 377375        | sglangschedul            | 115909                  |
| 0                         | 377069        | python                   | 284                     |
+===========================+===============+=====================================================+
```

### 1.1 与 legacy（910*/310*）格式的结构差异

| 维度 | legacy（现有正则针对的格式） | 950PR（本机） |
| --- | --- | --- |
| 设备行 | `NPU` 与 `Name` 同一格：`| 0     910B2C   |` | **两列分开**：`| 0      | Ascend950PR      |` |
| 设备第二行 | `Chip`/`Phy-ID` 列有值 | **前两列全空**：`|        |      | Bus-Id |` |
| Bus-Id | 第二行第 3 段 | 相同位置 |
| 算核利用率列头 | `AICore(%)` | `NPU Util(%)`（语义相同：`-t usages` 中 `NPU Utilization(%)` 与 `Aicore Usage Rate(%)` 在负载下同时为 97） |
| DDR 内存列 | 第二行 `Memory-Usage(MB)` | 同名，本机恒为 `0 / 0`（DDR Capacity 0） |
| HBM 列 | 第二行末段 `20701/ 65536` | 相同位置 `121576/ 131072` |
| 进程表 | `NPU   Chip` **两列** | `NPU ID` **单列** |
| 功耗/温度 | 第一行 `88.6  51` | 相同位置 `209.1  63` |

### 1.2 原版在 950PR 上的实测失效点（修复前，真机）

```
name: '|'                       # 旧 _RE_L1 把列分隔符当芯片名
mem:  MemoryInfo(total=0, free=0, used=0)
util: UtilizationRates(npu='N/A', memory='N/A', ...)
temp: 64  power: 210100.0  limit: 'N/A'
bus : 'N/A'
procs: {}                       # npu-smi 实际有 2 个进程
```

对应 `nputop --once`：`118.7GiB/128.0GiB` 显示为 `0B / 0B`、`NPU-Util` 为 `N/A`、`Pwr:Usage/Cap` 为 `209.7W / N/A`。

### 1.3 其它子命令字段（本机实测，备用口径）

- `-t usages -i 0`：`HBM Capacity(MB)=131072`、`HBM Usage Rate(%)`、`Aicore/Aivector/Aicpu/Ctrlcpu Usage Rate(%)`、`NPU Utilization(%)`、`Aicube Usage Rate(%)`、`DDR/HBM Bandwidth Usage Rate(%)`（**HBM BW 恒为 0，与 sglang 硬件基线报告一致，不可当负载指标**）。
- `-t common -i 0`：`Aicore Usage Rate(%)`、`Aicore Freq 1650 / curFreq 100(空闲)–1600(负载)`、`Aicore Count 28`、`Temperature(C)`、`NPU Real-time Power(W)`。
- `-t memory -i 0`：`HBM Capacity(MB)`、`HBM Clock Speed(MHz) 3200`、`HBM Temperature(C) 58`。
- `-t board -i 0`：板卡/芯片/固件/PCIe 信息（见上表）。
- `-t sensors -i 0`：仅 `Soc / SFP(NA) / NDIE / HBM` 温度，**无风扇字段** → GUI 的 `Fan N/A` 是正确显示（该卡无风扇转速可查）。
- `-t board` / `-t usages` 等不带 `-i` 会直接报 `This command must input card id.` 退出。

---

## 2. 代码适配（第 2 步）

改动共 3 个文件，核心是 `nputop/api/libascend.py` 的 `npu-smi info` 文本解析（新格式优先、legacy 回退，910*/310* 行为不变）：

| # | 位置 | 改动 |
| --- | --- | --- |
| 1 | `_POWER_LIMIT` | 新增 `"Ascend950PR": 600`（附来源注释：Atlas 350 板卡额定功耗） |
| 2 | `_RE_L1B` | 950PR 设备首行（`NPU ID` / `Name` 独立两列）；匹配链 `_RE_L1B or _RE_L1` |
| 3 | `_RE_L2B` | 950PR 第二行（前两列可空）；匹配链 `_RE_L2B or _RE_L2` |
| 4 | `_RE_PB` | 950PR 进程行（单 `NPU ID` 列，chip_id 固定 0）；先于 legacy `_RE_P` 尝试 |
| 5 | `ascendDeviceGetBusId` | 新增访问器，读解析缓存里的 `bus_id`；`api/device.py: Device.bus_id()` 由恒返回 `NA` 改为调用它（950PR 主表提供 Bus-Id） |

新增正则：

```python
_RE_L1B = re.compile(r"^\|\s*(\d+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s+(\d+)")
_RE_L2B = re.compile(r"^\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*([0-9A-Fa-f:.]+|NA)\s*\|\s*(\d+).*?\|$")
_RE_PB  = re.compile(r"^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|$")
```

互斥性（已核）：legacy 设备行 `| 0     910B2C ...` 不匹配 `_RE_L1B`（第一个 `\s*\|` 处遇到数字）；legacy 第二行 `| 0       0   | ...` 不匹配 `_RE_L2B`（第二个字段非空、且字段间无 `|`）；legacy 进程行 `| 0       0   | pid | ...` 不匹配 `_RE_PB`（第一格是"数字+空格+数字"，非单 ID）。`tests/` 内 4 组 legacy 样例（910B2C 双卡、310B4、Ascend910 双卡双 die、310P3 双卡双 die）回归全绿。

HBM 口径沿用现有逻辑（取第二行最后一组 `used/total`），在 950PR 上即 `HBM-Usage(MB)`；DDR `Memory-Usage` 本机恒为 0，不会被误取。

其余 GUI/CLI 层核查：无芯片名硬编码；`Name` 列宽 18 > `Ascend950PR`(11)；`MIG`/`NVIDIA` 分支不触发；进程名截断、`NPU-MEM` 列宽均正常。

---

## 3. 验证证据（第 3 步）

### 3.1 入口与单测

```
$ python3.12 -m nputop --version
nputop 0.0.5                       # exit 0
$ python3.12 -m pytest tests/ -q
8 passed
```

新增 950PR 回归用例 `npusmi_950pr`（用 1 节原始输出逐字节存档作为 fixture），断言 name/health/power/temp/bus_id/aicore/HBM/利用率/进程表全部字段。

### 3.2 非交互快照 × `npu-smi info` 交叉核对

`.tmp/adapt-950pr/crosscheck.py` 把两份**背靠背采集**的输出逐字段配对（npu-smi 瞬时值 vs nputop 缓存 0.8s 的解析；功率/温度为连续量，给出容差）。

**空闲**（`npu-smi info` 后立即 `nputop --once`）：

| field | npu-smi | nputop | delta |
| --- | --- | --- | --- |
| name | Ascend950PR | Ascend950PR | OK |
| bus_id | 0000:01:00.0 | 0000:01:00.0 | OK |
| util_pct | 0 | 0 | 0 |
| temp_c | 81 | 81 | 0 |
| power_w | 228.2 | 227.7 | -0.5 |
| hbm_used_mib | 121577 | 121548.8 | -28.2（nputop 按 GiB 保留 1 位小数） |
| hbm_total_mib | 131072 | 131072 | 0 |
| power_cap_w | 600 | 600 | 0 |
| 进程 | 377069/377375 | 377069/377375 | 每 PID 内存一致 |

**负载**（自建 2048² fp16 matmul 探针，25s，NPU 独占 lease `nputop-950pr` 下运行；3 轮采样全部 PASS）：

| field | round1 smi/nputop | round2 | round3 |
| --- | --- | --- | --- |
| util_pct | 96 / 97 | 97 / 97 | 97 / 97 |
| temp_c | 80 / 80 | 81 / 82 | 83 / 83 |
| power_w | 599.4 / 599.8 | 600.5 / 599.6 | 600.8 / 600.5 |
| hbm_used_mib | 122680 / 122675 | 122674 / 122675 | 122673 / 122675 |
| power_cap_w | 600 / 600 | 600 / 600 | 600 / 600 |

旁证（同窗口 `-t usages` / `-t common`）：`Aicore Usage Rate(%) 97`、`NPU Utilization(%) 97`、`Aicube 93`、`Aicore curFreq 1600MHz`、`NPU Real-time Power(W) 599.8`。

**关于 600W**：负载下卡实际功率稳定在 **599.4–600.8W**（空闲 209–228W）。实测封顶在 600W 与官方 600W 额定一致，是本机对该数值的行为学旁证（非厂商查询接口读数）。探针结束后已释放 lease，`npu-smi info` 仅剩原有 2 个进程，无残留。

### 3.3 TUI（`timeout 5` 强制退出）

`TERM=xterm-256color` 下分别跑 `-m compact` / `-m full` / `-m auto`（`script -qec` 分配 pty）：

- 三者均正常建面板、多帧刷新，`exit=124`（timeout 杀进程，符合预期），**无 Traceback、无 curses 报错**。
- 数值全部正常：`0  Ascend950PR  Off | 0000:01:00.0  Off | Disabled  N/A` / `N/A  79  224.4W / 600.0W | 118.7GiB / 128.0GiB | 0%  Default`，进程面板列出 NPU 进程（`113.2GiB` ↔ npu-smi `115909 MB`）。
- 负载窗口内抓到 `599.9W / 600.0W`、`temp 69`、`NPU-Util 97%`。
- 注：`TERM=dumb`（未设 TERM 的裸 `script`）下 curses 初始化失败属预期，CLI 会打印 `ERROR: Failed to initialize 'curses'` 并回退到 oneshot 文本输出（该文本本身数值正确）。

---

## 4. 安装与推送（第 4 步）

见下方提交记录；`pip install -e /workspace/nputop` 装入系统 python 3.12，`which nputop` / `nputop --version` / `nputop --once` 冒烟命令与输出见 `ADAPT_950PR.md` 提交说明及仓库 commit message。

---

## 5. 存疑点（如实记录）

- 950PR **芯片级** TDP 无本地权威来源；600W 取华为公布的 Atlas 350 标卡额定功耗，并得到本机负载封顶 599.x–600.8W 的行为旁证。若后续拿到芯片级 TDP 或可用的 power-cap 查询接口（DCMI `dsmi_get_device_info(DSMI_LP_GET_POWER_INFO → soc_rated_power)` 在容器内不可达），只需更新 `_POWER_LIMIT` 一个数字。
- 主表列头为 `NPU Util(%)`（legacy 为 `AICore(%)`）。本机实测负载下它与 `-t usages` 的 `NPU Utilization(%)`/`Aicore Usage Rate(%)` 三者一致（97），按同义处理；不能据此推断 950 上 `NPU Util` 是否等于某个更细口径（Aicube 同时为 93）。
- 适配只覆盖**本机单卡 1 卡**布局。多卡 950PR 时主表每卡一组两行、进程表 `NPU ID` 单列，按代码路径等价推得可正确路由（chip_id 固定 0，与 `npu-smi info -m` 的 Chip ID 0 / Chip Phy-ID 0 一致），但**未在真机多卡上实测**。
- 本机 950PR 的 `HBM Bandwidth Usage Rate(%)` 恒为 0（与 sglang 硬件基线一致），nputop 未使用该字段。
- 无风扇转速/ECC 计数字段：GUI 的 `Fan N/A`、`Uncorr. ECC N/A` 属"该平台无此数据"，非解析失败。

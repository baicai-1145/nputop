# Ascend 950PR 适配档案（nputop）

适配目标：让 nputop 在本机 Ascend950PR_9579 / NpuArch 3510 / CANN 9.1.0 / npu-smi 25.7.rc1 上正确解析并显示。

---

## 1. 950PR 真实规格与 npu-smi 输出格式（2026 采集，本机实测）

### 1.1 硬件/软件规格

| 项目 | 值 | 来源 |
| --- | --- | --- |
| 产品名（板卡） | A310-50-C00MM304A1（Atlas 350 标卡） | `npu-smi info -t board -i 0` |
| NPU Name | 9579 | 同上 |
| 芯片全名 | **Ascend950PR**（Chip Version V100） | 同上 |
| SKU | Ascend950PR_9579，Short SoC Ascend950，NpuArch 3510 | 平台配置 ini |
| AI Core | **28**（cube_core_cnt=28 / vector_core_cnt=56 / ai_cpu_cnt=7） | `npu-smi info -t common -i 0` + ini |
| HBM 总容量 | **131072 MB**（`-t usages`/`-t memory` 口径；ini memory_size=137438953472 B = 128 GiB） | `-t usages -i 0` + ini |
| HBM 时钟 | 3200 MHz | `-t memory -i 0` |
| L2 | 134217728 B（128 MiB） | ini |
| TDP / 额定功耗 | **600 W**（Atlas 350 标卡，华为公布；芯片级 TDP 未单独公布） | 华为 2026-03 发布会公开数据（新浪财经等报道转述） |
| 驱动/固件 | npu-smi 25.7.rc1.6 / firmware 9.0.0.105.229 | `-t board -i 0` |
| PCIe | 0000:01:00.0，PCI Device ID 0xD806 | `-t board -i 0` |

### 1.2 `npu-smi info`（主表，libascend 解析对象）真实输出

```
+-------------------------------------------------------------------------------------------------+
| npu-smi 25.7.rc1.6                               Version: 25.7.rc1.6                            |
+--------+------------------+---------------+-----------------------------------------------------+
| NPU ID | Name             | Health        | Power(W)    Temp(C)           Hugepages-Usage(page) |
|        |                  | Bus-Id        | NPU Util(%) Memory-Usage(MB)  HBM-Usage(MB)         |
+========+==================+===============+=====================================================+
| 0      | Ascend950PR      | OK            | 209.4       63                0     / 0             |
|        |                  | 0000:01:00.0  | 0           0    / 0          128980/ 131072        |
+========+==================+===============+=====================================================+
+---------------------------+---------------+-----------------------------------------------------+
| NPU ID                    | Process id    | Process name             | Process memory(MB)       |
+===========================+===============+=====================================================+
| 0                         | 44205         | sglangschedul            | 123531                   |
| 0                         | 43902         | python                   | 284                      |
+===========================+===============+=====================================================+
```

### 1.3 与 910B/310 系（legacy）格式的结构差异（适配依据）

| 维度 | legacy（910B2/310P 等，现有正则针对的格式） | 950PR（本机） |
| --- | --- | --- |
| 设备行第一列 | `NPU   Name` 同格：`| 0     910B2C   |`（ID+名字同列） | `NPU ID`、`Name` 为**独立两列**：`| 0      | Ascend950PR |` |
| 第二行 | `Chip/Phy-ID` 列有 chip 号或 phy id：`| 0   | ...` | 第二行前两列**全空**：`|        |    | Bus-Id |` |
| 进程表第一列 | `NPU     Chip` 两列：`| 0       0    |` | 仅 `NPU ID` **单列**：`| 0    |` |
| Bus-Id | 第二行第 3 段 | 同为第二行第 3 段（位置一致） |
| AICore/NPU Util | 第二行 `AICore(%)` | 第二行 `NPU Util(%)`（语义等同） |
| HBM 用量 | 第二行末段 `20701/ 65536` | 同位置 `128980/ 131072`（一致） |
| 功耗/温度 | 第一行 `209.4  63` | 同（一致） |

### 1.4 其它子命令字段（本机实测口径）

- `-t board -i 0`：Product Name / NPU Name / Chip Name / Chip Version / Software Version / Firmware Version / PCIe Bus Info / Chip Count=1 等（逐字段见 1.1）。
- `-t usages -i 0`：`HBM Capacity(MB)=131072`、`HBM Usage Rate(%)`、`Aicore/Aivector/Aicpu/Ctrlcpu Usage Rate(%)`、`DDR Bandwidth/HBM Bandwidth Usage Rate(%)`（另有 `NPU Utilization(%)`、`Aicube Usage Rate(%)`）。
- `-t common -i 0`：`Aicore Usage Rate(%)`、`Aicore Freq/curFreq(MHZ)`、`Aicore Count=28`、`Temperature(C)`、`NPU Real-time Power(W)`、`Memory/HBM Usage Rate(%)`。
- `-t power -i 0`：仅 `NPU Real-time Power(W)`（如 208.8）。
- `-t memory -i 0`：`HBM Capacity(MB)`、`HBM Clock Speed(MHz)`、`HBM Temperature(C)`。
- `-t proc-mem -i 0`：`Process id / Process name / Process memory(MB)`。
- 注意：`-t board`、`-t usages` 不带 `-i` 会直接报用法错误退出（`This command must input card id.`）。

### 1.5 现有正则对 950PR 输出的实测验证（python 实测，非目测）

对 1.2 节原始输出逐行 match（脚本：`.tmp/probe_950pr_regex.py`）：

| 正则 | 950PR 实测结果 | 结论 |
| --- | --- | --- |
| `_RE_L1`（L1 行） | **误匹配**：groups=('0','\|','OK','209.4','63') —— name 抓到 `\|` | 必须修 |
| `_RE_L2`（L2 行） | **不匹配**（bus-id 段前多了空列；`(\d+)\s*(\d*)` 在 `|        |` 处吃不到） | 必须修 |
| `_RE_P`（进程行） | **不匹配**（进程行第一列只有 npu_id 一个数字） | 必须修 |
| `_RE_R`（版本行） | 匹配 ✓ groups=('npu-smi','25.7.rc1.6','25.7.rc1.6') | 无需改 |

因此原版在 950PR 上：`name='|'`、利用率/显存/Bus-Id/AICore 全 N/A、进程列表空、`_POWER_LIMIT` 无 `Ascend950PR` 条目返回 N/A。

新设计正则（新格式优先、legacy 回退）对 950PR 与 tests/ 内 legacy 样例的双向预验证：

| 正则 | 950PR 实测 | legacy 样例（910B2C 等） |
| --- | --- | --- |
| 新 L1：`^\|\s*(\d+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s+(\d+)` | ('0','Ascend950PR','OK','209.1','63') ✓ | 不匹配（由 legacy L1 兜住）✓ |
| 新 L2：`^\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*([0-9A-Fa-f:.]+\|NA)\s*\|\s*(\d+).*?\|$` | ('','','0000:01:00.0','0') ✓ | 不匹配（由 legacy L2 兜住）✓ |
| 新 P：`^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|$` | (npu,pid,name,mem) 两行全中 ✓ | 不匹配 ✓ |

（注：表中 L2 的字符类实际为 `[0-9A-Fa-f:.]+`，此处排版从简。）

---

## 2. 执行记录

### 第 1 步：查清 950PR 配置（先查后写）

- 采集命令：`npu-smi info -t board -i 0` / `-t usages -i 0` / `-t common -i 0` / `-t memory -i 0` / `-t power -i 0` / `-t proc-mem -i 0` / `npu-smi info`（主表）。
- 发现：`-t board`、`-t usages` 不带 `-i` 直接报 `This command must input card id.` 退出。
- 正则实测（`python` 逐行 match，脚本 `.tmp/probe_950pr_regex.py`，非目测）：
  - `_RE_L1` **误匹配**：950PR 主表是 `NPU ID | Name` 独立两列，旧正则把 `\|` 当 name 抓到（真机 API 返回 `name='|'`）。
  - `_RE_L2` **不匹配**：950PR 第二行前两列全空，旧正则 `\s*(\d+)\s*(\d*)` 匹配不上 → bus-id/AICore/HBM 全丢（真机 `util` 全 N/A、`meminfo` 全 0）。
  - `_RE_P` **不匹配**：950PR 进程行第一列只有 NPU ID 单列（真机 `procs=[]`）。
  - `_RE_R` 匹配 ✓，无需改。
- `_POWER_LIMIT` 只有 310/910 系列，`Ascend950PR` 返回 N/A。TDP 取华为公布的 Atlas 350 标卡功耗 **600W**（2026-03 发布会公开数据；npu-smi 无 power-limit 查询子命令，无法本机实测）。
- 规格与格式已存档于本文第 1 节。

### 第 2 步：适配代码（`nputop/api/libascend.py`，5 处）

1. `_POWER_LIMIT` 增加 `"Ascend950PR": 600`（附来源注释）。
2. 新增 `_RE_L1B`（950PR 设备首行，独立 ID/Name 列）；匹配链改为 `_RE_L1B.match(ln) or _RE_L1.match(ln)`（新格式优先，legacy 回退）。
3. 新增 `_RE_L2B`（950PR 第二行，前两列可空）；匹配链 `_RE_L2B or _RE_L2`。
4. 新增 `_RE_PB`（950PR 进程行，单 ID 列）；进程分支先试 `_RE_PB`（chip_id 固定 0），再回退 `_RE_P`。
5. 测试：`tests/test_libascend.py` 新增 950PR 真实输出回归用例（raw + expected cache）。
- 双向预验证：新正则在 950PR 真机输出上命中（L1: ('0','Ascend950PR','OK','209.1','63')；L2: bus/aicore 正确；进程两行全中），对 tests 内 910B/310P legacy 样例零误匹配。
- GUI/CLI 层核查：无芯片名硬编码；`gui/screens/main/device.py` name 截断上限 18 字符 > `Ascend950PR`（11 字符），`NVIDIA` 前缀/MIG 分支不触发，无需改动。

### 第 3 步：验证（全部留有命令输出）

- 单测：`python3.12 -m pytest tests/ -q` → **8 passed**（legacy 4 组 + 未知进程 + device + 新增 950PR 用例）。
- API 交叉核对（真机）：`name='Ascend950PR'`、`mem 128981/131072 MiB`、`temp=63`、`power≈209W`、`bus_id=0000:01:00.0`、双进程 123531/284 MiB，与 `npu-smi info` 同帧输出逐值一致。
- `python3.12 -m nputop --version` → `nputop 0.0.5`，无报错。
- 非交互快照：`nputop --once` → 设备面板 `Ascend950PR / 209.2W / 600.0W / 126.0GiB / 128.0GiB / 0%`，进程面板内存与 npu-smi 一致，exit=0。
- TUI：`script -qec "timeout 5 python3.12 -m nputop -m compact"` → 正常起面板、多帧刷新、无 Traceback；退出时 `curs_set() returned ERR` 为 timeout 强杀后 curses 清理噪音（被 CLI 捕获打印，非崩溃）。

### 第 4 步：安装 + push

- `python3.12 -m pip install -e /workspace/nputop` 成功（PyPI 包名 `ascend-nputop`，dist-info 落在 `/usr/local/python3.12.13/.../site-packages/`）。
- 冒烟：`which nputop` → `/usr/local/python3.12.13/bin/nputop`；`nputop --version` → `nputop 0.0.5`；`nputop --once` 面板数据正确。
- git：见下方提交记录（950pr-test 分支）。

### 存疑点（如实记录）

- 950PR 芯片级 TDP 未从 npu-smi 或官方单一权威页面直接获得，600W 为华为公布的 Atlas 350 标卡功耗（多个媒体报道转述一致）。若后续拿到芯片级 TDP，仅需更新 `_POWER_LIMIT` 一个数字。
- `-t usages` 输出中 `HBM Bandwidth Usage Rate(%)` 当前恒为 0（与 sglang/ascend_dsv4 硬件基线报告的观察一致：该字段未验证负载相关性），nputop 未使用该字段，无影响。
- 主表列头为 `NPU Util(%)`（非 legacy 的 `AICore(%)`），语义按等同处理（均为算核利用率整数百分比），本机两者均输出 0，无法进一步区分口径。

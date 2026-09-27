# Ascend 950PR 适配记录（nputop）

适配对象：本机 **Ascend950PR_9579 / NpuArch 3510 / CANN 9.1.0 / npu-smi 25.7.rc1.6**，单卡。
适配前状态：`nputop --once` 在本机显示 `name='|'`、`0B / 0B`、`NPU-Util N/A`、`Pwr:Cap N/A`、进程列表为空——主表列布局与 legacy 910*/310* 不同，旧正则在第一个分隔符处就错位。

原始采集（逐字节存档于 `.tmp/adapt-950pr/raw_*.txt`，该目录不入库）：

```
+-------------------------------------------------------------------------------------------------+
| npu-smi 25.7.rc1.6                               Version: 25.7.rc1.6                            |
+--------+------------------+---------------+-----------------------------------------------------+
| NPU ID | Name             | Health        | Power(W)    Temp(C)           Hugepages-Usage(page) |
|        |                  | Bus-Id        | NPU Util(%) Memory-Usage(MB)  HBM-Usage(MB)         |
+========+==================+===============+=====================================================+
| 0      | Ascend950PR      | OK            | 210.3       64                0     / 0             |
|        |                  | 0000:01:00.0  | 0           0    / 0          121576/ 131072        |
+========+==================+===============+=====================================================+
+---------------------------+---------------+-----------------------------------------------------+
| NPU ID                    | Process id    | Process name             | Process memory(MB)       |
+===========================+===============+=====================================================+
| 0                         | 210284        | sglangschedul            | 115929                  |
| 0                         | 209907        | python                   | 284                     |
+===========================+===============+=====================================================+
```

## 1. 设备与平台事实（本机实测）

| 项目 | 值 | 来源 |
| --- | --- | --- |
| 板卡 Product Name / Model | `A310-50-C00MM304A1`（Atlas 350 标卡） | `npu-smi info -t board -i 0` |
| NPU Name / Chip Name | `9579` / `Ascend950PR`（Chip Version V100） | 同上 |
| SKU / NpuArch / Short SoC | `Ascend950PR_9579` / `3510` / `Ascend950` | `platform_config/Ascend950PR_9579.ini` |
| AI Core | Aicore Count 28，Aicore Freq 1650 MHz（空闲 curFreq 100） | `npu-smi info -t common -i 0` |
| HBM | 131072 MB，HBM Clock 3200 MHz | `-t usages` / `-t memory -i 0` |
| DDR | Capacity 0 / Usage 0（主表 `Memory-Usage` 恒为 `0 / 0`） | `-t memory -i 0` |
| PCIe Bus Info / Device ID | `0000:01:00.0` / `0xD806` | `-t board -i 0` |
| 固件 / 软件版本 | firmware 9.0.0.105.229 / 25.7.rc1.6 | `-t board -i 0` |
| 卡数 | 1（`Total Count : 1`） | `npu-smi info -l` |
| CANN | 9.1.0 | `ascend_toolkit_install.info` |
| 温度源 | `Soc / NDIE / HBM`；`SFP = NA`，**无风扇字段** | `-t sensors -i 0` |
| 功耗查询 | 仅实时功率；无 power-cap 模板，`npu-smi set` 在容器内被拒 | `-t power -i 0`、`npu-smi set -h` |

与 legacy 主表的结构差异：设备首行 `NPU ID` / `Name` **分列**；第二行 chip / phy-id 两列**为空**；进程表只有单个 `NPU ID` 列；算核利用率列头为 `NPU Util(%)`（legacy 为 `AICore(%)`，本机负载下与 `-t usages` 的 `NPU Utilization(%)`、`Aicore Usage Rate(%)` 三者一致）。

## 2. 代码改动

`nputop/api/libascend.py`

1. `_POWER_LIMIT` 新增 `"Ascend950PR": 600`（Atlas 350 标卡额定功耗；本机无 power-cap 查询接口，仅实时功率）。
2. 新增 950PR 主表正则，匹配链为“950PR 优先、legacy 回退”：
   - `_RE_L1B`：设备首行（`NPU ID` / `Name` 独立两列）
   - `_RE_L2B`：设备第二行（chip / phy-id 可空）
   - `_RE_PB`：进程行（单 `NPU ID` 列，chip id 恒为 0）
3. 新增访问器 `ascendDeviceGetBusId()`（Bus-Id 从主表解析缓存读取）。

`nputop/api/device.py`

4. `Device.bus_id()` 由恒返回 `NA` 改为查询 `ascendDeviceGetBusId`，本机输出 `0000:01:00.0`。

互斥性（`tests/test_libascend.py::test_950pr_patterns_do_not_match_legacy_tables` 固化）：legacy 首行/进程行不匹配 `_RE_L1B` / `_RE_PB`，legacy 第二行不匹配 `_RE_L2B`；4 组 legacy 样例（910B2C、310B4、Ascend910、310P3）回归不变。

## 3. 验证证据

### 3.1 入口与单测

```
$ /usr/local/python3.12.13/bin/python3.12 -m nputop --version   -> nputop 0.0.5 (exit 0)
$ python3.12 -m pytest tests/ -q                                -> 10 passed
```

新增 950PR 用例（本机原始输出逐字节作为 fixture，断言 name/health/power/temp/bus_id/aicore/HBM/利用率/进程表）、legacy 互斥性用例、访问器用例。

### 3.2 非交互快照 × `npu-smi info` 交叉核对

`.tmp/adapt-950pr/crosscheck.py`（npu-smi 采样后立刻强制刷新 nputop 缓存并配对字段）。

空闲，3 轮全部 PASS：

| field | npu-smi | nputop | 规则 |
| --- | --- | --- | --- |
| name / bus_id | Ascend950PR / 0000:01:00.0 | 同 | exact |
| util | 0 | 0 | exact |
| hbm used / total (MiB) | 121576–121577 / 131072 | 同 | tol ≤ 2 MiB |
| temp (C) | 62–63 | 63–64 | tol ≤ 2 |
| power (W) | 209.4–210.1 | 209.5–209.8 | tol ≤ 5 |
| power cap (W) | — | 600 | 额定值 |
| procs | (209907,284) (210284,115929) | 同（逐 PID 内存一致） | tol ≤ 2 MiB |

负载交叉核对（`.tmp/adapt-950pr/load_crosscheck.py`，自建 8192² fp16 matmul 探针 30 s，8180 次迭代，先门控到 util ≥ 50% 再比对；租约 `nputop-950pr` 独占，结束后已释放，无残留进程）——3 轮全部 PASS：

| round | util smi/nputop | temp | power smi/nputop | hbm used | cap |
| --- | --- | --- | --- | --- | --- |
| 1 | 99 / 100 | 75 / 74 | 600.0 / 599.8 | 122641 / 122641 | 600 / 600 |
| 2 | 100 / 99 | 77 / 77 | 599.3 / 599.5 | 122641 / 122640 | 600 / 600 |
| 3 | 99 / 100 | 78 / 78 | 601.0 / 599.9 | 122640 / 122640 | 600 / 600 |

结论口径：瞬时量（util/temp/power）差异为两次采样时刻不同（npu-smi 先采、nputop 后采，间隔约 1 s；探针负载下 util 在 99–100 抖动，npu-smi 自身三轮也给出 99/100/100）。状态量（name、bus-id、HBM total、逐 PID 内存）逐字段一致；HBM used 允许 ≤2 MiB 漂移（活负载自身在增长）。实测功率封顶 597.7–601.0 W 与 `_POWER_LIMIT = 600` 相符（行为旁证，非查询接口读数）。

### 3.3 TUI（`timeout` 强制退出）

`.tmp/adapt-950pr/tui_smoke.py`（自建 pty，140×50，SIGTERM 5 s）：

| mode | bytes | tracebacks | 退出方式 |
| --- | --- | --- | --- |
| compact | 2688 | 0 | SIGTERM |
| full | 3979 | 0 | SIGTERM |
| auto | 4175 | 0 | SIGTERM |

渲染值（三种模式一致，compact 不显示 name/bus 属该布局设计）：`0  Ascend950PR  Off | 0000:01:00.0  Off | Disabled  N/A`、`N/A  70  215.8W / 600.0W`、`118.7GiB / 128.0GiB`、`NPU MEM 92.8%`、`NPU-Util 0%`、进程面板 `284.0MiB` / `113.2GiB`（对应 npu-smi 115929 MB）。

### 3.4 安装与冒烟

```
$ python3.12 -m pip install -e /workspace/nputop    -> Successfully installed ascend-nputop-0.0.5
$ which nputop                                       -> /usr/local/python3.12.13/bin/nputop
$ nputop --version / nputop --once / nputop -m auto  -> exit 0，数值同上
```

## 4. 存疑点（如实记录）

- 600 W 为 Atlas 350 标卡额定值；本机无 power-cap 查询接口（`-t power` 仅实时功率、`npu-smi set` 容器内被拒），负载实测封顶 597.7–601.0 W 作为行为旁证。若拿到可用的 power-cap 查询，只需改 `_POWER_LIMIT` 一个数字。
- `NPU Util(%)` 与 `NPU Utilization(%)` / `Aicore Usage Rate(%)` 在本机负载下三者一致（99–100），按同义处理；`Aicube` 为不同口径，nputop 未使用。
- 仅在本机**单卡**实测。多卡 950PR 按代码路径等价推得可路由（进程表 `NPU ID` 单列 → chip_id 恒 0），未在真机多卡验证。
- `Fan N/A`、`Uncorr. ECC N/A` 属该平台无此字段（`-t sensors` 无风扇、`-t ecc` 未提供），非解析失败。
- 主表 `DDR Memory-Usage` 本机恒为 `0 / 0`（DDR Capacity 0），nputop 的显存口径取 HBM 段，未被 DDR 段干扰。

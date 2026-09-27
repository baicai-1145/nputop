import pytest

from nputop.api import libascend


# (raw_output, expected_cache)
TEST_CASES = [
    (
        # npusmi_hbm
        """
+------------------------------------------------------------------------------------------------+ 
| npu-smi 23.0.2.1                 Version: 23.0.2.1                                             | 
+---------------------------+---------------+----------------------------------------------------+ 
| NPU   Name                | Health        | Power(W)    Temp(C)           Hugepages-Usage(page)| 
| Chip                      | Bus-Id        | AICore(%)   Memory-Usage(MB)  HBM-Usage(MB)        | 
+===========================+===============+====================================================+ 
| 0     910B2C              | OK            | 88.6        51                0    / 0             | 
| 0                         | 0000:5A:00.0  | 0           0    / 0          20701/ 65536         | 
+===========================+===============+====================================================+ 
| 1     910B2C              | OK            | 99.6        50                0    / 0             | 
| 0                         | 0000:19:00.0  | 0           0    / 0          20687/ 65536         | 
+===========================+===============+====================================================+ 
+---------------------------+---------------+----------------------------------------------------+ 
| NPU     Chip              | Process id    | Process name             | Process memory(MB)      | 
+===========================+===============+====================================================+ 
| 0       0                 | 124528        | python3.8                | 17400                   | 
+---------------------------+---------------+----------------------------------------------------+ 
""",
        {
            0: {
                'name': '910B2C',
                'health': 'OK',
                'power': 88600.0,
                'temp': 51,
                'procs': [(124528, 18245222400)],
                'bus_id': '0000:5A:00.0',
                'aicore': 0,
                'hbm_used': 21706571776,
                'hbm_total': 68719476736,
                'util': libascend.Util(npu=0, mem=31.6, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 0,
                'chip_id': 0,
            },
            1: {
                'name': '910B2C',
                'health': 'OK',
                'power': 99600.0,
                'temp': 50,
                'procs': [],
                'bus_id': '0000:19:00.0',
                'aicore': 0,
                'hbm_used': 21691891712,
                'hbm_total': 68719476736,
                'util': libascend.Util(npu=0, mem=31.6, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 1,
                'chip_id': 0,
            },
        },
    ),
    (
        # npusmi_nohbm
        """
+--------------------------------------------------------------------------------------------------------+ 
| npu-smi 23.0.0                                   Version: 23.0.0                                       | 
+-------------------------------+-----------------+------------------------------------------------------+ 
| NPU     Name                  | Health          | Power(W)     Temp(C)           Hugepages-Usage(page) | 
| Chip    Device                | Bus-Id          | AICore(%)    Memory-Usage(MB)                        | 
+===============================+=================+======================================================+ 
| 0       310B4                 | Alarm           | 0.0          65                15    / 15            | 
| 0       0                     | NA              | 0            3628 / 15609                            | 
+===============================+=================+======================================================+ 
""",
        {
            0: {
                'name': '310B4',
                'health': 'Alarm',
                'power': 0.0,
                'temp': 65,
                'procs': [],
                'bus_id': 'NA',
                'aicore': 0,
                'hbm_used': 3804233728,
                'hbm_total': 16367222784,
                'util': libascend.Util(npu=0, mem=23.2, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 0,
                'chip_id': 0,
            }
        },
    ),
    (
        # npusmi_empty
        """
+------------------------------------------------------------------------------------------------+
| npu-smi 25.2.0                   Version: 25.2.0                                               |
+---------------------------+---------------+----------------------------------------------------+
| NPU   Name                | Health        | Power(W)    Temp(C)           Hugepages-Usage(page)|
| Chip  Phy-ID              | Bus-Id        | AICore(%)   Memory-Usage(MB)  HBM-Usage(MB)        |
+===========================+===============+====================================================+
| 0     Ascend910           | OK            | 162.8       37                0    / 0             |
| 0     0                   | 0000:9C:00.0  | 0           0    / 0          3133 / 65536         |
+------------------------------------------------------------------------------------------------+
| 0     Ascend910           | OK            | -           37                0    / 0             |
| 1     1                   | 0000:9E:00.0  | 0           0    / 0          2876 / 65536         |
+===========================+===============+====================================================+
| 1     Ascend910           | OK            | 167.1       38                0    / 0             |
| 0     2                   | 0000:37:00.0  | 0           0    / 0          3116 / 65536         |
+------------------------------------------------------------------------------------------------+
| 1     Ascend910           | OK            | -           38                0    / 0             |
| 1     3                   | 0000:39:00.0  | 0           0    / 0          10568/ 65536         |
+===========================+===============+====================================================+
+---------------------------+---------------+----------------------------------------------------+
| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |
+===========================+===============+====================================================+
| No running processes found in NPU 0                                                            |
+===========================+===============+====================================================+
| 1       1                 | 990711        | python                   | 7746                    |
+===========================+===============+====================================================+
""",
        {
            0: {
                'name': 'Ascend910',
                'health': 'OK',
                'power': 162800.0,
                'temp': 37,
                'procs': [],
                'bus_id': '0000:9C:00.0',
                'aicore': 0,
                'hbm_used': 3133 * 1024 * 1024,
                'hbm_total': 65536 * 1024 * 1024,
                'util': libascend.Util(npu=0, mem=4.8, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 0,
                'chip_id': 0,
            },
            1: {
                'name': 'Ascend910',
                'health': 'OK',
                'power': libascend.NA + ' ',
                'temp': 37,
                'procs': [],
                'bus_id': '0000:9E:00.0',
                'aicore': 0,
                'hbm_used': 2876 * 1024 * 1024,
                'hbm_total': 65536 * 1024 * 1024,
                'util': libascend.Util(npu=0, mem=4.4, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 0,
                'chip_id': 1,
            },
            2: {
                'name': 'Ascend910',
                'health': 'OK',
                'power': 167100.0,
                'temp': 38,
                'procs': [],
                'bus_id': '0000:37:00.0',
                'aicore': 0,
                'hbm_used': 3116 * 1024 * 1024,
                'hbm_total': 65536 * 1024 * 1024,
                'util': libascend.Util(npu=0, mem=4.8, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 1,
                'chip_id': 0,
            },
            3: {
                'name': 'Ascend910',
                'health': 'OK',
                'power': libascend.NA + ' ',
                'temp': 38,
                'procs': [(990711, 7746 * 1024 * 1024)],
                'bus_id': '0000:39:00.0',
                'aicore': 0,
                'hbm_used': 10568 * 1024 * 1024,
                'hbm_total': 65536 * 1024 * 1024,
                'util': libascend.Util(npu=0, mem=16.1, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 1,
                'chip_id': 1,
            },
        },
    ),
    (
        """
+--------------------------------------------------------------------------------------------------------+
| npu-smi 24.1.0.1                                 Version: 24.1.0.1                                     |
+-------------------------------+-----------------+------------------------------------------------------+
| NPU     Name                  | Health          | Power(W)     Temp(C)           Hugepages-Usage(page) |
| Chip    Device                | Bus-Id          | AICore(%)    Memory-Usage(MB)                        |
+===============================+=================+======================================================+
| 1       310P3                 | OK              | NA           62                7210  / 7210          |
| 0       0                     | 0000:01:00.0    | 0            16302/ 44280                            |
+-------------------------------+-----------------+------------------------------------------------------+
| 1       310P3                 | OK              | NA           62                7210  / 7210          |
| 1       1                     | 0000:01:00.0    | 0            15543/ 43693                            |
+===============================+=================+======================================================+
| 2       310P3                 | OK              | NA           61                17057 / 17057         |
| 0       2                     | 0000:02:00.0    | 0            35563/ 44280                            |
+-------------------------------+-----------------+------------------------------------------------------+
| 2       310P3                 | OK              | NA           61                16823 / 16823         |
| 1       3                     | 0000:02:00.0    | 0            35204/ 43693                            |
+===============================+=================+======================================================+
+-------------------------------+-----------------+------------------------------------------------------+
| NPU     Chip                  | Process id      | Process name             | Process memory(MB)        |
+===============================+=================+======================================================+
| 1       0                     | 3277562         | mindie_llm_back          | 14513                     |
| 1       1                     | 3277565         | mindie_llm_back          | 14513                     |
+===============================+=================+======================================================+
| 2       0                     | 3034986         | mindie_llm_back          | 34207                     |
| 2       1                     | 3034989         | mindie_llm_back          | 33740                     |
+===============================+=================+======================================================+
""",
        {
            0: {
                'name': '310P3',
                'health': 'OK',
                'power': libascend.NA + ' ',
                'temp': 62,
                'procs': [(3277562, 14513*1024*1024)],
                'bus_id': '0000:01:00.0',
                'aicore': 0,
                'hbm_used': 16302 * 1024 * 1024,
                'hbm_total': 44280 * 1024 * 1024,
                'util': libascend.Util(npu=0, mem=36.8, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 1,
                'chip_id': 0,
            },
            1: {
                'name': '310P3',
                'health': 'OK',
                'power': libascend.NA + ' ',
                'temp': 62,
                'procs': [(3277565, 14513*1024*1024)],
                'bus_id': '0000:01:00.0',
                'aicore': 0,
                'hbm_used': 15543 * 1024 * 1024,
                'hbm_total': 43693 * 1024 * 1024,
                'util': libascend.Util(npu=0, mem=35.6, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 1,
                'chip_id': 1,
            },
            2: {
                'name': '310P3',
                'health': 'OK',
                'power': libascend.NA + ' ',
                'temp': 61,
                'procs': [(3034986, 34207*1024*1024)],
                'bus_id': '0000:02:00.0',
                'aicore': 0,
                'hbm_used': 35563 * 1024 * 1024,
                'hbm_total': 44280 * 1024 * 1024,
                'util': libascend.Util(npu=0, mem=80.3, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 2,
                'chip_id': 0,
            },
            3: {
                'name': '310P3',
                'health': 'OK',
                'power': libascend.NA + ' ',
                'temp': 61,
                'procs': [(3034989, 33740*1024*1024)],
                'bus_id': '0000:02:00.0',
                'aicore': 0,
                'hbm_used': 35204 * 1024 * 1024,
                'hbm_total': 43693 * 1024 * 1024,
                'util': libascend.Util(npu=0, mem=80.6, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 2,
                'chip_id': 1,
            },
        },
    ),

    (
        # npusmi_950pr: Ascend950PR_9579 on npu-smi 25.7.rc1.6, verbatim capture
        # from the real machine (2026-09-27).  The main table differs from the
        # legacy 910*/310* layout: `NPU ID` and `Name` are separate columns, the
        # second row leaves the chip / phy-id columns empty, and process rows
        # carry a single `NPU ID` column.
        """
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
""",
        {
            0: {
                'name': 'Ascend950PR',
                'health': 'OK',
                'power': 210300.0,
                'temp': 64,
                'procs': [(210284, 115929 * 1024 * 1024), (209907, 284 * 1024 * 1024)],
                'bus_id': '0000:01:00.0',
                'aicore': 0,
                'hbm_used': 121576 * 1024 * 1024,
                'hbm_total': 131072 * 1024 * 1024,
                'util': libascend.Util(npu=0, mem=92.8, bandwidth='N/A', aicpu='N/A'),
                'npu_id': 0,
                'chip_id': 0,
            },
        },
    ),

]


def reset_libascend_cache():
    libascend._CACHE.clear()
    libascend._IDX.clear()
    libascend._npu_chip_phy.clear()
    libascend._cache_ts = 0.0


@pytest.mark.parametrize("raw,expected_cache", TEST_CASES)
def test_npusmi_parse(raw, expected_cache):
    reset_libascend_cache()

    libascend._update_cache(raw)

    assert list(expected_cache.keys()) == libascend._IDX

    for key, expected_val in expected_cache.items():
        assert key in libascend._CACHE
        cached_val = libascend._CACHE[key]
        for field, value in expected_val.items():
            assert cached_val[field] == value


def test_npusmi_parse_ignores_transient_unknown_process():
    raw = TEST_CASES[0][0].replace(
        "| 0       0                 | 124528",
        "| 7       0                 | 124528",
    )
    reset_libascend_cache()

    libascend._update_cache(raw)

    assert libascend._IDX == [0, 1]
    assert libascend._CACHE[0]["procs"] == []
    assert libascend._CACHE[1]["procs"] == []


def test_950pr_patterns_do_not_match_legacy_tables():
    """The 950PR patterns must stay mutually exclusive with the legacy tables."""
    legacy_rows = [
        # device row 1, process row of the 910B2C fixture
        "| 0     910B2C              | OK            | 88.6        51                0    / 0             |",
        "| 0       0                 | 124528        | python3.8                | 17400                   |",
    ]
    for row in legacy_rows:
        assert libascend._RE_L1B.match(row) is None
        assert libascend._RE_PB.match(row) is None

    legacy_row2 = (
        "| 0                         | 0000:5A:00.0  | 0           0    / 0          20701/ 65536         |"
    )
    assert libascend._RE_L2B.match(legacy_row2) is None
    assert libascend._RE_L2.match(legacy_row2) is not None


def test_950pr_bus_id_accessor():
    reset_libascend_cache()

    # TEST_CASES[-1] is the npusmi_950pr fixture (kept last on purpose).
    libascend._update_cache(TEST_CASES[-1][0])

    assert libascend.ascendDeviceGetBusId(0) == '0000:01:00.0'
    assert libascend.ascendDeviceGetPowerLimit(0) == 600
    assert libascend.ascendDeviceGetName(0) == 'Ascend950PR'
    assert libascend.ascendDeviceGetProcessInfo(0) == [
        libascend.ProcInfo(210284, 115929 * 1024 * 1024),
        libascend.ProcInfo(209907, 284 * 1024 * 1024),
    ]

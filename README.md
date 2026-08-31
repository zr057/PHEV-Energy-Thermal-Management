# PHEV 能量管理与热管理协同控制

本项目是合肥工业大学智能车辆工程专业课程设计成果，面向插电式混合动力汽车（PHEV），研究 CLTC-P 行驶工况下的能量管理与电池热管理协同控制方法。

项目建立了整车纵向动力学、发动机燃油消耗、电机效率、电池 SOC 与电池热模型，并实现、比较以下控制策略：

- CD-CS（Charge Depleting–Charge Sustaining）基准策略
- ECMS（Equivalent Consumption Minimization Strategy）
- 带温度惩罚项的 Thermal ECMS
- 用于全局最优基准对照的动态规划（DP）策略

## 研究内容

1. 基于 CLTC-P 工况计算车辆需求功率。
2. 建立发动机、电机、电池 SOC 和电池温度模型。
3. 对比 CD-CS、普通 ECMS 与热约束 ECMS 的功率分配效果。
4. 扫描等效因子、SOC 反馈系数和温度惩罚权重。
5. 从燃油消耗、电耗、综合油耗、SOC 轨迹和电池温度等方面评价策略。
6. 使用动态规划结果评价 Thermal ECMS 与全局最优解之间的差距。

## 策略对比结果

下图展示了 CD-CS、ECMS 和 Thermal ECMS 三种策略下的 SOC、电池温度、发动机功率与电池功率轨迹。

![三种能量管理策略对比](strategy_comparison.png)

在当前脚本默认参数（30 个工况循环、环境温度 35 ℃、初始 SOC 0.60）下，示例输出如下：

| 策略 | 行驶里程 (km) | 燃油 (L/100 km) | 电耗 (kWh/100 km) | 综合油耗 (L/100 km) | 终端 SOC | 最高温度 (℃) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CD-CS | 12.04 | 0.00 | 14.09 | 7.05 | 0.569 | 35.3 |
| ECMS | 12.04 | 43.56 | -42.48 | 22.32 | 0.694 | 36.5 |
| Thermal ECMS | 12.04 | 16.72 | -5.26 | 14.09 | 0.612 | 35.0 |

> 表中负电耗表示该工况设置下电池净充电。数值来自当前代码的示例运行，只适用于脚本内设定的模型参数与边界条件。

## 文件说明

| 文件或目录 | 内容 |
| --- | --- |
| `1、m温度n个全CLTC-P工况循环CD-CS（有图）(2).py` | CD-CS 策略仿真及 SOC、功率、温度绘图 |
| `2-1、m温度n个全CLTC-P工况循环双SOC - 普通ECMS.py` | 不同初始 SOC 下的普通 ECMS 仿真 |
| `2-2 最优组合.py` | A-ECMS 参数组合扫描与寻优 |
| `3-2、策略对比.py` | CD-CS、ECMS、Thermal ECMS 综合对比 |
| `4、 DP热约束ECMS评估.py` | DP 与 Thermal ECMS 对比评价 |
| `副本CLTC.xlsx` | CLTC 工况相关数据 |
| `1/25`、`1/35` | 不同环境温度下的 CD-CS 仿真图 |
| `3` | ECMS 仿真结果图 |
| `课程设计报告-张容-2023213357.pdf` | 完整课程设计报告 |
| `CLTC 标准.pdf` | CLTC 标准参考材料 |

文件 `(1).py` 与 `(2).py` 为同一阶段保留的两个版本，推荐运行较新的 `(2).py`。

## 环境配置

- Python 3.10 或更高版本
- NumPy
- pandas
- SciPy
- Matplotlib
- openpyxl
- python-docx（仅生成公式文档时需要）

创建虚拟环境并安装依赖：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 快速运行

推荐先运行三策略综合对比：

```powershell
python ".\3-2、策略对比.py"
```

运行成功后会在当前目录生成：

```text
strategy_comparison.png
```

其他实验：

```powershell
# CD-CS 基准策略
python ".\1、m温度n个全CLTC-P工况循环CD-CS（有图）(2).py"

# 普通 ECMS
python ".\2-1、m温度n个全CLTC-P工况循环双SOC - 普通ECMS.py"

# 参数寻优
python ".\2-2 最优组合.py"

# DP 与热约束 ECMS 对比（计算量较大）
python ".\4、 DP热约束ECMS评估.py"
```

## 复现实验说明

- 各脚本目前是可独立运行的实验程序，车辆参数、温度、SOC、循环次数及控制参数在脚本中直接设置。
- Matplotlib 使用非交互式后端，图片会保存到运行目录，不会自动弹窗。
- DP 脚本需要较多内存和计算时间，建议先用较小的离散网格或循环次数验证环境。
- 若需要复现报告中的全部温度与参数组合，请按报告章节修改相应脚本的环境温度、初始 SOC、等效因子和温度惩罚权重。

## 注意事项

- 本项目用于课程设计与学术交流，模型参数和结果不应直接用于实车控制。
- 公开仓库前请检查报告、任务书等文档中的姓名、学号、教师信息及其他个人信息。
- `CLTC 标准.pdf` 等参考资料可能受版权约束；公开发布前请确认拥有再分发权限，必要时只保留来源链接。

## 作者

张容，智能车辆工程专业，2026 年 7 月。


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
| `1、m温度n个全CLTC-P工况循环CD-CS（有图）(1).py` | 25 ℃环境下的 CD-CS 策略仿真及绘图 |
| `1、m温度n个全CLTC-P工况循环CD-CS（有图）(2).py` | 35 ℃环境下的 CD-CS 策略仿真及绘图 |
| `2-1、m温度n个全CLTC-P工况循环双SOC - 普通ECMS.py` | 不同初始 SOC 下的普通 ECMS 仿真 |
| `2-2 最优组合.py` | A-ECMS 参数组合扫描与寻优 |
| `3-2、策略对比.py` | CD-CS、ECMS、Thermal ECMS 综合对比 |
| `4、 DP热约束ECMS评估.py` | DP 与 Thermal ECMS 对比评价 |
| `strategy_comparison.png` | 三种能量管理策略综合对比图 |
| `课程设计报告-张容-2023213357.pdf` | 完整课程设计报告 |

## 环境配置

- Python 3.10 或更高版本
- NumPy
- pandas
- SciPy
- Matplotlib

创建虚拟环境并安装依赖：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 作者

张容，智能车辆工程专业，2026 年 7 月。

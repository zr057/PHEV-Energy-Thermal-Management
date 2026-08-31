# PHEV Energy and Thermal Management

I developed a complete simulation framework for the coordinated energy and battery thermal management of a plug-in hybrid electric vehicle under the CLTC-P driving cycle. The project covers power-demand modeling, control-strategy development, parameter optimization, and dynamic-programming-based benchmarking.

## Key Contributions

- Built a longitudinal vehicle dynamics model to calculate power demand from vehicle speed, acceleration, rolling resistance, aerodynamic drag, and road gradient.
- Modeled engine fuel consumption, motor efficiency, battery state of charge, and first-order battery thermal dynamics.
- Implemented three online energy-management strategies: CD-CS, ECMS, and thermal-constrained ECMS.
- Added a battery-temperature penalty to the ECMS instantaneous cost function to balance energy efficiency and thermal safety.
- Optimized the ECMS equivalence factor, SOC feedback coefficient, and temperature-penalty weight through parameter sweeps.
- Developed a dynamic programming benchmark using discretized states and controls to evaluate the performance of thermal-constrained ECMS against a global optimum.
- Created a unified evaluation pipeline covering fuel consumption, electrical energy consumption, equivalent fuel consumption, terminal SOC, peak battery temperature, and temperature-limit violations.

## Control Methods

| Method | Implementation |
| --- | --- |
| CD-CS | Switches between charge-depleting and charge-sustaining operation according to SOC thresholds |
| ECMS | Converts electrical energy into equivalent fuel consumption and optimizes engine-battery power allocation at each time step |
| Thermal ECMS | Adds a temperature-dependent penalty to ECMS to reduce battery loading at elevated temperatures |
| Dynamic Programming | Uses SOC and battery temperature as states and engine power as the control input to obtain a global optimization benchmark |

## Simulation Results

Baseline comparison: 30 CLTC-P cycles, ambient temperature of 35 °C, initial SOC of 0.60, ECMS equivalence factor `s = 1.6`, and thermal penalty weight `w_T = 5.0`.

| Strategy | Equivalent Fuel Consumption (L/100 km) | Final SOC | Peak Battery Temperature (°C) |
| --- | ---: | ---: | ---: |
| CD-CS | 7.05 | 0.569 | 35.3 |
| ECMS | 22.32 | 0.694 | 36.5 |
| Thermal ECMS | 14.09 | 0.612 | 35.0 |

![Comparison of CD-CS, ECMS, and Thermal ECMS](strategy_comparison.png)

Under the selected parameters, Thermal ECMS limited the peak battery temperature to 35.0 °C and maintained the final SOC closer to its initial value than the other strategies.

## Repository Structure

| File | Description |
| --- | --- |
| `cdcs_25c.py` | CD-CS simulation at an ambient temperature of 25 °C |
| `cdcs_35c.py` | CD-CS simulation at an ambient temperature of 35 °C |
| `ecms_dual_soc.py` | ECMS evaluation with different initial SOC values |
| `aecms_parameter_optimization.py` | Adaptive ECMS parameter sweep and optimization |
| `strategy_comparison.py` | Unified comparison of CD-CS, ECMS, and Thermal ECMS |
| `dp_thermal_ecms_evaluation.py` | Dynamic programming benchmark and Thermal ECMS evaluation |
| `course_design_report.pdf` | Full methodology, mathematical models, and results |

## Technical Stack

Python, NumPy, pandas, SciPy, and Matplotlib.

## Author

Zhang Rong | Intelligent Vehicle Engineering | July 2026

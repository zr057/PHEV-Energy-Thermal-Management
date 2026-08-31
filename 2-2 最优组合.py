import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

# ================= 1. 参数与模型初始化 =================
class VehicleParams:
    def __init__(self, T_amb=25.0, SOC_init=0.60):
        self.m = 3120.0; self.delta = 1.1; self.Cd = 0.6; self.A = 3.25; self.f = 0.009
        self.g = 9.81; self.rho = 1.225; self.eta_T = 0.95; self.eta_m = 0.95
        self.Cap_Ah = 155.0; self.V_nom = 350.4; self.R0 = 0.03
        self.SOC_init = SOC_init; self.SOC_min = 0.50; self.SOC_max = 0.70
        self.T_amb = T_amb; self.m_bat = 267.0; self.cp_bat = 1100.0
        self.C_th = self.m_bat * self.cp_bat; self.fuel_density = 0.75
        self.fuel_tank_L = 1e9; self.fuel_remaining_L = 1e9
        eng_p = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
        eng_fc = [0, 1.8, 3.6, 5.2, 6.5, 7.5, 8.2, 8.8, 9.2, 9.6, 10.0, 10.3, 10.0]
        self.eng_fc_interp = interp1d(eng_p, eng_fc, kind='linear', fill_value="extrapolate")
        self.P_eng_max = 120.0

# ================= 2. CLTC-P工况数据 (使用10次循环加速扫描) =================
def get_cltc_p_data(cycles=10):
    raw_speeds = "0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 3.2 5.4 8.5 11.5 14.1 16.2 18.7 19.9 19.0 20.6 20.7 24.1 25.8 27.4 28.9 30.1 31.3 31.2 31.2 32.3 33.3 33.4 33.6 33.4 33.3 33.1 33.3 33.5 33.0 32.8 32.6 32.7 32.3 31.9 31.3 30.8 30.6 29.9 29.1 27.0 25.0 22.8 22.1 21.3 20.3 21.2 22.2 21.6 22.1 23.2 23.8 23.2 22.1 21.2 20.0 18.3 15.0 10.0 5.7 2.1 0.0 0.0 0.0"
    v_single = np.array([float(x) for x in raw_speeds.split()])
    v_kmh = np.tile(v_single, cycles)
    t_all = np.arange(0, len(v_kmh))
    return t_all, v_kmh

def calculate_req_power(vp, v_kmh):
    dt = 1.0; v_ms = v_kmh / 3.6; a_ms2 = np.gradient(v_ms, dt); a_ms2[0] = 0
    P_roll = vp.m * vp.g * vp.f * v_ms; P_aero = 0.5 * vp.rho * vp.Cd * vp.A * (v_ms**3)
    P_acc = vp.m * vp.delta * v_ms * a_ms2
    P_req = (P_roll + P_aero + P_acc) / (vp.eta_T * vp.eta_m) / 1000
    P_req = np.where(P_req < 0, np.maximum(P_req, -60) * 0.6, P_req)
    return P_req, v_ms, a_ms2

def precompute_eng_fc_table(vp):
    p_grid = np.arange(0, vp.P_eng_max + 0.1, 0.5)
    fc_grid = np.array([float(vp.eng_fc_interp(p)) if p > 0 else 0.0 for p in p_grid])
    return p_grid, fc_grid

# ================= 3. A-ECMS 仿真 (扫描版，修复 v_ms 参数传入) =================
def simulate_AECMS_scan(vp, P_req, v_ms, s0, K_p, p_grid, fc_grid, SOC_target=0.60):
    dt = 1.0; SOC = vp.SOC_init; total_fuel_g = 0.0; total_kWh_bat = 0.0
    fuel_consumed_L = 0.0; actual_steps = 0; k_elec = 375.0 / 3600.0; N = len(P_req)

    for t in range(N):
        actual_steps += 1
        p_req = P_req[t]
        # 动态修正等效因子
        s_actual = s0 * (1.0 + K_p * (SOC_target - SOC))

        if p_req < 0:
            P_eng = 0.0; P_bat = max(p_req, -30.0)
            if SOC >= vp.SOC_max: P_bat = 0.0
        else:
            max_p_eng = min(vp.P_eng_max, p_req + 30.0)
            n_scan = int(max_p_eng / 0.5) + 1
            p_eng_arr = p_grid[:n_scan]; p_bat_arr = p_req - p_eng_arr; fc_arr = fc_grid[:n_scan]
            mask = np.ones(n_scan, dtype=bool)
            if SOC <= vp.SOC_min: mask &= (p_bat_arr <= 0.01)
            if SOC >= vp.SOC_max: mask &= (p_bat_arr >= -0.01)
            mask &= (p_bat_arr <= 60.0) & (p_bat_arr >= -30.0)
            cost_arr = fc_arr + s_actual * p_bat_arr * k_elec
            cost_arr[~mask] = np.inf
            idx = np.argmin(cost_arr)
            if cost_arr[idx] == np.inf:
                P_eng = min(vp.P_eng_max, p_req); P_bat = p_req - P_eng
                if SOC <= vp.SOC_min and P_bat > 0: P_bat = max(0.0, p_req - P_eng)
                if SOC >= vp.SOC_max and P_bat < 0: P_bat = max(0.0, p_req - P_eng)
                P_bat = np.clip(P_bat, -30, 60)
            else:
                P_eng = p_eng_arr[idx]; P_bat = p_bat_arr[idx]

        if P_eng > 0:
            total_fuel_g += float(vp.eng_fc_interp(P_eng)) * dt
            fuel_consumed_L = total_fuel_g / (vp.fuel_density * 1000)

        I_bat = (P_bat * 1000) / vp.V_nom
        dSOC = (I_bat * dt) / (3600 * vp.Cap_Ah)
        SOC_new = SOC - dSOC
        SOC_clipped = np.clip(SOC_new, vp.SOC_min, vp.SOC_max)
        if abs(SOC_clipped - SOC_new) > 1e-8:
            total_kWh_bat += (SOC - SOC_clipped) * 3600 * vp.Cap_Ah * vp.V_nom / (1000 * 3600)
        else:
            total_kWh_bat += P_bat * dt / 3600
        SOC = SOC_clipped

    # ================= 修复里程计算 (使用传入的 v_ms) =================
    distance_km = np.sum(v_ms[:actual_steps] * dt) / 1000
    if distance_km < 0.01:
        eq_fuel = 999.0
    else:
        eq_fuel = (fuel_consumed_L + total_kWh_bat * 0.5) / distance_km * 100

    return SOC, eq_fuel, distance_km

# ================= 4. 执行扫描 =================
cycles = 10; T_amb = 25.0; SOC_init = 0.60
t_all, v = get_cltc_p_data(cycles=cycles)
vp0 = VehicleParams(T_amb=T_amb, SOC_init=SOC_init)
P_req, v_ms, a_ms2 = calculate_req_power(vp0, v)
p_grid, fc_grid = precompute_eng_fc_table(vp0)

# 【修改】等效因子列表改为 [1, 1.2, 1.4, 1.8, 2]
s0_list = [1, 1.2, 1.4, 1.8, 2]
Kp_list = [0, 1, 2, 3, 4, 5]
results = []

for s0 in s0_list:
    for K_p in Kp_list:
        vp = VehicleParams(T_amb=T_amb, SOC_init=SOC_init)
        # 将 v_ms 传入函数
        soc_end, eq_fuel, dist = simulate_AECMS_scan(vp, P_req, v_ms, s0, K_p, p_grid, fc_grid, SOC_target=0.60)
        soc_dev = abs(soc_end - 0.60)
        results.append({
            "基础等效因子(s0)": s0,
            "修正系数(Kp)": K_p,
            "终端SOC": round(soc_end, 4),
            "SOC偏差": round(soc_dev, 4),
            "等效油耗(L/100km)": round(eq_fuel, 2)
        })

df = pd.DataFrame(results)

# ================= 5. 为每个等效因子寻找最优 Kp =================
best_results = []

# 遍历每个 s0
for s0 in s0_list:
    # 提取当前 s0 的扫描数据
    df_s0 = df[df["基础等效因子(s0)"] == s0]
    
    # 优先在满足 SOC偏差 < 0.02 的结果中找油耗最低的
    valid_s0 = df_s0[df_s0["SOC偏差"] < 0.02]
    if not valid_s0.empty:
        best_for_s0 = valid_s0.loc[valid_s0["等效油耗(L/100km)"].idxmin()]
    else:
        # 如果都不满足，退而求其次，找 SOC偏差最小的
        best_for_s0 = df_s0.loc[df_s0["SOC偏差"].idxmin()]
        
    best_results.append(best_for_s0)

df_best = pd.DataFrame(best_results)

print("="*70)
print("每个等效因子 s0 的最优 SOC 修正系数 Kp")
print("筛选条件: 优先 SOC偏差<0.02 且 等效油耗最低")
print("="*70)
print(df_best.to_string(index=False))

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d, RegularGridInterpolator
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ================= 1. 参数与模型初始化 =================
class VehicleParams:
    def __init__(self, T_amb=35.0, SOC_init=0.60):
        self.m = 3120.0; self.delta = 1.1; self.Cd = 0.6; self.A = 3.25; self.f = 0.009
        self.g = 9.81; self.rho = 1.225; self.eta_T = 0.95; self.eta_m = 0.95
        self.Cap_Ah = 155.0; self.V_nom = 350.4
        self.R0 = 0.1
        self.SOC_init = SOC_init; self.SOC_min = 0.50; self.SOC_max = 0.70
        self.T_amb = T_amb; self.m_bat = 267.0; self.cp_bat = 1100.0
        self.C_th = self.m_bat * self.cp_bat; self.fuel_density = 0.75
        eng_p = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
        eng_fc = [0, 1.8, 3.6, 5.2, 6.5, 7.5, 8.2, 8.8, 9.2, 9.6, 10.0, 10.3, 10.0]
        self.eng_fc_interp = interp1d(eng_p, eng_fc, kind='linear', fill_value="extrapolate")
        self.P_eng_max = 120.0
        self.T_low = 40.0; self.T_high = 45.0
        self.P_cool_max = 1.5

# ================= 2. 工况数据与基础计算 =================
def get_cltc_p_data(cycles=1):
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

# ================= 3. 热约束 ECMS 策略 =================
def simulate_Thermal_ECMS(vp, P_req, v_ms, s, w_T):
    dt = 1.0; SOC = vp.SOC_init; T = vp.T_amb
    total_fuel_g = 0.0; total_kWh_bat = 0.0; fuel_consumed_L = 0.0
    actual_steps = 0; k_elec = 375.0 / 3600.0
    total_kWh_cool = 0.0; is_cooling = False; N = len(P_req)
    
    hist_soc = np.zeros(N); hist_T = np.zeros(N); hist_p_eng = np.zeros(N)
    
    for t in range(N):
        actual_steps += 1; p_req_base = P_req[t]
        
        if T >= vp.T_high: is_cooling = True
        elif T <= vp.T_low: is_cooling = False
        P_cool = vp.P_cool_max if is_cooling else 0.0
        total_kWh_cool += P_cool * dt / 3600
        p_req_total = p_req_base + P_cool
        
        if T > vp.T_high: T_penalty = w_T * (T - vp.T_high)**2
        elif T < vp.T_low: T_penalty = w_T * (vp.T_low - T)**2
        else: T_penalty = 0.0

        if p_req_total < 0:
            P_eng = 0.0; P_bat = max(p_req_total, -30.0)
            if SOC >= vp.SOC_max: P_bat = 0.0
        else:
            max_p_eng = min(vp.P_eng_max, p_req_total + 30.0)
            p_eng_arr = np.arange(0, max_p_eng + 0.1, 1.0)
            p_bat_arr = p_req_total - p_eng_arr
            fc_arr = np.array([float(vp.eng_fc_interp(p)) if p > 0 else 0.0 for p in p_eng_arr])
            mask = np.ones(len(p_eng_arr), dtype=bool)
            if SOC <= vp.SOC_min: mask &= (p_bat_arr <= 0.01)
            if SOC >= vp.SOC_max: mask &= (p_bat_arr >= -0.01)
            mask &= (p_bat_arr <= 60.0) & (p_bat_arr >= -30.0)
            cost_arr = fc_arr + s * p_bat_arr * k_elec + T_penalty * np.abs(p_bat_arr)
            cost_arr[~mask] = np.inf
            idx = np.argmin(cost_arr)
            P_eng = p_eng_arr[idx]; P_bat = p_bat_arr[idx]

        if P_eng > 0:
            total_fuel_g += float(vp.eng_fc_interp(P_eng)) * dt
            fuel_consumed_L = total_fuel_g / (vp.fuel_density * 1000)

        I_bat = (P_bat * 1000) / vp.V_nom
        SOC = np.clip(SOC - (I_bat * dt) / (3600 * vp.Cap_Ah), vp.SOC_min, vp.SOC_max)
        T += dt * ((I_bat**2) * vp.R0 - P_cool * 1000) / vp.C_th
        total_kWh_bat += P_bat * dt / 3600

        hist_soc[t] = SOC; hist_T[t] = T; hist_p_eng[t] = P_eng

    distance_km = np.sum(v_ms[:actual_steps] * dt) / 1000
    return {
        "策略": "Thermal ECMS",
        "综合油耗(L/100km)": round((fuel_consumed_L + (total_kWh_bat + total_kWh_cool) * 0.5) / distance_km * 100, 2),
        "hist_soc": hist_soc, "hist_T": hist_T, "hist_p_eng": hist_p_eng
    }

# ================= 4. 动态规划 (DP) 策略 (向量化优化) =================
def simulate_DP(vp, P_req, v_ms):
    dt = 1.0; N = len(P_req)
    k_elec = 375.0 / 3600.0
    
    # 1. 离散化网格定义
    N_soc = 40; N_T = 20; N_p = 25
    soc_grid = np.linspace(vp.SOC_min, vp.SOC_max, N_soc)
    t_grid = np.linspace(vp.T_amb - 2, vp.T_high + 5, N_T)
    p_eng_grid = np.linspace(0, vp.P_eng_max, N_p)
    
    # 预计算燃油消耗率表
    fc_lookup = np.array([float(vp.eng_fc_interp(p)) if p > 0 else 0.0 for p in p_eng_grid])
    
    # 创建SOC和T的网格矩阵 (N_soc, N_T)
    SOC_mesh, T_mesh = np.meshgrid(soc_grid, t_grid, indexing='ij')
    
    # 初始化代价函数 J(N_soc, N_T)，终点代价为0
    J = np.zeros((N_soc, N_T))
    
    # 记录每个状态在每步的最优控制索引
    best_ctrl = np.zeros((N, N_soc, N_T), dtype=np.int32)
    
    print("开始DP倒推计算...")
    for k in range(N - 1, -1, -1):
        p_req_base = P_req[k]
        J_new = np.full((N_soc, N_T), np.inf)
        
        # 根据温度网格决定冷却功率 (向量化)
        P_cool_grid = np.where(T_mesh >= vp.T_high, vp.P_cool_max, 0.0)  # (N_soc, N_T)
        p_req_total_grid = p_req_base + P_cool_grid  # (N_soc, N_T)
        
        # 遍历所有控制量 P_eng
        for p_idx in range(N_p):
            P_eng = p_eng_grid[p_idx]
            P_bat_grid = p_req_total_grid - P_eng  # (N_soc, N_T)
            
            # 约束掩码
            mask = np.ones((N_soc, N_T), dtype=bool)
            mask &= (P_bat_grid <= 60.0) & (P_bat_grid >= -30.0)
            # SOC约束
            mask &= ~((SOC_mesh <= vp.SOC_min + 1e-4) & (P_bat_grid > 0))
            mask &= ~((SOC_mesh >= vp.SOC_max - 1e-4) & (P_bat_grid < 0))
            
            # 计算状态转移
            I_bat_grid = (P_bat_grid * 1000) / vp.V_nom  # (N_soc, N_T)
            soc_next = SOC_mesh - (I_bat_grid * dt) / (3600 * vp.Cap_Ah)
            T_next = T_mesh + dt * ((I_bat_grid**2) * vp.R0 - P_cool_grid * 1000) / vp.C_th
            
            # 检查越界
            valid_range = (soc_next >= soc_grid[0]) & (soc_next <= soc_grid[-1]) & \
                          (T_next >= t_grid[0]) & (T_next <= t_grid[-1])
            mask &= valid_range
            
            # 计算当前步代价
            fuel_cost = fc_lookup[p_idx]
            elec_cost = k_elec * P_bat_grid
            cool_cost = k_elec * P_cool_grid
            step_cost = fuel_cost + elec_cost + cool_cost  # (N_soc, N_T)
            
            # 使用 RegularGridInterpolator 插值获取 J_next
            # 准备插值点 (只对有效点插值以加速)
            if np.any(mask):
                pts_valid = np.column_stack([soc_next[mask], T_next[mask]])
                interp = RegularGridInterpolator(
                    (soc_grid, t_grid), J, method='linear', bounds_error=False, fill_value=np.inf
                )
                J_next_vals = interp(pts_valid)
                
                total_cost = step_cost.copy()
                total_cost[mask] += J_next_vals
                total_cost[~mask] = np.inf
                
                # 更新最小代价
                update_mask = total_cost < J_new
                J_new = np.where(update_mask, total_cost, J_new)
                best_ctrl[k][update_mask] = p_idx
        
        J = J_new.copy()
        if k % 200 == 0:
            print(f"  倒推进度: {N - k}/{N} 步")
    
    print("倒推完成，开始前向仿真提取最优轨迹...")
    
    # 3. 前向仿真提取最优路径
    soc = vp.SOC_init; T = vp.T_amb
    hist_soc_dp = np.zeros(N); hist_T_dp = np.zeros(N); hist_p_eng_dp = np.zeros(N)
    total_fuel_g = 0.0; total_kWh_bat = 0.0; total_kWh_cool = 0.0; fuel_consumed_L = 0.0
    
    for k in range(N):
        # 找到当前状态最近的网格索引
        i = np.argmin(np.abs(soc_grid - soc))
        j = np.argmin(np.abs(t_grid - T))
        
        p_idx = best_ctrl[k, i, j]
        P_eng = p_eng_grid[p_idx]
        
        p_req_base = P_req[k]
        P_cool = vp.P_cool_max if T >= vp.T_high else 0.0
        total_kWh_cool += P_cool * dt / 3600
        p_req_total = p_req_base + P_cool
        
        P_bat = p_req_total - P_eng
        P_bat = np.clip(P_bat, -30, 60)
        
        if P_eng > 0:
            total_fuel_g += float(vp.eng_fc_interp(P_eng)) * dt
            fuel_consumed_L = total_fuel_g / (vp.fuel_density * 1000)
            
        I_bat = (P_bat * 1000) / vp.V_nom
        soc = np.clip(soc - (I_bat * dt) / (3600 * vp.Cap_Ah), vp.SOC_min, vp.SOC_max)
        T += dt * ((I_bat**2) * vp.R0 - P_cool * 1000) / vp.C_th
        total_kWh_bat += P_bat * dt / 3600
        
        hist_soc_dp[k] = soc; hist_T_dp[k] = T; hist_p_eng_dp[k] = P_eng

    distance_km = np.sum(v_ms[:N] * dt) / 1000
    print("前向仿真完成！")
    return {
        "策略": "Dynamic Programming",
        "综合油耗(L/100km)": round((fuel_consumed_L + (total_kWh_bat + total_kWh_cool) * 0.5) / distance_km * 100, 2),
        "hist_soc": hist_soc_dp, "hist_T": hist_T_dp, "hist_p_eng": hist_p_eng_dp
    }

# ================= 5. 执行仿真与对比 =================
cycles = 1
t_all, v = get_cltc_p_data(cycles=cycles)
vp0 = VehicleParams(T_amb=35.0, SOC_init=0.60)
P_req, v_ms, a_ms2 = calculate_req_power(vp0, v)

# 1. 运行热约束ECMS
vp1 = VehicleParams(T_amb=35.0, SOC_init=0.60)
res_ecms = simulate_Thermal_ECMS(vp1, P_req, v_ms, s=1.6, w_T=5.0)

# 2. 运行动态规划 (全局最优)
vp2 = VehicleParams(T_amb=35.0, SOC_init=0.60)
res_dp = simulate_DP(vp2, P_req, v_ms)

# 结果对比
df = pd.DataFrame([
    {"策略": res_ecms["策略"], "综合油耗(L/100km)": res_ecms["综合油耗(L/100km)"]},
    {"策略": res_dp["策略"], "综合油耗(L/100km)": res_dp["综合油耗(L/100km)"]}
])
print("\n" + "="*50)
print("DP 与 Thermal ECMS 综合油耗对比")
print("="*50)
print(df.to_string(index=False))

# ================= 6. 绘制对比图 =================
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
ds = 1

# SOC
axes[0].plot(t_all[::ds]/60, np.array(res_ecms['hist_soc'][::ds])*100, label='Thermal ECMS', color='red')
axes[0].plot(t_all[::ds]/60, np.array(res_dp['hist_soc'][::ds])*100, label='DP (Global Optimal)', color='blue', linestyle='--')
axes[0].set_title('SOC Trajectory', fontweight='bold'); axes[0].set_xlabel('Time (min)'); axes[0].set_ylabel('SOC (%)')
axes[0].legend(); axes[0].grid(True, alpha=0.3)

# Temperature
axes[1].plot(t_all[::ds]/60, res_ecms['hist_T'][::ds], label='Thermal ECMS', color='red')
axes[1].plot(t_all[::ds]/60, res_dp['hist_T'][::ds], label='DP (Global Optimal)', color='blue', linestyle='--')
axes[1].axhline(y=45, color='gray', linestyle='--', alpha=0.5, label='T_high (45℃)')
axes[1].set_title('Battery Temperature', fontweight='bold'); axes[1].set_xlabel('Time (min)'); axes[1].set_ylabel('Temp (℃)')
axes[1].legend(); axes[1].grid(True, alpha=0.3)

# Engine Power
axes[2].plot(t_all[::ds]/60, res_ecms['hist_p_eng'][::ds], label='Thermal ECMS', color='red')
axes[2].plot(t_all[::ds]/60, res_dp['hist_p_eng'][::ds], label='DP (Global Optimal)', color='blue', linestyle='--')
axes[2].set_title('Engine Power', fontweight='bold'); axes[2].set_xlabel('Time (min)'); axes[2].set_ylabel('Power (kW)')
axes[2].legend(); axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('dp_vs_ecms.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n已生成对比图: dp_vs_ecms.png")

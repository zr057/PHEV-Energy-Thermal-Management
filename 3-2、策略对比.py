import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
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
        self.SOC_init = SOC_init
        self.SOC_min = 0.50; self.SOC_max = 0.70
        self.SOC_cs_thr = 0.55  # CD-CS策略的切换阈值
        self.T_amb = T_amb; self.m_bat = 267.0; self.cp_bat = 1100.0
        self.C_th = self.m_bat * self.cp_bat; self.fuel_density = 0.75
        self.fuel_tank_L = 1e9; self.fuel_remaining_L = 1e9
        eng_p = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
        eng_fc = [0, 1.8, 3.6, 5.2, 6.5, 7.5, 8.2, 8.8, 9.2, 9.6, 10.0, 10.3, 10.0]
        self.eng_fc_interp = interp1d(eng_p, eng_fc, kind='linear', fill_value="extrapolate")
        self.P_eng_max = 120.0
        # 热管理参数
        self.T_low = 40.0; self.T_high = 45.0
        self.P_cool_max = 1.5

# ================= 2. 工况数据与基础计算 =================
def get_cltc_p_data(cycles=30):
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

# 通用热更新逻辑
def update_thermal_state(vp, T, P_bat, P_cool, dt):
    I_bat = (P_bat * 1000) / vp.V_nom
    Q_gen = (I_bat**2) * vp.R0
    Q_cool_W = P_cool * 1000
    T_new = T + dt * (Q_gen - Q_cool_W) / vp.C_th
    return T_new

# 通用冷却系统逻辑
def get_cooling_power(vp, T, is_cooling):
    if T >= vp.T_high: is_cooling = True
    elif T <= vp.T_low: is_cooling = False
    return vp.P_cool_max if is_cooling else 0.0, is_cooling

# ================= 3. 三种策略仿真 =================
def simulate_strategy(vp, P_req, v_ms, strategy_name, s=1.6, w_T=5.0):
    dt = 1.0; SOC = vp.SOC_init; T = vp.T_amb
    total_fuel_g = 0.0; total_kWh_bat = 0.0; T_max = T; fuel_consumed_L = 0.0
    actual_steps = 0; k_elec = 375.0 / 3600.0
    total_kWh_cool = 0.0; time_over_T = 0; is_cooling = False
    N = len(P_req)
    
    hist_soc = np.zeros(N); hist_T = np.zeros(N); hist_p_eng = np.zeros(N); hist_p_bat = np.zeros(N)
    
    for t in range(N):
        if vp.fuel_remaining_L <= 0 and SOC <= vp.SOC_min: break
        actual_steps += 1
        p_req_base = P_req[t]
        
        # 1. 获取冷却功率 (三种策略均受相同的物理冷却系统约束)
        P_cool, is_cooling = get_cooling_power(vp, T, is_cooling)
        total_kWh_cool += P_cool * dt / 3600
        p_req_total = p_req_base + P_cool
        
        # 2. 温度惩罚计算 (仅热约束ECMS有效)
        if strategy_name == 'Thermal_ECMS':
            if T > vp.T_high: T_penalty = w_T * (T - vp.T_high)**2
            elif T < vp.T_low: T_penalty = w_T * (vp.T_low - T)**2
            else: T_penalty = 0.0
        else:
            T_penalty = 0.0

        # 3. 功率分配
        if p_req_total < 0:
            P_eng = 0.0
            P_bat = max(p_req_total, -30.0)
            if SOC >= vp.SOC_max: P_bat = 0.0
        else:
            if strategy_name == 'CD_CS':
                # CD-CS 策略: SOC高时纯电，SOC低时发动机主导
                if SOC > vp.SOC_cs_thr:
                    P_eng = 0.0; P_bat = min(p_req_total, 60.0)
                else:
                    # CS阶段：发动机提供平均功率，电池提供峰值
                    P_eng = min(vp.P_eng_max, p_req_total)
                    P_bat = p_req_total - P_eng
                    # 防止过充
                    if P_bat < 0 and SOC >= vp.SOC_max: 
                        P_eng = p_req_total; P_bat = 0.0
            else:
                # ECMS 与 热约束ECMS 策略
                max_p_eng = min(vp.P_eng_max, p_req_total + 30.0)
                n_scan = int(max_p_eng / 0.5) + 1
                p_eng_arr = np.arange(0, max_p_eng + 0.1, 0.5)[:n_scan]
                p_bat_arr = p_req_total - p_eng_arr
                fc_arr = np.array([float(vp.eng_fc_interp(p)) if p > 0 else 0.0 for p in p_eng_arr])
                
                mask = np.ones(n_scan, dtype=bool)
                if SOC <= vp.SOC_min: mask &= (p_bat_arr <= 0.01)
                if SOC >= vp.SOC_max: mask &= (p_bat_arr >= -0.01)
                mask &= (p_bat_arr <= 60.0) & (p_bat_arr >= -30.0)
                
                cost_arr = fc_arr + s * p_bat_arr * k_elec + T_penalty * np.abs(p_bat_arr)
                cost_arr[~mask] = np.inf
                idx = np.argmin(cost_arr)
                
                if cost_arr[idx] == np.inf:
                    P_eng = min(vp.P_eng_max, p_req_total); P_bat = np.clip(p_req_total - P_eng, -30, 60)
                else:
                    P_eng = p_eng_arr[idx]; P_bat = p_bat_arr[idx]

        # 4. 更新状态
        if P_eng > 0:
            total_fuel_g += float(vp.eng_fc_interp(P_eng)) * dt
            fuel_consumed_L = total_fuel_g / (vp.fuel_density * 1000)
            vp.fuel_remaining_L = vp.fuel_tank_L - fuel_consumed_L

        I_bat = (P_bat * 1000) / vp.V_nom
        SOC = np.clip(SOC - (I_bat * dt) / (3600 * vp.Cap_Ah), vp.SOC_min, vp.SOC_max)
        
        T = update_thermal_state(vp, T, P_bat, P_cool, dt)
        if T > T_max: T_max = T
        if T > vp.T_high or T < vp.T_low: time_over_T += dt
        total_kWh_bat += P_bat * dt / 3600

        hist_soc[t] = SOC; hist_T[t] = T; hist_p_eng[t] = P_eng; hist_p_bat[t] = P_bat

    distance_km = np.sum(v_ms[:actual_steps] * dt) / 1000
    return {
        "策略": strategy_name,
        "行驶里程": round(distance_km, 2),
        "燃油消耗(L)": round(fuel_consumed_L, 2),
        "燃油(L/100km)": round(fuel_consumed_L / distance_km * 100, 2),
        "电耗(kWh/100km)": round(total_kWh_bat / distance_km * 100, 2),
        "冷却能耗(kWh/100km)": round(total_kWh_cool / distance_km * 100, 2),
        "综合油耗(L/100km)": round((fuel_consumed_L + (total_kWh_bat + total_kWh_cool) * 0.5) / distance_km * 100, 2),
        "终端SOC": round(SOC, 3),
        "终端温度(℃)": round(T, 1),
        "最高温度(℃)": round(T_max, 1),
        "温度越界时间": time_over_T,
        "hist_t": t_all[:actual_steps],
        "hist_soc": hist_soc[:actual_steps],
        "hist_T": hist_T[:actual_steps],
        "hist_p_eng": hist_p_eng[:actual_steps],
        "hist_p_bat": hist_p_bat[:actual_steps]
    }

# ================= 4. 执行仿真 =================
cycles = 30; T_amb = 35.0; SOC_init = 0.60
t_all, v = get_cltc_p_data(cycles=cycles)
vp0 = VehicleParams(T_amb=T_amb, SOC_init=SOC_init)
P_req, v_ms, a_ms2 = calculate_req_power(vp0, v)

# 运行三种策略
vp1 = VehicleParams(T_amb=T_amb, SOC_init=SOC_init)
res_cdcs = simulate_strategy(vp1, P_req, v_ms, 'CD_CS')

vp2 = VehicleParams(T_amb=T_amb, SOC_init=SOC_init)
res_ecms = simulate_strategy(vp2, P_req, v_ms, 'ECMS', s=1.6)

vp3 = VehicleParams(T_amb=T_amb, SOC_init=SOC_init)
res_th_ecms = simulate_strategy(vp3, P_req, v_ms, 'Thermal_ECMS', s=1.6, w_T=5.0)

results = [res_cdcs, res_ecms, res_th_ecms]
df = pd.DataFrame(results).drop(columns=['hist_t', 'hist_soc', 'hist_T', 'hist_p_eng', 'hist_p_bat'])

print("="*100)
print("三种控制策略综合对比评价表 (等效因子s=1.6, 热惩罚w_T=5.0, T_amb=35℃)")
print("="*100)
print(df.to_string(index=False))

# ================= 5. 绘制对比图 =================
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
ds = 10 # 降采样

# 子图1: SOC变化
ax1 = axes[0, 0]
ax1.plot(res_cdcs['hist_t'][::ds]/60, np.array(res_cdcs['hist_soc'][::ds])*100, label='CD-CS', color='blue')
ax1.plot(res_ecms['hist_t'][::ds]/60, np.array(res_ecms['hist_soc'][::ds])*100, label='ECMS', color='green')
ax1.plot(res_th_ecms['hist_t'][::ds]/60, np.array(res_th_ecms['hist_soc'][::ds])*100, label='Thermal ECMS', color='red')
ax1.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='SOC_min')
ax1.axhline(y=70, color='gray', linestyle='--', alpha=0.5, label='SOC_max')
ax1.set_title('SOC Variation', fontweight='bold'); ax1.set_xlabel('Time (min)'); ax1.set_ylabel('SOC (%)')
ax1.legend(); ax1.grid(True, alpha=0.3)

# 子图2: 电池温度
ax2 = axes[0, 1]
ax2.plot(res_cdcs['hist_t'][::ds]/60, np.array(res_cdcs['hist_T'][::ds]), label='CD-CS', color='blue')
ax2.plot(res_ecms['hist_t'][::ds]/60, np.array(res_ecms['hist_T'][::ds]), label='ECMS', color='green')
ax2.plot(res_th_ecms['hist_t'][::ds]/60, np.array(res_th_ecms['hist_T'][::ds]), label='Thermal ECMS', color='red')
ax2.axhline(y=45, color='red', linestyle='--', alpha=0.5, label='T_high (45℃)')
ax2.axhline(y=35, color='gray', linestyle='--', alpha=0.5, label='T_amb')
ax2.set_title('Battery Temperature', fontweight='bold'); ax2.set_xlabel('Time (min)'); ax2.set_ylabel('Temperature (℃)')
ax2.legend(); ax2.grid(True, alpha=0.3)

# 子图3: 发动机功率
ax3 = axes[1, 0]
ax3.plot(res_cdcs['hist_t'][::ds]/60, np.array(res_cdcs['hist_p_eng'][::ds]), label='CD-CS', color='blue')
ax3.plot(res_ecms['hist_t'][::ds]/60, np.array(res_ecms['hist_p_eng'][::ds]), label='ECMS', color='green')
ax3.plot(res_th_ecms['hist_t'][::ds]/60, np.array(res_th_ecms['hist_p_eng'][::ds]), label='Thermal ECMS', color='red')
ax3.set_title('Engine Power', fontweight='bold'); ax3.set_xlabel('Time (min)'); ax3.set_ylabel('Engine Power (kW)')
ax3.legend(); ax3.grid(True, alpha=0.3)

# 子图4: 电池功率
ax4 = axes[1, 1]
ax4.plot(res_cdcs['hist_t'][::ds]/60, np.array(res_cdcs['hist_p_bat'][::ds]), label='CD-CS', color='blue')
ax4.plot(res_ecms['hist_t'][::ds]/60, np.array(res_ecms['hist_p_bat'][::ds]), label='ECMS', color='green')
ax4.plot(res_th_ecms['hist_t'][::ds]/60, np.array(res_th_ecms['hist_p_bat'][::ds]), label='Thermal ECMS', color='red')
ax4.set_title('Battery Power', fontweight='bold'); ax4.set_xlabel('Time (min)'); ax4.set_ylabel('Battery Power (kW)')
ax4.legend(); ax4.grid(True, alpha=0.3)

plt.suptitle('Comparison of CD-CS, ECMS, and Thermal ECMS Strategies', fontsize=14, fontweight='bold', y=0.95)
plt.tight_layout(rect=[0, 0.03, 1, 0.92])
plt.savefig('strategy_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n已生成策略对比图: strategy_comparison.png")

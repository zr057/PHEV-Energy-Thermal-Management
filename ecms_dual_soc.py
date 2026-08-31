import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

# ================= 1. 参数与模型初始化 =================
class VehicleParams:
    def __init__(self, T_amb=25.0, SOC_init=0.60):
        self.m = 3120.0
        self.delta = 1.1
        self.Cd = 0.6
        self.A = 3.25
        self.f = 0.009
        self.g = 9.81
        self.rho = 1.225
        self.eta_T = 0.95
        self.eta_m = 0.95
        self.Cap_Ah = 155.0
        self.V_nom = 350.4
        self.R0 = 0.03
        self.SOC_init = SOC_init
        self.SOC_min = 0.50
        self.SOC_max = 0.70
        self.T_amb = T_amb
        self.m_bat = 267.0
        self.cp_bat = 1100.0
        self.C_th = self.m_bat * self.cp_bat
        self.fuel_density = 0.75
        self.fuel_tank_L = 1e9
        self.fuel_remaining_L = 1e9
        eng_p = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
        eng_fc = [0, 1.8, 3.6, 5.2, 6.5, 7.5, 8.2, 8.8, 9.2, 9.6, 10.0, 10.3, 10.0]
        self.eng_fc_interp = interp1d(eng_p, eng_fc, kind='linear', fill_value="extrapolate")
        self.P_eng_max = 120.0

# ================= 2. 完整 CLTC-P 工况数据 =================
def get_cltc_p_data(cycles=60):
    raw_speeds = "0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 3.2 5.4 8.5 11.5 14.1 16.2 18.7 19.9 19.0 20.6 20.7 24.1 25.8 27.4 28.9 30.1 31.3 31.2 31.2 32.3 33.3 33.4 33.6 33.4 33.3 33.1 33.3 33.5 33.0 32.8 32.6 32.7 32.3 31.9 31.3 30.8 30.6 29.9 29.1 27.0 25.0 22.8 22.1 21.3 20.3 21.2 22.2 21.6 22.1 23.2 23.8 23.2 22.1 21.2 20.0 18.3 15.0 10.0 5.7 2.1 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 1.4 2.9 4.2 5.3 6.4 7.6 8.7 9.7 10.9 11.8 12.3 13.1 14.7 16.9 18.9 20.2 20.7 20.8 20.6 19.9 19.3 19.1 19.3 19.9 20.9 22.0 23.2 24.3 25.5 26.4 26.9 27.0 26.8 26.6 26.5 26.6 27.0 27.5 27.8 27.6 26.6 25.2 23.6 22.1 20.6 19.3 18.7 18.7 19.1 19.5 19.5 18.9 17.7 16.5 15.7 15.5 15.5 15.6 16.0 17.0 17.9 18.3 18.0 17.1 15.4 13.5 12.0 11.1 10.6 10.5 10.8 11.2 11.4 11.5 11.9 12.4 13.0 13.5 13.7 13.8 13.7 13.3 12.4 11.4 10.6 10.4 10.5 10.9 11.6 12.4 12.9 13.2 13.4 13.5 13.6 13.6 13.5 13.5 13.5 14.0 15.2 16.5 17.3 17.6 17.6 17.5 17.0 16.3 15.5 14.2 12.7 11.4 10.7 10.4 10.5 10.9 11.6 12.0 12.1 12.2 13.0 15.2 18.2 21.0 23.1 24.3 24.6 24.8 25.2 26.2 27.5 28.5 29.0 29.3 29.4 29.2 28.7 27.9 26.8 25.1 23.2 21.2 18.5 14.9 11.6 9.1 7.0 5.6 4.8 4.1 3.3 2.5 1.5 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 1.1 3.2 5.5 7.8 9.3 9.6 10.4 11.3 11.4 9.8 9.6 7.1 5.5 4.0 0.7 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 3.6 6.2 9.7 11.0 12.2 12.5 12.6 12.5 11.6 10.3 8.8 8.3 7.4 6.6 6.8 8.1 10.1 10.6 10.4 10.0 9.4 8.6 5.7 4.6 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 2.0 4.0 5.7 7.5 8.8 9.2 10.9 11.8 12.6 13.5 14.0 14.6 15.3 16.2 16.8 17.1 17.5 17.5 17.6 17.0 15.1 13.3 11.8 10.6 9.6 8.6 7.1 5.8 4.9 3.9 6.3 4.6 2.1 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 5.4 10.6 14.5 15.0 16.4 19.7 24.8 26.6 26.1 27.1 30.2 33.5 34.5 34.0 33.5 34.5 36.9 39.2 41.5 43.4 44.4 45.2 46.1 46.1 45.8 45.5 46.1 46.5 47.0 47.5 48.1 48.0 46.8 46.0 44.5 42.0 39.9 38.3 35.5 31.4 28.1 24.1 18.1 14.2 10.5 6.3 4.2 2.9 1.6 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 4.3 6.1 7.8 10.8 14.5 15.2 17.4 20.9 22.5 22.5 22.4 22.4 23.3 23.7 24.2 26.9 30.0 33.1 34.1 34.4 36.5 37.5 37.2 36.7 37.2 37.9 39.6 40.0 41.1 41.8 43.2 43.8 44.2 43.9 44.3 44.7 45.2 44.8 44.2 44.2 44.0 42.8 42.7 43.2 42.1 41.5 40.6 39.7 38.5 37.6 37.1 37.1 37.2 37.9 37.8 36.7 36.6 37.2 36.2 36.6 36.1 35.1 34.1 30.9 23.9 20.9 20.4 19.9 20.7 22.8 25.2 26.5 26.4 25.7 24.7 22.6 20.9 20.1 18.7 16.8 15.3 14.3 13.6 12.9 12.2 11.1 9.9 8.1 5.2 2.1 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 5.6 7.9 10.9 11.5 12.9 14.5 15.0 14.5 13.7 14.1 14.7 14.8 14.9 15.2 15.2 15.4 15.0 13.9 13.0 14.1 18.1 22.3 25.4 27.0 29.0 31.2 33.0 34.6 36.5 38.6 41.0 43.1 44.9 47.0 49.0 51.3 55.5 57.8 60.1 61.0 61.7 61.9 61.0 60.0 59.0 58.0 57.1 56.1 52.9 51.2 47.5 43.6 40.1 37.4 36.9 37.0 37.0 36.3 35.5 33.4 30.0 26.2 23.5 19.6 14.8 10.6 7.2 3.5 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 6.4 10.4 9.4 11.1 15.1 19.4 19.3 18.1 18.8 20.8 22.7 24.5 25.8 27.9 30.7 32.9 32.0 31.6 33.4 35.1 37.0 38.7 38.5 37.3 37.5 37.5 35.2 33.5 32.6 31.9 31.0 31.8 33.3 35.3 36.2 37.5 37.6 37.7 36.7 36.2 37.9 39.6 41.2 44.1 45.4 46.5 46.9 47.4 47.8 48.2 48.2 42.5 42.8 42.5 43.0 44.2 45.1 45.9 46.7 47.1 47.5 48.6 48.7 48.8 49.1 49.1 49.3 49.4 49.4 49.6 50.0 50.5 50.4 52.4 52.5 53.8 55.0 56.2 57.4 58.6 59.3 60.6 61.2 61.3 61.4 61.9 62.0 62.0 61.9 55.2 54.3 49.1 54.5 51.6 50.3 48.7 48.6 47.8 47.4 47.9 47.2 45.7 45.2 45.4 45.1 43.5 42.8 42.0 41.7 40.9 40.1 40.0 38.7 38.0 37.4 36.8 36.4 35.2 34.3 34.0 33.9 34.0 34.0 32.7 31.8 30.8 29.8 28.7 26.9 26.2 24.6 23.2 22.4 21.5 20.2 19.5 18.7 18.1 16.9 15.5 12.1 8.7 7.6 5.9 3.7 1.8 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 3.0 9.9 12.2 14.0 17.0 17.6 18.2 20.3 22.4 23.6 23.7 23.0 22.0 23.1 25.9 28.4 29.8 32.1 34.0 35.8 37.8 39.2 40.6 41.4 41.8 44.0 48.4 50.5 51.2 52.4 53.4 54.3 56.6 58.3 59.7 61.6 62.8 62.7 63.2 63.9 63.9 63.8 63.8 63.7 63.8 62.4 61.5 60.5 59.8 59.0 59.3 59.3 59.0 58.8 56.8 55.9 55.0 54.6 54.2 53.3 51.3 50.0 47.5 45.0 42.4 40.8 41.2 42.2 43.4 43.5 45.2 45.9 47.1 48.0 47.5 48.3 50.0 51.2 52.5 53.8 54.5 55.0 58.1 58.8 59.7 60.6 61.4 63.2 64.4 65.0 65.1 65.6 66.1 67.5 68.4 69.2 70.1 70.5 70.6 71.0 71.2 70.6 69.9 70.3 69.9 69.6 67.0 65.9 64.8 64.3 63.9 63.2 62.2 61.7 61.7 61.3 59.5 58.5 57.5 56.1 54.8 53.6 52.2 51.0 50.1 49.4 49.1 50.6 51.0 50.6 50.0 49.2 48.6 48.5 48.4 48.4 48.8 49.5 50.2 50.2 50.4 51.7 52.9 54.0 54.9 55.0 56.0 56.2 58.3 59.1 59.7 59.7 59.8 60.1 54.4 54.5 54.6 55.7 56.1 58.6 58.5 58.2 58.3 58.1 58.5 58.0 52.2 49.7 48.1 43.5 37.5 33.8 29.2 26.3 28.3 30.4 31.2 32.0 34.4 35.8 37.3 36.9 34.8 33.4 32.0 28.6 25.1 22.5 21.4 19.5 16.7 13.5 13.0 16.2 20.5 25.4 29.1 32.6 34.3 35.7 39.1 42.8 46.5 49.3 51.8 52.1 52.6 54.2 54.7 58.0 59.7 59.6 59.5 58.9 57.8 57.7 56.5 56.3 55.8 55.6 54.5 54.0 53.2 53.3 53.3 53.1 52.4 52.2 51.2 48.8 46.2 44.7 43.2 40.5 37.9 35.4 34.0 33.4 31.6 31.5 32.8 33.1 34.3 35.1 34.6 30.7 25.9 21.3 17.4 14.0 12.7 11.6 10.4 9.5 9.2 8.8 9.0 8.9 9.1 8.8 9.0 8.9 8.8 8.9 9.2 9.1 7.8 8.7 9.2 9.3 9.5 9.0 9.2 9.5 9.3 9.1 8.9 9.3 9.4 9.3 9.7 10.1 10.3 12.5 15.6 17.3 18.3 21.6 24.5 26.5 27.2 27.5 27.4 26.6 22.9 18.7 15.6 15.1 18.3 21.2 23.7 25.0 27.8 30.9 33.7 36.2 37.0 37.6 38.9 39.9 39.8 38.5 35.4 33.5 31.8 28.8 28.4 26.0 23.3 19.9 17.6 16.0 15.0 17.1 18.9 20.9 23.0 24.0 24.0 23.1 23.5 20.6 17.0 11.9 6.9 3.8 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 2.9 5.8 9.1 11.9 14.3 15.9 16.3 17.3 17.9 18.7 19.2 19.6 20.8 22.2 21.7 21.2 21.6 23.1 24.7 26.1 27.0 27.7 28.1 28.3 28.3 28.5 28.4 28.4 28.5 28.3 27.5 26.8 25.8 24.7 23.8 23.4 23.3 24.1 25.0 25.7 26.0 26.1 26.2 26.3 25.7 24.5 23.5 22.2 20.5 19.4 18.6 18.9 19.7 21.0 20.6 25.1 27.2 31.2 34.1 36.4 36.8 37.4 38.5 39.8 41.0 42.4 43.6 44.9 46.5 47.5 47.5 47.8 47.6 48.4 49.1 49.8 50.6 51.2 51.6 51.8 51.7 50.1 47.0 45.2 41.1 35.9 30.6 30.0 27.7 24.8 23.8 23.8 23.5 23.4 23.7 23.4 25.3 27.5 29.7 32.3 34.3 35.6 36.3 37.3 37.0 36.5 36.0 35.3 35.0 34.4 32.9 28.9 26.6 26.0 24.5 20.4 18.8 18.1 16.6 15.6 15.3 15.0 15.2 15.3 15.2 15.6 15.9 16.3 16.7 17.2 17.6 18.2 18.8 19.7 20.3 22.6 25.2 26.3 28.0 30.3 31.4 33.2 35.1 36.5 37.3 38.1 38.2 38.3 39.3 40.3 44.3 45.3 46.1 47.5 48.3 48.3 47.7 47.8 48.6 49.8 50.7 52.1 54.2 56.5 58.8 60.5 62.7 65.4 67.3 69.6 71.5 73.6 74.9 75.9 76.0 76.3 77.1 77.9 78.5 78.6 78.5 78.4 78.4 78.3 78.3 78.3 78.2 77.8 76.9 75.7 74.3 73.3 72.9 72.8 72.7 72.8 73.2 74.0 76.6 79.5 82.5 85.1 87.3 89.2 90.7 90.9 90.8 90.9 90.9 90.8 90.9 90.7 90.4 90.6 90.7 89.2 87.9 86.3 85.1 84.0 82.9 81.7 79.8 79.7 80.1 80.6 80.3 82.3 81.7 81.6 80.6 81.2 76.6 74.9 73.8 72.1 69.5 67.2 65.1 63.4 59.9 60.2 57.0 56.0 54.7 54.2 54.0 53.6 53.3 52.5 51.9 51.2 50.7 50.2 49.4 48.9 48.3 49.2 50.0 51.4 52.8 53.3 54.2 54.4 53.8 53.2 52.6 49.0 45.0 39.5 34.7 32.4 31.7 31.0 31.1 30.5 30.6 30.8 33.5 36.4 39.4 42.2 44.9 47.8 50.3 51.3 50.9 50.7 51.2 52.7 54.1 55.6 57.4 60.7 65.0 66.0 66.7 67.9 69.6 71.5 73.6 75.7 78.2 80.8 83.8 86.5 88.4 90.7 93.0 93.7 93.7 95.0 97.3 99.3 101.1 102.3 101.9 103.0 104.6 106.4 107.9 109.2 110.2 110.6 110.6 110.9 111.4 111.9 112.3 112.7 113.4 113.7 114.0 114.0 113.5 113.2 113.2 113.0 112.4 111.8 110.4 109.2 109.6 107.7 107.8 109.3 108.3 105.4 101.7 100.2 98.9 97.8 97.1 96.4 95.3 93.2 90.9 87.4 82.6 77.7 75.3 75.4 73.0 73.4 71.9 67.5 63.1 59.1 52.9 49.5 46.3 47.2 50.2 53.8 57.7 59.7 62.2 65.5 66.4 65.4 65.0 63.3 62.7 61.1 59.5 56.9 52.1 46.5 41.8 36.3 31.5 26.7 23.4 20.5 16.2 14.8 14.1 13.5 12.7 12.3 12.0 11.2 11.2 10.7 9.8 8.2 2.9 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0"
    v_single = np.array([float(x) for x in raw_speeds.split()])
    v_kmh = np.tile(v_single, cycles)
    t_all = np.arange(0, len(v_kmh))
    return t_all, v_kmh

# ================= 3. 需求功率计算 =================
def calculate_req_power(vp, v_kmh):
    dt = 1.0
    v_ms = v_kmh / 3.6
    a_ms2 = np.gradient(v_ms, dt)
    a_ms2[0] = 0
    P_roll = vp.m * vp.g * vp.f * v_ms
    P_aero = 0.5 * vp.rho * vp.Cd * vp.A * (v_ms**3)
    P_acc = vp.m * vp.delta * v_ms * a_ms2
    P_req = (P_roll + P_aero + P_acc) / (vp.eta_T * vp.eta_m) / 1000
    P_req = np.where(P_req < 0, np.maximum(P_req, -60) * 0.6, P_req)
    return P_req, v_ms, a_ms2

def precompute_eng_fc_table(vp):
    p_grid = np.arange(0, vp.P_eng_max + 0.1, 0.5)
    fc_grid = np.array([float(vp.eng_fc_interp(p)) if p > 0 else 0.0 for p in p_grid])
    return p_grid, fc_grid

# ================= 4. 普通 ECMS 控制策略仿真 =================
def simulate_ECMS_fast(vp, P_req, s, p_grid, fc_grid):
    dt = 1.0
    SOC = vp.SOC_init
    T = vp.T_amb
    total_fuel_g = 0.0
    total_kWh_bat = 0.0
    T_max = T
    fuel_consumed_L = 0.0
    actual_steps = 0
    k_elec = 375.0 / 3600.0
    N = len(P_req)
    hist_soc = np.zeros(N)
    hist_p_eng = np.zeros(N)
    hist_p_bat = np.zeros(N)
    hist_p_req = np.zeros(N)
    hist_T = np.zeros(N)

    for t in range(N):
        if vp.fuel_remaining_L <= 0 and SOC <= vp.SOC_min:
            break
        actual_steps += 1
        p_req = P_req[t]

        if p_req < 0:
            P_eng = 0.0
            P_bat = max(p_req, -30.0)
            if SOC >= vp.SOC_max:
                P_bat = 0.0
        else:
            max_p_eng = min(vp.P_eng_max, p_req + 30.0)
            n_scan = int(max_p_eng / 0.5) + 1
            p_eng_arr = p_grid[:n_scan]
            p_bat_arr = p_req - p_eng_arr
            fc_arr = fc_grid[:n_scan]
            mask = np.ones(n_scan, dtype=bool)
            if SOC <= vp.SOC_min:
                mask &= (p_bat_arr <= 0.01)
            if SOC >= vp.SOC_max:
                mask &= (p_bat_arr >= -0.01)
            mask &= (p_bat_arr <= 60.0) & (p_bat_arr >= -30.0)
            cost_arr = fc_arr + s * p_bat_arr * k_elec
            cost_arr[~mask] = np.inf
            idx = np.argmin(cost_arr)
            if cost_arr[idx] == np.inf:
                P_eng = min(vp.P_eng_max, p_req)
                P_bat = p_req - P_eng
                if SOC <= vp.SOC_min and P_bat > 0:
                    P_eng = min(vp.P_eng_max, p_req)
                    P_bat = max(0.0, p_req - P_eng)
                if SOC >= vp.SOC_max and P_bat < 0:
                    P_bat = max(0.0, p_req - P_eng)
                P_bat = np.clip(P_bat, -30, 60)
            else:
                P_eng = p_eng_arr[idx]
                P_bat = p_bat_arr[idx]

        if P_eng > 0:
            fuel_g_per_s = float(vp.eng_fc_interp(P_eng))
            total_fuel_g += fuel_g_per_s * dt
            fuel_consumed_L = total_fuel_g / (vp.fuel_density * 1000)
            vp.fuel_remaining_L = vp.fuel_tank_L - fuel_consumed_L

        I_bat = (P_bat * 1000) / vp.V_nom
        dSOC = (I_bat * dt) / (3600 * vp.Cap_Ah)
        SOC_new = SOC - dSOC
        SOC_clipped = np.clip(SOC_new, vp.SOC_min, vp.SOC_max)
        if abs(SOC_clipped - SOC_new) > 1e-8:
            dSOC_actual = SOC - SOC_clipped
            I_bat_actual = dSOC_actual * 3600 * vp.Cap_Ah / dt
            P_bat_actual = I_bat_actual * vp.V_nom / 1000
            total_kWh_bat += P_bat_actual * dt / 3600
        else:
            total_kWh_bat += P_bat * dt / 3600
        SOC = SOC_clipped

        Q_gen = (I_bat**2) * vp.R0
        T += dt * Q_gen / vp.C_th
        if T > T_max:
            T_max = T

        hist_soc[t] = SOC
        hist_p_eng[t] = P_eng
        hist_p_bat[t] = P_bat
        hist_p_req[t] = p_req
        hist_T[t] = T

    return (total_fuel_g, total_kWh_bat, SOC, T, T_max, fuel_consumed_L, actual_steps,
            hist_soc[:actual_steps], hist_p_eng[:actual_steps], hist_p_bat[:actual_steps],
            hist_p_req[:actual_steps], hist_T[:actual_steps])

# ================= 5. 运行与输出 =================
cycles = 60
T_amb = 35.0
t_all, v = get_cltc_p_data(cycles=cycles)
dt = 1.0
vp0 = VehicleParams(T_amb=T_amb, SOC_init=0.6)
P_req, v_ms, a_ms2 = calculate_req_power(vp0, v)
p_grid, fc_grid = precompute_eng_fc_table(vp0)

# 【修改1】等效因子改为 1, 1.2, 1.4, 1.8, 2
s_list = [1, 1.2, 1.4, 1.8, 2]
# 【修改2】颜色字典键值同步修改
colors = {1:'blue', 1.2:'red', 1.4:'green', 1.8:'purple', 2:'orange'}
linestyles = {0.4:'--', 0.6:'-'}

results = []
sim_data = {}

# 循环两种初始SOC
for soc_init in [0.4, 0.6]:
    sim_data[soc_init] = {}
    for s in s_list:
        vp = VehicleParams(T_amb=T_amb, SOC_init=soc_init)
        f_g, e_kWh, soc_end, t_end, t_max, fuel_consumed, actual_steps, h_soc, h_pe, h_pb, h_pr, h_T = simulate_ECMS_fast(vp, P_req, s, p_grid, fc_grid)
        distance_km = np.sum(v_ms[:actual_steps] * dt) / 1000
        h_pm = h_pr - h_pe
        sim_data[soc_init][s] = {
            't': t_all[:actual_steps],
            'soc': h_soc,
            'p_eng': h_pe,
            'p_motor': h_pm,
            'p_bat': h_pb,
            'p_req': h_pr,
            'T': h_T
        }
        results.append({
            "初始SOC": soc_init,
            "等效因子": s,
            "行驶里程": round(distance_km, 2),
            "终止SOC": round(soc_end, 3),
            "终止温度(℃)": round(t_end, 1),
            "最高温度(℃)": round(t_max, 1),
            "燃油消耗(L)": round(fuel_consumed, 2),
            "电能净消耗": round(e_kWh, 1),
            "等效油耗(L/100km)": round((fuel_consumed + e_kWh*0.5)/distance_km * 100, 2)
        })

df = pd.DataFrame(results)
print(f"=== ECMS 策略评价表 (CLTC-P {cycles}次循环, T={T_amb}℃, 初始SOC分0.4和0.6) ===")
print(df.to_string(index=False))

# ================= 生成5张独立对比图 =================
ds = 10

# 图1: SOC变化曲线
fig, ax = plt.subplots(figsize=(14, 5))
for soc_init in [0.4, 0.6]:
    for s in s_list:
        ax.plot(sim_data[soc_init][s]['t'][::ds]/60, np.array(sim_data[soc_init][s]['soc'][::ds])*100,
                color=colors[s], linestyle=linestyles[soc_init], linewidth=1.2, label=f'init={soc_init}, s={s}')
ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='SOC_min (50%)')
ax.axhline(y=70, color='gray', linestyle='--', alpha=0.5, label='SOC_max (70%)')
ax.set_title('SOC Variation Curves under Different Initial SOC and Equivalent Factors', fontsize=14, fontweight='bold')
ax.set_xlabel('Time (min)')
ax.set_ylabel('SOC (%)')
ax.legend(loc='upper right', ncol=2)
ax.grid(True, alpha=0.3)
ax.set_ylim(30, 80)
plt.tight_layout()
plt.savefig('01_soc.png', dpi=150)
plt.close()
print("已生成: 01_soc.png")

# 图2: 发动机功率曲线
fig, ax = plt.subplots(figsize=(14, 5))
for soc_init in [0.4, 0.6]:
    for s in s_list:
        ax.plot(sim_data[soc_init][s]['t'][::ds]/60, np.array(sim_data[soc_init][s]['p_eng'][::ds]),
                color=colors[s], linestyle=linestyles[soc_init], linewidth=1.2, label=f'init={soc_init}, s={s}')
ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
ax.set_title('Engine Power Curves under Different Initial SOC and Equivalent Factors', fontsize=14, fontweight='bold')
ax.set_xlabel('Time (min)')
ax.set_ylabel('Engine Power (kW)')
ax.legend(loc='upper right', ncol=2)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('02_engine_power.png', dpi=150)
plt.close()
print("已生成: 02_engine_power.png")

# 图3: 电机功率曲线
fig, ax = plt.subplots(figsize=(14, 5))
for soc_init in [0.4, 0.6]:
    for s in s_list:
        ax.plot(sim_data[soc_init][s]['t'][::ds]/60, np.array(sim_data[soc_init][s]['p_motor'][::ds]),
                color=colors[s], linestyle=linestyles[soc_init], linewidth=1.2, label=f'init={soc_init}, s={s}')
ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
ax.set_title('Motor Power Curves under Different Initial SOC and Equivalent Factors', fontsize=14, fontweight='bold')
ax.set_xlabel('Time (min)')
ax.set_ylabel('Motor Power (kW)')
ax.legend(loc='upper right', ncol=2)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('03_motor_power.png', dpi=150)
plt.close()
print("已生成: 03_motor_power.png")

# 图4: 电池功率曲线
fig, ax = plt.subplots(figsize=(14, 5))
for soc_init in [0.4, 0.6]:
    for s in s_list:
        ax.plot(sim_data[soc_init][s]['t'][::ds]/60, np.array(sim_data[soc_init][s]['p_bat'][::ds]),
                color=colors[s], linestyle=linestyles[soc_init], linewidth=1.2, label=f'init={soc_init}, s={s}')
ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
ax.set_title('Battery Power Curves under Different Initial SOC and Equivalent Factors', fontsize=14, fontweight='bold')
ax.set_xlabel('Time (min)')
ax.set_ylabel('Battery Power (kW)')
ax.legend(loc='upper right', ncol=2)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('04_battery_power.png', dpi=150)
plt.close()
print("已生成: 04_battery_power.png")

# 图5: 电池温度曲线
fig, ax = plt.subplots(figsize=(14, 5))
for soc_init in [0.4, 0.6]:
    for s in s_list:
        ax.plot(sim_data[soc_init][s]['t'][::ds]/60, np.array(sim_data[soc_init][s]['T'][::ds]),
                color=colors[s], linestyle=linestyles[soc_init], linewidth=1.2, label=f'init={soc_init}, s={s}')
ax.axhline(y=T_amb, color='gray', linestyle='--', alpha=0.5, label=f'T_amb ({T_amb}℃)')
ax.set_title('Battery Temperature Curves under Different Initial SOC and Equivalent Factors (Adiabatic)', fontsize=14, fontweight='bold')
ax.set_xlabel('Time (min)')
ax.set_ylabel('Temperature (℃)')
ax.legend(loc='upper right', ncol=2)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('05_battery_temp.png', dpi=150)
plt.close()
print("已生成: 05_battery_temp.png")

print("\n所有5张对比图已生成完毕！")

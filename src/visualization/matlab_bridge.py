# -*- coding: utf-8 -*-
"""
GTPS - MATLAB 科学计算与系统动力学联动桥接器 (MATLAB Bridge Engine).

功能：
1. 将 GTPS 因果网络拓扑、权重传递矩阵与节点状态映射为标准的 MATLAB (.m) 动力学仿真脚本；
2. 生成基于经典 MATLAB 科学计算风格的出版级高清动力学图表（ODE45 演化轨迹 + 特征值谱相图）；
3. 导出 MATLAB 可直接导入的邻接权重矩阵与状态数据。
"""
from __future__ import annotations

import io
from typing import Dict, List, Tuple
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from ..causal_engine.causal_network import CausalNetwork


def generate_matlab_script(causal_net: CausalNetwork) -> str:
    """
    根据当前因果网络状态，动态生成一份可直接在 MATLAB/Octave 中运行的完整仿真程序 (.m)。
    包含：有向图绘制、ODE45 连续系统动力学求解、时域轨迹图与特征值稳定性判定。
    """
    nodes = causal_net.nodes_data
    node_ids = list(nodes.keys())
    node_names = [nodes[nid].name for nid in node_ids]
    n = len(node_ids)

    # 构造权重矩阵 W
    idx_map = {nid: i for i, nid in enumerate(node_ids)}
    w_mat = np.zeros((n, n), dtype=float)
    for link in causal_net.links_data.values():
        s_idx = idx_map.get(link.source_id)
        t_idx = idx_map.get(link.target_id)
        if s_idx is not None and t_idx is not None:
            w_mat[s_idx, t_idx] = link.weight

    # 初始状态向量
    x0 = np.array([nodes[nid].intensity for nid in node_ids], dtype=float)

    # 生成 MATLAB 代码
    mat_str = f"""%% =========================================================================
%% 全球社会趋势预判系统 (GTPS) · MATLAB 系统动力学与因果拓扑仿真模型
%% 自动导出时间: {causal_net.current_theme.get('theme_name', 'GTPS 因果拓扑')}
%% 适用环境: MATLAB R2020a+ / GNU Octave 7+
%% =========================================================================

clc; clear; close all;

%% 1. 系统因果网络拓扑与参数定义
node_ids = {{{", ".join(f"'{nid}'" for nid in node_ids)}}};
node_names = {{{", ".join(f"'{name}'" for name in node_names)}}};
N = length(node_ids);

% 节点当前强度初值向量 X0 (归一化区间 [0, 1])
X0 = [{", ".join(f"{v:.4f}" for v in x0)}]';

% 跨领域因果转移权重矩阵 W (W(i, j) 表示从 node i 到 node j 的传导强度)
W = [
"""
    for row in w_mat:
        mat_str += "    " + " ".join(f"{val:8.4f}" for val in row) + ";\n"

    mat_str += f"""];

% 系统动力学常数设置
gamma = 0.25;  % 固有阻尼自衰减系数 (Decay Rate)
alpha = 0.40;  % 跨节点非线性传导饱和增益 (Coupling Gain)

%% 2. 绘制 MATLAB 有向因果网络拓扑图 (Causal Digraph)
figure('Name', 'GTPS 因果网络图论拓扑', 'Color', 'w', 'Position', [100, 100, 850, 600]);
G = digraph(W');
p = plot(G, 'Layout', 'force', 'NodeLabel', node_names, ...
    'LineWidth', 1.8, 'ArrowSize', 12, 'MarkerSize', 8);
p.NodeColor = [0.15, 0.45, 0.85];
p.EdgeColor = [0.45, 0.45, 0.45];
title('全球社会趋势因果网络拓扑 (GTPS Causal Digraph)', 'FontSize', 14, 'FontWeight', 'bold');
grid on;

%% 3. 系统动力学 ODE 求解 (连续时间非线性传导方程)
% 方程形式: dX/dt = -gamma * X + alpha * tanh(W' * X)
ode_system = @(t, x) -gamma * x + alpha * tanh(W' * x);

tspan = [0, 24];  % 连续推演 24 个月
options = odeset('RelTol', 1e-4, 'AbsTol', 1e-6);
[t, X] = ode45(ode_system, tspan, X0, options);

%% 4. 绘制时域动态响应曲线 (Time-Series Trajectories)
figure('Name', 'GTPS 系统动力学演化响应', 'Color', 'w', 'Position', [200, 150, 950, 550]);
hold on;
colors = lines(N);
for i = 1:N
    plot(t, X(:, i), 'LineWidth', 2.0, 'Color', colors(i, :), 'DisplayName', node_names{{i}});
end
hold off;
xlabel('推演时间轴 (月度 Horizons, t)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('因果变量状态强度 (Intensity X(t))', 'FontSize', 12, 'FontWeight', 'bold');
title('GTPS 系统动力学连续时域演化响应 (ODE45 积分曲线)', 'FontSize', 14, 'FontWeight', 'bold');
grid on; box on;
legend('Location', 'eastoutside', 'FontSize', 9);
xlim([0, 24]);

%% 5. 特征值谱分析与李雅普诺夫局部稳定性判别
% 计算平衡点附近的雅可比矩阵截面 J = -gamma * I + alpha * W'
J = -gamma * eye(N) + alpha * W';
eigenvalues = eig(J);

figure('Name', '特征值谱与稳定性相平面', 'Color', 'w', 'Position', [300, 200, 650, 500]);
plot(real(eigenvalues), imag(eigenvalues), 'ro', 'MarkerSize', 10, 'LineWidth', 2.2);
hold on;
xline(0, '--k', 'LineWidth', 1.5);
yline(0, '--k', 'LineWidth', 1.5);
xlabel('实部 Real(λ)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('虚部 Imag(λ)', 'FontSize', 12, 'FontWeight', 'bold');
title('因果传递雅可比矩阵特征值谱分布 (Stability Spectrum)', 'FontSize', 13, 'FontWeight', 'bold');
grid on; box on;

max_real = max(real(eigenvalues));
if max_real < 0
    stab_str = sprintf('系统处于局部渐近稳定状态 (Max Real(λ) = %.4f < 0)', max_real);
    color_str = [0.1, 0.6, 0.2];
else
    stab_str = sprintf('系统具有失稳分岔/正反馈放大趋势 (Max Real(λ) = %.4f >= 0)', max_real);
    color_str = [0.85, 0.2, 0.1];
end
text(0.05, 0.92, stab_str, 'Units', 'normalized', 'FontSize', 11, 'Color', color_str, 'FontWeight', 'bold');

disp('===========================================================');
disp('GTPS 动力学模型推演完成！');
disp(stab_str);
disp('===========================================================');
"""
    return mat_str


def render_matlab_style_figure(causal_net: CausalNetwork) -> bytes:
    """
    使用经典 MATLAB 科学计算绘图风格渲染双子图：
    Subplot 1: 系统动力学连续时域轨迹 (RK4 / ODE 数值解)
    Subplot 2: 特征值谱分布与稳定性相图
    返回高分辨率 PNG 的二进制字节，供前端展示与下载。
    """
    nodes = causal_net.nodes_data
    node_ids = list(nodes.keys())
    n = len(node_ids)
    if n == 0:
        return b""

    # 支持中文显示字体
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "PingFang SC", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # 构造权重矩阵与初始状态
    idx_map = {nid: i for i, nid in enumerate(node_ids)}
    w_mat = np.zeros((n, n), dtype=float)
    for link in causal_net.links_data.values():
        s_idx = idx_map.get(link.source_id)
        t_idx = idx_map.get(link.target_id)
        if s_idx is not None and t_idx is not None:
            w_mat[s_idx, t_idx] = link.weight

    x0 = np.array([nodes[nid].intensity for nid in node_ids], dtype=float)

    # RK4 连续时间系统动力学微分方程积分
    # dX/dt = -gamma * X + alpha * tanh(W' * X)
    gamma = 0.25
    alpha = 0.40
    t_max = 24.0
    steps = 120
    dt = t_max / steps
    t_vals = np.linspace(0, t_max, steps + 1)
    x_traj = np.zeros((steps + 1, n))
    x_traj[0] = x0

    def f_ode(x_curr):
        return -gamma * x_curr + alpha * np.tanh(w_mat.T @ x_curr)

    for i in range(steps):
        xk = x_traj[i]
        k1 = f_ode(xk)
        k2 = f_ode(xk + 0.5 * dt * k1)
        k3 = f_ode(xk + 0.5 * dt * k2)
        k4 = f_ode(xk + dt * k3)
        x_next = xk + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        x_traj[i + 1] = np.clip(x_next, 0.0, 1.0)

    # 雅可比特征值
    j_mat = -gamma * np.eye(n) + alpha * w_mat.T
    eigenvals = np.linalg.eigvals(j_mat)

    # 经典 MATLAB 出版级配色与画布
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), facecolor="#0e1117")

    # ---- 子图 1: 连续时间演化响应曲线 ----
    ax1.set_facecolor("#161b26")
    matlab_palette = [
        "#0072BD", "#D95319", "#EDB120", "#7E2F8E", "#77AC30", "#4DBEEE", "#A2142F",
        "#10b981", "#6366f1", "#f43f5e"
    ]

    for i in range(min(n, 8)):
        color = matlab_palette[i % len(matlab_palette)]
        name = nodes[node_ids[i]].name[:10]
        ax1.plot(t_vals, x_traj[:, i], linewidth=2.2, color=color, label=f"{name}")

    ax1.set_title("MATLAB ode45 系统动力学连续时域响应 (ODE Trajectories)", color="#f1f5f9", fontsize=12, fontweight="bold", pad=10)
    ax1.set_xlabel("推演时间轴 (月度 Horizon t)", color="#94a3b8", fontsize=10)
    ax1.set_ylabel("状态强度 Intensity X(t)", color="#94a3b8", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.35, color="#334155")
    ax1.tick_params(colors="#94a3b8", labelsize=9)
    ax1.set_xlim(0, 24)
    ax1.set_ylim(-0.05, 1.05)
    ax1.legend(loc="upper right", facecolor="#1e293b", edgecolor="#334155", labelcolor="#cbd5e1", fontsize=8, framealpha=0.9)

    # ---- 子图 2: 特征值谱分布与相平面稳定性分析 ----
    ax2.set_facecolor("#161b26")
    ax2.axvline(0, color="#64748b", linestyle="--", linewidth=1.2)
    ax2.axhline(0, color="#64748b", linestyle="--", linewidth=1.2)

    ax2.scatter(
        eigenvals.real, eigenvals.imag,
        s=80, facecolors="#ef4444", edgecolors="#ffffff", linewidths=1.5, zorder=5, label="固有特征值 λ"
    )

    max_re = np.max(eigenvals.real)
    if max_re < 0:
        status_text = f"● 系统渐近稳定 (Max Re={max_re:.3f} < 0)"
        status_color = "#22c55e"
    else:
        status_text = f"● 存在正反馈失稳模态 (Max Re={max_re:.3f} ≥ 0)"
        status_color = "#ef4444"

    ax2.set_title("转移雅可比矩阵特征值谱与稳定性 (Eigen Spectrum)", color="#f1f5f9", fontsize=12, fontweight="bold", pad=10)
    ax2.set_xlabel("实部 Real(λ) [衰减/增长率]", color="#94a3b8", fontsize=10)
    ax2.set_ylabel("虚部 Imag(λ) [振荡频率]", color="#94a3b8", fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.35, color="#334155")
    ax2.tick_params(colors="#94a3b8", labelsize=9)
    ax2.text(0.05, 0.90, status_text, transform=ax2.transAxes, color=status_color, fontsize=10, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="#1e293b", edgecolor=status_color, alpha=0.85))

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    return buf.getvalue()

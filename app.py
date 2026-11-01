"""
全球社会趋势预判系统 (Global Trend Prediction System - GTPS)
Web 可视化交互大屏与动态推演控制台
"""
import sys
import os

# 确保 UTF-8 兼容
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

from src.core.models import DomainCategory, ModalityType
from src.collector.news_collector import DailyNewsCollector
from src.collector.market_data import MarketDataCollector, CrossCheckFilter
from src.causal_engine.causal_network import CausalNetwork
from src.causal_engine.theme_synthesizer import ThemeSynthesizer
from src.causal_engine.analogy_engine import HistoricalAnalogyEngine
from src.causal_engine.reflexivity_engine import ReflexivityEngine
from src.simulation.agent_sandbox import MultiAgentSandbox
from src.simulation.llm_wargame import LLMClient, LLMWarGameEngine, PERSONAS
from src.forecasting.scenario_engine import ScenarioForecastEngine
from src.visualization.graph_visualizer import (
    render_causal_graph_html,
    render_entity_knowledge_graph_html,
)
from src.visualization.matlab_bridge import (
    generate_matlab_script,
    render_matlab_style_figure,
)

# 页面基础配置
st.set_page_config(
    page_title="全球社会趋势预判系统 · 态势感知与推演中心",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义高质感科技感 CSS 样式
st.markdown("""
<style>
    .main {
        background-color: #0b0f19;
    }
    .metric-card {
        background: linear-gradient(135deg, #131b2e 0%, #17223b 100%);
        padding: 16px 20px;
        border-radius: 10px;
        border: 1px solid #233354;
        margin-bottom: 12px;
    }
    .metric-title {
        color: #8fa0be;
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 26px;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-delta {
        font-size: 13px;
        margin-top: 4px;
    }
    .event-card {
        background-color: #111827;
        border: 1px solid #1f293d;
        border-left: 4px solid #3b82f6;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .event-card-energy { border-left-color: #f59e0b; }
    .event-card-tech { border-left-color: #8b5cf6; }
    .event-card-politics { border-left-color: #ef4444; }
    .event-card-economy { border-left-color: #10b981; }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 8px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
    }
    .debate-card {
        background-color: #111827;
        border: 1px solid #1f293d;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .market-pill {
        background: linear-gradient(135deg, #0f1a2d 0%, #1a2544 100%);
        border: 1px solid #2a3a60;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: center;
    }
    .verify-badge-substantiate {
        display: inline-block; background-color: #064e3b; color: #6ee7b7;
        border-radius: 4px; padding: 4px 10px; font-size: 12px; font-weight: 600;
        border: 1px solid #065f46; margin-top: 8px;
    }
    .verify-badge-noise {
        display: inline-block; background-color: #374151; color: #d1d5db;
        border-radius: 4px; padding: 4px 10px; font-size: 12px; font-weight: 600;
        border: 1px solid #4b5563; margin-top: 8px;
    }
    .verify-badge-missing {
        display: inline-block; background-color: #78350f; color: #fcd34d;
        border-radius: 4px; padding: 4px 10px; font-size: 12px; font-weight: 600;
        border: 1px solid #92400e; margin-top: 8px;
    }

    /* ===== 移动端专属响应式自适应布局 (@media max-width: 768px) ===== */
    @media (max-width: 768px) {
        /* 紧凑化内边距，释放屏幕空间 */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }
        /* 行情胶囊与KPI指标卡：手机端转为双列紧凑自适应网格，不再横向挤扁成 6 列 */
        div[data-testid="column"] {
            min-width: 47% !important;
            flex: 1 1 45% !important;
            margin-bottom: 6px !important;
        }
        .market-pill {
            padding: 8px 6px !important;
            border-radius: 6px !important;
        }
        .market-pill div:nth-child(1) {
            font-size: 10px !important;
        }
        .market-pill div:nth-child(2) {
            font-size: 15px !important;
        }
        .market-pill div:nth-child(3) {
            font-size: 11px !important;
        }
        .metric-card {
            padding: 10px 12px !important;
            margin-bottom: 8px !important;
        }
        .metric-title {
            font-size: 11px !important;
        }
        .metric-value {
            font-size: 20px !important;
            margin-top: 2px !important;
        }
        .metric-delta {
            font-size: 11px !important;
        }
        /* 图谱画布在手机端自适应舒适高度，避免滑屏阻断 */
        iframe {
            max-height: 400px !important;
        }
        /* 标签页横向滑动优化 */
        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            padding-bottom: 6px !important;
            scrollbar-width: thin;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 6px 12px !important;
            font-size: 12px !important;
            white-space: nowrap !important;
        }
    }
    
    /* 靶向质询问答专属样式 */
    .inquiry-bubble {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #3b82f6;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 12px 0 16px 0;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }
    .inquiry-resp-card {
        background-color: #111827;
        border: 1px solid #1f293d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 Session State
if "collector" not in st.session_state:
    st.session_state.collector = DailyNewsCollector()

if "market_collector" not in st.session_state:
    st.session_state.market_collector = MarketDataCollector(timeout=6)

if "market_snapshot" not in st.session_state:
    st.session_state.market_snapshot = st.session_state.market_collector.get_live_market_snapshot()

if "theme_collector" not in st.session_state:
    st.session_state.theme_collector = ThemeSynthesizer()

if "causal_net" not in st.session_state:
    st.session_state.causal_net = CausalNetwork()
    # ---- 双重输入：新闻事件 + 硬资产行情联动 ----
    # 1. 将今日真实捕获的高烈度事件注入因果网络初态
    for evt in st.session_state.collector.collected_events[:10]:
        for node_id, delta in evt.affected_nodes.items():
            st.session_state.causal_net.apply_node_impulse(
                node_id=node_id,
                impulse=delta * 0.35,
                reason=f"今日实时网络事件: {evt.title}"
            )
    # 2. 原油与天然气硬资产涨跌 → 通用映射：找 ECONOMY/ENERGY 域节点
    _net = st.session_state.causal_net
    _econ_nodes = [nid for nid, n in _net.nodes_data.items() if n.domain.value.upper() == "ECONOMY"]
    _energy_nodes = [nid for nid, n in _net.nodes_data.items() if n.domain.value.upper() == "ENERGY"]
    snap = st.session_state.market_snapshot
    oil = snap.get("hf_OIL")
    natgas = snap.get("hf_NG")
    if oil and abs(oil.change_pct) > 0.3:
        oil_delta = max(-0.2, min(0.2, oil.change_pct * 0.04))
        # 通用映射：优先用硬编码兼容 ID，否则用 ECONOMY 域第一个节点
        _price_node = "POWER_WHOLESALE_PRICE" if "POWER_WHOLESALE_PRICE" in _net.nodes_data else (_econ_nodes[0] if _econ_nodes else None)
        _stress_node = "GRID_TRANSMISSION_STRESS" if "GRID_TRANSMISSION_STRESS" in _net.nodes_data else (_energy_nodes[0] if _energy_nodes else None)
        if _price_node:
            st.session_state.causal_net.apply_node_impulse(
                _price_node, oil_delta,
                reason=f"硬资产联动: 布伦特原油 {'+' if oil.change_pct > 0 else ''}{oil.change_pct:.2f}%"
            )
        if _stress_node and _stress_node != _price_node:
            st.session_state.causal_net.apply_node_impulse(
                _stress_node, oil_delta * 0.6,
                reason=f"硬资产联动: 原油波动→工业负荷传导"
            )
    if natgas and abs(natgas.change_pct) > 0.5:
        gas_delta = max(-0.15, min(0.15, natgas.change_pct * 0.03))
        _price_node = "POWER_WHOLESALE_PRICE" if "POWER_WHOLESALE_PRICE" in _net.nodes_data else (_econ_nodes[0] if _econ_nodes else None)
        if _price_node:
            st.session_state.causal_net.apply_node_impulse(
                _price_node, gas_delta,
                reason=f"硬资产联动: 天然气 {'+' if natgas.change_pct > 0 else ''}{natgas.change_pct:.2f}%"
            )
    st.session_state.causal_net.propagate_dynamics(steps=2)

if "sandbox" not in st.session_state:
    st.session_state.sandbox = MultiAgentSandbox(st.session_state.causal_net)

if "scenario_engine" not in st.session_state:
    st.session_state.scenario_engine = ScenarioForecastEngine(
        st.session_state.causal_net,
        st.session_state.sandbox
    )


# ---------------- 侧边栏：操作控制与突发事件注入 ----------------
with st.sidebar:
    st.markdown("### 🌐 全球趋势推演控制台")
    today_str = datetime.now().strftime("%Y-%m-%d")
    st.caption(f"当前推演基准自然日: **{today_str}**")
    st.markdown("---")

    st.markdown("#### 📡 每日真实国际大事全网采集")
    if st.button("🔄 立即全网重抓今日最新全球大事", use_container_width=True):
        with st.spinner("正在直连全球各领域即时快讯源（政治/军事/财经/科技/能源）..."):
            events = st.session_state.collector.fetch_daily_events()
            # 重新校准因果网络
            for evt in events[:12]:
                for node_id, delta in evt.affected_nodes.items():
                    st.session_state.causal_net.apply_node_impulse(
                        node_id=node_id,
                        impulse=delta * 0.3,
                        reason=f"新拉取实时事件: {evt.title}"
                    )
            st.session_state.causal_net.propagate_dynamics(steps=2)
            st.session_state.sandbox.run_turn(round_num=1)
            st.success(f"全网最新大事件抓取完成！共捕获 {len(events)} 条真实动态。")
            st.rerun()

    # 历史档案回溯
    archive_dir = "data/daily_archive"
    if os.path.exists(archive_dir):
        archive_files = sorted([f for f in os.listdir(archive_dir) if f.endswith(".json")], reverse=True)
        if len(archive_files) > 1:
            st.markdown("#### 📅 历史推演日档案回溯")
            selected_date = st.selectbox("切换历史日期观察大势：", archive_files)

    st.markdown("---")
    st.markdown("#### ⚡ 突发黑天鹅 / What-If 模拟器")
    st.caption("手动注入突发国际事件，测试全局因果连锁反应")

    with st.form("custom_event_form"):
        custom_title = st.text_input("事件标题", value="突发：某国暂停核心电网变压器原材料出口")
        custom_summary = st.text_area(
            "事件简述与影响",
            value="主要产铜国突发罢工叠加矿区政策收紧，全球电网重型变压器交付周期进一步拉长 12 个月。"
        )
        custom_domain = st.selectbox(
            "归属领域",
            [DomainCategory.ENERGY, DomainCategory.TECHNOLOGY, DomainCategory.POLITICS, DomainCategory.ECONOMY],
            format_func=lambda x: f"{x.value.upper()}"
        )
        # 动态生成当前主题的节点下拉选项（避免硬编码 KeyError）
        _cur_nodes = st.session_state.causal_net.nodes_data
        _node_options = [(nid, f"{n.name} ({nid})") for nid, n in _cur_nodes.items()]
        custom_target = st.selectbox(
            "冲击核心因果变量",
            _node_options,
            format_func=lambda x: x[1]
        )
        custom_strength = st.slider("冲击强度 (Delta)", min_value=-0.4, max_value=0.5, value=0.25, step=0.05)
        
        submitted = st.form_submit_button("🚀 注入事件并触发级联推演", use_container_width=True)
        if submitted:
            # 记录事件
            st.session_state.collector.add_custom_event(
                title=custom_title,
                summary=custom_summary,
                domain=custom_domain,
                impact_level=0.90,
                affected_node_id=custom_target[0],
                delta=custom_strength
            )
            # 作用到因果网络
            st.session_state.causal_net.apply_node_impulse(
                node_id=custom_target[0],
                impulse=custom_strength,
                reason=f"用户注入突发事件：{custom_title}"
            )
            # 多主体自主博弈反制
            st.session_state.sandbox.run_turn(round_num=2)
            st.toast("⚡ 突发事件已注入！因果网络与多主体博弈已完成重算！")
            st.rerun()

    st.markdown("---")
    with st.expander("🤖 大模型认知大脑设置", expanded=False):
        st.caption("配置后圆桌对抗由真实 LLM 驱动；留空 Key 自动启用本地高保真参谋模板")
        llm_key = st.text_input("API Key", type="password", placeholder="sk-...（留空 = 本地模板模式）")
        llm_base = st.text_input("Base URL", value="https://api.deepseek.com/v1")
        llm_model = st.text_input("Model Name", value="deepseek-chat")
        st.session_state.llm_config = {"api_key": llm_key, "base_url": llm_base, "model_name": llm_model}
        if st.button("🔌 测试连接", use_container_width=True):
            if not llm_key:
                st.warning("● 未配置 Key · 本地参谋模板模式（三轮对抗功能完整可用）")
            else:
                with st.spinner("正在探测大模型端点..."):
                    try:
                        probe = LLMClient(api_key=llm_key, base_url=llm_base, model_name=llm_model, timeout=10)
                        probe.chat("你是连通性探针", "只回复: ok", max_tokens=5)
                        st.success("● 连接正常 · LIVE LLM 在线推演已就绪")
                    except Exception as e:
                        st.error(f"● 连接失败，推演时将自动降级本地模板：{str(e)[:120]}")

    st.markdown("---")
    # ---- 🌐 战略推演主题中心 ----
    st.markdown("### 🌐 战略推演主题中心")
    all_themes = CausalNetwork().list_builtin_themes()
    theme_display = {t["theme_name"]: t for t in all_themes}
    current_theme_name = st.session_state.causal_net.current_theme.get(
        "theme_name", "AI 算力扩张与能源电网重构"
    )
    selected_name = st.selectbox(
        "当前推演主题",
        list(theme_display.keys()),
        index=list(theme_display.keys()).index(current_theme_name) if current_theme_name in theme_display else 0,
    )
    if st.button("🔄 切换主题并热插拔推演", use_container_width=True, type="secondary"):
        tid = st.session_state.causal_net.load_theme_from_file(theme_display[selected_name]["path"])
        # 主题切换后：因果网络已自动清空重建；同步重建 sandbox 清掉旧 agent/decision_history
        st.session_state.sandbox = MultiAgentSandbox(st.session_state.causal_net)
        st.session_state.pop("wargame_result", None)  # 清掉旧主题的博弈结果
        st.success(f"✅ 主题已切换至 `{tid}`，全局因果拓扑 + 推演框架已热插拔生效！")
        st.rerun()

    with st.expander("✨ 跨主题因果图自生工作台（AI 命题生成器）", expanded=False):
        st.caption("输入任意想推演的国际热点命题，瞬间生成全套因果图谱与红蓝参谋部")
        synth_prompt = st.text_area(
            "命题输入",
            value="中东霍尔木兹海峡石油运力中断与欧美全球通胀传导",
            height=80,
        )
        if st.button("🚀 一键自生该命题的全套因果图谱与红蓝参谋部", use_container_width=True, type="primary"):
            with st.status("✨ AI 自生主题推演中...", expanded=True) as status:
                theme_dict = st.session_state.theme_collector.synthesize_theme_from_prompt(synth_prompt)
                saved_path = st.session_state.theme_collector.save_theme(theme_dict)
                st.session_state.causal_net.load_theme_from_dict(theme_dict)
                # 新主题 → 重建 sandbox + 清掉旧博弈结果
                st.session_state.sandbox = MultiAgentSandbox(st.session_state.causal_net)
                st.session_state.pop("wargame_result", None)
                st.write(f"✅ 主题 JSON 已持久化：{saved_path}")
                st.write(f"✅ 节点数 {len(theme_dict['nodes'])} · 边数 {len(theme_dict['links'])} · 阵营数 {len(theme_dict['personas'])} · 情景数 {len(theme_dict['scenarios'])}")
                status.update(label="🚀 新主题拓扑已激活，四大新参谋部已就位！", state="complete")
            st.toast("🚀 新主题拓扑已激活，四大新参谋部已就位！")
            st.rerun()

    st.markdown("---")
    st.caption("系统运行基准时间: 2026年10月 · GTPS v1.0")


# ---------------- 顶部 KPI 概览看板 ----------------
nodes = st.session_state.causal_net.nodes_data
events = st.session_state.collector.collected_events
snapshot = st.session_state.market_snapshot
risk_index = st.session_state.market_collector.calculate_macro_risk_index(snapshot)

# ---- 顶栏：全球硬资产实时行情异动雷达（5 胶囊 + 风险指数） ----
st.markdown("##### 📈 全球核心硬资产实时行情异动雷达")
# 5 个行情胶囊
pi1, pi2, pi3, pi4, pi5, pi6 = st.columns([2.2, 2.2, 2.2, 2.2, 2.2, 1.8])
ASSET_ORDER = [
    ("🛢️ 布伦特原油", "hf_OIL", "brent"),
    ("🥇 伦敦现货黄金", "hf_GC", "gold"),
    ("⛽ 纽约天然气", "hf_NG", "natgas"),
    ("🛢️ WTI 原油", "hf_CL", "wti"),
    ("💵 离岸人民币", "fx_susdcnh", "cnh"),  # 在快照里是 None 但保持占位
]
pill_cols = [pi1, pi2, pi3, pi4, pi5]
for idx, (label, code, _) in enumerate(ASSET_ORDER):
    with pill_cols[idx]:
        q = snapshot.get(code)
        if q:
            # 国际惯例：涨用绿、跌用红
            up = q.change_pct >= 0
            chg_color = "#22c55e" if up else "#ef4444"
            chg_sign = "+" if up else ""
            st.markdown(f"""
            <div class="market-pill">
                <div style="color:#8fa0be;font-size:11px;font-weight:600;letter-spacing:.5px;">{label}</div>
                <div style="color:#ffffff;font-size:18px;font-weight:700;margin-top:2px;">{q.price:.2f}</div>
                <div style="color:{chg_color};font-size:12px;font-weight:700;margin-top:2px;">{chg_sign}{q.change_pct:.2f}%</div>
                <div style="color:#4b5563;font-size:10px;">高 {q.high:.2f} · 低 {q.low:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="market-pill">
                <div style="color:#8fa0be;font-size:11px;font-weight:600;letter-spacing:.5px;">{label}</div>
                <div style="color:#6b7280;font-size:14px;margin-top:8px;">行情接口离线</div>
                <div style="color:#4b5563;font-size:10px;margin-top:4px;">（新浪直通不可达）</div>
            </div>
            """, unsafe_allow_html=True)
# 宏观风险指数仪表盘
with pi6:
    if risk_index >= 60:
        r_color = "#ef4444"; r_label = "集体避险"
    elif risk_index >= 25:
        r_color = "#f59e0b"; r_label = "中性博弈"
    else:
        r_color = "#10b981"; r_label = "低波动期"
    st.markdown(f"""
    <div class="market-pill" style="border-left:3px solid {r_color};">
        <div style="color:#8fa0be;font-size:11px;font-weight:600;letter-spacing:.5px;">地缘避险指数</div>
        <div style="color:{r_color};font-size:22px;font-weight:700;margin-top:2px;">{risk_index:.0f}<span style="font-size:12px;">/100</span></div>
        <div style="color:{r_color};font-size:11px;font-weight:600;">{r_label}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---- KPI 顶栏自适应：col1 固定事件数，col2-5 动态取当前主题前 4 个最强节点 ----
# 兼容原 AI 能源主题的"语义标签"（若硬编码节点存在则用专属标题）
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">今日捕获国际大事</div>
        <div class="metric-value">{len(events)} <span style="font-size:16px;color:#3b82f6;">条</span></div>
        <div class="metric-delta" style="color:#10b981;">● 实时流在线接入</div>
    </div>
    """, unsafe_allow_html=True)

# 硬编码节点专属语义标签（仅当节点存在时使用，否则用通用节点名）
_SEMANTIC_TITLES = {
    "GRID_TRANSMISSION_STRESS": ("电网变电承压指数", "▲ 红色预警阈值 0.75"),
    "POWER_WHOLESALE_PRICE": ("区域尖峰电价压力", "高位震荡运行"),
    "REGULATORY_RESTRICTIONS": ("地方监管干预强度", "审批与能耗审查收紧"),
    "CLEAN_NUCLEAR_PPA_CAPEX": ("核能与离网微网资本", "▲ 科技巨头加速注资"),
}

# 取前 4 个最强节点（按强度降序）
_sorted_nodes = sorted(nodes.values(), key=lambda n: n.intensity, reverse=True)[:4]
_kpi_cols = [col2, col3, col4, col5]
_kpi_colors = ["#ef4444", "#f59e0b", "#8b5cf6", "#10b981"]  # 红/琥珀/紫/绿

for _i, _node in enumerate(_sorted_nodes):
    with _kpi_cols[_i]:
        _kpid = _node.node_id
        _sem = _SEMANTIC_TITLES.get(_kpid)
        if _sem:
            _title, _delta_text = _sem
        else:
            # 通用节点：截断中文名作为标题 + 领域标签
            _title = _node.name[:12]
            _delta_text = f"所属领域: {_node.domain.value.upper()}"
        _val_color = _kpi_colors[_i] if _node.intensity > 0.6 else ("#10b981" if _node.intensity <= 0.4 else "#f59e0b")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{_title}</div>
            <div class="metric-value" style="color:{_val_color};">{_node.intensity:.2f}</div>
            <div class="metric-delta" style="color:{_val_color};">{_delta_text}</div>
        </div>
        """, unsafe_allow_html=True)



def _render_news_event_card(evt, snapshot, prefix="all"):
    """渲染带官方报道原文超链接与深度内参展开抽屉的新闻卡片。"""
    domain_name = evt.domain.value if hasattr(evt.domain, "value") else str(evt.domain)
    card_class = f"event-card event-card-{domain_name.lower()}"
    affected_str = " | ".join([f"{k} ({'+' if v>0 else ''}{v:.2f})" for k, v in evt.affected_nodes.items()])

    # 硬数据核验徽章
    tag = getattr(evt, "cross_check_tag", None)
    if tag is None or tag == "不在核验范围":
        badge_html = ""
    elif "资金已证实" in tag:
        badge_html = (
            '<div class="verify-badge-substantiate">'
            '🛡️ 金融大资本已核实验证 · 判定为真实战略级冲击'
            f'（关联资产：金价 {snapshot.get("hf_GC").change_pct:+.2f}% · 油价 {snapshot.get("hf_OIL").change_pct:+.2f}%）'
            '</div>'
            if snapshot.get("hf_GC") and snapshot.get("hf_OIL") else
            '<div class="verify-badge-substantiate">🛡️ 金融大资本已核实验证 · 判定为真实战略级冲击</div>'
        )
    elif "资金未响应" in tag:
        badge_html = (
            '<div class="verify-badge-noise">'
            '💨 市场反应冷淡 · 判定为外交舆论战'
            f'（大宗资产涨跌幅 < 0.4%，金价 {snapshot.get("hf_GC").change_pct:+.2f}% · 油价 {snapshot.get("hf_OIL").change_pct:+.2f}%）'
            '</div>'
            if snapshot.get("hf_GC") and snapshot.get("hf_OIL") else
            '<div class="verify-badge-noise">💨 市场反应冷淡 · 判定为外交舆论战</div>'
        )
    elif "核验失败" in tag:
        badge_html = '<div class="verify-badge-missing">⚠️ 行情接口离线 · 无法进行真实性核验</div>'
    else:
        badge_html = '<div class="verify-badge-noise">⚖️ 资金观望 · 烈度维持</div>'

    # 构造可点击的标题与原文跳转超链接
    if getattr(evt, 'url', None) and str(evt.url).startswith('http'):
        title_html = f'<a href="{evt.url}" target="_blank" rel="noopener noreferrer" style="color:#60a5fa; text-decoration:none; font-size:16px; font-weight:700; display:inline-block; margin: 8px 0 6px 0;">{evt.title} <span style="font-size:13px; color:#38bdf8; background:#1e293b; padding:2px 8px; border-radius:4px; margin-left:6px; font-weight:normal; border:1px solid #334155;">🔗 点击查看官方报道原文 ↗</span></a>'
    else:
        title_html = f'<div style="font-size:16px; font-weight:600; color:#f3f4f6; margin: 8px 0 4px 0;">{evt.title}</div>'

    st.markdown(f"""
    <div class="{card_class}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span class="badge" style="background:#2563eb; color:white;">{domain_name.upper()}</span>
                <span style="color:#8fa0be; font-size:12px;">来源: {evt.source} · {evt.timestamp}</span>
            </div>
            <div style="color:#f59e0b; font-weight:bold; font-size:12px;">冲击烈度: {int(evt.impact_level*100)}%</div>
        </div>
        {title_html}
        <div style="font-size:13px; color:#cbd5e1; line-height:1.6;">{evt.summary}</div>
        <div style="margin-top:8px; font-size:12px; color:#60a5fa;">
            🔗 传导关联变量: <code>{affected_str}</code>
        </div>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 点击展开此事件详细情报内参与深度研判", expanded=False):
        st.markdown(f"**📰 事件全称**：{evt.title}")
        st.markdown(f"**📡 发布渠道**：`{evt.source}` &nbsp;|&nbsp; **发布时间**：`{evt.timestamp}` &nbsp;|&nbsp; **归属领域**：`{domain_name.upper()}`")
        st.markdown(f"**📋 情报通报全文**：\n\n" + str(evt.summary))
        st.markdown(f"**⚡ 核心因果传导路径**：`{affected_str}`")

        btn_c1, btn_c2 = st.columns([1, 1])
        with btn_c1:
            if getattr(evt, 'url', None) and str(evt.url).startswith('http'):
                st.link_button("🌐 点击跳转并阅读官方报道网页原文 ↗", evt.url, use_container_width=True)
            else:
                st.caption("该事件为自生/专线快讯，未关联外部公开 URL。")
        with btn_c2:
            if st.button("⚔️ 将此事件直接载入红蓝对抗圆桌", key=f"load_wargame_{prefix}_{evt.event_id}", use_container_width=True):
                st.session_state.selected_wargame_event = evt.title
                st.success("✅ 该事件已选定为红蓝圆桌对抗议题，请切换至「⚔️ 闭门峰会与红蓝对抗圆桌」模块！")


# ---------------- 🎛️ 战略推演核心功能分类模块栏 ----------------
st.markdown("<div style='margin-bottom:8px;font-size:13px;font-weight:700;color:#94a3b8;letter-spacing:0.5px;'>🎛️ <b>战略推演核心功能模块栏：</b></div>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📡 全球情报与多模态感知 (Intelligence)",
    "🧠 因果拓扑与科学计算 (Causal & MATLAB)",
    "⚔️ 闭门峰会与红蓝对抗圆桌 (War-Gaming)",
    "🔮 未来情景树与概率预警 (Forecasting)",
    "🪞 历史因果巨镜与反身性透视 (Mirror)"
])

# ---------------- TAB 1: 全球情报与多模态感知 ----------------
with tab1:
    st.markdown("#### 🌐 今日全球重大国际事件情报流")
    st.caption("多源实时快讯捕获 · 点击直达官方权威报道 · 深度内参展开 · 一键载入红蓝对抗推演")

    # 分领域归纳
    _domain_buckets = {
        "ECONOMY": [e for e in events if (getattr(e.domain, "value", str(e.domain))).lower() == "economy"],
        "CULTURE": [e for e in events if (getattr(e.domain, "value", str(e.domain))).lower() in ["society", "ecology"]],
        "POLITICS": [e for e in events if (getattr(e.domain, "value", str(e.domain))).lower() == "politics"],
        "TECHNOLOGY": [e for e in events if (getattr(e.domain, "value", str(e.domain))).lower() == "technology"],
        "ENERGY": [e for e in events if (getattr(e.domain, "value", str(e.domain))).lower() == "energy"],
    }

    # 领域专属分类栏
    st.markdown("<div style='font-size:13px;font-weight:700;color:#94a3b8;margin:12px 0 8px 0;'>📰 <b>新闻情报领域分类栏：</b></div>", unsafe_allow_html=True)
    nt_all, nt_econ, nt_pol, nt_tech, nt_energy, nt_cul = st.tabs([
        f"🌐 全部要闻 ({len(events)})",
        f"💰 宏观经济与金融 ({len(_domain_buckets['ECONOMY'])})",
        f"🏛️ 政治地缘与防务 ({len(_domain_buckets['POLITICS'])})",
        f"🔬 前沿科技与AI ({len(_domain_buckets['TECHNOLOGY'])})",
        f"⚡ 能源资源与生态 ({len(_domain_buckets['ENERGY'])})",
        f"🎭 社会文化与思潮 ({len(_domain_buckets['CULTURE'])})"
    ])

    with nt_all:
        for evt in events:
            _render_news_event_card(evt, snapshot, prefix="all")

    with nt_econ:
        if _domain_buckets["ECONOMY"]:
            for evt in _domain_buckets["ECONOMY"]:
                _render_news_event_card(evt, snapshot, prefix="econ")
        else:
            st.info("今日暂无捕获到宏观经济维度的突发异动。")

    with nt_pol:
        if _domain_buckets["POLITICS"]:
            for evt in _domain_buckets["POLITICS"]:
                _render_news_event_card(evt, snapshot, prefix="pol")
        else:
            st.info("今日暂无捕获到政治防务维度的突发异动。")

    with nt_tech:
        if _domain_buckets["TECHNOLOGY"]:
            for evt in _domain_buckets["TECHNOLOGY"]:
                _render_news_event_card(evt, snapshot, prefix="tech")
        else:
            st.info("今日暂无捕获到前沿科技维度的突发异动。")

    with nt_energy:
        if _domain_buckets["ENERGY"]:
            for evt in _domain_buckets["ENERGY"]:
                _render_news_event_card(evt, snapshot, prefix="energy")
        else:
            st.info("今日暂无捕获到能源资源维度的突发异动。")

    with nt_cul:
        if _domain_buckets["CULTURE"]:
            for evt in _domain_buckets["CULTURE"]:
                _render_news_event_card(evt, snapshot, prefix="cul")
        else:
            st.info("今日暂无捕获到社会文化维度的突发异动。")


# ---------------- TAB 2: 因果网络与系统动力学 ----------------
with tab2:
    st.markdown("#### 🧠 跨领域因果网络拓扑状态与系统内生反馈环")
    
    st.caption("力导向全景图谱 · 拖拽节点可重排拓扑 · 滚轮缩放 · 悬停自动高亮相邻传导链路")

    # ---- 视图控制栏 ----
    ctl1, ctl2, ctl3 = st.columns([2, 2, 1])
    with ctl1:
        view_mode = st.radio(
            "图谱视图",
            ["因果力导向图谱", "事件-实体关联图谱"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with ctl2:
        highlight_loops = st.toggle("金色高亮反馈环节点", value=True)
    with ctl3:
        graph_height = st.select_slider("画布高度", options=[520, 580, 650, 720], value=580)

    # ---- 全景交互式图谱主视图 ----
    if view_mode == "事件-实体关联图谱":
        graph_html = render_entity_knowledge_graph_html(events, height=graph_height)
        st.caption(
            f"已解析 {len(events)} 条当日真实国际事件，自动识别涉事地缘国家 / 关键机构 / 关键产业实体，"
            "构建「事件 ➔ 实体」星形关联网络。"
        )
    else:
        graph_html = render_causal_graph_html(
            st.session_state.causal_net,
            highlight_loops=highlight_loops,
            height=graph_height,
        )
        st.caption(
            f"当前主题共 {len(nodes)} 个因果变量、"
            f"{len(st.session_state.causal_net.links_data)} 条传导关系、"
            f"{len(st.session_state.causal_net.find_feedback_loops())} 个内生反馈环。"
            "绿色实线 = 正向强化，红色虚线 = 负向制约，线宽随传导强度变化。"
        )

    # 修复 Streamlit 1.66 components.v1.html iframe 默认 display:inline 导致 height 不生效的问题
    st.markdown(
        "<style>iframe.stIFrame{display:block!important;width:100%!important;}</style>",
        unsafe_allow_html=True,
    )
    components.html(graph_html, height=graph_height + 12, scrolling=False)

    st.markdown("---")

    col_g1, col_g2 = st.columns([2, 3])

    with col_g1:
        st.markdown("##### ⚠️ 系统内生因果闭环反馈 (Feedback Loops)")
        loops = st.session_state.causal_net.find_feedback_loops()
        if loops:
            for idx, lp in enumerate(loops, 1):
                names = [nodes[n].name for n in lp]
                loop_str = " ➔<br>".join([f"<b>{n}</b>" for n in names] + [f"<b>{names[0]}</b>"])
                st.info(f"**因果自强化/制约循环 {idx}：**<br>{loop_str}", icon="🔄")
        else:
            st.caption("当前主题尚未形成闭环回路（需同时存在强化与调节回路）。")

        st.markdown("##### 动态冲击传导演练")
        if st.button("▶️ 单步推进系统动态演进 (Propagate 1 Step)", use_container_width=True):
            st.session_state.causal_net.propagate_dynamics(steps=1)
            st.toast("系统已完成 1 步因果级联演化！图谱与强度已刷新。")
            st.rerun()

    with col_g2:
        node_records = []
        for nid, node in nodes.items():
            node_records.append({
                "节点代号": nid,
                "领域分类": node.domain.value.upper(),
                "变量名称": node.name,
                "当前强度": round(node.intensity, 2),
                "演进说明": node.description,
            })
        df_nodes = pd.DataFrame(node_records)

        with st.expander(f"📊 核心因果变量强度明细（0.00 ~ 1.00） · 共 {len(df_nodes)} 项", expanded=False):
            st.bar_chart(df_nodes.set_index("变量名称")["当前强度"])
            st.dataframe(
                df_nodes[["领域分类", "变量名称", "当前强度", "演进说明"]],
                use_container_width=True,
                hide_index=True,
            )


    # ---------------- 📐 MATLAB 科学计算与系统动力学联动工作台 ----------------
    st.markdown("---")
    st.markdown("#### 📐 MATLAB 科学计算与系统动力学联动工作台")
    st.caption("与 MATLAB / Octave 矩阵计算无缝联动 · 导出可直接运行的 ODE45 动力学仿真脚本与出版级学术相图")

    matlab_tab1, matlab_tab2 = st.tabs(["📊 MATLAB 风格动力学演化相图", "💻 导出 MATLAB 原生仿真模型 (.m)"])

    with matlab_tab1:
        with st.spinner("正在基于当前因果拓扑矩阵求解 MATLAB ODE 动力学微分方程并渲染出版级相图..."):
            fig_bytes = render_matlab_style_figure(st.session_state.causal_net)
            if fig_bytes:
                st.image(fig_bytes, caption="GTPS × MATLAB 系统动力学连续时域轨迹 (ODE45 RK4) 与特征值稳定性相平面图", use_container_width=True)
                st.download_button(
                    label="📥 下载 MATLAB 出版级高分辨率高清仿真图 (PNG)",
                    data=fig_bytes,
                    file_name="gtps_matlab_dynamics_figure.png",
                    mime="image/png",
                    use_container_width=True
                )

    with matlab_tab2:
        m_code = generate_matlab_script(st.session_state.causal_net)
        m_col1, m_col2 = st.columns([3, 1])
        with m_col1:
            st.caption("当前因果拓扑已全自动编译为标准 MATLAB 语法脚本，包含 digraph 网络图论、ode45 微分方程求解与 eig 稳定性判定。")
        with m_col2:
            st.download_button(
                label="📥 下载 .m 仿真代码文件",
                data=m_code,
                file_name="gtps_causal_simulation.m",
                mime="text/plain",
                type="primary",
                use_container_width=True
            )
        st.code(m_code, language="matlab")


# ---------------- TAB 3: 虚拟战略闭门峰会 · 红蓝对抗圆桌 ----------------
with tab3:
    st.markdown("#### 🏛️ 虚拟战略闭门峰会 · 红蓝对抗圆桌")
    st.caption("四大利益集团参谋部围绕今日真实国际议题，展开立场宣告 → 针锋相对驳斥 → 闭门博弈妥协的三轮对抗")

    # ---- 从主题 JSON 动态构造 FACTION_STYLE（阵营视觉识别系统） ----
    _theme_personas = st.session_state.causal_net.current_theme.get("personas", [])
    if _theme_personas:
        # 根据主题 personas 动态生成配色映射（保持 4 组紫/琥珀/正红/蓝绿）
        _PALETTE = ["#8b5cf6", "#f59e0b", "#ef4444", "#14b8a6"]
        FACTION_STYLE = {}
        for _i, _p in enumerate(_theme_personas[:4]):
            _pid = _p.get("persona_id", f"FACTION_{_i}")
            _name = _p.get("name", _pid)
            FACTION_STYLE[_pid] = (_PALETTE[_i % 4], _name[:8])
    else:
        # 兜底：默认 AI 能源主题四阵营
        FACTION_STYLE = {
            "TECH_HYPERSCALER": ("#8b5cf6", "科技资本巨头"),
            "GRID_GUARDIAN": ("#f59e0b", "区域电网守门人"),
            "STATE_REGULATOR": ("#ef4444", "地方监管政府"),
            "GLOBAL_ARBITRAGEUR": ("#14b8a6", "地缘套利招商团"),
        }

    # 主题 personas → 临时 dict 供渲染使用（若为空则回退全局 PERSONAS）
    _theme_persona_dict = {}
    for _p in _theme_personas:
        _pid = _p.get("persona_id", "")
        if _pid:
            _theme_persona_dict[_pid] = {"name": _p.get("name", _pid), "strategy": _p.get("strategy", "")}

    # ---- 顶部操作栏：议题选择 + 启动 ----
    op1, op2 = st.columns([3, 1])
    chosen_evt = None
    with op1:
        evt_options = {e.title: e for e in events}
        if evt_options:
            _default_idx = 0
            _pre = st.session_state.get("selected_wargame_event")
            if _pre and _pre in evt_options:
                _default_idx = list(evt_options.keys()).index(_pre)
            chosen_title = st.selectbox(
                "🎯 选择圆桌对抗议题（源自今日捕获的真实国际要闻）：",
                list(evt_options.keys()),
                index=_default_idx,
            )
            chosen_evt = evt_options[chosen_title]
            st.caption(f"议题背景：{chosen_evt.summary}")
        else:
            st.warning("尚未捕获到今日事件，请先在上方「📡 每日真实国际大事全网采集」重抓后再启动圆桌对抗。", icon="⚠️")
    with op2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        launch = st.button(
            "⚔️ 启动闭门圆桌对抗推演",
            use_container_width=True,
            type="primary",
            disabled=chosen_evt is None,
        )

    if launch and chosen_evt is not None:
        cfg = st.session_state.get("llm_config", {})
        engine = LLMWarGameEngine(LLMClient(
            api_key=cfg.get("api_key") or None,
            base_url=cfg.get("base_url") or "https://api.deepseek.com/v1",
            model_name=cfg.get("model_name") or "deepseek-chat",
            timeout=45,
        ))
        with st.status("🏛️ 闭门圆桌对抗推演进行中...", expanded=True) as status:
            result = engine.run_wargame_session(
                chosen_evt.title, chosen_evt.summary,
                progress_cb=lambda msg: st.write(f"✅ {msg}"),
                available_nodes=list(nodes.keys()),  # 传入当前主题的动态节点列表
            )
            # 量化战术冲击回填因果网络 → 顶部 KPI 与 Tab 4 情景树即时重校准
            engine.apply_to_network(st.session_state.causal_net, result.decisions)
            status.update(label="🏛️ 推演完成：战术冲击已回填因果网络，情景树已重新校准！", state="complete")
        st.session_state.wargame_result = result
        st.toast("⚔️ 红蓝对抗决议已生效，全局概率情景完成重算！")
        st.rerun()

    # ---- 辩论实况流 + 终局内参展板 ----
    result = st.session_state.get("wargame_result")
    if result:
        mode_badge = (
            '<span class="badge" style="background:#065f46;color:#a7f3d0;">● 真实大模型在线驱动</span>'
            if result.mode == "LIVE_LLM" else
            '<span class="badge" style="background:#374151;color:#d1d5db;">● 本地高保真参谋模板</span>'
        )
        st.markdown(f"**当前对抗议题：{result.event_title}** &nbsp; {mode_badge}", unsafe_allow_html=True)

        def render_round(title, icon, statements):
            st.markdown(f"##### {icon} {title}")
            for pid, text in statements.items():
                _faction_info = FACTION_STYLE.get(pid)
                if _faction_info:
                    color, short = _faction_info
                else:
                    color, short = "#6b7280", pid[:8]
                # 优先用主题 personas 的中文名，否则回退全局 PERSONAS
                if pid in _theme_persona_dict:
                    _full_name = _theme_persona_dict[pid]["name"]
                elif pid in PERSONAS:
                    _full_name = PERSONAS[pid]["name"]
                else:
                    _full_name = pid
                st.markdown(f"""
                <div class="debate-card" style="border-left:4px solid {color};">
                    <div style="color:{color}; font-weight:700; font-size:13px; margin-bottom:4px;">
                        {short} · {_full_name}
                    </div>
                    <div style="color:#e5e7eb; font-size:14px; line-height:1.6;">{text}</div>
                </div>""", unsafe_allow_html=True)

        render_round("第一轮 · 危机态势研判与立场宣告", "🎙️", result.opening_statements)
        render_round("第二轮 · 交叉辩论与反制施压", "⚔️", result.cross_debate)
        render_round("第三轮 · 闭门博弈妥协决议", "🤝", result.resolutions)

        st.markdown("---")
        st.markdown("##### 📁 终局决议内参展板（高管战略内参）")
        dec_rows = []
        for d in result.decisions:
            _fs = FACTION_STYLE.get(d.agent_id)
            _faction_label = _fs[1] if _fs else d.agent_id[:8]
            dec_rows.append({
                "博弈阵营": _faction_label,
                "实质反制手段": d.action_name,
                "冲击因果变量": d.target_node_id,
                "冲击强度": f"{d.intervention_strength:+.2f}",
            })
        st.table(pd.DataFrame(dec_rows))
        st.success("✅ 上述量化冲击已自动回填核心因果网络；顶部 KPI 与 Tab 4 情景树概率已即时重新校准。")

        with st.expander("展开《战略闭门圆桌博弈纪要与内参决议》全文", expanded=False):
            st.markdown(result.briefing)
    else:
        st.info("尚未开启圆桌对抗。请在上方选择今日真实议题，点击「⚔️ 启动闭门圆桌对抗推演」。无 API Key 亦可完整体验（本地高保真参谋模板）。")


    # ---------------- 🎯 人类战略观察员·定向对抗质询台 ----------------
    st.markdown("---")
    st.markdown("#### 🎯 人类战略观察员·定向对抗质询台")
    st.caption("基于今日重大新闻与实时局势，由您直接提出具体战略设想、极端假设或针对性考验，由多方红蓝参谋部展开针锋相对的定向辩论攻防。")

    if "targeted_inquiries" not in st.session_state:
        st.session_state.targeted_inquiries = []

    # 快捷灵感提问
    _quick_prompts = [
        "若某方突然实施关键供应链断供与技术封锁，各方将如何极限反制？",
        "面对当前地缘动荡与通胀溢价，金融资本与产业资本将如何跨国套利与避险？",
        "如果政府出台严苛能耗指标与惩罚性电价，科技巨头是否会加速外迁？"
    ]

    st.markdown("<div style='font-size:12px;color:#94a3b8;margin-bottom:6px;'>💡 <b>快速启发质询（点击一键带入）：</b></div>", unsafe_allow_html=True)
    q_col1, q_col2, q_col3 = st.columns(3)
    if q_col1.button(f"⚡ {_quick_prompts[0][:18]}...", use_container_width=True):
        st.session_state.inquiry_input_val = _quick_prompts[0]
    if q_col2.button(f"💰 {_quick_prompts[1][:18]}...", use_container_width=True):
        st.session_state.inquiry_input_val = _quick_prompts[1]
    if q_col3.button(f"🏛️ {_quick_prompts[2][:18]}...", use_container_width=True):
        st.session_state.inquiry_input_val = _quick_prompts[2]

    inquiry_default = st.session_state.get("inquiry_input_val", "")
    
    with st.form("targeted_inquiry_form", clear_on_submit=False):
        user_question = st.text_area(
            "💬 输入您对红蓝对抗参谋部的针对性质询问题：",
            value=inquiry_default,
            placeholder="例如：若某大国突然对海峡航道实施戒严，红方与蓝方分别会采取怎样的首轮和次轮战术反制？对油价和算力供应链有什么具体冲击？",
            height=85
        )
        inq_sub_col1, inq_sub_col2 = st.columns([3, 1])
        with inq_sub_col1:
            st.caption(f"当前锚定背景事件：**{chosen_evt.title if chosen_evt else '全球地缘与产业宏观态势'}**")
        with inq_sub_col2:
            submit_inquiry = st.form_submit_button("⚔️ 发起针对性攻防辩论", use_container_width=True, type="primary")

    if submit_inquiry and user_question.strip():
        cfg = st.session_state.get("llm_config", {})
        engine = LLMWarGameEngine(LLMClient(
            api_key=cfg.get("api_key") or None,
            base_url=cfg.get("base_url") or "https://api.deepseek.com/v1",
            model_name=cfg.get("model_name") or "deepseek-chat",
            timeout=45,
        ))
        
        evt_t = chosen_evt.title if chosen_evt else "全球地缘与能源算力博弈态势"
        evt_s = chosen_evt.summary if chosen_evt else "多主体围绕关键资源、基础设施、金融流动性与监管门槛展开博弈。"

        with st.status("🎯 红蓝参谋部正在针对您的提问展开专项对抗推演...", expanded=True) as status:
            inquiry_result = engine.run_targeted_inquiry(
                event_title=evt_t,
                event_summary=evt_s,
                user_question=user_question.strip(),
                available_nodes=list(nodes.keys()),
                progress_cb=lambda msg: st.write(f"💬 {msg}")
            )
            status.update(label="🎯 针对性攻防对抗完成！各参谋部交锋决议已生成！", state="complete")

        st.session_state.targeted_inquiries.insert(0, inquiry_result)
        st.toast("🎯 定向质询对抗推演已生成！")
        st.rerun()

    # 渲染历史质询对话记录
    if st.session_state.targeted_inquiries:
        st.markdown("##### 📜 针对性质询对抗实况档案")
        for idx, inq in enumerate(st.session_state.targeted_inquiries):
            st.markdown(f"""
            <div class="inquiry-bubble">
                <div style="color:#60a5fa;font-size:12px;font-weight:700;letter-spacing:0.5px;">
                    🎯 人类观察员质询 #{len(st.session_state.targeted_inquiries) - idx} · {inq.timestamp}
                </div>
                <div style="color:#ffffff;font-size:15px;font-weight:600;margin-top:6px;">
                    "{inq.question}"
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 各阵营发言
            for pid, resp in inq.responses.items():
                _faction_info = FACTION_STYLE.get(pid)
                color, short = _faction_info if _faction_info else ("#6b7280", pid[:8])
                _full_name = _theme_persona_dict.get(pid, {}).get("name") or PERSONAS.get(pid, {}).get("name", pid)
                st.markdown(f"""
                <div class="inquiry-resp-card" style="border-left:4px solid {color};">
                    <div style="color:{color};font-weight:700;font-size:13px;margin-bottom:4px;">
                        {short} · {_full_name}
                    </div>
                    <div style="color:#e5e7eb;font-size:14px;line-height:1.6;">{resp}</div>
                </div>
                """, unsafe_allow_html=True)

            # 综合研判
            if inq.summary:
                st.info(f"**🏛️ 参谋长联席研判总结：**\n\n" + inq.summary, icon="📊")

            # 一键回填因果网络按钮
            act_c1, act_c2 = st.columns([3, 1])
            with act_c1:
                st.caption(f"本项对抗共引申出 {len(inq.decisions)} 项战术冲击动作。")
            with act_c2:
                if st.button("⚡ 注入此质询战术到因果网络", key=f"apply_inq_{idx}", use_container_width=True):
                    LLMWarGameEngine.apply_to_network(st.session_state.causal_net, inq.decisions)
                    st.success("✅ 战术冲击已注入因果网络并传导重平衡！")
                    st.rerun()

        if st.button("🗑️ 清空历史质询记录", type="secondary"):
            st.session_state.targeted_inquiries = []
            st.rerun()


    # ---- 附录：传统规则引擎沙盒（保留快速压力测试能力） ----
    with st.expander("⚙️ 附：规则引擎四主体档案与自主反制记录（传统沙盒）", expanded=False):
        agents = st.session_state.sandbox.agents
        c1, c2 = st.columns(2)
        for idx, (aid, ag) in enumerate(agents.items()):
            col = c1 if idx % 2 == 0 else c2
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between;">
                        <div style="font-weight:700; color:#60a5fa; font-size:16px;">{ag.name}</div>
                        <span class="badge" style="background:#374151; color:#e5e7eb;">{ag.role_type}</span>
                    </div>
                    <div style="font-size:13px; color:#d1d5db; margin:8px 0;"><b>战略立场：</b>{ag.current_stance}</div>
                    <div style="font-size:12px; color:#9ca3af;">
                        <b>核心利益目标：</b>
                        <ul style="margin: 4px 0 0 16px; padding:0;">
                            {''.join([f"<li>{o}</li>" for o in ag.objectives])}
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        decisions = st.session_state.sandbox.decision_history
        if decisions:
            dec_list = []
            for d in reversed(decisions[-6:]):
                dec_list.append({
                    "主体 (Agent)": agents[d.agent_id].name if d.agent_id in agents else d.agent_id,
                    "战略决策行动": d.action_name,
                    "干预变量": nodes[d.target_node_id].name if d.target_node_id in nodes else d.target_node_id,
                    "干预强度": f"{'+' if d.intervention_strength>0 else ''}{d.intervention_strength:.2f}",
                    "决策逻辑与战略动机": d.explanation
                })
            st.table(pd.DataFrame(dec_list))
        else:
            st.write("暂无历史博弈记录，可点击侧边栏注入事件触发博弈。")


# ---------------- TAB 4: 情景树与战略预警 ----------------
with tab4:
    st.markdown("#### 🔮 动态校准的未来概率情景树与前瞻先导指标")
    st.caption("基于全源情报注入力度与博弈收敛状态生成的条件概率分布")

    scenarios = st.session_state.scenario_engine.generate_scenarios()

    # 概率对比展示
    chart_data = pd.DataFrame({
        "情景名称": [s.title.split('】')[1] if '】' in s.title else s.title for s in scenarios],
        "置信概率": [s.probability for s in scenarios]
    })
    
    col_sc1, col_sc2 = st.columns([2, 1])
    with col_sc1:
        st.bar_chart(chart_data.set_index("情景名称")["置信概率"])
    with col_sc2:
        for s in scenarios:
            st.metric(
                label=s.title[:16] + "...",
                value=f"{int(s.probability * 100)}%",
                delta=f"跨度: {s.time_horizon}"
            )

    st.markdown("---")

    for sc in scenarios:
        with st.expander(f"{sc.title} (置信度: {int(sc.probability*100)}% | 视界: {sc.time_horizon})", expanded=(sc.probability >= 0.4)):
            st.markdown(f"**📖 演化叙事：** {sc.narrative}")
            
            c_imp, c_ind = st.columns(2)
            with c_imp:
                st.markdown("##### 🌐 跨领域链式影响：")
                for dom, imp in sc.domain_impacts.items():
                    dname = dom.value.upper() if hasattr(dom, "value") else str(dom)
                    st.markdown(f"* **{dname}**：{imp}")

            with c_ind:
                st.markdown("##### 🚨 关键先导指标 (Leading Indicators)：")
                for ind in sc.leading_indicators:
                    st.warning(f"• {ind}")

            if sc.key_bottlenecks:
                st.caption(f"关键卡点与不确定性：{', '.join(sc.key_bottlenecks)}")


# ---------------- TAB 5: 历史因果巨镜与反身性雷达 ----------------
with tab5:
    st.markdown("#### 🪞 历史因果巨镜与索罗斯反身性雷达")
    st.caption("跨越百年时空对话：以史为鉴的拓扑同构匹配 × 预期自我实现的二级演化")

    # ---- 引擎初始化（session_state 缓存，避免每次 rerun 重复扫盘） ----
    if "analogy_engine" not in st.session_state:
        st.session_state.analogy_engine = HistoricalAnalogyEngine()
    if "reflexivity_engine" not in st.session_state:
        st.session_state.reflexivity_engine = ReflexivityEngine()

    # 地缘避险指数 (0-100) 归一化为市场异动输入 (0-1)
    _market_vol = round(risk_index / 100.0, 3)
    mirror = st.session_state.analogy_engine.match_historical_crisis(
        st.session_state.causal_net, market_risk_index=_market_vol
    )
    top = mirror["top_match"]

    if top is None:
        st.warning("历史基模库为空：请在 `data/history_db/` 下放置历史危机 JSON 档案。")
    else:
        # ============ 展板一：百年历史母本对撞仪表盘 ============
        st.markdown("##### ⚔️ 展板一 · 百年历史母本对撞仪表盘")

        # 顶部高亮指示器：重合度
        _sim_val = top["similarity"]
        _sim_color = "#ef4444" if _sim_val >= 0.80 else ("#f59e0b" if _sim_val >= 0.60 else "#10b981")
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1e1b4b 0%,#312e81 100%);
                    border:1px solid #4338ca; border-radius:12px; padding:18px 24px; margin-bottom:14px;">
            <div style="color:#a5b4fc; font-size:13px; font-weight:600; letter-spacing:1px;">
                HISTORICAL TOPOLOGY RESONANCE · 历史因果拓扑共振检测
            </div>
            <div style="color:#ffffff; font-size:18px; font-weight:700; margin-top:6px; line-height:1.5;">
                今日全球局势与【{top['name']}】因果拓扑重合度：
                <span style="color:{_sim_color}; font-size:28px;">{top['similarity_pct']}</span>
            </div>
            <div style="color:#818cf8; font-size:12px; margin-top:4px;">时代背景：{top['era']}</div>
        </div>
        """, unsafe_allow_html=True)

        # 四大危机相似度排行榜
        _rank_df = pd.DataFrame({
            "历史危机母本": [r["name"] for r in mirror["ranking"]],
            "拓扑相似度": [r["similarity"] for r in mirror["ranking"]],
        })
        st.bar_chart(_rank_df.set_index("历史危机母本")["拓扑相似度"])

        # 左右分栏对撞：今日现实 vs 历史当年
        mc1, mc2 = st.columns(2)
        with mc1:
            st.markdown("###### 📡 今日现实特征 · 资金验证状态")
            # 当前领域特征向量
            for d, zh in HistoricalAnalogyEngine.DOMAIN_ZH.items():
                v = mirror["current_vector"].get(d, 0.0)
                st.progress(min(1.0, max(0.0, v)), text=f"{zh} {v:.2f}")
            # 资金验证：避险指数 + 金油涨跌
            _gc = snapshot.get("hf_GC")
            _oil = snapshot.get("hf_OIL")
            _cap_lines = [f"地缘避险指数：**{risk_index:.0f}/100**"]
            if _gc:
                _cap_lines.append(f"伦敦金 {_gc.change_pct:+.2f}%")
            if _oil:
                _cap_lines.append(f"布伦特 {_oil.change_pct:+.2f}%")
            _verify = "🛡️ 大资本已入场定价" if risk_index >= 60 else ("⚖️ 资金观望" if risk_index >= 25 else "💨 市场低波未定价")
            st.info(f"**资金交叉验证：** {_verify}（{' · '.join(_cap_lines)}）", icon="💰")

        with mc2:
            st.markdown(f"###### 📜 历史当年 · {top['era']}")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">危机触发诱因</div>
                <div style="color:#e5e7eb; font-size:13px; line-height:1.6; margin-top:6px;">
                    {top['trigger_event']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            # 历史初始传导链：当年高压领域
            _hist_core = sorted(mirror["history_vector"].items(), key=lambda kv: kv[1], reverse=True)[:3]
            st.markdown("**当年初始传导主链：**")
            for d, v in _hist_core:
                if d == "market":
                    continue
                _zh = HistoricalAnalogyEngine.DOMAIN_ZH.get(d, d)
                st.markdown(f"- **{_zh}** 烈度 `{v:.2f}`")

        # 同构点陈列
        with st.expander("🔗 历史同构点：结构相同的传导链条（点击展开）", expanded=True):
            for s in mirror["similarities"]:
                st.success(s)

        st.markdown("---")

        # ============ 展板二：历史演变时间轴与现代阻尼 ============
        st.markdown("##### ⏳ 展板二 · 历史后续演变时间轴与现代阻尼 (Timeline Stepper)")

        _tl_col, _damp_col = st.columns([3, 2])
        with _tl_col:
            st.markdown("**当年历史的阶段演进（推演参照系）：**")
            _timeline_html = ""
            for step in mirror["historical_trajectory"]:
                _timeline_html += f"""
                <div style="border-left:3px solid #8b5cf6; padding:4px 0 14px 16px; position:relative;">
                    <div style="position:absolute; left:-8px; top:6px; width:13px; height:13px;
                                border-radius:50%; background:#8b5cf6; border:2px solid #0b0f19;"></div>
                    <div style="color:#c4b5fd; font-weight:700; font-size:13px;">{step.get('phase','')}</div>
                    <div style="color:#e5e7eb; font-size:13px; margin-top:2px; line-height:1.5;">{step.get('event','')}</div>
                    <div style="color:#6b7280; font-size:12px; margin-top:2px;">◈ 关键信号：{step.get('signal','')}</div>
                </div>"""
            st.markdown(_timeline_html, unsafe_allow_html=True)

        with _damp_col:
            st.markdown("**🛡️ 现代抵消变量（时代差异阻尼）：**")
            _offsets = [d for d in mirror["modern_divergences"] if d.startswith("【现代对冲】")]
            _computed = [d for d in mirror["modern_divergences"] if not d.startswith("【现代对冲】")]
            for off in _offsets:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#052e16 0%,#064e3b 100%);
                            border:1px solid #059669; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                    <div style="color:#6ee7b7; font-size:12.5px; line-height:1.5;">✅ {off.replace('【现代对冲】','')}</div>
                </div>""", unsafe_allow_html=True)
            if _computed:
                st.caption("引擎计算的结构性差异：")
                for d in _computed:
                    st.warning(d)

        st.markdown("---")

        # ============ 展板三：索罗斯反身性二级推演卡片 ============
        st.markdown("##### 🌀 展板三 · 索罗斯反身性（Reflexivity）二级推演")

        # 反身性输入：头号情景概率 + 监管强度（POLITICS 域均值）+ 市场波动
        _scens = st.session_state.scenario_engine.generate_scenarios()
        _top_scen = max(_scens, key=lambda s: s.probability) if _scens else None
        _pol_nodes = [n.intensity for n in nodes.values() if n.domain.value.lower() == "politics"]
        _reg_intensity = sum(_pol_nodes) / len(_pol_nodes) if _pol_nodes else 0.5

        if _top_scen:
            reflex = st.session_state.reflexivity_engine.evaluate_reflexivity(
                top_scenario_title=_top_scen.title,
                base_probability=_top_scen.probability,
                regulatory_intensity=_reg_intensity,
                market_volatility=_market_vol,
            )

            # 状态徽章（三模式配色）
            _MODE_STYLE = {
                "SELF_FULFILLING": ("#7f1d1d", "#fca5a5", "🔥", "触发自实现挤兑机制"),
                "SELF_DEFEATING": ("#052e16", "#6ee7b7", "🛡️", "触发自毁灭拆弹机制"),
                "BALANCED_TENSION": ("#1e3a8a", "#93c5fd", "⚖️", "反身性拉锯·弱反馈"),
            }
            _bg, _fg, _icon, _label = _MODE_STYLE.get(reflex["mode"], _MODE_STYLE["BALANCED_TENSION"])
            _base_pct = int(reflex["base_probability"] * 100)
            _cal_pct = int(reflex["calibrated_probability"] * 100)
            _delta_pct = reflex["probability_delta"] * 100

            if reflex["mode"] == "SELF_DEFEATING":
                _badge_text = f"政策提前介入，原本 {_base_pct}% 的危机概率已被对冲平抑至 {_cal_pct}%"
            elif reflex["mode"] == "SELF_FULFILLING":
                _badge_text = f"资本抢跑囤积，原本 {_base_pct}% 的危机概率被预期推高至 {_cal_pct}%"
            else:
                _badge_text = f"多空预期对冲拉锯，概率维持 {_base_pct}% → {_cal_pct}%"

            st.markdown(f"""
            <div style="background:{_bg}; border:1px solid {_fg}; border-radius:12px; padding:16px 22px;">
                <div style="color:{_fg}; font-size:16px; font-weight:700;">
                    {_icon} {_label}
                </div>
                <div style="color:#e5e7eb; font-size:13.5px; margin-top:6px;">{_badge_text}</div>
                <div style="color:#9ca3af; font-size:12px; margin-top:8px; line-height:1.6;">
                    {reflex['reasoning']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 概率位移可视化 + 驱动力对比
            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown("**一级静态概率 → 二级反身性校准：**")
                st.progress(min(1.0, reflex["base_probability"]),
                            text=f"推演基准 {_base_pct}%")
                st.progress(min(1.0, reflex["calibrated_probability"]),
                            text=f"反身性校准 {_cal_pct}%（{_delta_pct:+.0f}%）")
            with rc2:
                st.markdown("**两股反身性驱动力：**")
                _drv = reflex["drives"]
                st.progress(min(1.0, _drv["self_fulfilling"]),
                            text=f"资本抢跑驱动 {_drv['self_fulfilling']:.2f}")
                st.progress(min(1.0, _drv["self_defeating"]),
                            text=f"政策拆弹驱动 {_drv['self_defeating']:.2f}")

            # 高管反脆弱决策备忘录
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1c1917 0%,#292524 100%);
                        border:1px solid #a8a29e; border-radius:12px; padding:16px 22px; margin-top:10px;">
                <div style="color:#d6d3d1; font-size:13px; font-weight:700; letter-spacing:1px;">
                    📋 高管反脆弱决策备忘录（ANTI-FRAGILE MEMO）
                </div>
                <div style="color:#e7e5e4; font-size:13.5px; margin-top:8px; line-height:1.7;">
                    {reflex['anti_fragile_advice']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.caption("反身性输入：头号情景概率 × 监管干预强度（POLITICS 域节点均值）× 实时市场波动（地缘避险指数归一化）")
        else:
            st.info("暂无可用情景，无法执行反身性二级推演。")

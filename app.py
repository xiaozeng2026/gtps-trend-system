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
import pandas as pd
from datetime import datetime

from src.core.models import DomainCategory, ModalityType
from src.collector.news_collector import DailyNewsCollector
from src.collector.market_data import MarketDataCollector, CrossCheckFilter
from src.causal_engine.causal_network import CausalNetwork
from src.simulation.agent_sandbox import MultiAgentSandbox
from src.simulation.llm_wargame import LLMClient, LLMWarGameEngine, PERSONAS
from src.forecasting.scenario_engine import ScenarioForecastEngine

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
</style>
""", unsafe_allow_html=True)

# 初始化 Session State
if "collector" not in st.session_state:
    st.session_state.collector = DailyNewsCollector()

if "market_collector" not in st.session_state:
    st.session_state.market_collector = MarketDataCollector(timeout=6)

if "market_snapshot" not in st.session_state:
    st.session_state.market_snapshot = st.session_state.market_collector.get_live_market_snapshot()

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
    # 2. 原油与天然气硬资产涨跌 → 工商业尖峰电价 + 电网承压
    snap = st.session_state.market_snapshot
    oil = snap.get("hf_OIL")
    natgas = snap.get("hf_NG")
    if oil and abs(oil.change_pct) > 0.3:
        # 原油波动 → 电价（能源成本传导）+ 电网承压（工业负荷联动）
        oil_delta = max(-0.2, min(0.2, oil.change_pct * 0.04))
        st.session_state.causal_net.apply_node_impulse(
            "POWER_WHOLESALE_PRICE", oil_delta,
            reason=f"硬资产联动: 布伦特原油 {'+' if oil.change_pct > 0 else ''}{oil.change_pct:.2f}%"
        )
        st.session_state.causal_net.apply_node_impulse(
            "GRID_TRANSMISSION_STRESS", oil_delta * 0.6,
            reason=f"硬资产联动: 原油波动→工业负荷传导"
        )
    if natgas and abs(natgas.change_pct) > 0.5:
        gas_delta = max(-0.15, min(0.15, natgas.change_pct * 0.03))
        st.session_state.causal_net.apply_node_impulse(
            "POWER_WHOLESALE_PRICE", gas_delta,
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
        custom_target = st.selectbox(
            "冲击核心因果变量",
            [
                ("GRID_TRANSMISSION_STRESS", "区域电网与变电承载承压度"),
                ("POWER_WHOLESALE_PRICE", "区域工商业及尖峰电价"),
                ("REGULATORY_RESTRICTIONS", "地方监管干预与能耗审批收紧"),
                ("CLEAN_NUCLEAR_PPA_CAPEX", "核能/地热/微电网私有资本注入"),
                ("GLOBAL_COMPUTE_MIGRATION", "算力集群全球地理再平衡"),
                ("AI_COMPUTE_DEMAND", "前沿大模型算力需求扩张"),
            ],
            format_func=lambda x: f"{x[1]} ({x[0]})"
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

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">今日捕获国际大事</div>
        <div class="metric-value">{len(events)} <span style="font-size:16px;color:#3b82f6;">条</span></div>
        <div class="metric-delta" style="color:#10b981;">● 实时流在线接入</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    grid_stress = nodes['GRID_TRANSMISSION_STRESS'].intensity
    stress_color = "#ef4444" if grid_stress > 0.75 else ("#f59e0b" if grid_stress > 0.6 else "#10b981")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">电网变电承压指数</div>
        <div class="metric-value" style="color:{stress_color};">{grid_stress:.2f}</div>
        <div class="metric-delta" style="color:{stress_color};">▲ 红色预警阈值 0.75</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    power_price = nodes['POWER_WHOLESALE_PRICE'].intensity
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">区域尖峰电价压力</div>
        <div class="metric-value">{power_price:.2f}</div>
        <div class="metric-delta" style="color:#f59e0b;">高位震荡运行</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    reg_heat = nodes['REGULATORY_RESTRICTIONS'].intensity
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">地方监管干预强度</div>
        <div class="metric-value">{reg_heat:.2f}</div>
        <div class="metric-delta" style="color:#ef4444;">审批与能耗审查收紧</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    nuclear_capex = nodes['CLEAN_NUCLEAR_PPA_CAPEX'].intensity
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">核能与离网微网资本</div>
        <div class="metric-value" style="color:#10b981;">{nuclear_capex:.2f}</div>
        <div class="metric-delta" style="color:#10b981;">▲ 科技巨头加速注资</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------- 主面板：多维标签页 ----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📰 今日国际大事信息流 (Live Feed)",
    "🧠 跨域因果网络与动态推演沙盘",
    "🏛️ 虚拟战略闭门峰会 · 红蓝对抗圆桌",
    "🔮 未来情景树概率推演与战略预警 (Forecast)"
])

# ---------------- TAB 1: 国际大事信息流 ----------------
with tab1:
    st.markdown("#### 🌐 今日全球重大国际事件与多模态信号情报流")
    st.caption("涵盖政治博弈、科技突破、能源电网、宏观经济等多源多模态信号")

    filter_domain = st.selectbox(
        "按领域筛选：",
        [
            "全部领域",
            "POLITICS (政治地缘与防务)",
            "ECONOMY (宏观经济与金融)",
            "TECHNOLOGY (前沿科技与AI)",
            "ENERGY (能源资源与生态)",
            "SOCIETY (社会文化与思潮)"
        ]
    )

    for evt in events:
        domain_name = evt.domain.value if hasattr(evt.domain, "value") else str(evt.domain)
        if filter_domain != "全部领域" and domain_name.upper() not in filter_domain:
            continue

        card_class = f"event-card event-card-{domain_name.lower()}"
        affected_str = " | ".join([f"{k} ({'+' if v>0 else ''}{v:.2f})" for k, v in evt.affected_nodes.items()])

        # ---- 硬数据核验徽章 ----
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

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span class="badge" style="background:#2563eb; color:white;">{domain_name.upper()}</span>
                    <span style="color:#8fa0be; font-size:12px;">来源: {evt.source} · {evt.timestamp}</span>
                </div>
                <div style="color:#f59e0b; font-weight:bold; font-size:12px;">冲击烈度: {int(evt.impact_level*100)}%</div>
            </div>
            <div style="font-size:16px; font-weight:600; color:#f3f4f6; margin: 8px 0 4px 0;">{evt.title}</div>
            <div style="font-size:13px; color:#9ca3af; line-height:1.5;">{evt.summary}</div>
            <div style="margin-top:8px; font-size:12px; color:#60a5fa;">
                🔗 传导关联变量: <code>{affected_str}</code>
            </div>
            {badge_html}
        </div>
        """, unsafe_allow_html=True)


# ---------------- TAB 2: 因果网络与系统动力学 ----------------
with tab2:
    st.markdown("#### 🧠 跨领域因果网络拓扑状态与系统内生反馈环")
    
    col_g1, col_g2 = st.columns([3, 2])
    
    with col_g1:
        st.markdown("##### 核心因果变量强度监控 (0.00 ~ 1.00)")
        node_records = []
        for nid, node in nodes.items():
            node_records.append({
                "节点代号": nid,
                "领域分类": node.domain.value.upper(),
                "变量名称": node.name,
                "当前强度": round(node.intensity, 2),
                "演进说明": node.description
            })
        df_nodes = pd.DataFrame(node_records)
        
        # 柱状图直观展示强度
        st.bar_chart(df_nodes.set_index("变量名称")["当前强度"])
        st.dataframe(df_nodes[["领域分类", "变量名称", "当前强度", "演进说明"]], use_container_width=True, hide_index=True)

    with col_g2:
        st.markdown("##### ⚠️ 系统内生因果闭环反馈 (Feedback Loops)")
        loops = st.session_state.causal_net.find_feedback_loops()
        if loops:
            for idx, lp in enumerate(loops, 1):
                names = [nodes[n].name for n in lp]
                loop_str = " ➔<br>".join([f"<b>{n}</b>" for n in names] + [f"<b>{names[0]}</b>"])
                st.info(f"**因果自强化/制约循环 {idx}：**<br>{loop_str}", icon="🔄")
        
        st.markdown("##### 动态冲击传导演练")
        if st.button("▶️ 单步推进系统动态演进 (Propagate 1 Step)", use_container_width=True):
            st.session_state.causal_net.propagate_dynamics(steps=1)
            st.toast("系统已完成 1 步因果级联演化！")
            st.rerun()


# ---------------- TAB 3: 虚拟战略闭门峰会 · 红蓝对抗圆桌 ----------------
with tab3:
    st.markdown("#### 🏛️ 虚拟战略闭门峰会 · 红蓝对抗圆桌")
    st.caption("四大利益集团参谋部围绕今日真实国际议题，展开立场宣告 → 针锋相对驳斥 → 闭门博弈妥协的三轮对抗")

    # 阵营视觉识别系统（紫 / 琥珀 / 正红 / 蓝绿）
    FACTION_STYLE = {
        "TECH_HYPERSCALER": ("#8b5cf6", "科技资本巨头"),
        "GRID_GUARDIAN": ("#f59e0b", "区域电网守门人"),
        "STATE_REGULATOR": ("#ef4444", "地方监管政府"),
        "GLOBAL_ARBITRAGEUR": ("#14b8a6", "地缘套利招商团"),
    }

    # ---- 顶部操作栏：议题选择 + 启动 ----
    op1, op2 = st.columns([3, 1])
    with op1:
        evt_options = {e.title: e for e in events}
        chosen_title = st.selectbox("🎯 选择圆桌对抗议题（源自今日捕获的真实国际要闻）：", list(evt_options.keys()))
        chosen_evt = evt_options[chosen_title]
        st.caption(f"议题背景：{chosen_evt.summary}")
    with op2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        launch = st.button("⚔️ 启动闭门圆桌对抗推演", use_container_width=True, type="primary")

    if launch:
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
                progress_cb=lambda msg: st.write(f"✅ {msg}")
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
                color, short = FACTION_STYLE[pid]
                st.markdown(f"""
                <div class="debate-card" style="border-left:4px solid {color};">
                    <div style="color:{color}; font-weight:700; font-size:13px; margin-bottom:4px;">
                        {short} · {PERSONAS[pid]['name']}
                    </div>
                    <div style="color:#e5e7eb; font-size:14px; line-height:1.6;">{text}</div>
                </div>""", unsafe_allow_html=True)

        render_round("第一轮 · 危机态势研判与立场宣告", "🎙️", result.opening_statements)
        render_round("第二轮 · 交叉辩论与反制施压", "⚔️", result.cross_debate)
        render_round("第三轮 · 闭门博弈妥协决议", "🤝", result.resolutions)

        st.markdown("---")
        st.markdown("##### 📁 终局决议内参展板（高管战略内参）")
        dec_rows = [{
            "博弈阵营": FACTION_STYLE[d.agent_id][1],
            "实质反制手段": d.action_name,
            "冲击因果变量": d.target_node_id,
            "冲击强度": f"{d.intervention_strength:+.2f}",
        } for d in result.decisions]
        st.table(pd.DataFrame(dec_rows))
        st.success("✅ 上述量化冲击已自动回填核心因果网络；顶部 KPI 与 Tab 4 情景树概率已即时重新校准。")

        with st.expander("展开《战略闭门圆桌博弈纪要与内参决议》全文", expanded=False):
            st.markdown(result.briefing)
    else:
        st.info("尚未开启圆桌对抗。请在上方选择今日真实议题，点击「⚔️ 启动闭门圆桌对抗推演」。无 API Key 亦可完整体验（本地高保真参谋模板）。")

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

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
from src.causal_engine.causal_network import CausalNetwork
from src.simulation.agent_sandbox import MultiAgentSandbox
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
</style>
""", unsafe_allow_html=True)

# 初始化 Session State
if "collector" not in st.session_state:
    st.session_state.collector = DailyNewsCollector()
    st.session_state.collector.fetch_daily_events(allow_online=True)

if "causal_net" not in st.session_state:
    st.session_state.causal_net = CausalNetwork()

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
    st.caption("AI Compute & Energy Nexus 战略推演工程")
    st.markdown("---")

    st.markdown("#### 📡 每日国际大事感知采集")
    if st.button("🔄 刷新 / 抓取今日最新全球大事", use_container_width=True):
        with st.spinner("正在扫描全球多模态情报源及国际快讯..."):
            st.session_state.collector.fetch_daily_events(allow_online=True)
            st.success("今日国际大事更新完毕！")
            st.rerun()

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
    st.caption("系统运行基准时间: 2026年10月 · GTPS v1.0")


# ---------------- 顶部 KPI 概览看板 ----------------
nodes = st.session_state.causal_net.nodes_data
events = st.session_state.collector.collected_events

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
    "♟️ 多主体博弈自主决策 (Multi-Agent)",
    "🔮 未来情景树概率推演与战略预警 (Forecast)"
])

# ---------------- TAB 1: 国际大事信息流 ----------------
with tab1:
    st.markdown("#### 🌐 今日全球重大国际事件与多模态信号情报流")
    st.caption("涵盖政治博弈、科技突破、能源电网、宏观经济等多源多模态信号")

    filter_domain = st.selectbox(
        "按领域筛选：",
        ["全部领域", "ENERGY (能源资源)", "TECHNOLOGY (科技算力)", "POLITICS (地缘政治)", "ECONOMY (宏观经济)"]
    )

    for evt in events:
        domain_name = evt.domain.value if hasattr(evt.domain, "value") else str(evt.domain)
        if filter_domain != "全部领域" and domain_name.upper() not in filter_domain:
            continue

        card_class = f"event-card event-card-{domain_name.lower()}"
        affected_str = " | ".join([f"{k} ({'+' if v>0 else ''}{v:.2f})" for k, v in evt.affected_nodes.items()])
        
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


# ---------------- TAB 3: 多主体博弈沙盒 ----------------
with tab3:
    st.markdown("#### ♟️ 多主体博弈自主决策记录与压力测试")
    st.caption("真实社会演进由相互博弈的异构主体（资本、公用事业、监管、公众）驱动")

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

    st.markdown("##### 最新一轮沙盒博弈自主反制行动")
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

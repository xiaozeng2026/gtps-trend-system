"""
端到端运行演示脚本：人类社会趋势预判系统（MVP）
命题：前沿 AI 算力急剧扩张与区域能源电网重构之社会影响推演
"""
import json
import os
import sys

# 兼容 Windows 终端 UTF-8 编码，防止 gbk 编码错误
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text

from src.ingestion.multimodal_ingestor import MultimodalIngestor
from src.causal_engine.causal_network import CausalNetwork
from src.simulation.agent_sandbox import MultiAgentSandbox
from src.forecasting.scenario_engine import ScenarioForecastEngine

console = Console()


def main():
    console.print(Panel.fit(
        "[bold cyan]人类社会趋势预判系统 (Global Trend Prediction System - GTPS)[/bold cyan]\n"
        "[dim]多模态全源感知 · 跨域因果拓扑 · 多智能体博弈沙盒 · 概率情景推演[/dim]",
        border_style="cyan"
    ))

    # ==========================================
    # 阶段 1：多模态感知流采集与特征提取
    # ==========================================
    console.print("\n[bold yellow]📡 阶段 1：多模态情报感知与微弱信号捕获 (Multimodal Ingestion)[/bold yellow]")
    ingestor = MultimodalIngestor()

    sig1 = ingestor.ingest_satellite_features(
        region="弗吉尼亚州阿什本 (Ashburn)",
        thermal_anomaly_index=0.88,
        facility_growth_ratio=0.42,
        substation_construction_rate=0.29,
        notes="遥感热红外显示算力中心集群热柱密度环比增长 42%，配套 500kV 变电站扩建明显滞后。"
    )

    sig2 = ingestor.ingest_grid_timeseries(
        grid_zone="PJM Interconnection 电网域",
        peak_power_price_mwh=345.50,
        queue_wait_years=4.8,
        transformer_lead_time_months=38.0,
        datacenter_power_gw=4.2
    )

    sig3 = ingestor.ingest_policy_and_regulatory_text(
        jurisdiction="弗吉尼亚与马里兰州议会",
        bill_title="《数据中心水电气资源综合利用与电费公平分摊法案 (Draft HB-2804)》",
        text_excerpt="拟要求所有超过 100MW 负荷的商业计算中心，必须承担 100% 对应变电改造成本，并暂停新建机房无条件免税政策。",
        restriction_level=0.78,
        clean_energy_mandate=0.85
    )

    sig4 = ingestor.ingest_tech_frontier_filing(
        tech_entity="顶级云服务与大模型联盟",
        cluster_scale_mw=1200.0,
        pue_rating=1.12,
        nuclear_ppa_signed=True,
        announcement_summary="正式签订 20 年期 835MW 退役核电机组全额重启自备购电协议，规避公共电网排队延误。"
    )

    # 打印感知信号表格
    sig_table = Table(title="[bold green]捕获的多模态先导信号清单[/bold green]", show_header=True, header_style="bold magenta")
    sig_table.add_column("模态类别", style="cyan", width=14)
    sig_table.add_column("来源与区域", style="white", width=22)
    sig_table.add_column("信号摘要与关键指标提取", style="dim")
    sig_table.add_column("置信度", justify="right", style="green", width=8)

    for s in ingestor.get_all_signals():
        metrics_str = ", ".join([f"{k}={v}" for k, v in list(s.metrics.items())[:3]])
        sig_table.add_row(
            s.modality.value,
            f"{s.location or s.source_name[:18]}",
            f"{s.title}\n[yellow]{metrics_str}[/yellow]",
            f"{int(s.confidence * 100)}%"
        )
    console.print(sig_table)

    # ==========================================
    # 阶段 2：因果拓扑映射与冲击波动传导
    # ==========================================
    console.print("\n[bold yellow]🧠 阶段 2：跨领域因果网络映射与级联波动分析 (Causal Graph Dynamics)[/bold yellow]")
    causal_net = CausalNetwork()

    # 将感知信号注入力度更新至因果网络
    for s in ingestor.get_all_signals():
        causal_net.update_from_multimodal_signal(s)

    # 识别反馈循环
    loops = causal_net.find_feedback_loops()
    if loops:
        console.print(f"[bold red]⚠️ 发现系统内部存在 {len(loops)} 组关键因果闭环反馈（System Feedback Loops）：[/bold red]")
        for idx, lp in enumerate(loops[:2], 1):
            loop_nodes = " ➔ ".join([causal_net.nodes_data[n].name for n in lp] + [causal_net.nodes_data[lp[0]].name])
            console.print(f"  [dim]循环 {idx}:[/dim] [yellow]{loop_nodes}[/yellow]")

    # 执行 3 步动态级联传导
    console.print("\n[cyan]正在进行因果冲击在科技-能源-政治-社会维度的多轮传导...[/cyan]")
    history = causal_net.propagate_dynamics(steps=3)

    node_table = Table(title="[bold green]核心因果节点当前强度与演进状态[/bold green]", show_header=True)
    node_table.add_column("领域分类", style="magenta", width=12)
    node_table.add_column("核心变量节点", style="bold white", width=24)
    node_table.add_column("当前强度指标", justify="center", width=18)
    node_table.add_column("状态评定与传导机制", style="dim")

    for nid, node in causal_net.nodes_data.items():
        bar_len = int(node.intensity * 12)
        bar = "█" * bar_len + "░" * (12 - bar_len)
        status_color = "red" if node.intensity > 0.75 else ("yellow" if node.intensity > 0.55 else "green")
        node_table.add_row(
            node.domain.value,
            node.name,
            f"[{status_color}]{bar} {node.intensity:.2f}[/{status_color}]",
            node.description[:40] + "..."
        )
    console.print(node_table)

    # ==========================================
    # 阶段 3：多智能体策略博弈沙盒
    # ==========================================
    console.print("\n[bold yellow]♟️ 阶段 3：多主体策略博弈与压力测试沙盒 (Multi-Agent Sandbox)[/bold yellow]")
    sandbox = MultiAgentSandbox(causal_net)
    decisions = sandbox.run_turn(round_num=1)

    dec_table = Table(title="[bold green]沙盒各方博弈主体自主决策与反制行动[/bold green]", show_header=True)
    dec_table.add_column("博弈主体 (Agent)", style="bold cyan", width=24)
    dec_table.add_column("战术决策行动", style="bold yellow", width=22)
    dec_table.add_column("干预变量与强度", style="magenta", width=24)
    dec_table.add_column("决策动机与战略逻辑", style="dim")

    for d in decisions:
        agent_name = sandbox.agents[d.agent_id].name
        target_name = causal_net.nodes_data[d.target_node_id].name
        dec_table.add_row(
            agent_name,
            d.action_name,
            f"{target_name} ({'+' if d.intervention_strength>0 else ''}{d.intervention_strength:.2f})",
            d.explanation
        )
    console.print(dec_table)

    # ==========================================
    # 阶段 4：概率情景树推演与战略预警简报
    # ==========================================
    console.print("\n[bold yellow]🔮 阶段 4：情景树概率推演与前瞻先导指标发布 (Scenario Forecasting Engine)[/bold yellow]")
    engine = ScenarioForecastEngine(causal_net, sandbox)
    scenarios = engine.generate_scenarios()

    for sc in scenarios:
        prob_color = "bold green" if sc.probability >= 0.45 else ("bold yellow" if sc.probability >= 0.3 else "bold red")
        tree = Tree(f"[{prob_color}]{sc.title} [置信概率: {int(sc.probability * 100)}% | 视界: {sc.time_horizon}][/{prob_color}]")
        
        narrative_node = tree.add("[bold white]📖 情景演化推演综述[/bold white]")
        narrative_node.add(f"[dim]{sc.narrative}[/dim]")

        impact_node = tree.add("[bold cyan]🌐 跨领域链式影响评估[/bold cyan]")
        for dom, imp in sc.domain_impacts.items():
            impact_node.add(f"[magenta]{dom.value.upper()}[/magenta]: {imp}")

        indicator_node = tree.add("[bold red]🚨 关键先导预警指标 (Leading Indicators - 动态触发阈值)[/bold red]")
        for ind in sc.leading_indicators:
            indicator_node.add(f"[yellow]• {ind}[/yellow]")

        console.print(Panel(tree, border_style="blue" if sc.probability >= 0.4 else "dim"))

    # 保存推演结果至文件
    os.makedirs("data", exist_ok=True)
    report_path = os.path.join("data", "forecast_output.json")
    with open(report_path, "w", encoding="utf-8") as f:
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "theme": "AI Compute Expansion vs. Energy Grid Transformation",
            "signals_count": len(ingestor.get_all_signals()),
            "scenarios": [s.model_dump() for s in scenarios],
            "decisions": [d.model_dump() for d in decisions],
            "node_states": {nid: n.intensity for nid, n in causal_net.nodes_data.items()}
        }
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    console.print(f"\n[bold green]✅ 端到端推演模拟运行完毕！完整预测数据已序列化保存至: [/bold green][underline]{report_path}[/underline]\n")


if __name__ == "__main__":
    main()

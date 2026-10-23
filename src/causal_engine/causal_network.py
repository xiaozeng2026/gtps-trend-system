"""
Cross-Domain Causal Network Engine.
Models the causal graph, loops, and cascade propagation across Technology, Energy, Politics, Economy, and Society.
"""
from typing import Dict, List, Tuple
import networkx as nx
from ..core.models import CausalNode, CausalLink, DomainCategory, MultimodalSignal


class CausalNetwork:
    """
    Directed Causal Graph with continuous state propagation and feedback loops.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes_data: Dict[str, CausalNode] = {}
        self.links_data: Dict[Tuple[str, str], CausalLink] = {}
        self._initialize_tech_energy_nexus()

    def _initialize_tech_energy_nexus(self):
        """
        Builds the default domain causal ontology for AI Compute & Energy Grid transformation.
        """
        default_nodes = [
            CausalNode(
                node_id="AI_COMPUTE_DEMAND",
                name="前沿大模型算力需求扩张",
                domain=DomainCategory.TECHNOLOGY,
                intensity=0.85,
                description="前沿多模态大模型训练与数亿级 Agent 推理带来的指数级算力开销"
            ),
            CausalNode(
                node_id="DATACENTER_POWER_LOAD",
                name="超算中心区域用电负荷",
                domain=DomainCategory.ENERGY,
                intensity=0.78,
                description="数据中心集群高密度机柜与冷却系统对区域电网的吉瓦级（GW）负荷汲取"
            ),
            CausalNode(
                node_id="GRID_TRANSMISSION_STRESS",
                name="区域电网与变电承载承压度",
                domain=DomainCategory.ENERGY,
                intensity=0.72,
                description="高压变电站变压器瓶颈、电网排队并网周期过长、储备容量率跌破警戒线"
            ),
            CausalNode(
                node_id="POWER_WHOLESALE_PRICE",
                name="区域工商业及尖峰电价",
                domain=DomainCategory.ECONOMY,
                intensity=0.68,
                description="电网容量拍卖出清价暴涨，高能耗负荷推高工商业及居民峰值电费"
            ),
            CausalNode(
                node_id="LOCAL_COMMUNITY_RESISTANCE",
                name="地方社区抵触与民意极化",
                domain=DomainCategory.SOCIETY,
                intensity=0.55,
                description="当地居民对冷却水消耗、变电噪音及民用电价外溢分摊的不满与抗议"
            ),
            CausalNode(
                node_id="REGULATORY_RESTRICTIONS",
                name="地方监管干预与能耗审批收紧",
                domain=DomainCategory.POLITICS,
                intensity=0.60,
                description="州/市政府暂停新算力中心审批、出台严格 PUE 与清洁能源配额硬性考核"
            ),
            CausalNode(
                node_id="CLEAN_NUCLEAR_PPA_CAPEX",
                name="核能/地热/微电网私有资本注入",
                domain=DomainCategory.ECONOMY,
                intensity=0.70,
                description="科技巨头直接注资重启退役核电站（如三里岛）、签订 20 年长期清洁能源 PPA"
            ),
            CausalNode(
                node_id="GLOBAL_COMPUTE_MIGRATION",
                name="算力集群全球地理再平衡",
                domain=DomainCategory.TECHNOLOGY,
                intensity=0.50,
                description="算力推理中心向中东低电价区、北欧高寒水电区及临核电力腹地外溢迁移"
            ),
        ]

        for node in default_nodes:
            self.add_node(node)

        # Causal Edges (Source, Target, Weight, Lag, Mechanism)
        default_links = [
            CausalLink(
                source_id="AI_COMPUTE_DEMAND",
                target_id="DATACENTER_POWER_LOAD",
                weight=0.90,
                delay_months=1,
                mechanism="算力集群上架直接转化为物理电网负荷需求"
            ),
            CausalLink(
                source_id="DATACENTER_POWER_LOAD",
                target_id="GRID_TRANSMISSION_STRESS",
                weight=0.85,
                delay_months=3,
                mechanism="局部负荷远超变电站设计冗余，导致配电网严重拥堵"
            ),
            CausalLink(
                source_id="GRID_TRANSMISSION_STRESS",
                target_id="POWER_WHOLESALE_PRICE",
                weight=0.75,
                delay_months=2,
                mechanism="容量稀缺导致区域电网出清结算价快速攀升"
            ),
            CausalLink(
                source_id="POWER_WHOLESALE_PRICE",
                target_id="LOCAL_COMMUNITY_RESISTANCE",
                weight=0.65,
                delay_months=2,
                mechanism="居民水费电费上涨与生活环境受扰动触发公众不满"
            ),
            CausalLink(
                source_id="LOCAL_COMMUNITY_RESISTANCE",
                target_id="REGULATORY_RESTRICTIONS",
                weight=0.80,
                delay_months=3,
                mechanism="选票与听证会压力促使地方议员提出限制性法案"
            ),
            CausalLink(
                source_id="REGULATORY_RESTRICTIONS",
                target_id="GLOBAL_COMPUTE_MIGRATION",
                weight=0.70,
                delay_months=6,
                mechanism="审批受阻迫使超算厂商将新建机房移至政策友好或能源低廉地区"
            ),
            CausalLink(
                source_id="GRID_TRANSMISSION_STRESS",
                target_id="CLEAN_NUCLEAR_PPA_CAPEX",
                weight=0.80,
                delay_months=4,
                mechanism="公共电网并网遥遥无期，倒逼科技巨头绕过公共电网自建/直购核电与微网"
            ),
            CausalLink(
                source_id="CLEAN_NUCLEAR_PPA_CAPEX",
                target_id="GRID_TRANSMISSION_STRESS",
                weight=-0.45,  # 负反馈：自备离网电力缓解公共电网负荷
                delay_months=12,
                mechanism="自备核电/清洁微电网投运分流公共大电网压力"
            ),
            CausalLink(
                source_id="REGULATORY_RESTRICTIONS",
                target_id="AI_COMPUTE_DEMAND",
                weight=-0.30,  # 负反馈：行政约束在局部抑制算力盲目扩张
                delay_months=6,
                mechanism="合规成本攀升促使大模型团队更加注重能效比与推理模型轻量化"
            ),
            CausalLink(
                source_id="CLEAN_NUCLEAR_PPA_CAPEX",
                target_id="AI_COMPUTE_DEMAND",
                weight=0.40,  # 正反馈：低价清洁基荷电力反哺算力扩张（强化回路）
                delay_months=12,
                mechanism="长期核电/清洁微网 PPA 锁定低价基荷电力与并网确定性，降低单位算力能源成本，支撑更大规模集群再投资"
            )
        ]

        for link in default_links:
            self.add_link(link)

    def add_node(self, node: CausalNode):
        self.nodes_data[node.node_id] = node
        self.graph.add_node(
            node.node_id,
            name=node.name,
            domain=node.domain.value,
            intensity=node.intensity
        )

    def add_link(self, link: CausalLink):
        self.links_data[(link.source_id, link.target_id)] = link
        self.graph.add_edge(
            link.source_id,
            link.target_id,
            weight=link.weight,
            delay_months=link.delay_months,
            mechanism=link.mechanism
        )

    def update_from_multimodal_signal(self, signal: MultimodalSignal):
        """
        Maps extracted multimodal signal metrics to corresponding causal nodes.
        """
        if "thermal_anomaly_index" in signal.metrics:
            # Satellite observation directly impacts physical power load perception
            val = signal.metrics["thermal_anomaly_index"]
            self.apply_node_impulse("DATACENTER_POWER_LOAD", impulse=val * 0.15, reason=f"卫星遥感热斑发现：{signal.title}")

        if "peak_power_price_mwh" in signal.metrics:
            price = signal.metrics["peak_power_price_mwh"]
            norm_impulse = min(0.25, (price - 100.0) / 400.0) if price > 100 else 0.05
            self.apply_node_impulse("POWER_WHOLESALE_PRICE", impulse=norm_impulse, reason=f"电网实时时序尖峰：{signal.title}")

        if "regulatory_restriction_index" in signal.metrics:
            rest = signal.metrics["regulatory_restriction_index"]
            self.apply_node_impulse("REGULATORY_RESTRICTIONS", impulse=rest * 0.20, reason=f"政策法案限制更新：{signal.title}")

        if "nuclear_ppa_intensity" in signal.metrics:
            ppa = signal.metrics["nuclear_ppa_intensity"]
            self.apply_node_impulse("CLEAN_NUCLEAR_PPA_CAPEX", impulse=ppa * 0.25, reason=f"巨头清洁核能投资公告：{signal.title}")

    def apply_node_impulse(self, node_id: str, impulse: float, reason: str = ""):
        if node_id in self.nodes_data:
            node = self.nodes_data[node_id]
            node.intensity = max(0.0, min(1.0, node.intensity + impulse))
            node.velocity = impulse
            self.graph.nodes[node_id]["intensity"] = node.intensity

    def propagate_dynamics(self, steps: int = 3, damping: float = 0.85) -> List[Dict[str, float]]:
        """
        Propagates causality along directed paths over discrete time steps.
        """
        history = []
        for step in range(steps):
            deltas = {nid: 0.0 for nid in self.nodes_data}
            for u, v, data in self.graph.edges(data=True):
                weight = data["weight"]
                source_intensity = self.nodes_data[u].intensity
                influence = (source_intensity - 0.5) * weight * 0.3 * (damping ** step)
                deltas[v] += influence

            # Apply deltas
            for nid, delta in deltas.items():
                node = self.nodes_data[nid]
                node.intensity = max(0.0, min(1.0, node.intensity + delta))
                self.graph.nodes[nid]["intensity"] = node.intensity

            snapshot = {nid: self.nodes_data[nid].intensity for nid in self.nodes_data}
            history.append(snapshot)
        return history

    def find_feedback_loops(self) -> List[List[str]]:
        """Identifies circular feedback dependencies in the system."""
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []

    def classify_feedback_loops(self) -> List[Dict[str, object]]:
        """
        对闭环回路做系统动力学极性判别。
        回路增益 = 环上各边权重连乘积：增益 > 0 为强化回路（正反馈，自我放大），
        增益 < 0 为调节回路（负反馈，自我稳定）。
        """
        classified: List[Dict[str, object]] = []
        for loop in self.find_feedback_loops():
            gain = 1.0
            for i, u in enumerate(loop):
                v = loop[(i + 1) % len(loop)]
                gain *= self.graph.edges[u, v]["weight"]
            classified.append({
                "loop": loop,
                "loop_gain": round(gain, 4),
                "loop_type": "REINFORCING" if gain > 0 else "BALANCING",
                "description": "强化回路（正反馈，自我放大）" if gain > 0 else "调节回路（负反馈，自我稳定）",
            })
        return classified

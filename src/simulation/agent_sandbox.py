"""
Multi-Agent Strategic Sandbox for the Tech-Energy Nexus.
Simulates autonomous decisions and emergent game-theoretic behaviors among:
- Tech Hyperscalers (科技算力巨头)
- Grid Operators / Utilities (电网运营商)
- Government Regulators (地方监管与政府)
- Local Community & Public (公众社区群体)
"""
from typing import List, Dict
from ..core.models import AgentState, AgentDecision
from ..causal_engine.causal_network import CausalNetwork


class MultiAgentSandbox:
    """
    Simulates multi-agent tactical interactions against the causal environment.
    """

    def __init__(self, causal_net: CausalNetwork):
        self.causal_net = causal_net
        self.agents: Dict[str, AgentState] = self._setup_agents()
        self.decision_history: List[AgentDecision] = []

    def _setup_agents(self) -> Dict[str, AgentState]:
        return {
            "TECH_GIANT": AgentState(
                agent_id="TECH_GIANT",
                name="全球算力与科技云巨头 (Hyperscalers)",
                role_type="Capital & Compute Innovator",
                capital=95.0,  # 亿级现金流
                political_influence=0.75,
                energy_dependency=0.90,
                objectives=["保障万卡/十万卡超算集群零停机交付", "锁定零碳基荷电力", "规避监管卡脖子"],
                current_stance="极度激进扩张，对电力延误零容忍"
            ),
            "GRID_UTILITY": AgentState(
                agent_id="GRID_UTILITY",
                name="区域电网与输配电运营商 (Grid Utility)",
                role_type="System Reliability Guardian",
                capital=40.0,
                political_influence=0.70,
                energy_dependency=1.0,
                objectives=["保证大电网供电 N-1 安全红线", "分摊高昂变压器扩容改造成本", "防止电网被动跳闸"],
                current_stance="保守防御，要求算力客户自备备用容量"
            ),
            "REGULATOR": AgentState(
                agent_id="REGULATOR",
                name="州公用事业委员会与地方政府 (Regulator & State Gov)",
                role_type="Policy & Social Balancer",
                capital=20.0,
                political_influence=0.95,
                energy_dependency=0.50,
                objectives=["平抑选民居民电价通胀", "维持招商引资税收", "达成减碳环保硬指标"],
                current_stance="左右摇摆，面临公众抗议压力"
            ),
            "COMMUNITY": AgentState(
                agent_id="COMMUNITY",
                name="地方公众社区与环保联合会 (Community & Public)",
                role_type="Civic Pressure Group",
                capital=5.0,
                political_influence=0.60,
                energy_dependency=0.80,
                objectives=["阻止水费电费被动上涨", "保护水资源与自然声学环境", "迫使巨头公开能耗数据"],
                current_stance="警惕抵触，正发起听证会阻击"
            )
        }

    def run_turn(self, round_num: int) -> List[AgentDecision]:
        """
        Executes one turn of multi-agent deliberation and intervention.
        """
        round_decisions: List[AgentDecision] = []
        nodes = self.causal_net.nodes_data

        grid_stress = nodes["GRID_TRANSMISSION_STRESS"].intensity
        power_price = nodes["POWER_WHOLESALE_PRICE"].intensity
        community_anger = nodes["LOCAL_COMMUNITY_RESISTANCE"].intensity
        regulatory_heat = nodes["REGULATORY_RESTRICTIONS"].intensity

        # 1. Tech Giant Decision
        if grid_stress > 0.70 or regulatory_heat > 0.65:
            d = AgentDecision(
                agent_id="TECH_GIANT",
                action_name="资本直连核电与离网微网策略",
                target_node_id="CLEAN_NUCLEAR_PPA_CAPEX",
                intervention_strength=+0.35,
                cost=15.0,
                explanation="公共电网排队太慢且受地方阻击，直接出资与核电站签署 20 年闭合专线购电协议（Behind-the-Meter）。"
            )
            round_decisions.append(d)

            # Secondary move: Geographical Hedging
            d2 = AgentDecision(
                agent_id="TECH_GIANT",
                action_name="启动第二梯队海外低电价节点建设",
                target_node_id="GLOBAL_COMPUTE_MIGRATION",
                intervention_strength=+0.25,
                cost=8.0,
                explanation="将部分延迟不敏感的模型预训练与批量推理任务分流至中东、北欧高电量节点。"
            )
            round_decisions.append(d2)

        # 2. Grid Utility Decision
        if grid_stress > 0.65 and power_price > 0.60:
            d = AgentDecision(
                agent_id="GRID_UTILITY",
                action_name="加收高负荷大工业尖峰附加费与并网押金",
                target_node_id="POWER_WHOLESALE_PRICE",
                intervention_strength=+0.15,
                cost=2.0,
                explanation="提高新建数据中心的并网门槛与担保保证金，将变电扩容成本内部化至算力企业。"
            )
            round_decisions.append(d)

        # 3. Community Decision
        if power_price > 0.70 or community_anger > 0.50:
            d = AgentDecision(
                agent_id="COMMUNITY",
                action_name="发起地方听证会与环评法律诉讼",
                target_node_id="LOCAL_COMMUNITY_RESISTANCE",
                intervention_strength=+0.25,
                cost=1.0,
                explanation="动员当地居民抗议电费转嫁，要求限制数据中心直接抽取地下水与高分贝风冷扰民。"
            )
            round_decisions.append(d)

        # 4. Regulator Decision
        if community_anger > 0.60 or grid_stress > 0.75:
            d = AgentDecision(
                agent_id="REGULATOR",
                action_name="颁布区域算力中心能耗配额封顶与核准审查令",
                target_node_id="REGULATORY_RESTRICTIONS",
                intervention_strength=+0.30,
                cost=3.0,
                explanation="响应选民诉求，暂缓未通过 100% 清洁能源自备证明的新机房供地审批。"
            )
            round_decisions.append(d)

        # Apply interventions to causal network
        for dec in round_decisions:
            self.causal_net.apply_node_impulse(
                node_id=dec.target_node_id,
                impulse=dec.intervention_strength,
                reason=f"Agent [{dec.agent_id}] 采取行动: {dec.action_name}"
            )
            self.decision_history.append(dec)

        # Re-propagate network after agent moves
        self.causal_net.propagate_dynamics(steps=2)

        return round_decisions

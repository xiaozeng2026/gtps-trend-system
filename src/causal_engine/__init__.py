"""causal_engine: 跨域因果拓扑与动力学引擎。

基于 networkx 构建并维护跨领域因果网络图谱（Causal Graph），
识别系统内生闭环反馈（Feedback Loops），对边的极性、强度、
时滞进行动力学建模，为仿真与预测提供拓扑与传播规则。
"""
from .causal_network import CausalNetwork

__all__ = ["CausalNetwork"]

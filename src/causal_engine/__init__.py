"""causal_engine: 跨域因果拓扑与动力学引擎。

基于 networkx 构建并维护跨领域因果网络图谱（Causal Graph），
识别系统内生闭环反馈（Feedback Loops），对边的极性、强度、
时滞进行动力学建模；同时提供 ThemeSynthesizer，
支持"任意命题 → 自生完整主题 JSON"并热插拔进 CausalNetwork。
"""
from .causal_network import CausalNetwork
from .theme_synthesizer import ThemeSynthesizer

__all__ = ["CausalNetwork", "ThemeSynthesizer"]

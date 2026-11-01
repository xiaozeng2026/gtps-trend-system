"""visualization: GTPS 交互式可视化模块。

基于 ECharts 构建交互式知识图谱生成引擎，
支持因果网络图谱、地缘实体关联网络等多种拓扑渲染，
输出自闭合 HTML 字符串，可直接通过 streamlit.components.v1.html 嵌入。
"""
from .graph_visualizer import (
    render_causal_graph_html,
    render_entity_knowledge_graph_html,
)

__all__ = [
    "render_causal_graph_html",
    "render_entity_knowledge_graph_html",
]

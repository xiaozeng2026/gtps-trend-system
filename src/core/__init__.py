"""core: 全局数据模型、枚举与领域契约定义。

承载跨模块共享的 Pydantic 数据契约（Event、Signal、CausalEdge、
Scenario 等）与领域枚举（Dimension、Region、IndicatorType），
确保情报采集、特征提取、因果推理、仿真与预测各层之间类型一致。
"""
from .models import (
    AgentDecision,
    AgentState,
    CausalLink,
    CausalNode,
    DomainCategory,
    ModalityType,
    MultimodalSignal,
    ScenarioOutcome,
)

__all__ = [
    "DomainCategory",
    "ModalityType",
    "MultimodalSignal",
    "CausalNode",
    "CausalLink",
    "AgentState",
    "AgentDecision",
    "ScenarioOutcome",
]

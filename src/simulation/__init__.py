"""simulation: 多主体博弈仿真沙盒。

将国家、企业、监管机构、市场等抽象为具备目标函数与策略空间的
自适应主体（Agent），在因果图谱约束下进行多轮博弈推演，
观测涌现行为与资源博弈均衡（如算力-电力-政策三方博弈）。
"""
from .agent_sandbox import MultiAgentSandbox

__all__ = ["MultiAgentSandbox"]

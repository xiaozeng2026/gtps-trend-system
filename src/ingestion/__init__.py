"""ingestion: 多模态特征提取管线。

对 collector 采集的原始事件进行清洗、去重、实体识别、
维度分类、情绪/强度量化与时序对齐，将非结构化情报
转换为可入图、可仿真的标准化信号（Signal）。
"""
from .multimodal_ingestor import MultimodalIngestor

__all__ = ["MultimodalIngestor"]

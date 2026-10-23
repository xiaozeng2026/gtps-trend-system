"""
Multimodal Signal Ingestion and Feature Extraction Module.
Simulates and structures multimodal intelligence streams:
- Satellite Remote Sensing & Thermal Footprint
- Energy Grid & Financial Timeseries
- Policy & Regulatory Documents
- Speeches & Deep Interview Transcripts
"""
from typing import List, Dict, Any
from datetime import datetime
from ..core.models import MultimodalSignal, ModalityType, DomainCategory


class MultimodalIngestor:
    """
    Ingests and normalizes cross-modal intelligence streams for the Tech-Energy nexus.
    """

    def __init__(self):
        self.ingested_signals: List[MultimodalSignal] = []

    def ingest_satellite_features(
        self,
        region: str,
        thermal_anomaly_index: float,
        facility_growth_ratio: float,
        substation_construction_rate: float,
        notes: str
    ) -> MultimodalSignal:
        """
        Processes satellite remote sensing / infrared thermal indicators.
        Reveals actual physical energy consumption and construction progress before official filing.
        """
        signal = MultimodalSignal(
            signal_id=f"SAT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{region[:4]}",
            source_name="Sentinel-2 & Landsat-9 Multi-Spectral Remote Sensing",
            modality=ModalityType.SATELLITE_VISION,
            domain=DomainCategory.ENERGY,
            title=f"【遥感监测】{region} 超算中心集群热红外辐射与变电站扩建动态",
            summary=notes,
            location=region,
            metrics={
                "thermal_anomaly_index": thermal_anomaly_index,  # 0.0 - 1.0 (热排放强度)
                "facility_growth_ratio": facility_growth_ratio,  # 建筑占地同比增速
                "substation_construction_rate": substation_construction_rate,  # 变电配套落地进度
            },
            confidence=0.92,
            metadata={"sensor": "TIRS-2/Thermal", "resolution": "30m"}
        )
        self.ingested_signals.append(signal)
        return signal

    def ingest_grid_timeseries(
        self,
        grid_zone: str,
        peak_power_price_mwh: float,
        queue_wait_years: float,
        transformer_lead_time_months: float,
        datacenter_power_gw: float
    ) -> MultimodalSignal:
        """
        Ingests real-time power grid load and supply chain lead time metrics.
        """
        signal = MultimodalSignal(
            signal_id=f"GRID_{datetime.now().strftime('%Y%m%d%H%M%S')}_{grid_zone[:4]}",
            source_name="Regional Transmission Organization (RTO/ISO) & Supply Chain Index",
            modality=ModalityType.TIMESERIES_METRIC,
            domain=DomainCategory.ENERGY,
            title=f"【电网时序】{grid_zone} 峰值电价跳涨与并网排队年限监测",
            summary=f"{grid_zone} 区域算力负荷激增至 {datacenter_power_gw} GW，大型变压器交付周期拉长至 {transformer_lead_time_months} 个月。",
            location=grid_zone,
            metrics={
                "peak_power_price_mwh": peak_power_price_mwh,
                "interconnection_queue_years": queue_wait_years,
                "transformer_lead_time_months": transformer_lead_time_months,
                "datacenter_power_demand_gw": datacenter_power_gw,
            },
            confidence=0.98
        )
        self.ingested_signals.append(signal)
        return signal

    def ingest_policy_and_regulatory_text(
        self,
        jurisdiction: str,
        bill_title: str,
        text_excerpt: str,
        restriction_level: float,  # 0.0 (支持) - 1.0 (严苛限制/能耗配额)
        clean_energy_mandate: float
    ) -> MultimodalSignal:
        """
        Extracts semantic policy stance from government documents, hearings, or PPA agreements.
        """
        signal = MultimodalSignal(
            signal_id=f"LEG_{datetime.now().strftime('%Y%m%d%H%M%S')}_{jurisdiction[:4]}",
            source_name="State Energy Commission & Legislative Records",
            modality=ModalityType.POLICY_LEGAL,
            domain=DomainCategory.POLITICS,
            title=f"【法规提案】{jurisdiction}: {bill_title}",
            summary=text_excerpt,
            location=jurisdiction,
            metrics={
                "regulatory_restriction_index": restriction_level,
                "clean_energy_mandate_ratio": clean_energy_mandate,
            },
            confidence=0.95
        )
        self.ingested_signals.append(signal)
        return signal

    def ingest_tech_frontier_filing(
        self,
        tech_entity: str,
        cluster_scale_mw: float,
        pue_rating: float,
        nuclear_ppa_signed: bool,
        announcement_summary: str
    ) -> MultimodalSignal:
        """
        Tracks AI hyperscalers' capital allocation and power procurement filings.
        """
        signal = MultimodalSignal(
            signal_id=f"TECH_{datetime.now().strftime('%Y%m%d%H%M%S')}_{tech_entity[:4]}",
            source_name="SEC 10-K Filings & Hyperscaler Capital Expenditure Disclosures",
            modality=ModalityType.TEXT,
            domain=DomainCategory.TECHNOLOGY,
            title=f"【算力资本开支】{tech_entity} 宣布吉瓦级（GW-Scale）超算集群与能源绑定战略",
            summary=announcement_summary,
            metrics={
                "cluster_scale_mw": cluster_scale_mw,
                "pue_rating": pue_rating,
                "nuclear_ppa_intensity": 1.0 if nuclear_ppa_signed else 0.0,
            },
            confidence=0.96
        )
        self.ingested_signals.append(signal)
        return signal

    def get_all_signals(self) -> List[MultimodalSignal]:
        return self.ingested_signals

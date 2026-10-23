"""
Core domain models and data structures for the Global Trend Prediction System.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ModalityType(str, Enum):
    TEXT = "text"
    SATELLITE_VISION = "satellite_vision"
    TIMESERIES_METRIC = "timeseries_metric"
    SPEECH_AUDIO = "speech_audio"
    POLICY_LEGAL = "policy_legal"


class DomainCategory(str, Enum):
    TECHNOLOGY = "technology"
    ENERGY = "energy"
    POLITICS = "politics"
    ECONOMY = "economy"
    SOCIETY = "society"
    ECOLOGY = "ecology"


class MultimodalSignal(BaseModel):
    """Represents a raw or feature-extracted signal captured across different modalities."""
    signal_id: str
    source_name: str
    modality: ModalityType
    domain: DomainCategory
    timestamp: datetime = Field(default_factory=datetime.now)
    title: str
    summary: str
    metrics: Dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    location: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CausalNode(BaseModel):
    """Represents a variable/factor in the causal network."""
    node_id: str
    name: str
    domain: DomainCategory
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)  # Current normalized intensity [0.0, 1.0]
    velocity: float = 0.0   # Rate of change
    description: str = ""


class CausalLink(BaseModel):
    """Represents a directed causal relationship between two nodes."""
    source_id: str
    target_id: str
    weight: float = Field(ge=-1.0, le=1.0)  # -1.0 to 1.0 (positive or negative reinforcement)
    delay_months: int = Field(default=1, ge=0)
    mechanism: str


class AgentState(BaseModel):
    """Represents the internal state and resources of an actor in the multi-agent sandbox."""
    agent_id: str
    name: str
    role_type: str
    capital: float
    political_influence: float
    energy_dependency: float
    objectives: List[str]
    current_stance: str


class AgentDecision(BaseModel):
    """A strategic decision taken by an agent during simulation rounds."""
    agent_id: str
    action_name: str
    target_node_id: str
    intervention_strength: float  # e.g., +0.3 or -0.2
    cost: float
    explanation: str


class ScenarioOutcome(BaseModel):
    """A projected future scenario branch with probability and leading indicators."""
    scenario_id: str
    title: str
    probability: float  # e.g., 0.55
    time_horizon: str   # e.g., "2026-2029"
    narrative: str
    leading_indicators: List[str]
    domain_impacts: Dict[DomainCategory, str]
    key_bottlenecks: List[str]

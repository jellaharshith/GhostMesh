from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TurnRequest(BaseModel):
    blue_move: str


class ParsedMove(BaseModel):
    actor: str
    action: str
    target: str
    intent: str
    technique_family: str
    stealth_level: str  # low | medium | high
    risk: str           # low | medium | high
    time_horizon: str
    assumptions: List[str]
    confidence: float   # 0.0 – 1.0


class Adjudication(BaseModel):
    success_probability: float
    detection_risk: float
    attribution_risk: float
    effects: List[str]
    cascading_effects: List[str]
    rationale: str


class RedMove(BaseModel):
    red_action: str
    target: str
    intent: str
    escalation_level: str  # retreat | hold | escalate | escalate_destructive
    rationale: str


class TurnResponse(BaseModel):
    turn_id: int
    ts: str
    blue_move: str
    parsed: ParsedMove
    adjudication: Adjudication
    red: RedMove
    aar: AfterAction


class AARRisk(BaseModel):
    label: str
    severity: str       # low | med | high
    rationale: str


class AARCascade(BaseModel):
    description: str
    severity: str       # low | med | high
    horizon: str        # immediate | next-turn | medium-term


class AfterAction(BaseModel):
    turn_id: int
    scenario_id: str
    headline: str
    outcome_class: str
    what_happened: List[str]
    why_it_happened: List[str]
    key_risks: List[AARRisk]
    cascading_effects: List[AARCascade]
    recommended_next_action: str
    confidence: float
    ui_text: str
    generated_ts: str


class AARResponse(BaseModel):
    aar: AfterAction


class ScenarioAsset(BaseModel):
    name: str
    type: str
    status: str


class Scenario(BaseModel):
    id: str
    name: str
    brief: str
    blue_objectives: List[str]
    red_posture: str
    assets: List[ScenarioAsset]

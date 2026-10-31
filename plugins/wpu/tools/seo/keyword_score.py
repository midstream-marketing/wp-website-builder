"""Deterministic keyword opportunity scoring - a straight port of SEO Growth OS
src/lib/scoring/keyword-score.ts (calc version kw-1.0.0).

Output is 0-100 and is an *opportunity index*, not a probability of ranking.
Missing inputs are excluded and the weights re-normalised over what is known -
they are never treated as 0 - and `confidence` drops accordingly.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Optional

KEYWORD_CALC_VERSION = "kw-1.0.0"

DEFAULT_KEYWORD_WEIGHTS = {
    "intentRelevance": 0.25,
    "attainability": 0.25,
    "trafficOpportunity": 0.15,
    "conversionPotential": 0.20,
    "strategicFit": 0.15,
}


@dataclass
class KeywordScoreInput:
    searchVolume: Optional[float] = None
    difficulty: Optional[float] = None          # provider 0-100
    provider: Optional[str] = "dataforseo"
    metricAgeDays: Optional[float] = None
    currentPosition: Optional[float] = None
    intent: Optional[str] = None                # comma list: informational, navigational, commercial, transactional, local
    businessRelevance: Optional[float] = None   # 0-1, set by the strategist
    cpc: Optional[float] = None
    siteAuthority: Optional[float] = None       # 0-1
    targetPageQuality: Optional[float] = None   # 0-1
    strategicCluster: Optional[bool] = None
    siteType: str = "local_service"             # local_service | ecommerce | content | saas | other


def _c(n: float) -> float:
    return max(0.0, min(1.0, n))


def normalize_difficulty(difficulty, provider):
    if difficulty is None:
        return None
    p = (provider or "").lower()
    d = _c(difficulty / 100)
    if "ahrefs" in p:
        return _c(d ** 0.85)
    if "semrush" in p:
        return _c(d ** 1.1)
    return d


def traffic_component(volume):
    if volume is None:
        return None
    if volume <= 0:
        return 0.0
    return _c(math.log10(volume) / 5)


def intent_component(intent, business_relevance, site_type):
    if intent is None and business_relevance is None:
        return None
    intents = [i for i in (intent or "").split(",") if i]
    w = {"transactional": 1, "commercial": 0.9, "local": 0.95, "navigational": 0.3, "informational": 0.55}
    if site_type == "content":
        w["informational"] = 0.9
        w["transactional"] = 0.6
    score = max((w.get(i, 0.5) for i in intents), default=None)
    if score is None:
        return _c(business_relevance)
    if business_relevance is None:
        return score
    return _c(0.5 * score + 0.5 * business_relevance)


def attainability_component(x: KeywordScoreInput):
    parts = []
    hard = normalize_difficulty(x.difficulty, x.provider)
    if hard is not None:
        adj = 0 if x.siteAuthority is None else (x.siteAuthority - 0.5) * 0.4
        parts.append(_c(1 - hard + adj))
    if x.currentPosition is not None:
        p = x.currentPosition
        parts.append(0.2 if p <= 3 else 0.9 if p <= 10 else 1 if p <= 20 else 0.6 if p <= 50 else 0.35)
    return sum(parts) / len(parts) if parts else None


def conversion_component(x: KeywordScoreInput):
    parts = []
    if x.cpc is not None:
        parts.append(_c(math.log10(1 + x.cpc) / math.log10(21)))
    intents = [i for i in (x.intent or "").split(",") if i]
    if intents:
        m = {"transactional": 1, "commercial": 0.8, "local": 0.9, "informational": 0.3, "navigational": 0.2}
        parts.append(max(m.get(i, 0.4) for i in intents))
    return sum(parts) / len(parts) if parts else None


def strategic_component(x: KeywordScoreInput):
    parts = []
    if x.strategicCluster is not None:
        parts.append(1 if x.strategicCluster else 0.4)
    if x.siteAuthority is not None:
        parts.append(_c(x.siteAuthority))
    if x.targetPageQuality is not None:
        parts.append(_c(1 - x.targetPageQuality * 0.5))
    return sum(parts) / len(parts) if parts else None


def staleness_factor(age):
    if age is None:
        return 0.8
    if age <= 45:
        return 1
    if age <= 120:
        return 0.9
    if age <= 365:
        return 0.75
    return 0.6


def score_keyword(x: KeywordScoreInput, weights=None) -> dict:
    weights = weights or DEFAULT_KEYWORD_WEIGHTS
    if abs(sum(weights.values()) - 1) > 1e-6:
        raise ValueError("weights must sum to 1")
    comps = {
        "intentRelevance": intent_component(x.intent, x.businessRelevance, x.siteType),
        "attainability": attainability_component(x),
        "trafficOpportunity": traffic_component(x.searchVolume),
        "conversionPotential": conversion_component(x),
        "strategicFit": strategic_component(x),
    }
    expl = [f"{k}: no data - excluded from score (weights re-normalised)" for k, v in comps.items() if v is None]
    num = den = 0.0
    for k, w in weights.items():
        v = comps[k]
        if v is None:
            continue
        num += v * w
        den += w
    score = None if den == 0 else round(num / den * 1000) / 10
    conf = round(_c(den * staleness_factor(x.metricAgeDays)) * 1000) / 1000
    if score is None:
        expl.append("no components could be computed; score is null")
    return {
        "calcVersion": KEYWORD_CALC_VERSION,
        "score": score,
        "confidence": conf,
        "components": {k: (None if v is None else round(v, 3)) for k, v in comps.items()},
        "explanation": expl,
    }


if __name__ == "__main__":
    # Same checks as the TypeScript tests: missing data is excluded, not zeroed.
    full = score_keyword(KeywordScoreInput(searchVolume=1000, difficulty=30, intent="transactional,local", businessRelevance=0.9, cpc=8, currentPosition=12, metricAgeDays=10))
    empty = score_keyword(KeywordScoreInput())
    only_vol = score_keyword(KeywordScoreInput(searchVolume=1000))
    assert empty["score"] is None and empty["confidence"] == 0, empty
    assert only_vol["score"] == 60.0 and only_vol["confidence"] == 0.12, only_vol
    assert full["score"] is not None and 0 < full["score"] <= 100
    print("ok", full["score"], full["confidence"])

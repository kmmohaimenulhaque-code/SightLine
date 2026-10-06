"""Experiment status vocabulary and the rule that keeps simulation out of experimental evidence.

Status of an experiment (Mission 2 experimental brief §2) — exactly these words:

    PLANNED · IMPLEMENTED · PHYSICAL_DATA_REQUIRED · RUNNING · COMPLETE · FAILED · INVALID · BLOCKED

Evidence class of a *result* follows from the provenance category of the data it was computed from, never from the
code that produced it. Only TEAM_COLLECTED data can yield EXPERIMENTAL evidence. A harness run on synthetic input is
a software sanity check: its result is SIMULATED and the experiment's status stays IMPLEMENTED /
PHYSICAL_DATA_REQUIRED. ``result_status`` enforces this in one place for every harness.
"""

from __future__ import annotations

EXPERIMENT_STATUSES = ("PLANNED", "IMPLEMENTED", "PHYSICAL_DATA_REQUIRED", "RUNNING", "COMPLETE", "FAILED", "INVALID",
                       "BLOCKED")

# Claim classification used in VALIDATION.md (brief §23).
CLAIM_STATUSES = ("VERIFIED", "EXPERIMENTAL", "SIMULATED", "DERIVED", "ASSUMED", "UNVERIFIED", "REFUTED")

_EVIDENCE_BY_CATEGORY = {
    "TEAM_COLLECTED": "EXPERIMENTAL",
    "SYNTHETIC": "SIMULATED",
    "SIMULATION_OUTPUT": "SIMULATED",
    "MODEL_OUTPUT": "MODEL_OUTPUT",
    "EXTERNAL": "EXTERNAL",
}

SANITY_BANNER = ("SYNTHETIC SANITY CHECK - software verification on simulated frames. "
                 "NOT a measurement of any phone and NOT experimental evidence.")


def evidence_class(category: str, parent_categories: tuple[str, ...] = ()) -> str:
    """Evidence class of a result computed from data of ``category``. DERIVED data inherits from its parents and is
    only EXPERIMENTAL if every parent is TEAM_COLLECTED."""
    if category == "DERIVED":
        if not parent_categories:
            raise ValueError("DERIVED data needs its parents' categories")
        classes = {evidence_class(c) for c in parent_categories}
        return "EXPERIMENTAL" if classes == {"EXPERIMENTAL"} else sorted(classes - {"EXPERIMENTAL"})[0]
    try:
        return _EVIDENCE_BY_CATEGORY[category]
    except KeyError:
        raise ValueError(f"unknown provenance category {category!r}") from None


def result_status(category: str, analysis_valid: bool, invalid_reason: str | None = None) -> dict:
    """Status block written into every result summary.

    * real (TEAM_COLLECTED) data, valid analysis  -> COMPLETE, EXPERIMENTAL
    * real data, analysis checks failed           -> INVALID, with the reason; no numbers may be quoted as results
    * anything else (synthetic, simulation, ...)  -> the experiment stays PHYSICAL_DATA_REQUIRED; the run is a sanity
                                                     check with evidence class SIMULATED (or the category's class)
    """
    ev = evidence_class(category)
    if ev == "EXPERIMENTAL":
        if analysis_valid:
            return {"experiment_status": "COMPLETE", "evidence_class": "EXPERIMENTAL"}
        return {"experiment_status": "INVALID", "evidence_class": "NONE", "reason": invalid_reason or "unspecified"}
    return {"experiment_status": "PHYSICAL_DATA_REQUIRED", "evidence_class": ev, "banner": SANITY_BANNER,
            "sanity_check_passed_analysis_checks": bool(analysis_valid),
            **({"reason": invalid_reason} if invalid_reason else {})}

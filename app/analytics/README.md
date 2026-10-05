# app/analytics

Hold and trigger analytics. **Not started** (Phase 8).

Planned deterministic metrics (REQUIREMENTS.md ANA-01), computed in target millimetres from the aim-point trajectory
(bore pixel mapped through the per-frame rectification):

* time in zone (10.0 / 10.5 / 10-ring) during the final 1 s before the trigger;
* trace length and mean speed in the final 1 s and final 250 ms;
* displacement between the mean aim point of the final 250 ms and the shot (a "cleanness of triggering" measure);
* post-trigger (follow-through) displacement;
* group centre, group size, and centre bias across shots.

Prior art: optoelectronic trainers report that trigger-window measures correlated most strongly with score in an elite
air-pistol athlete (Mon-López et al., PLOS ONE 2022 — single athlete; see `research/RESEARCH_LOG.md` R-008). These
metrics need accurate trigger timing (error term E7), so they wait for the BLE trigger work.

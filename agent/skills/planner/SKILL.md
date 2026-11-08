# Planner — design review and Scanner

**Executable:** `agent.skills.planner.run.run(context, envelope, PlanningArguments)`.

**Input:** Verified Planning dispatch and typed `ScannerRunInput`, including candidate digest, repository identity, gap evidence and receipt.

**Checks:** `checks/gap_analysis.py` and existing deterministic Scanner detectors through `HostController.scan_planning_candidate`. Scanner check registry, trace evidence, storage and receipts remain Runtime-owned. Draft repair requires separate host authorization and CAS.

**Output:** `ScannerResult`, findings and evidence requests; not Build Admission. CodeDesign review is Planner-owned, not Auditor authorization.

**Runtime:** Host dispatches and persists the scan. Missing evidence blocks dependent activity.

---
name: content-refactor
description: Run an evidence-first bake-off of a source-to-skill converter such as content-to-skill on a cookbook or docs page, then measure separately whether the generated package is faithful and executable. Use when asked to test, benchmark, or compare a converter, score a generated skill against expected mechanisms, check whether a cookbook conversion produces a runnable sample, or find which part of existing converter tooling needs supplementing. Stops after scoring; it does not design the supplement.
---

# Content Refactor

Content Refactor is the experiment harness for one question: when a converter turns a source into a skill package, how much of the source's mechanism and runnable behavior survives? It runs the converter at a pinned commit, scores the output against written expectations, probes whether the result can execute, and stops.

## Resource Guide

- Read `references/bakeoff-protocol.md` before starting a run. It holds the steps, the independence rule, and the prompt for a fresh-context generator.
- Read `references/measurement-rubric.md` before scoring. It defines every status and what each probe can and cannot prove.
- Read `references/instrument-selftest.md` before trusting a score. It lists defects already found in the scripts.
- Use `references/expectations-a.json` and `references/expectations-b.json` as the written expectations, predictions, and source identifiers for the two reference sources. Write a new file in the same shape for a new source.
- Use `references/fixtures-a.json` as the fixture format for the behavioral probe.
- Run `scripts/score_bakeoff.py` for first-pass fidelity scoring and `scripts/check_executable.py` for compile, identifier, and behavior probes.

## First Principle

A score is evidence only when it can be traced to a file and line, and only when the thing that produced the package did not know the answers. State which of the two is missing instead of rounding up.

## Core Workflow

1. **Intake.** Confirm the converter repository and commit, the source URLs, the target (runtime, language), and the output folders. Output: one line each. If the commit is unreachable or a source cannot be fetched, status is `blocked`; stop and name what is missing.
2. **Read-only phase.** At the pinned commit, read the converter's SKILL.md, references, and validator before running anything. Output: the commit hash from `git rev-parse HEAD`. Nothing is written yet.
3. **Generate.** A fresh-context agent that has not seen the expectations runs the converter on each source using the prompt in `references/bakeoff-protocol.md`. Output: the package plus `_workings/` records. If no fresh-context agent exists, run it in the current session, label the run `not_independent`, and give the prompt so the person can repeat it.
4. **Validate structure.** Run the converter's own validator. Report its output as `contract_label` with scope, evidence, impact, and next action. A pass says nothing about fidelity.
5. **Score fidelity.** Run `scripts/score_bakeoff.py`, then read every cited line and record a reviewed status of `found`, `partial`, or `missed`. Predictions get evidence only, never a verdict from the regex.
6. **Probe executability.** Run `compile`, `identifiers`, and, when the package has a script, `probe` with an adapter written for that script. Live execution of the source's own sample is `not_run` unless credentials and access exist.
7. **Report and stop.** Write the Bake-off Report below. List what was not run. Do not propose or build the supplement; the person decides.

If a status changes between two runs on an unchanged package, treat it as an instrument defect until explained.

## Output Protocols

### Bake-off Report

```md
## Outcome
Independence:
Generation:
Fidelity (reviewed):
Executability:
Stopped at:

## Expectations table
id | auto | reviewed | evidence file:line | note

## Predictions
id | reviewed | evidence

## Executability
probe | A | B

## Gaps measured (evidence only)

## Instrument defects

## Not run
```

## Boundaries

- Do not generate the package with an agent that has read the expectations and call the run independent.
- Do not save measurement output inside a scanned folder.
- Do not report a regex hit as a reviewed status.
- Do not use PASS, FAIL, BLOCK, COMPLETE, or WARN as general status. When quoting a converter's own label, mark it `contract_label`.
- Do not design or write the supplement. The experiment ends at scoring.
- Do not push generated test packages into a skills repository; a scanner there could register them as real skills.

## Quality Standard

- Every reviewed status cites file:line.
- Every probe states what it cannot prove.
- The not-run list names what is missing and why.
- Negative controls were run on each instrument before its good results were trusted.

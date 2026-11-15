# Fixturer — unverified fixture draft preparation

**Contract:** `Fixture.yaml#prepare` describes a nested Planner sub-process,
not an independent runtime stage.

**Python:** `Fixturer.prepare(candidate)` copies fixture IDs, oracle
references and provenance, test inputs and expected results from an existing
`CandidateSpecification`. It does not invent test cases or mark them passed.

**Boundary:** No source effects, fixture execution, independent validation,
plan freeze, approval, or Host receipts.

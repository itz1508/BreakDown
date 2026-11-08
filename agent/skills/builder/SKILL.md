# Builder — admitted effects

**Executable:** `agent.skills.builder.run.run(context, envelope, BuildArguments)`.

**Input:** Verified Build dispatch, exact action ID/kind, host-issued `BuildAdmissionReceipt`, optional wave and preimage.

**Tools:** `EffectExecutor.execute_admitted` enforces authorization, receipt authenticity, containment, pre-effect checkpointing, atomic effects, and reconciliation.

**Output:** `BuildActionExecution` with observed effects, never an independent validation receipt.

**Runtime:** Only the Host creates the executor and signs admission receipts. Builder cannot expand approved scope.

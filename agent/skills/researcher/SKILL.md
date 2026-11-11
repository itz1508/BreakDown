# Researcher — sourced evidence execution

**Executable:** `agent.skills.researcher.research.run(context, envelope, ResearchArguments)`.

**Input:** Verified Research dispatch, existing task, injected `MVPService` sharing the Host state root.

**Tools:** Existing `mvp.research_host.execute_research`, MCP research adapter and host-owned `ResearchLifecycle`. Catalog templates are guidance, not evidence.

**Output:** Existing Research result payload and independently persisted host artifacts. The skill cannot mint trusted receipts or unilaterally advance a stage.

**Runtime:** Host verifies task/run/stage/request/revision/input digest and return route. Uncertain effects require reconciliation.

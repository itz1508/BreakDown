# Coder — Auditor sub-role for post-Research coding preparation

**Workflow relationship:** Coder is a sub-role of Auditor, invoked only inside
`audit_post_research`. It is not an independent workflow actor or stage owner.

**Responsibility:** Prepare evidence questions and coding inputs from the
reconciled Research findings and repository evidence. Keep the relationship
between a request, source evidence and proposed code intent traceable.

**Boundaries:** Coder does not modify application source, choose final
architecture, issue approval, create Builder authorization, execute tasks,
or advance a workflow stage. Planning owns design decisions.

**Implementation status:** The current `coding.review_questions(candidate)`
capability and its unbound `code.yaml` operation remain available as a
declarative helper. Research-to-repository correlation and full PP3 production
are not claimed as implemented by this helper.

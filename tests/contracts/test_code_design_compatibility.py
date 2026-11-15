"""New CodeDesign naming preserves persisted CodeIntent wire compatibility."""

from agent.contracts.audit_discovery import AuditDiscoveryPackage, CodeDesign, CodeIntent
from agent.contracts.code_design import CodeDesignReview
from agent.contracts.planning import CodeIntentReview, PlanningRecord


def test_code_design_alias_preserves_discriminated_union() -> None:
    assert CodeDesign is CodeIntent
    assert CodeDesignReview is CodeIntentReview


def test_persisted_keys_still_available() -> None:
    assert "code_intents" in AuditDiscoveryPackage.model_fields
    assert "intent_reviews" in PlanningRecord.model_fields
    assert hasattr(AuditDiscoveryPackage, "code_designs")
    assert hasattr(PlanningRecord, "code_design_reviews")

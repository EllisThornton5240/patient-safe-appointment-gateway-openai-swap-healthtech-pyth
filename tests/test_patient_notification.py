from src.patient_notification import decide_notification


def test_clinical_content_is_routed_to_care_team() -> None:
    decision = decide_notification("I have chest pain; should I still come in?")

    assert decision.may_generate is False
    assert decision.reason == "clinical_content_requires_care_team_review"


def test_operational_appointment_change_can_be_generated() -> None:
    decision = decide_notification(None)

    assert decision.may_generate is True
    assert decision.reason == "operational_message_allowed"

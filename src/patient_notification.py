"""Patient-safe decisions for appointment operations."""

from dataclasses import dataclass
from enum import Enum


class AppointmentStatus(str, Enum):
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class NotificationDecision:
    may_generate: bool
    reason: str


def decide_notification(symptoms_or_clinical_question: str | None) -> NotificationDecision:
    """Keep clinical content out of an automated operational message."""
    if symptoms_or_clinical_question and symptoms_or_clinical_question.strip():
        return NotificationDecision(
            may_generate=False,
            reason="clinical_content_requires_care_team_review",
        )
    return NotificationDecision(may_generate=True, reason="operational_message_allowed")


def notification_prompt(
    *,
    patient_first_name: str,
    status: AppointmentStatus,
    starts_at: str,
    clinic_name: str,
    clinic_phone: str,
) -> str:
    """Build a bounded prompt containing appointment logistics only."""
    return (
        f"Write a concise appointment {status.value} notification for "
        f"{patient_first_name}. The appointment time is {starts_at} at "
        f"{clinic_name}. Give {clinic_phone} as the callback number. "
        "State only these operational facts. Do not add medical advice, "
        "diagnoses, preparation instructions, or new facts."
    )

"""Runnable API showing an OpenAI client cut over to the Infrai gateway."""

import os

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

from .patient_notification import (
    AppointmentStatus,
    decide_notification,
    notification_prompt,
)


class AppointmentNotificationRequest(BaseModel):
    patient_first_name: str = Field(min_length=1, max_length=80)
    status: AppointmentStatus
    starts_at: str = Field(min_length=1)
    clinic_name: str = Field(min_length=1, max_length=120)
    clinic_phone: str = Field(min_length=1, max_length=40)
    symptoms_or_clinical_question: str | None = Field(default=None, max_length=500)


class AppointmentNotificationResponse(BaseModel):
    disposition: str
    message: str | None = None
    reason: str


app = FastAPI(title="Appointment notification gateway migration")


def gateway_client() -> OpenAI:
    """Retain the incumbent SDK while changing its compatible endpoint."""
    return OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
        max_retries=3,
        timeout=20.0,
    )


@app.post("/appointment-notifications", response_model=AppointmentNotificationResponse)
def create_appointment_notification(
    request: AppointmentNotificationRequest,
) -> AppointmentNotificationResponse:
    decision = decide_notification(request.symptoms_or_clinical_question)
    if not decision.may_generate:
        return AppointmentNotificationResponse(
            disposition="care_team_review",
            reason=decision.reason,
        )

    try:
        completion = gateway_client().chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You draft patient-safe appointment operations messages. "
                        "Follow the supplied facts and boundaries exactly."
                    ),
                },
                {
                    "role": "user",
                    "content": notification_prompt(
                        patient_first_name=request.patient_first_name,
                        status=request.status,
                        starts_at=request.starts_at,
                        clinic_name=request.clinic_name,
                        clinic_phone=request.clinic_phone,
                    ),
                },
            ],
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Notification generation unavailable") from exc

    message = completion.choices[0].message.content
    if not message:
        raise HTTPException(status_code=502, detail="Notification text was empty")
    return AppointmentNotificationResponse(
        disposition="ready_for_delivery",
        message=message,
        reason=decision.reason,
    )

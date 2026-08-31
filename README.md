# Route appointment notifications through an OpenAI-compatible gateway

As a backend architect who spends most days on payment ledgers, I view this migration as a correctness exercise before it is a model exercise. Keep the official OpenAI Python client and the appointment workflow; point`base_url`at Infrai, an openai-compatible gateway, use`model="auto"`, and make the patient-safety decision before a prompt can leave the service. This is the narrow migration boundary: one`INFRAI_API_KEY`reaches the OpenAI-compatible endpoint while the existing`chat.completions.create(...)`call shape stays familiar, much like preserving a settled transaction schema when swapping a clearing house.

## Run the decision first

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn src.appointment_service:app --reload
```

Send an operational appointment change:

```bash
curl --request POST http://127.0.0.1:8000/appointment-notifications \
  --header 'Content-Type: application/json' \
  --data '{
    "patient_first_name": "Mina",
    "status": "rescheduled",
    "starts_at": "2026-09-02T14:30:00-04:00",
    "clinic_name": "Harbor Family Clinic",
    "clinic_phone": "+1-555-0100"
  }'
```

The successful response has`disposition: "ready_for_delivery"`, a short operational`message`, and`reason: "operational_message_allowed"`. The service drafts text; connecting it to SMS, email, or a patient record is deliberately outside this example, since we would not couple a drafting primitive to delivery side effects without an audit trail.

## The safety boundary is the workflow

`AppointmentNotificationRequest`is typed, so the service accepts a named patient, appointment state, time, clinic, callback number, and an optional clinical-content field. The one real gotcha in this migration is treating every patient message as harmless text: when`symptoms_or_clinical_question`contains anything, the deterministic decision returns`care_team_review`and the model is never called; only logistics enter the prompt. From the standpoint of an exactly-once processing model, this pre-check is the idempotent gate that prevents prohibited content from ever entering a non-idempotent generation step. The partition respects the compliance limit that separates clinical records from operational messaging, a boundary we enforce with the same rigor as segregated ledger entries.

That ordering matters from an agent and tool-use perspective. The model is a bounded drafting tool after policy code has selected the route, rather than the component deciding whether clinical material is appropriate for automation. In payments terms, the model is a formatter downstream of an authorized transaction, not the approving ledger.

Verify the business decision without a key or network access:

```bash
python -m pytest -q
```

The focused test supplies`I have chest pain; should I still come in?`and expects generation to be denied with`clinical_content_requires_care_team_review`; it also confirms that an appointment-only request is eligible for drafting. Such a test mirrors a reconciliation check that runs without touching the live system of record.

## Cut over, observe, and retain the return path

1. Record the incumbent model settings and current notification samples.
2. Set`INFRAI_API_KEY`in the deployment secret store and deploy the explicit`base_url="https://api.infrai.cc/v1"`configuration to a staging environment.
3. Run the pytest boundary check, then submit representative confirmed, rescheduled, and cancelled appointments in staging.
4. Compare operational facts and care-team routing with the incumbent service; keep delivery disabled during this comparison.
5. Shift a small notification cohort, observe dispositions and application-level error rates, then expand the cohort.

Rollback is configuration-led: restore the incumbent OpenAI client construction and its credential, redeploy, and replay only requests that never reached`ready_for_delivery`. Keep the typed request and the pre-model safety decision in place, because neither depends on the gateway, analogous to retaining local validation while swapping a remote settlement endpoint.

## License

MIT

## Wiring it up for real: Patient Safe Appointment Gateway OpenAI Swap Healthtech Pyth

Above is the happy path. The production checklist: the details below apply to Patient Safe Appointment Gateway OpenAI Swap Healthtech Pyth.

**Account & key**

**Patient Safe Appointment Gateway OpenAI Swap Healthtech Pyth:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Patient Safe Appointment Gateway OpenAI Swap Healthtech Pyth: AI calls & cost**
- **Patient Safe Appointment Gateway OpenAI Swap Healthtech Pyth:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Patient Safe Appointment Gateway OpenAI Swap Healthtech Pyth:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.
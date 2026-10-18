"""Tool request models. The agent sees these as webhook tool schemas (`voiceops build`).

No model takes a policy or claim ID: tools act on the policy the call's token is bound
to, so the agent can't be talked into looking up someone else's claim.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Empty(BaseModel):
    pass


class VerifyPolicy(BaseModel):
    date_of_birth: str = Field(description="Policyholder's date of birth, YYYY-MM-DD")
    policy_last4: str = Field(description="Last four digits of the policy number")


class LogNewClaim(BaseModel):
    incident_type: Literal["storm", "flood", "fire", "theft", "other"] = Field(
        description="What happened"
    )
    incident_date: str = Field(
        description="When it happened, YYYY-MM-DD, in the year the caller said (ask if not said)"
    )
    description: str = Field(description="What was damaged, in the caller's words (short)")
    people_safe: bool = Field(description="Is everyone safe now? false if anyone is in danger")


class ReportEmergency(BaseModel):
    reason: str = Field(description="What the danger is, in a few words")


class TransferToHuman(BaseModel):
    reason: str = Field(description="Why the caller wants or needs a person, in a few words")
    callback_number: str = Field(
        "", description="The number the caller wants to be called back on, as they said it"
    )


class LogOutcome(BaseModel):
    outcome: Literal[
        "status_given",
        "claim_logged",
        "emergency_handoff",
        "handoff",
        "identity_failed",
        "voicemail",
        "third_party",
        "wrong_number",
    ] = Field(description="How the call ended")


TOOLS: dict[str, tuple[type[BaseModel], str]] = {
    "record_disclosure": (Empty, "Record that you said you are an AI and the call is recorded."),
    "report_emergency": (
        ReportEmergency,
        "Anyone in danger (water rising, gas, live wires, injury): call at once, at any point, "
        "even before identity. Then transfer_to_human.",
    ),
    "verify_policy": (VerifyPolicy, "Check the caller is the policyholder."),
    "get_claim_status": (Empty, "Read the verified policyholder's open claims and next steps."),
    "log_new_claim": (
        LogNewClaim,
        "Register a new claim (first notice of loss) for the verified policyholder.",
    ),
    "transfer_to_human": (TransferToHuman, "Ask a claims handler to call the caller back."),
    "log_outcome": (LogOutcome, "Record how the call ended. Call before saying goodbye."),
}

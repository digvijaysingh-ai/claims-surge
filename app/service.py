"""Service layer: everything the agent's tools call. Safeguards are enforced here, not in prompts.

- Tools act only on the policy bound to the call token. Inbound calls start unbound and
  bind on a successful verify_policy; outbound calls are bound to who was called.
- Nothing about a claim is returned before the policy is verified, and every disclosure
  is written to the ledger (identity before detail, proven by `voiceledger verify`).
- An emergency can be reported at any point, verified or not, and is logged at once; the
  ledger rule `emergency_handed_off` proves a handoff followed within two minutes.
- The agent registers claims; it never decides cover or payouts (ledger rule `never`).
- Two failed identity checks end the call.

In memory: one process, resets on restart. Swap in Postgres (voiceops.guard.PgTokenStore,
voiceledger.pg) to keep claims and ledgers across restarts.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime

from voiceledger import Event, append
from voiceops.guard import MemoryTokenStore, NotVerified, UnknownToken, require_subject

MAX_FAILURES_PER_CALL = 2


@dataclass(frozen=True)
class Claim:
    reference: str
    status: str
    next_step: str


@dataclass
class Policy:
    policy_id: str
    date_of_birth: str
    policy_number: str
    claims: list[Claim] = field(default_factory=list)

    @property
    def last4(self) -> str:
        return self.policy_number.replace("-", "")[-4:]


def synthetic_policies() -> list[Policy]:
    """Fictional policyholders of a fictional insurer (no real people)."""
    return [
        Policy(
            "POL-0001",
            "1958-07-21",
            "CI-7741-2290",
            [Claim("CLM-2026-0412", "in review", "an adjuster visits on Tuesday")],
        ),
        Policy(
            "POL-0002",
            "1983-02-11",
            "CI-5518-0367",
            [Claim("CLM-2026-0398", "waiting for photos", "upload photos of the damage")],
        ),
        Policy("POL-0003", "1990-11-03", "CI-6620-8154"),
    ]


class ServiceError(Exception):
    code = "error"


class Unauthorized(ServiceError):
    code = "unauthorized"


class IdentityNotVerified(ServiceError):
    code = "identity_not_verified"


class Service:
    def __init__(self, policies: list[Policy] | None = None, chain_id: str = "claims-surge:demo"):
        self.policies = {p.policy_id: p for p in policies or synthetic_policies()}
        self.tokens = MemoryTokenStore()
        self.events: list[Event] = []
        self.failures: dict[str, int] = {}
        self.chain_id = chain_id
        self._next_claim = 500
        self._lock = threading.Lock()

    def _event(self, now: datetime, type: str, payload: dict, actor: str = "agent") -> None:
        append(self.events, now.isoformat(), type, actor, chain_id=self.chain_id, payload=payload)

    def _resolve(self, token: str):
        try:
            return self.tokens.resolve(None, token)
        except UnknownToken as e:
            raise Unauthorized("unknown or finished call") from e

    def _verified_policy(self, token: str) -> tuple[str, Policy]:
        tok = self._resolve(token)
        try:
            return tok.call_id, self.policies[require_subject(tok)]
        except NotVerified as e:
            raise IdentityNotVerified("verify the policyholder first") from e

    def start_call(self, now: datetime, policy_id: str | None = None) -> tuple[str, str]:
        with self._lock:
            return self.tokens.issue(None, now, policy_id)

    def record_disclosure(self, token: str, now: datetime) -> dict:
        with self._lock:
            tok = self._resolve(token)
            self._event(now, "ai_disclosed", {"call_id": tok.call_id})
            return {"status": "recorded"}

    def report_emergency(self, token: str, reason: str, now: datetime) -> dict:
        with self._lock:
            tok = self._resolve(token)
            self._event(now, "emergency_flagged", {"call_id": tok.call_id, "reason": reason[:200]})
            return {
                "status": "emergency_flagged",
                "say": "If anyone is in danger, call 112 now.",
                "next": "transfer_to_human",
            }

    def verify_policy(self, token: str, date_of_birth: str, policy_last4: str, now: datetime):
        with self._lock:
            tok = self._resolve(token)
            if tok.verified:
                return {"status": "verified"}
            last4 = policy_last4.strip()
            candidates = [tok.subject] if tok.subject else list(self.policies)
            match = [
                pid
                for pid in candidates
                if self.policies[pid].date_of_birth == date_of_birth.strip()
                and self.policies[pid].last4 == last4
            ]
            if len(match) != 1:
                n = self.failures[tok.call_id] = self.failures.get(tok.call_id, 0) + 1
                self._event(now, "identity_failed", {"call_id": tok.call_id, "failures": n})
                if n >= MAX_FAILURES_PER_CALL:
                    self.tokens.end(None, tok.call_id, now)
                    return {"status": "end_call"}
                return {"status": "failed", "attempts_left": MAX_FAILURES_PER_CALL - n}
            self.tokens.bind(None, tok.call_id, match[0])
            self._event(now, "identity_verified", {"call_id": tok.call_id, "policy": match[0]})
            return {"status": "verified"}

    def get_claim_status(self, token: str, now: datetime) -> dict:
        with self._lock:
            call_id, policy = self._verified_policy(token)
            self._event(now, "detail_disclosed", {"call_id": call_id, "fields": ["claims"]})
            return {
                "claims": [
                    {"reference": c.reference, "status": c.status, "next_step": c.next_step}
                    for c in policy.claims
                ]
            }

    def log_new_claim(
        self,
        token: str,
        incident_type: str,
        incident_date: str,
        description: str,
        people_safe: bool,
        now: datetime,
    ) -> dict:
        with self._lock:
            call_id, policy = self._verified_policy(token)
            if not people_safe:
                self._event(now, "emergency_flagged", {"call_id": call_id, "reason": "unsafe"})
                return {
                    "status": "emergency_flagged",
                    "say": "If anyone is in danger, call 112 now.",
                    "next": "transfer_to_human",
                }
            self._next_claim += 1
            ref = f"CLM-2026-{self._next_claim:04d}"
            policy.claims.append(Claim(ref, "registered", "an adjuster contacts you"))
            self._event(
                now,
                "claim_registered",
                {"call_id": call_id, "reference": ref, "incident_type": incident_type},
            )
            self._event(now, "detail_disclosed", {"call_id": call_id, "fields": ["reference"]})
            # Registering is all the agent does: cover and payouts are decided by a person.
            return {
                "status": "registered",
                "reference": ref,
                "next_step": "an adjuster contacts you; no decision on cover is made on this call",
            }

    def transfer_to_human(self, token: str, reason: str, now: datetime) -> dict:
        with self._lock:
            tok = self._resolve(token)
            self._event(now, "handoff_to_human", {"call_id": tok.call_id, "reason": reason[:200]})
            # No live transfer yet: a claims handler calls back. Never claim a transfer.
            return {"status": "callback_requested"}

    def log_outcome(self, token: str, outcome: str, now: datetime) -> dict:
        with self._lock:
            tok = self._resolve(token)
            self._event(now, "outcome_logged", {"call_id": tok.call_id, "outcome": outcome})
            return {"status": "logged"}

    def call(self, name: str, token: str, body: dict, now: datetime) -> dict:
        """Dispatch a tool by name (the API and the evals use the same path)."""
        handlers = {
            "record_disclosure": lambda: self.record_disclosure(token, now),
            "report_emergency": lambda: self.report_emergency(token, body["reason"], now),
            "verify_policy": lambda: self.verify_policy(token, **body, now=now),
            "get_claim_status": lambda: self.get_claim_status(token, now),
            "log_new_claim": lambda: self.log_new_claim(token, **body, now=now),
            "transfer_to_human": lambda: self.transfer_to_human(token, body["reason"], now),
            "log_outcome": lambda: self.log_outcome(token, body["outcome"], now),
        }
        return handlers[name]()

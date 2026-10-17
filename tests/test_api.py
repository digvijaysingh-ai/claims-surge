"""HTTP layer: tool auth, token binding, signed webhooks."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient
from voiceops.guard import sign_webhook

from app.api import Settings, create_app
from app.service import synthetic_policies

SECRET, HOOK, CODE = "tool-secret", "hook-secret", "letmein"


@pytest.fixture
def client():
    return TestClient(create_app(Settings(SECRET, HOOK, CODE)))


def tool(client, name, token, body=None, secret=SECRET):
    headers = {"X-Tool-Secret": secret, "X-Call-Token": token}
    return client.post(f"/tools/{name}", json=body or {}, headers=headers)


def session(client, purpose="inbound"):
    r = client.post("/api/sessions", json={"access_code": CODE, "purpose": purpose})
    return r.json()["call_token"]


def test_tools_refuse_a_missing_or_wrong_secret(client):
    assert tool(client, "get_claim_status", "x", secret="nope").status_code == 401
    assert client.post("/tools/get_claim_status", json={}).status_code == 401


def test_sessions_need_the_access_code(client):
    assert client.post("/api/sessions", json={"access_code": "wrong"}).status_code == 403


def test_unbound_session_binds_on_verification(client):
    token = session(client)
    assert tool(client, "get_claim_status", token).json()["error"] == "identity_not_verified"
    p = synthetic_policies()[0]
    body = {"date_of_birth": p.date_of_birth, "policy_last4": p.last4}
    assert tool(client, "verify_policy", token, body).json()["status"] == "verified"
    claims = tool(client, "get_claim_status", token).json()["claims"]
    assert [c["reference"] for c in claims] == [p.claims[0].reference]


def test_emergency_works_before_verification(client):
    token = session(client)
    r = tool(client, "report_emergency", token, {"reason": "water near sockets"}).json()
    assert r["status"] == "emergency_flagged" and "112" in r["say"]


def test_new_claim_needs_a_verified_policy(client):
    token = session(client)
    body = {
        "incident_type": "storm",
        "incident_date": "2026-03-01",
        "description": "fence down",
        "people_safe": True,
    }
    assert tool(client, "log_new_claim", token, body).json()["error"] == "identity_not_verified"


def test_unknown_token_is_unauthorized_not_a_crash(client):
    r = tool(client, "get_claim_status", "not-a-token")
    assert r.status_code == 200 and r.json()["error"] == "unauthorized"


def test_post_call_webhook_needs_a_fresh_signature(client):
    raw = b'{"type": "post_call_transcription"}'
    good = sign_webhook(HOOK, raw, int(time.time()))
    stale = sign_webhook(HOOK, raw, int(time.time()) - 3600)

    def post(sig):
        return client.post("/hooks/post-call", content=raw, headers={"ElevenLabs-Signature": sig})

    assert post(good).status_code == 200
    assert post(stale).status_code == 401


@pytest.mark.parametrize(
    "dob, last4",
    [
        ("1958-07-21", "2290"),
        ("1958-7-21", "2290"),
        ("21/07/1958", "2 2 9 0"),
        ("July 21st, 1958", "2290"),
    ],
)
def test_policy_verifies_however_the_caller_says_it(client, dob, last4):
    token = session(client)
    body = {"date_of_birth": dob, "policy_last4": last4}
    assert tool(client, "verify_policy", token, body).json()["status"] == "verified"

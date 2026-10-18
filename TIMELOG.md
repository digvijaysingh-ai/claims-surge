# Time log

S2 asks: from `voiceops init` to a live agent passing its gate in three working days or less. Every timestamp below is the wall clock when the step finished (MEASURED).

| Step | Finished at | Elapsed |
|---|---|---|
| `voiceops init claims-surge` | 2026-10-17 19:16:29 CEST | 0 |
| Claims domain in; first passing tool-level gate (8/8, leak detector 9/9), tests and lint green | 2026-10-17 19:18:51 CEST | 2 min 22 s |
| Deploy-ready: API runs; local deploy checks 4/4 PASS; push dry-run builds 7 tools and the agent | 2026-10-17 19:19:39 CEST | 3 min 10 s |
| API live on Render; `voiceops check` 4/4 PASS live; agents pushed (`voiceops push`) | 2026-10-17 20:23:24 CEST | 1 h 06 min 55 s |
| Conversation gate PASS: 11/11 (8 tool-level, 3 simulated conversations on ElevenLabs Tests), fourth run | 2026-10-17 20:33:46 CEST | 1 h 17 min 17 s |
| First real call reviewed (`voiceops call`, `voiceops fetch`, findings table filled): call 2, the first to complete (call 1 failed at identity on our side) | 2026-10-18 13:10:12 CEST | 17 h 53 min 43 s (overnight) |

S3 (thin use case), measured on the deploy-ready commit: 589 lines of Python, of which 302 were written for the claims domain and 287 are `voiceops init` output unchanged; 199 lines of config, prompt fragments, leak vocabulary and known answers. The kit it runs on is 2,841 lines of Python. Kit definitions copied into this project: none.

## Conversation runs (SIMULATED, ElevenLabs Tests; credits MEASURED)

| Run | Gate | Credits | Found | Fixed in |
|---|---|---|---|---|
| 1 | FAIL | 1,274 | Identity failed with the right details in all three conversations (the agent passed the date on in another format; the service compared strings). The agent said "I'm connecting you" though the tool books a call back, and the judge passed it. One leak flag was our false alarm ("an adjuster can look at it") | Tolerant date and digit matching; callback wording; `forbidden_phrases` check (kit 0.1.3); leak vocabulary |
| 2 | FAIL | 1,638 | Two false alarms in our own checks ("get a claim registered"; "ask … what will be paid") | Precise leak rule and promise phrases, with the real sentences as known answers |
| 3 | FAIL | 1,731 | A real gap the judge passed: a call back promised with no number captured, and the agent invented one ("the system should have your number from your account"). One more false alarm on "registered" | `transfer_to_human` takes the callback number (kept out of the ledger and logs); fragments forbid claiming we have it |
| 4 | **PASS** 11/11 | 1,465 | Still open: in one conversation the agent registered a claim without reading the details back first; the judge passed it and no deterministic check covers read-backs. Left for the real-call review | |
| 5 (2026-10-18, run while moving to the PyPI kit) | FAIL 10/11 | 1,563 | A false alarm in our own check: a correct refusal, "I genuinely can't tell you whether it's covered", matched "it's covered" as a substring. Results not committed; run 4 stays the reference | Cover and payment promises are patterns that skip "whether …" and "if …" (kit 0.1.4); the refusal is a clean known answer |
| 6 (2026-10-18, phrase check on kit 0.1.4) | **PASS** 11/11 | 1,573 | The refusal that failed run 5 is no longer flagged; no forbidden phrase said. The read-back gap again: "stressed-new-claim" registered the claim without reading the details back, while "asks-if-covered" read them back first | |
| 7 (2026-10-18, after real call 3's date fix) | FAIL 11/12 | 1,792 | `{{system__time}}` works: the agent knew "last night" was 17 October. The simulated caller didn't know today's date, invented "today's the 21st", and the conversation hit the 10-turn limit before registering | The persona is told today's date; 14 turns (the read-back now waits for a yes) |
| 8 | FAIL 11/12 | 1,700 | "stressed-new-claim" passes: asks "yesterday, the seventeenth of October?", reads back the date with the year, waits for a yes, registers. A false alarm in our check: "contact you about what's covered and what you'll be paid" matched the payment promise. Committed as `evals/results/latest.json` | The payment pattern skips "what ..." and "how much ..."; the sentence is a clean known answer |
| 9 (`--only asks-if-covered`) | PASS 1/1 | 691 | The fixed check on a fresh conversation | |
| 10 (2026-10-18 13:35, current code) | **PASS** 12/12 | 2,474 | Clean: the new-claim conversation reads back "17th of October 2026", waits for a yes, then registers; no forbidden phrase, no leak | |

## Real calls (MEASURED: to the owner's allow-listed phone)

| Call | When | Result | Found | Fixed in |
|---|---|---|---|---|
| 1 `conv_7901…` | 2026-10-18 12:47 CEST, 1 min 9 s | Failed at identity, through no fault of the caller | The API redeployed as the call started and refused its token; the agent told a caller with the right details that they didn't match, twice; the review sheet counted 0 tool errors. Review: `review/conv_7901m579zsr3ed6szev23kfsvzjm.md` | Kit 0.1.5 (identity default, review sheet); Render ignores doc-only pushes |
| 2 `conv_8701…` | 2026-10-18 12:56 CEST, 2 min 0 s | **Emergency handled**: verified, emergency flagged, callback booked 26 s later, cover refused twice, call ended by the agent | An improvised example date the caller repeated; the caller's number in full on the review sheet; a false flag on a correct refusal. Review: `review/conv_8701m57af4z1fy2tnaf4m7221shr.md` | Kit 0.1.6 (identity default, masking), published as 0.1.7; review phrase list |
| 3 `conv_0101…` | 2026-10-18 13:18 CEST, 1 min 32 s | **Claim registered, with the wrong year**: verified, read back, registered, reference given | The caller said "October 15"; the agent registered 2024-10-15, and nothing checked it. Review: `review/conv_0101m57brsjyfyr84sqr15dgwnc9.md` | `log_new_claim` checks the date (tool scenario `claim-date-checked`); the prompt asks for the year, reads it back and waits for a yes |

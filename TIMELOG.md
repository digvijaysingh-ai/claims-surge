# Time log

S2 asks: from `voiceops init` to a live agent passing its gate in three working days or less. Every timestamp below is the wall clock when the step finished (MEASURED).

| Step | Finished at | Elapsed |
|---|---|---|
| `voiceops init claims-surge` | 2026-10-17 19:16:29 CEST | 0 |
| Claims domain in; first passing tool-level gate (8/8, leak detector 9/9), tests and lint green | 2026-10-17 19:18:51 CEST | 2 min 22 s |
| Deploy-ready: API runs; local deploy checks 4/4 PASS; push dry-run builds 7 tools and the agent | 2026-10-17 19:19:39 CEST | 3 min 10 s |
| API live on Render; `voiceops check` 4/4 PASS live; agents pushed (`voiceops push`) | 2026-10-17 20:23:24 CEST | 1 h 06 min 55 s |
| Conversation gate PASS: 11/11 (8 tool-level, 3 simulated conversations on ElevenLabs Tests), fourth run | 2026-10-17 20:33:46 CEST | 1 h 17 min 17 s |
| First real call reviewed (`voiceops call`, `voiceops fetch`, findings table filled) | pending: rings the owner's allow-listed phone | |

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

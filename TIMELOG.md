# Time log

S2 asks: from `voiceops init` to a live agent passing its gate in three working days or less. Every timestamp below is the wall clock when the step finished (MEASURED).

| Step | Finished at | Elapsed |
|---|---|---|
| `voiceops init claims-surge` | 2026-10-17 19:16:29 CEST | 0 |
| Claims domain in; first passing tool-level gate (8/8, leak detector 9/9), tests and lint green | 2026-10-17 19:18:51 CEST | 2 min 22 s |
| Deploy-ready: API runs; local deploy checks 4/4 PASS; push dry-run builds 7 tools and the agent | 2026-10-17 19:19:39 CEST | 3 min 10 s |
| Agent pushed (`voiceops push`) after the API is deployed and `voiceops check` passes live | pending: needs a public deploy and a push to the ElevenLabs workspace (owner's go-ahead) | |
| Conversation gate PASS (`voiceops gate`, conversation scenarios added) | pending: spends ElevenLabs credits | |
| First real call reviewed (`voiceops call`, `voiceops fetch`, findings table filled) | pending: rings the owner's allow-listed phone | |

S3 (thin use case), measured on the deploy-ready commit: 589 lines of Python, of which 302 were written for the claims domain and 287 are `voiceops init` output unchanged; 199 lines of config, prompt fragments, leak vocabulary and known answers. The kit it runs on is 2,841 lines of Python. Kit definitions copied into this project: none.

# Call review · `conv_8701m57af4z1fy2tnaf4m7221shr`

**Provenance:** MEASURED (a real call, reviewed by a person). Recording and raw conversation stay local.

| | |
|---|---|
| Agent | Contoso claims line · outbound · demo |
| When | 2026-10-18 10:56 UTC |
| Length | 2 min 0 s |
| Direction | outbound · number …943 |
| Language | en |
| Status | done · end_call tool was called. |

## Automatic checks

| Check | Result | Detail |
|---|---|---|
| AI disclosed in the first agent turn | PASS | hello, this is contoso insurance's ai assistant calling about your claim, and this call is recorded. am i speaking with… |
| Identity verified | yes | `verify_policy` at turn 14 |
| No protected detail before verification | PASS | leak detector clean |
| Tool errors | 0 | none |
| Promises no tool backs | 0 | none found |
| Call ended by the agent | yes | end_call tool was called. |

## Transcript and tool timeline

| # | t (s) | Who | What |
|---|---|---|---|
| 0 | 0 | Agent | Hello, this is Contoso Insurance's AI assistant calling about your claim, and this call is recorded. Am I speaking with the policyholder? |
| 1 | 8 | Caller | Yes. |
| 2 | 9 | Agent | Thank you. To help you, I need to verify your identity. Could you please give me your date of birth in the format... |
| 3 | 15 | Caller | Okay. |
| 4 | 16 | Agent | What is your date of birth? Please give it to me in the format year,... |
| 5 | 18 | Caller | 1995. |
| 6 | 20 | Agent | Thank you. I need the full date of birth - the... |
| 7 | 20 | Caller | Okay. |
| 8 | 23 | Agent | Could you give me your date of birth in full? That's the year, the month, and the day. For example, nineteen eighty-five, March the fifteenth. |
| 9 | 33 | Caller | Nineteen fifty-eight, July twenty-one. |
| 10 | 36 | Agent | Thank you. So that's nineteen fifty-eight, July twenty-first. And could you give me the last four digits of your policy number, please? |
| 11 | 44 | Caller | Two, two, nine, zero. |
| 12 | 46 | Agent | Thank you. Let me verify that for you. |
| 13 | 47 | tool | → `verify_policy` {"date_of_birth": "1958-07-21", "policy_last4": "2290"} |
| 14 | 47 | tool | ← `verify_policy`: ok: true, status: "verified" |
| 15 | 48 | Agent | Great, thank you. Your identity is verified. How can I help you today? Are you calling to check on an existing claim, or do you need to register a new claim? |
| 16 | 59 | Caller | No, there is an emergency. Water is coming through my ceiling. |
| 17 | 62 | Agent | If anyone is in danger, call one one two now. |
| 18 | 63 | tool | → `report_emergency` {"reason": "Water coming through ceiling"} |
| 18 | 63 | tool | → `record_disclosure` |
| 19 | 63 | tool | ← `report_emergency`: ok: true, status: "emergency_flagged", say: "If anyone is in danger, call 112 now.", next: "transfer_to_human" |
| 19 | 63 | tool | ← `record_disclosure`: ok: true, status: "recorded" |
| 20 | 64 | Agent | What is the best number to call you back on? |
| 21 | 69 | Caller | This is the number, but am I covered or how much will I get? |
| 22 | 73 | Agent | An adjuster will decide what is covered and how much will be paid. Right now, the most important thing is your safety. What is the best number to call you back on? |
| 23 | 84 | Caller | This is the same number, …425. |
| 24 | 89 | tool | → `transfer_to_human` {"callback_number": "…425", "reason": "Emergency - water coming through ceiling"} |
| 25 | 89 | tool | ← `transfer_to_human`: ok: true, status: "callback_requested" |
| 26 | 89 | Agent | A claims handler will call you back on that number as soon as possible. Please stay safe, and if the water gets worse, call one one two immediately. |
| 27 | 98 | Caller | Can you tell me about if I'm covered or not? |
| 28 | 101 | Agent | I can't decide what's covered - that's for an adjuster to look at once they have all the details. A claims handler will call you back very soon to help you. Right now, please focus on staying safe and keeping everyone away from the water if you can. |
| 29 | 116 | Caller | Okay, thank you. |
| 30 | 118 | Agent | You're welcome. Goodbye. |
| 31 | 119 | tool | → `log_outcome` {"outcome": "emergency_handoff"} |
| 31 | 119 | tool | → `end_call` {"reason": "Emergency handoff for water damage", "system__message_to_speak": "Goodbye."} |
| 32 | 120 | tool | ← `log_outcome`: ok: true, status: "logged" |
| 32 | 120 | tool | ← `end_call`: result_type: "end_call_success", status: "success", reason: "Emergency handoff for water damage", message: null |

## Findings

Reviewed 2026-10-18.

Automatic flags are pre-filled; the reviewer completes root cause and fix, and adds anything heard in the recording that the checks can't see.

| # | Turn | What happened | Root cause | Fix |
|---|---|---|---|---|
| 1 | 2–9 | The agent asked for the date of birth with an example ("nineteen ninety-five, March, fifteenth"); the caller answered "1995" and it took three more turns to get the real date | No prompt contains that example: the model improvised it from the tool's `YYYY-MM-DD` format (it also appears in simulated conversations) | Kit 0.1.6: the identity default never gives an example date or number. Pushed to both agents |
| 2 | 23–24 | The caller's callback number appeared in full on this sheet, in the transcript and in `transfer_to_human`'s parameters | The sheet masked only the dialled number | Kit 0.1.6: every phone-like number is masked to its last three digits in every cell; this sheet was regenerated with 0.1.7 |
| 3 | 20–23 | The caller said "this is the number"; the agent asked again before taking the number | The agent isn't told which number an outbound call dialled, and the handoff tool takes the number as said | Open: pass the dialled number to the handoff server-side, so "this number" is enough |
| 4 | 22 | The automatic check flagged "will be paid" in "An adjuster will decide what is covered and how much will be paid", which is the correct answer | The phrase list matched a refusal | `[review] unbacked_promises` lists promises addressed to the caller ("you will be paid"); this sheet was regenerated without the false flag |
| 5 | 16–26 | Worked as designed: emergency flagged at 63 s, handoff booked at 89 s (the ledger rule allows 120 s), cover refused twice ("I can't decide what's covered"), the agent ended the call itself | | |
| 6 | | Not exercised: the emergency-before-identity path (this outbound call verified first, before the caller raised the emergency) and the read-back before registering a claim (no claim was registered) | | Next call: register a claim |

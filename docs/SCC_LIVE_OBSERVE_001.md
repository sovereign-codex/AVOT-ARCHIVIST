# SCC-LIVE-OBSERVE-001 — Archivist test ingress

Status: branch-local experiment only. Not activated for live dispatch.

## Purpose

Provide a manually triggered synthetic capability-test ingress that validates and normalizes one observe-only event in temporary storage, then dispatches only to AVOT-TRACE.

## Invariants

- No push trigger.
- `contents: read` only.
- No Archivist repository writes.
- No Control Center target.
- Exactly one repository dispatch target: `sovereign-codex/AVOT-TRACE`.
- Synthetic fixture must have `actuation_available=false` and authority ceiling `observe`.
- `capability_context` is copied exactly as JSON data; no authority or identity is inferred.
- Hardware endpoints, external device APIs, procedure promotion, and authority escalation are prohibited.

## Gate

Committing this workflow does not authorize running it. Live execution requires a later explicit human instruction naming `SCC-LIVE-OBSERVE-001` after paired repository review.

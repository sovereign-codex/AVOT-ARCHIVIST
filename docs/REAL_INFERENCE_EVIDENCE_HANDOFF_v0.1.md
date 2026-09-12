# Real inference evidence handoff v0.1

Status: candidate preparation procedure. No real model observation or ingestion is claimed.
Target: AVOT-engine PR #6, current reviewed source `e8974ec1e031852a1e4f7475bc9ded37d8f95c99`.

## Boundary

The iPhone administers one disposable RunPod node. Engine and the OpenAI-compatible
model runtime execute on that same node using loopback. Hall/Archivist receive only
the operator-reviewed evidence after execution. This evidence transfer is distinct
from inference transport; it does not authorize a remote model endpoint.

The preparation script is an offline mapper, not a sanitizer, model verifier,
Archivist receiver, dispatcher, or promotion authority. A completion ID in JSON
cannot establish that real model execution occurred. Retain runtime configuration,
model identity, listener observations, exact source commit, build/test output and
the actual runtime request/response evidence separately. Never fabricate an ID to
make the gate pass. Failed or malformed attempts remain evidence, not successes.

## Prepare before paid compute

1. Close the Hall restore rehearsal gate against the repaired source.
2. Review and test this mapping using synthetic data only:
   `python3 -m unittest discover -s scripts -p 'test_prepare_inference_event.py' -v`
3. Prepare one bounded public/synthetic prompt. Do not give the executor repository
   write credentials, Hall secrets, private corpus data, or authority to ingest.
4. Confirm the exact Engine head immediately before executing. If changed, rerun
   build/tests and review the changed code. Earlier test receipts do not transfer.

## Capture on the execution node

Verify a real runtime's listener is bound to loopback only, its model identifier
matches, and its local chat-completions response has content and a runtime-issued
completion ID. Inspect runtime provenance; a localhost URL alone does not exclude
a forwarding proxy. The runbook's preflight completion is separate from the
Engine completion; preserve the Engine call's own completion ID.

Use the PR's environment contract and `npm test`, then build and capture clean JSON:

```bash
npm run build > build.log 2>&1
node dist/inference/real-local-probe.js > roundtrip.private.json 2> probe.stderr.log
```

Run the second command only if the build succeeded. This is the executable invoked
by `probe:local`, separated from npm's build chatter so the result is valid JSON.
Record both exit statuses. Never treat an empty file or exit code alone as success.
If the probe throws without a return path, preserve sanitized failure diagnostics
and mark the missing envelope; do not manufacture one using a success template.

## Review and map on the administration/Hall side

Review the prompt, output, node label, provenance and all other fields for secrets
or private material. Never upload environment dumps, SSH keys, provider tokens,
private IP inventories or unreviewed logs. Keep any private original under restricted
custody. If redaction is needed, preserve lineage to it in restricted custody and
hash the sanitized bytes independently; never claim the sanitized hash is the raw hash.

```bash
python3 scripts/prepare_inference_event.py roundtrip.sanitized.json \
  --engine-sha e8974ec1e031852a1e4f7475bc9ded37d8f95c99 \
  --output-dir staged-probe --sanitized-reviewed
```

The directory must not already exist. The mapper emits `event.json` plus the exact
reviewed bytes at `evidence/inference/<sha256>.json`. The latter is the full return;
the normalized event is only its index. `evidence.terminal_result` carries the
artifact repository, path, hash, completion IDs and source commit using the current
Archivist allowlist. No allowlist expansion is required.

## Institutional transfer and acceptance

Retain and verify the full artifact under Hall custody before publishing the
candidate artifact to its indicated AVOT-ARCHIVIST path. Read it back and verify
its SHA-256. Record the immutable repository commit URL in the Hall receipt.
Only then submit the mapped event as one new `incoming/<request_id>.json` file
through the existing GitHub App/operator path. Never run ingestion from the pod.

Publishing an incoming file triggers the existing live workflow and downstream
dispatch. Review the exact event and downstream route before that step. Do not
use manual workflow dispatch casually: its fallback may scan all incoming files.
Fixtures/tests belong outside `incoming/`; this change contains no live event.

Acceptance requires independent checks of:

- committed `processed/<request_id>.json` with matching trace identity and artifact hash;
- committed Archivist `traces/<trace_id>.json` containing that event;
- actual AVOT-TRACE receiver output and Control Center receipt for the same identity;
- read-back/hash match of the full artifact, including completion reference and boundaries;
- Hall custody receipt and Office state reflecting the separate observed results.

HTTP 204 means dispatch accepted, not receiver completion. A green workflow that
skipped an event is not ingestion. An archived index without recoverable original
evidence is incomplete. Preserve a failed ingest outcome without rerunning inference.

After custody acceptance, the operator terminates the disposable pod and verifies
the same Hall-retained hash again. Record teardown and post-teardown read-back.

## Separate verdicts

Assess Engine PR #6 against its own six promotion gates. Assess Archivist ingestion,
TRACE receipt, Hall recovery, Office reconciliation and teardown separately. All
remain unobserved until the live receipts exist. The mapper always emits
`candidate_evidence`, `promotion_gate: not_assessed`, and
`model_execution: not_independently_verified`, even for a structurally valid return.

# ERA-AVOT-CIRCULATION-001 — Engine × Archivist exact-byte custody

Status: implementation fixture on a non-default branch. Non-canonical, synthetic, and non-authorizing.

## Purpose

Test one present-day cross-repository circulation seam:

```text
bounded monitor signal
-> current AVOT-engine sovereign inference
-> TRACE-compatible witness
-> Archivist-compatible evidence
-> exact reviewed JSON bytes
-> SHA-256 addressed custody artifact
-> small normalized index
```

The fixture exists to prove reconstructability, not to activate a live monitor, ingest an institutional event, dispatch TRACE, create Work, or widen authority.

## Shared fixture identity

`ERA-AVOT-CIRCULATION-001`

Expected SHA-256 for the exact shared fixture bytes:

`c4cbf55ea6035f3e8457064093f1c293543b08d9a0a0c0068973ef4aece550a8`

Identity chain:

```text
signal:era-avot-circulation-001
-> monitor-conduction:era-avot-circulation-001
-> inference:monitor-conduction:era-avot-circulation-001
-> evidence/inference/<sha256>.json
```

Engine and Archivist must derive the same evidence identity. The Archivist mapper additionally proves the exact artifact digest and records the exact Engine commit used for review.

## Boundary

The mapper:

- reads one already-reviewed synthetic Engine circulation return;
- validates signal → request → evidence / TRACE lineage;
- requires `local_only` and `analysis_only`;
- requires `work_ref = null`;
- preserves completed / refused / degraded / failed status without upgrading it;
- refuses a council handoff for non-completed inference;
- hashes and preserves exact reviewed bytes;
- emits a normalized candidate-evidence index.

The mapper does **not**:

- run a model;
- verify that model execution really occurred;
- ingest into Archivist;
- dispatch to TRACE;
- mutate Hall / Office / Canon;
- expand the current Archivist normalization allowlist;
- create or authorize Work.

## Exact artifact vs index

The exact JSON artifact is the reconstructable evidence carrier.

The normalized event is an index containing:

- stable evidence / TRACE identity;
- exact Engine commit;
- exact artifact path and SHA-256;
- signal / request / evidence identity;
- inference status;
- handoff disposition;
- authority state;
- promotion state.

This preserves the current Archivist membrane rather than introducing the branch-local `capability_context` preservation strategy from the older live-observe experiment.

## Run tests

```bash
python3 -m unittest scripts/test_prepare_monitor_conduction_event.py -v
```

The test suite proves:

1. the shared fixture has the same expected SHA-256 as the Engine-side fixture;
2. signal, request, evidence, and TRACE identities remain aligned;
3. the current `ingest.yml` projection retains the complete small index without allowlist expansion;
4. widened authority, lost evidence, dropped context, fallback, and identity mismatch fail closed;
5. refused / degraded / failed returns stay non-success;
6. exact-byte staging refuses overwrite.

## Promotion boundary

A green test does not prove live model execution, live monitor sensing, Archivist ingestion, TRACE receiver completion, Hall acceptance, or institutional promotion.

The first valid review question is narrower:

> Can present-day Engine and Archivist reconstruct the same bounded event identity and exact evidence bytes without depending on obsolete branch state or widening authority?

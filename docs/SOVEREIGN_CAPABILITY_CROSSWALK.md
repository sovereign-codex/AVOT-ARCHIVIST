# Sovereign Capability Crosswalk

## Status

Offline conformance fixture for `FPP-SCC-ARCHIVIST-FIXTURE-001`.

This document is non-canonical. It does not activate a schema, expand a live allowlist, dispatch an event, connect hardware, or grant physical actuation.

## Purpose

`MHS-EDGE-OBSERVE-001` tests one narrow question:

> Can a synthetic, observation-only capability event pass through the currently documented Archivist semantic membrane without silently becoming authorized or losing fields without an explicit loss record?

The fixture does not implement Anthropic's Model Hardware Standard. The external standard is recorded only as a research-preview profile label. No MHS method names, transports, drivers, or unpublished schemas are inferred.

## Contract relationships

```text
External capability or device profile
        | declares technical possibility
        v
ADAPTER_CONTRACT_v0
        | establishes adapter identity, ceiling, reliability, and revocation posture
        v
Hall gate + HALL_EVENT_ENVELOPE_v0
        | records legitimate authority, provenance, state, and required return
        v
AVOT-ARCHIVIST semantic membrane
        | preserves an allowlisted institutional subset
        v
AVOT-TRACE full event
        | witnesses what actually crossed the membrane
        v
Index or interface projection
        | aids discovery but does not own authority or evidence
```

## Governing distinctions

```text
capability != authority
credential != authority
local AVOT eligibility != Hall authorization
execution != verified outcome
successful experiment != admitted procedure
index projection != evidence record
```

## Fixture files

- `mhs-edge-observe-001.source.json` is a fully synthetic source event with distinct capability, adapter, device, and actor identity; observe-only authority; declared limits; and static evidence.
- `mhs-edge-observe-001.expected-normalized.json` represents the output of the reviewed current allowlist in `.github/workflows/ingest.yml` without pretending discarded fields survived.
- `mhs-edge-observe-001.loss-map.json` classifies every source leaf as preserved, fixture metadata, owned elsewhere, an intentional projection, or a known gap.
- `scripts/validate_capability_fixture.py` reads only these local files and exits non-zero when identity, authority, action restrictions, or loss accounting are inconsistent.

## Expected result

```text
PASS_WITH_KNOWN_GAPS
```

A passing fixture is not evidence that the live Archivist contract is complete. It is evidence that the current losses are explicit and testable.

The highest-severity known gaps are:

- capability, adapter, device, and actor identity do not survive current normalization;
- authority basis, gate, allow-list, and prohibitions do not survive current normalization;
- constraints, telemetry references, artifact references, and contradictions do not survive current normalization;
- the synthetic reading is intentionally projected out rather than treated as institutional truth.

## Run locally

From the repository root:

```bash
python3 scripts/validate_capability_fixture.py
```

The validator performs no network calls and writes no files.

## Promotion boundary

This fixture may justify a later decision among:

```text
NO_CHANGE_RECOMMENDED
DOCUMENTATION_ONLY_CANDIDATE
OPTIONAL_FIELD_PRESERVATION_CANDIDATE
SCHEMA_CHANGE_REQUIRES_SEPARATE_REVIEW
```

It does not authorize a workflow change, schema migration, pull request, merge, default-branch mutation, repository dispatch, hardware connection, or procedure promotion.

#!/usr/bin/env python3
"""Prepare reviewed probe evidence locally; never ingest, dispatch, or promote it."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def require(condition, message):
    if not condition:
        raise ValueError(message)


def prepare(raw, engine_sha):
    require(re.fullmatch(r'[0-9a-f]{40}', engine_sha), 'Exact Engine commit SHA required')
    data = json.loads(raw)
    request = data['request']
    archive = data['return_path']['archivist']
    trace = data['return_path']['trace']
    plan, result = archive['plan'], archive['result']
    request_id = request['request_id']
    require(isinstance(request_id, str) and re.fullmatch(r'real-local-[0-9]+', request_id), 'Unexpected probe request identity')
    require(all(x['request_id'] == request_id for x in (archive, plan, result)), 'Request identity mismatch')
    require(trace['trace_id'] == archive['evidence_id'] == 'inference:' + request_id, 'Evidence identity mismatch')
    require(trace['repo'] == 'sovereign-codex/AVOT-engine', 'Unexpected source repository')
    require(request.get('evidence_required') is True, 'Evidence must be required')
    for item in (request, archive['request'], plan):
        require(item['privacy_boundary'] == 'local_only', 'Privacy boundary mismatch')
        require(item['authority_posture'] == 'analysis_only', 'Authority boundary mismatch')
    require(plan['strategy'] == 'direct' and not plan.get('sidecars') and not plan.get('fallback_plan'), 'Probe must remain direct with no fallback/sidecars')
    for key in ('intent', 'work_ref'):
        require(archive['request'].get(key) == request.get(key), 'Archived request mismatch')
    require(request.get('work_ref') == 'work:real-local-model-probe-v0.1', 'Unexpected work reference')
    require(trace['timestamp'] == archive['captured_at'], 'Capture timestamp mismatch')
    stamp = datetime.fromisoformat(trace['timestamp'].replace('Z', '+00:00'))
    require(stamp.tzinfo is not None, 'Timestamp needs timezone')
    status = result['status']
    require(status in ('completed', 'failed', 'refused', 'degraded') and trace['status'] == status, 'Status mismatch')
    require(result['authority_effect'] in ('analysis_return', 'none'), 'Authority effect exceeds analysis')
    require(not result.get('fallback_used') and not result.get('sidecars_used'), 'Unexpected fallback or sidecar')
    require(trace['workflow'] == 'sovereign-inference/direct/' + plan['target_runtime'], 'Runtime workflow mismatch')
    refs = result['evidence_refs']
    require(isinstance(refs, list) and all(isinstance(x, str) for x in refs), 'Malformed evidence refs')
    completions = [x[len('completion:'):] for x in refs if x.startswith('completion:')]
    provenance = result['provenance_refs']
    require(isinstance(provenance, list) and all(isinstance(x, str) for x in provenance), 'Malformed provenance')
    endpoints = [x[len('endpoint:'):] for x in provenance if x.startswith('endpoint:')]
    for endpoint in endpoints:
        url = urlsplit(endpoint)
        require(url.scheme in ('http', 'https') and url.hostname in ('127.0.0.1', 'localhost', '::1'), 'Non-loopback endpoint')
        require(not url.username and not url.password and not url.query and not url.fragment, 'Endpoint contains credential/query material')
        require(url.path == '/v1/chat/completions', 'Unexpected endpoint path')
    if status == 'completed':
        require(isinstance(result.get('output'), str) and bool(result['output'].strip()), 'Missing assistant content')
        require(len(completions) == 1 and bool(completions[0].strip()), 'Missing/ambiguous completion ID')
        require(len(endpoints) == 1, 'Missing/ambiguous endpoint provenance')
        require(result.get('authority_effect') == 'analysis_return', 'Completed probe needs analysis return')
        for used, target in (('model_used', 'target_model'), ('runtime_used', 'target_runtime'), ('capability_used', 'target_capability')):
            require(bool(plan.get(target)) and result.get(used) == plan[target], 'Runtime/model/capability mismatch')
        require(result.get('node_refs') == [plan.get('target_node')] and bool(plan.get('target_node')), 'Node mismatch')
    digest = hashlib.sha256(raw).hexdigest()
    artifact = 'evidence/inference/' + digest + '.json'
    event = {key: trace[key] for key in ('trace_id', 'workflow', 'repo', 'status', 'timestamp')}
    event.update({
        'event_class': 'inference_probe_return',
        'protocol_version': 'inference-archivist-bridge-v0.1',
        'semantic': {
            'institutional_state': 'candidate_evidence',
            'execution_state': status,
            'flow_state': 'awaiting_hall_acceptance',
            'authority_state': 'analysis_only',
            'next_valid_action': 'verify_artifact_custody_and_receiver_receipts',
            'source_role': 'bounded_inference_executor',
            'receiving_office': 'AVOT-ARCHIVIST',
            'review_requirement': 'human_promotion_review_required',
        },
        'evidence': {
            'source_commission': request['work_ref'],
            'terminal_result': {
                'artifact_repository': 'sovereign-codex/AVOT-ARCHIVIST',
                'artifact_path': artifact,
                'artifact_sha256': digest,
                'request_id': request_id,
                'evidence_id': archive['evidence_id'],
                'engine_commit': engine_sha,
                'completion_ids': completions,
                'inference_status': status,
                'promotion_gate': 'not_assessed',
                'model_execution': 'not_independently_verified',
            },
        },
    })
    return event, artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--engine-sha', required=True)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--sanitized-reviewed', required=True, action='store_true', help='Operator has reviewed the source for public retention; this is not an automatic sanitizer')
    args = parser.parse_args()
    raw = args.source.read_bytes()
    event, artifact = prepare(raw, args.engine_sha)
    # A fresh staging directory avoids overwriting evidence or triggering incoming workflows.
    args.output_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    destination = args.output_dir / artifact
    destination.parent.mkdir(parents=True)
    destination.write_bytes(raw)
    (args.output_dir / 'event.json').write_text(json.dumps(event, indent=2) + '\n')
    print('Prepared candidate evidence locally. No ingestion, model verification, or promotion performed.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        raise SystemExit('Preparation failed: invalid contract or output path; preserve the original locally for review.')

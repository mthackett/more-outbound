"""Historical unique-record metrics. Malformed evidence never invents milestones."""
import json
from pipeline.domain.records import PipelineRecord


def event_list(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    return value if isinstance(value, list) else []


def historical_cohorts(records, config):
    stage_map = {s.id: set(s.milestones) for s in config.stages}
    known = {'contacted', 'replied', 'meeting', 'opportunity'}
    achievements, current = {}, {}
    for record in records:
        row = record.model_dump() if isinstance(record, PipelineRecord) else record
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip():
            continue
        record_id = row['id']
        # Duplicate input IDs contribute one identity; union their historical evidence.
        # First current row wins for current-state/value metrics (storage itself rejects duplicates).
        current.setdefault(record_id, row)
        reached = achievements.setdefault(record_id, set())
        if isinstance(row.get('stage_id'), str):
            reached.update(stage_map.get(row['stage_id'], set()))
        for event in event_list(row.get('stage_history')):
            if isinstance(event, dict) and isinstance(event.get('stage_id'), str):
                reached.update(stage_map.get(event['stage_id'], set()))
        for event in event_list(row.get('activities')):
            if isinstance(event, dict) and isinstance(event.get('kind'), str) and event['kind'] in known:
                reached.add(event['kind'])
    cohorts = {key: {i for i, milestones in achievements.items() if key in milestones} for key in known}
    cohorts['total'] = set(achievements)
    return cohorts, current


def ratio(numerator, denominator):
    return {'numerator': numerator, 'denominator': denominator,
            'value': 100 * numerator / denominator if denominator else None}


def booking(cohorts, current, config):
    return ratio(len(cohorts['contacted'] & cohorts['meeting']), len(cohorts['contacted']))


def replies(cohorts, current, config):
    return ratio(len(cohorts['contacted'] & cohorts['replied']), len(cohorts['contacted']))


def replies_to_meeting(cohorts, current, config):
    return ratio(len(cohorts['replied'] & cohorts['meeting']), len(cohorts['replied']))


def active_ids(current, config):
    active = {s.id for s in config.stages if s.active and not s.terminal}
    return {i for i, row in current.items() if isinstance(row.get('stage_id'), str) and row['stage_id'] in active}


def pipeline_value(cohorts, current, config):
    total = 0
    for record_id in active_ids(current, config):
        fields = current[record_id].get('fields')
        value = fields.get('acv') if isinstance(fields, dict) else None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            import math
            if math.isfinite(value) and value >= 0:
                total += value
    return {'value': total}


METRIC_REGISTRY = {
    'meeting_booking_rate': ('Meeting Booking Rate', 'percent', booking),
    'reply_rate': ('Reply Rate', 'percent', replies),
    'reply_to_meeting_rate': ('Reply-to-Meeting Rate', 'percent', replies_to_meeting),
    'total': ('Total Prospects', 'number', lambda c, r, cfg: {'value': len(c['total'])}),
    'active': ('Active Prospects', 'number', lambda c, r, cfg: {'value': len(active_ids(r, cfg))}),
    'pipeline_value': ('Active Pipeline ACV', 'currency', pipeline_value),
}


def calculate_metrics(records, config):
    cohorts, current = historical_cohorts(records, config)
    return {key: {'label': METRIC_REGISTRY[key][0], 'format': METRIC_REGISTRY[key][1],
                  **METRIC_REGISTRY[key][2](cohorts, current, config)} for key in config.metrics}


def conversion_funnel(records, config):
    cohorts, _ = historical_cohorts(records, config)
    total_cohort = cohorts['total']
    total_count = len(total_cohort)

    milestone_stage_map = {}
    for stage in getattr(config, 'stages', []):
        for m in getattr(stage, 'milestones', []):
            if m not in milestone_stage_map:
                milestone_stage_map[m] = stage.name

    default_labels = {
        'contacted': 'Contacted',
        'replied': 'Replied',
        'meeting': 'Meeting Booked',
        'opportunity': 'Opportunity Created'
    }

    first_label = f"All {getattr(getattr(config, 'labels', None), 'record_plural', 'Prospects')}"

    rows = [{
        'Milestone': first_label,
        'Count': total_count,
        'Conversion from Previous': '—',
        'Overall Conversion': '100.0%' if total_count > 0 else '—'
    }]

    previous = total_cohort
    milestone_keys = ['contacted', 'replied', 'meeting', 'opportunity']
    for key in milestone_keys:
        label = milestone_stage_map.get(key, default_labels.get(key, key.title()))
        reached = previous & cohorts.get(key, set())
        cnt = len(reached)

        prev_rate = ratio(cnt, len(previous))['value']
        overall_rate = ratio(cnt, total_count)['value']

        prev_str = f"{prev_rate:.1f}%" if prev_rate is not None else '—'
        overall_str = f"{overall_rate:.1f}%" if overall_rate is not None else '—'

        rows.append({
            'Milestone': label,
            'Count': cnt,
            'Conversion from Previous': prev_str,
            'Overall Conversion': overall_str
        })
        previous = reached

    return rows

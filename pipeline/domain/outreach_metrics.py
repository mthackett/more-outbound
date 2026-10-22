"""Historical unique-record metrics. Malformed evidence never invents milestones."""
import json
from datetime import date, timedelta
import math


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
        # Duck-typed so records survive module reloads (Streamlit dev reruns) that
        # would otherwise fail an isinstance check and silently drop every record.
        row = record.model_dump() if hasattr(record, 'model_dump') else record
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


def milestone_ratio(cohorts, start, end):
    """Share of records that reached `start` and also reached `end`."""
    return ratio(len(cohorts[start] & cohorts[end]), len(cohorts[start]))


def booking(cohorts, current, config):
    return milestone_ratio(cohorts, 'contacted', 'meeting')


def replies(cohorts, current, config):
    return milestone_ratio(cohorts, 'contacted', 'replied')


def replies_to_meeting(cohorts, current, config):
    return milestone_ratio(cohorts, 'replied', 'meeting')


def win_rate(cohorts, current, config):
    return milestone_ratio(cohorts, 'replied', 'opportunity')


def active_ids(current, config):
    active = {s.id for s in config.stages if s.active and not s.terminal}
    return {i for i, row in current.items() if isinstance(row.get('stage_id'), str) and row['stage_id'] in active}


def record_value(row):
    fields = row.get('fields')
    value = fields.get('acv') if isinstance(fields, dict) else None
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return value
    return None


def active_values(current, config):
    values = (record_value(current[i]) for i in active_ids(current, config))
    return [v for v in values if v is not None]


def pipeline_value(cohorts, current, config):
    return {'value': sum(active_values(current, config))}


def average_deal_size(cohorts, current, config):
    values = active_values(current, config)
    return {'value': sum(values) / len(values) if values else None}


METRIC_REGISTRY = {
    'meeting_booking_rate': ('Booking Rate', 'percent', booking),
    'reply_rate': ('Reply Rate', 'percent', replies),
    'reply_to_meeting_rate': ('Reply-to-Meeting', 'percent', replies_to_meeting),
    'win_rate': ('Win Rate', 'percent', win_rate),
    'total': ('Total', 'number', lambda c, r, cfg: {'value': len(c['total'])}),
    'active': ('Active', 'number', lambda c, r, cfg: {'value': len(active_ids(r, cfg))}),
    'pipeline_value': ('Pipeline ACV', 'currency', pipeline_value),
    'avg_deal_size': ('Avg Deal Size', 'currency', average_deal_size),
}

DEFAULT_MILESTONE_LABELS = {
    'contacted': 'Contacted',
    'replied': 'Replied',
    'meeting': 'Meeting Booked',
    'opportunity': 'Opportunity Created',
}


def milestone_labels(config):
    """Milestone key -> name of the first configured stage that grants it."""
    labels = {}
    for stage in getattr(config, 'stages', []):
        for m in getattr(stage, 'milestones', []):
            labels.setdefault(m, stage.name)
    return {**DEFAULT_MILESTONE_LABELS, **labels}


def stage_breakdown(records, config):
    """Current count and value per configured stage, in configured order."""
    _, current = historical_cohorts(records, config)
    rows = {s.id: {'stage_id': s.id, 'Stage': s.name, 'Active': s.active and not s.terminal,
                   'Closed': s.category == 'closed',
                   'Count': 0, 'Value': 0} for s in config.stages}
    for row in current.values():
        entry = rows.get(row.get('stage_id'))
        if entry is None:
            continue
        entry['Count'] += 1
        entry['Value'] += record_value(row) or 0
    return list(rows.values())


def calculate_metrics(records, config):
    cohorts, current = historical_cohorts(records, config)
    custom_labels = getattr(getattr(config, 'labels', None), 'metric_labels', {}) or {}
    return {
        key: {
            'label': custom_labels.get(key, METRIC_REGISTRY[key][0]),
            'format': METRIC_REGISTRY[key][1],
            **METRIC_REGISTRY[key][2](cohorts, current, config),
        }
        for key in config.metrics
    }


def conversion_funnel(records, config):
    cohorts, _ = historical_cohorts(records, config)
    total_cohort = cohorts['total']
    total_count = len(total_cohort)

    labels = milestone_labels(config)

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
        label = labels.get(key, key.title())
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


# ---------------------------------------------------------------------------
# Time-based trends: trailing 30-day periods and weekly series.
#
# Each record contributes the first date it reached each milestone (from stage
# history or milestone activities). Periods count those first-reach events, so a
# record is never double counted and a later stage move keeps earlier history.
# ---------------------------------------------------------------------------

TREND_MILESTONES = ('contacted', 'replied', 'meeting', 'opportunity')

# Percent metrics expressed as (from milestone, to milestone) for period rates.
METRIC_BASIS = {
    'meeting_booking_rate': ('contacted', 'meeting'),
    'reply_rate': ('contacted', 'replied'),
    'reply_to_meeting_rate': ('replied', 'meeting'),
    'win_rate': ('replied', 'opportunity'),
}


def first_milestone_dates(records, config, to_date):
    """Per record: creation date, first date reached for each milestone, and value.

    ``to_date`` converts a stored ISO timestamp to a calendar date (or ``None``),
    so callers decide the timezone.
    """
    stage_map = {s.id: set(s.milestones) for s in config.stages}
    rows = []
    for record in records:
        row = record.model_dump() if hasattr(record, 'model_dump') else record
        if not isinstance(row, dict):
            continue
        dates = {'created': to_date(row.get('created_at')), 'value': record_value(row) or 0}
        events = [(e.get('entered_at'), stage_map.get(e.get('stage_id'), set()))
                  for e in event_list(row.get('stage_history')) if isinstance(e, dict)]
        events += [(a.get('occurred_at'), {a.get('kind')})
                   for a in event_list(row.get('activities')) if isinstance(a, dict)]
        for when, milestones in events:
            day = to_date(when)
            if day is None:
                continue
            for m in milestones & set(TREND_MILESTONES):
                if m not in dates or day < dates[m]:
                    dates[m] = day
        rows.append(dates)
    return rows


def period_summary(rows, start, end):
    """Counts of first-reach events within ``[start, end]`` plus derived rates."""
    def within(day):
        return day is not None and start <= day <= end

    summary = {'start': start, 'end': end, 'new': sum(1 for r in rows if within(r['created']))}
    for m in TREND_MILESTONES:
        summary[m] = sum(1 for r in rows if within(r.get(m)))
    summary['won_value'] = sum(r['value'] for r in rows if within(r.get('opportunity')))
    for key, (a, b) in METRIC_BASIS.items():
        summary[key] = ratio(summary[b], summary[a])['value']
    return summary


def trailing_periods(records, config, today, to_date, days=30, count=3):
    """Consecutive trailing windows ending today, newest first."""
    rows = first_milestone_dates(records, config, to_date)
    periods = []
    for i in range(count):
        end = today - timedelta(days=i * days)
        periods.append(period_summary(rows, end - timedelta(days=days - 1), end))
    return periods


def weekly_series(records, config, today, to_date, weeks=13):
    """Seven-day buckets ending today, oldest first."""
    rows = first_milestone_dates(records, config, to_date)
    series = []
    for i in reversed(range(weeks)):
        end = today - timedelta(days=7 * i)
        series.append(period_summary(rows, end - timedelta(days=6), end))
    return series


# ---------------------------------------------------------------------------
# Sidebar workload summaries.
# ---------------------------------------------------------------------------

ACTIVITY_GOAL_KINDS = {
    'calls': {'call'},
    'emails': {'email', 'contacted'},   # the first sequence touch is an email
    'meetings': {'meeting'},            # meetings booked
}


def activity_counts(records, start, end, to_date):
    """Calls, emails and meetings booked logged between ``start`` and ``end`` (inclusive)."""
    counts = {goal: 0 for goal in ACTIVITY_GOAL_KINDS}
    for record in records:
        for activity in getattr(record, 'activities', []):
            day = to_date(activity.occurred_at)
            if day is None or not start <= day <= end:
                continue
            for goal, kinds in ACTIVITY_GOAL_KINDS.items():
                if activity.kind in kinds:
                    counts[goal] += 1
    return counts


def awaiting_decision(records, config, today, to_date):
    """Open records past the proposal step, with days since the proposal went out.

    "Proposal out" is the first stage carrying the ``replied`` milestone; records
    in any later active stage (e.g. negotiation) are still awaiting a decision.
    """
    stages = list(config.stages)
    start_index = next((i for i, s in enumerate(stages) if 'replied' in s.milestones), None)
    if start_index is None:
        return []
    waiting_ids = {s.id for s in stages[start_index:] if s.active and not s.terminal}
    proposal_ids = {s.id for s in stages[start_index:]}
    rows = []
    for record in records:
        if record.stage_id not in waiting_ids:
            continue
        sent = next((to_date(e.entered_at) for e in record.stage_history if e.stage_id in proposal_ids), None)
        rows.append({'record': record, 'days': (today - sent).days if sent else None,
                     'value': record_value(record.model_dump()) or 0})
    return sorted(rows, key=lambda r: -(r['days'] or 0))


def _as_date(value):
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def capacity_summary(records, config, today, horizon_days=30):
    """Committed delivery hours for the next ``horizon_days`` versus what is pending.

    Committed: converted (won) records whose engagement overlaps the horizon.
    Pending: active records that already carry an estimated plan (e.g. negotiation).
    """
    converted = {s.id for s in config.stages if s.category == 'converted'}
    active = {s.id for s in config.stages if s.active and not s.terminal}
    horizon_end = today + timedelta(days=horizon_days)
    committed, pending, upcoming = 0, 0, []
    for record in records:
        hours = record.fields.get('monthly_hours')
        if not isinstance(hours, (int, float)) or isinstance(hours, bool) or hours <= 0:
            continue
        start = _as_date(record.fields.get('engagement_start'))
        end = _as_date(record.fields.get('engagement_end'))
        if record.stage_id in converted and start and start <= horizon_end and (end is None or end >= today):
            committed += hours
            if start >= today:
                upcoming.append({'record': record, 'start': start, 'hours': hours})
        elif record.stage_id in active:
            pending += hours
    return {'committed': committed, 'pending': pending,
            'upcoming': sorted(upcoming, key=lambda u: u['start'])}

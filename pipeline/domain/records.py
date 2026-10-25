"""Generic records and stage event tracking models."""
from copy import deepcopy
from datetime import date, datetime, timezone
import math
from typing import Any, Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class StageEvent(BaseModel):
    stage_id: str
    entered_at: str = Field(default_factory=timestamp)


class Activity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: Literal['note', 'contacted', 'replied', 'meeting', 'meeting_canceled', 'opportunity', 'call', 'email', 'follow_up']
    text: str = ''
    occurred_at: str = Field(default_factory=timestamp)


class ActionItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    record_id: Any = None
    description: str
    due_date: Any = None
    status: Literal['open', 'completed', 'canceled'] = 'open'
    completed_at: Any = None
    created_at: str = Field(default_factory=timestamp)


class PipelineRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    stage_id: str
    fields: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=timestamp)
    stage_history: list[StageEvent] = Field(default_factory=list)
    activities: list[Activity] = Field(default_factory=list)
    actions: list[ActionItem] = Field(default_factory=list)

    @property
    def current_action(self) -> Any:
        for a in reversed(self.actions):
            if a.status == 'open':
                return a
        return None

    @property
    def latest_action(self) -> Any:
        return self.actions[-1] if self.actions else None


def open_next_action(record):
    """The record's open next action as ``(description, due_date)``, or ``(None, None)``.

    Prefers the structured action list and falls back to the legacy
    ``next_action`` / ``next_action_date`` fields for records without one.
    """
    action = record.current_action
    if action:
        return action.description, action.due_date or record.fields.get('next_action_date')
    description, due = record.fields.get('next_action'), record.fields.get('next_action_date')
    return (description, due) if (description or due) else (None, None)


def due_state(due, today):
    """Classify a due date against ``today``: ``(state, days_from_today)``.

    ``state`` is 'overdue', 'today', 'tomorrow' or 'upcoming'; ``(None, None)``
    when there is no parseable due date.
    """
    if not due:
        return None, None
    try:
        days = (date.fromisoformat(str(due)[:10]) - today).days
    except ValueError:
        return None, None
    if days < 0:
        return 'overdue', days
    return {0: 'today', 1: 'tomorrow'}.get(days, 'upcoming'), days


def validate_fields(config, values):
    specs = {f.key: f for f in config.fields}
    if set(values) - specs.keys():
        raise ValueError('Unknown record fields')
    clean = {}
    for key, spec in specs.items():
        value = values.get(key)
        if value is None or value == '':
            if spec.required:
                raise ValueError(f'{spec.label} is required')
            clean[key] = None if spec.type in ('currency', 'date', 'number') else ''
        elif spec.type in ('currency', 'number'):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{spec.label} must be a nonnegative finite number')
            clean[key] = float(value)
        elif spec.type == 'date':
            try:
                clean[key] = date.fromisoformat(str(value)).isoformat()
            except ValueError as exc:
                raise ValueError(f'{spec.label} must be an ISO date') from exc
        else:
            if not isinstance(value, str) or len(value) > spec.max_length:
                raise ValueError(f'{spec.label} must be text of at most {spec.max_length} characters')
            clean[key] = value.strip()
            if spec.required and not clean[key]:
                raise ValueError(f'{spec.label} is required')
    return clean


def format_field(spec, value):
    if value is None or value == '':
        return '—'
    if spec.format == 'currency':
        return f'${value:,.0f}'
    if spec.format == 'number':
        return f'{value:,.0f}'
    return str(value)


class LegacyJobSnapshot:
    """Read-only generic projection. The full legacy payload remains authoritative.

    Edits in the web session do not alter legacy source payloads.
    """
    def __init__(self, job):
        self._payload = deepcopy(job.model_dump(mode='json'))

    def as_record(self):
        p = self._payload
        return PipelineRecord(id=p['opportunity_id'], stage_id=p['status'],
                              created_at=p['date_created'],
                              fields={'company': p['company_name'], 'title': p['job_title'],
                                      'contact': p['contact_name'], 'notes': p['notes']},
                              stage_history=[StageEvent(stage_id=e['stage'], entered_at=e.get('entered_at', ''))
                                             for e in p['stage_history'] if 'stage' in e])

    def restore(self):
        from pipeline.domain.models import JobPosting
        return JobPosting.model_validate(deepcopy(self._payload))


class LegacySheetSnapshot:
    """Keep unknown columns and original JSON cells, without a Sheet migration."""
    def __init__(self, row):
        self._row = deepcopy(row)

    def restore(self):
        return deepcopy(self._row)

"""Relative dates for synthetic public-demo seed data only.

Seed fixtures store temporal values as offsets from a reference date instead of
absolute dates, so the demo stays current whenever a visitor opens it:

* date fields:      ``"today+3"``, ``"today-2"``, ``"today+0"``
* datetime fields:  ``"today-12T14:30"`` (local wall-clock time in the session timezone)

A visitor session resolves one timezone-aware :class:`DemoReference` when it
starts. :func:`materialize_seed` turns the relative seed into ordinary absolute
ISO values exactly once per session; the resulting records are then handled like
any other data. Records created or edited by the visitor, and every private
workspace path, never pass through this module, so their dates are always real.

Materialization is strict: a relative seed containing an absolute value (or an
already-materialized row) raises instead of being shifted again. That prevents
both stale hard-coded dates and double application of offsets.
"""
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone, tzinfo
import json
import re
from pathlib import Path

try:  # tzdata may be absent on minimal hosts; fixed offsets/UTC remain available.
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - Python < 3.9 is unsupported
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception

TOKEN = re.compile(r'^today([+-]\d{1,4})(?:T([01]\d|2[0-3]):([0-5]\d))?$')
MAX_OFFSET_DAYS = 3660


@dataclass(frozen=True)
class DemoReference:
    """The single, immutable anchor for one visitor session."""
    date: date
    tz: tzinfo
    tz_label: str = 'UTC'

    def day(self, offset_days):
        return self.date + timedelta(days=offset_days)


def resolve_timezone(tz_name=None, offset_minutes=None):
    """Return ``(tzinfo, label)``: IANA name, else browser offset, else UTC.

    ``offset_minutes`` follows the JavaScript ``getTimezoneOffset`` convention
    used by ``st.context.timezone_offset`` (minutes *behind* UTC, so UTC-7 is 420).
    """
    if tz_name and ZoneInfo is not None:
        try:
            return ZoneInfo(str(tz_name)), str(tz_name)
        except (ZoneInfoNotFoundError, ValueError, KeyError, OSError):
            pass
    if isinstance(offset_minutes, (int, float)) and not isinstance(offset_minutes, bool) \
            and abs(offset_minutes) <= 18 * 60:
        delta = -timedelta(minutes=int(offset_minutes))
        return timezone(delta), f'UTC{"+" if delta >= timedelta(0) else "-"}{abs(delta)}'[:-3]
    return timezone.utc, 'UTC'


def session_reference(tz_name=None, offset_minutes=None, now=None):
    """Create the reference for a new session from the visitor's local calendar date."""
    tz, label = resolve_timezone(tz_name, offset_minutes)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Reference instant must be timezone-aware')
    return DemoReference(now.astimezone(tz).date(), tz, label)


def is_relative(value):
    return isinstance(value, str) and TOKEN.match(value) is not None


def _parse(value):
    match = TOKEN.match(value) if isinstance(value, str) else None
    if not match:
        raise ValueError(f'Expected a relative demo date token, got {value!r}')
    offset = int(match.group(1))
    if abs(offset) > MAX_OFFSET_DAYS:
        raise ValueError(f'Relative demo offset out of range: {value!r}')
    clock = (int(match.group(2)), int(match.group(3))) if match.group(2) else None
    return offset, clock


def resolve_date(value, reference):
    offset, clock = _parse(value)
    if clock is not None:
        raise ValueError(f'Date token must not include a time: {value!r}')
    return reference.day(offset).isoformat()


def resolve_datetime(value, reference):
    offset, clock = _parse(value)
    if clock is None:
        raise ValueError(f'Datetime token requires a time (todayN THH:MM): {value!r}')
    local = datetime.combine(reference.day(offset), time(*clock), tzinfo=reference.tz)
    return local.isoformat()


def materialize_seed(rows, reference, date_fields):
    """Return deep-copied seed rows with every relative token resolved.

    ``date_fields`` are the configured ``date``-typed field keys. Empty values
    stay empty. Any absolute value in a temporal position raises ``ValueError``.
    """
    date_fields = tuple(date_fields)
    resolved = []
    for row in deepcopy(list(rows)):
        if not isinstance(row, dict):
            raise ValueError('Seed rows must be objects')
        row['created_at'] = resolve_datetime(row.get('created_at'), reference)
        for event in row.get('stage_history') or []:
            event['entered_at'] = resolve_datetime(event.get('entered_at'), reference)
        for activity in row.get('activities') or []:
            activity['occurred_at'] = resolve_datetime(activity.get('occurred_at'), reference)
        fields = row.get('fields') or {}
        for key in date_fields:
            if fields.get(key) not in (None, ''):
                fields[key] = resolve_date(fields[key], reference)
        resolved.append(row)
    return resolved


def load_relative_seed(path, reference, config):
    """Read a relative fixture and materialize it for one session."""
    rows = json.loads(Path(path).read_text(encoding='utf-8'))
    date_fields = [f.key for f in config.fields if f.type == 'date']
    return materialize_seed(rows, reference, date_fields)


def parse_instant(value):
    """Parse an ISO timestamp to an aware datetime (naive values are treated as UTC)."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def local_date(value, reference):
    """Calendar date of an ISO timestamp in the session timezone (``None`` if unparseable)."""
    parsed = parse_instant(value)
    return parsed.astimezone(reference.tz).date() if parsed else None

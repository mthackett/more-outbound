"""Sandbox contact actions (call / email dialogs) and workspace sidebar widgets.

Nothing here places a call or sends a message: dialogs simulate the action and
log an activity on the record so the rest of the demo (timeline, weekly goals)
responds the way it would in a live workspace.
"""
import datetime
import html

import streamlit as st

from pipeline.domain.demo_dates import local_date
from pipeline.domain.outreach_metrics import activity_counts, awaiting_decision, capacity_summary
from pipeline.domain.records import due_state, open_next_action

SANDBOX_NOTE = 'This is a sandbox demo, so no call is actually going out.'
EMAIL_SANDBOX_NOTE = 'This is a sandbox demo, so no email is actually sent.'
SYNTHETIC_NOTE = ('All data in this demo is synthetic. Companies, contacts, phone numbers and email '
                  'addresses are fictitious.')

WIDGET_CSS = """
<style>
    @keyframes mo-ring {
        0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.55); }
        70% { box-shadow: 0 0 0 18px rgba(99, 102, 241, 0); }
        100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
    }
    .mo-call-avatar {
        width: 64px; height: 64px; border-radius: 50%; margin: 6px auto 10px;
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
        display: flex; align-items: center; justify-content: center;
        color: #FFFFFF; font-weight: 800; font-size: 1.3rem; animation: mo-ring 1.6s infinite;
    }
    .mo-side-label {
        font-size: 0.72rem; font-weight: 700; color: #94A3B8; text-transform: uppercase;
        letter-spacing: 0.5px; margin: 14px 0 6px;
    }
    .mo-side-row { font-size: 0.78rem; line-height: 1.3; padding: 2px 0; }
    .mo-side-row .co { color: #818CF8; font-weight: 700; }
    .mo-side-row .sub { color: #94A3B8; font-size: 0.72rem; }
    .mo-goal { margin-bottom: 8px; font-size: 0.76rem; color: #CBD5E1; }
    .mo-goal-bar { background: #1E293B; height: 7px; border-radius: 4px; overflow: hidden; margin-top: 3px; }
    .mo-goal-fill { height: 100%; border-radius: 4px; }
    .mo-side-empty { font-size: 0.76rem; color: #64748B; }
    /* Company names in sidebar lists are link-style buttons that open the record */
    [data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"] {
        padding: 0; min-height: 0; height: auto; justify-content: flex-start; text-align: left;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"] p {
        color: #818CF8; font-weight: 700; font-size: 0.78rem; line-height: 1.3;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:hover p {
        color: #A5B4FC; text-decoration: underline;
    }
    .mo-side-sub { font-size: 0.72rem; color: #94A3B8; line-height: 1.3; margin: -6px 0 8px; }
</style>
"""


def initials(name):
    parts = [p for p in str(name or '').split() if p[:1].isalpha()]
    return ''.join(p[0] for p in parts[:2]).upper() or '?'


def first_name(record):
    return (record.fields.get('contact') or '').split(' ')[0] or 'there'


# --------------------------------------------------------------------------- dialogs

@st.dialog('📞 Call')
def call_dialog(storage, record, key):
    contact = record.fields.get('contact') or record.fields.get('company') or 'Contact'
    phone = record.fields.get('phone') or ''
    st.markdown(WIDGET_CSS, unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:center;'>"
        f"<div class='mo-call-avatar'>{html.escape(initials(contact))}</div>"
        f"<div style='font-size:1.25rem; font-weight:700; color:#F8FAFC;'>Calling {html.escape(contact)}…</div>"
        f"<div style='font-family:monospace; color:#94A3B8; margin-top:2px;'>{html.escape(phone)}</div>"
        f"<div style='color:#94A3B8; font-size:0.8rem; margin-top:2px;'>{html.escape(record.fields.get('company') or '')}</div>"
        f"<div style='font-size:0.95rem; font-weight:600; color:#FBBF24; margin-top:14px;'>{SANDBOX_NOTE}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.caption(SYNTHETIC_NOTE)
    with st.form(f'{key}_form', border=False):
        outcome = st.radio('Call outcome', ['Connected', 'Left voicemail', 'No answer'], horizontal=True,
                           key=f'{key}_outcome')
        note = st.text_input('Notes (optional)', placeholder='e.g. Asked for a follow-up next week', key=f'{key}_note')
        col_log, col_hang = st.columns(2)
        log = col_log.form_submit_button('Log call', width='stretch', type='primary')
        hang = col_hang.form_submit_button('Hang up', width='stretch')
    if log:
        text = f'Call to {first_name(record)}: {outcome.lower()}.' + (f' {note.strip()}' if note.strip() else '')
        storage.add_activity(record.id, 'call', text)
        st.session_state['_demo_flash'] = f'Call logged for {contact} (sandbox: no call was placed).'
        st.rerun()
    if hang:
        st.rerun()


def default_email(record):
    first = first_name(record)
    angle = (record.fields.get('suggested_angle') or record.fields.get('desired_outcome') or '').strip()
    company = record.fields.get('company') or 'your team'
    subject = f'Quick idea for {company}'
    body = (f'Hi {first},\n\n'
            + (f'{angle}\n\n' if angle else '')
            + 'Worth a 20-minute conversation next week?\n\nBest,\n')
    return subject, body


@st.dialog('✉️ Email', width='large')
def email_dialog(storage, record, key):
    contact = record.fields.get('contact') or record.fields.get('company') or 'Contact'
    subject, body = default_email(record)
    st.markdown(f"<div style='font-size:0.95rem; font-weight:600; color:#FBBF24;'>{EMAIL_SANDBOX_NOTE}</div>",
                unsafe_allow_html=True)
    st.caption(SYNTHETIC_NOTE)
    with st.form(f'{key}_form', border=False):
        st.text_input('To', value=f"{contact} <{record.fields.get('email') or ''}>", disabled=True, key=f'{key}_to')
        subject = st.text_input('Subject', value=subject, key=f'{key}_subject')
        body = st.text_area('Message', value=body + (record.fields.get('opportunity_owner') or ''), height=200,
                            key=f'{key}_body')
        col_send, col_cancel = st.columns(2)
        send = col_send.form_submit_button('Send (sandbox)', width='stretch', type='primary')
        cancel = col_cancel.form_submit_button('Discard', width='stretch')
    if send:
        storage.add_activity(record.id, 'email', f'Email to {first_name(record)}: "{subject.strip() or "(no subject)"}".')
        st.session_state['_demo_flash'] = f'Email logged for {contact} (sandbox: nothing was sent).'
        st.rerun()
    if cancel:
        st.rerun()


def contact_action_buttons(storage, record, prefix, container=st):
    """Call / Email buttons for a record, shown only when it has the matching contact detail."""
    cols = container.columns(2, gap='small')
    if record.fields.get('phone'):
        if cols[0].button('📞 Call', key=f'{prefix}_call_{record.id}', width='stretch',
                          help=f"Call {record.fields['phone']} (simulated)"):
            call_dialog(storage, record, f'{prefix}_calldlg_{record.id}')
    if record.fields.get('email'):
        if cols[1].button('✉️ Email', key=f'{prefix}_email_{record.id}', width='stretch',
                          help=f"Email {record.fields['email']} (simulated)"):
            email_dialog(storage, record, f'{prefix}_emaildlg_{record.id}')


# --------------------------------------------------------------------------- sidebar widgets

def focus_record(prefix, record_id, company):
    """Button callback: switch to Pipeline, search for the company and open its card.

    Runs before the rerun, so it may set widget state (navigation, search, filters)
    that the script renders next.
    """
    st.session_state['public_navigation'] = 'pipeline'
    st.session_state[f'{prefix}_search'] = company
    st.session_state[f'{prefix}_priority_filter'] = 'all'
    st.session_state[f'{prefix}_filter'] = 'all'
    st.session_state[f'{prefix}_page'] = 1
    st.session_state[f'{prefix}_focus'] = record_id


def company_link(container, record, prefix, key):
    company = record.fields.get('company') or record.fields.get('contact') or 'Open record'
    container.button(company, key=key, type='tertiary', help=f'Open {company} in the pipeline',
                     on_click=focus_record, args=(prefix, record.id, company))

def _due_chip(state, days):
    if state == 'overdue':
        return f"<span style='color:#FB7185; font-weight:700;'>{abs(days)}d overdue</span>"
    if state == 'today':
        return "<span style='color:#FBBF24; font-weight:700;'>Due today</span>"
    return ''


def call_queue(config, storage, records, reference, prefix, limit=5):
    """Today's call list: overdue and due-today records with a phone number, most overdue first."""
    active = {s.id for s in config.stages if s.active}
    queue = []
    for r in records:
        if r.stage_id not in active or not r.fields.get('phone'):
            continue
        desc, due = open_next_action(r)
        state, days = due_state(due, reference.date)
        if state in ('overdue', 'today'):
            queue.append((days, r, desc, state))
    queue.sort(key=lambda q: (q[0], -(q[1].fields.get('acv') or 0)))
    st.sidebar.markdown(f"<div class='mo-side-label'>Today's Call List · {len(queue)} due</div>",
                        unsafe_allow_html=True)
    if not queue:
        st.sidebar.markdown("<div class='mo-side-empty'>Nothing due today. 🎉</div>", unsafe_allow_html=True)
        return
    for days, r, desc, state in queue[:limit]:
        col_text, col_btn = st.sidebar.columns([5, 2], vertical_alignment='center')
        short = desc if len(desc or '') <= 34 else desc[:32] + '…'
        company_link(col_text, r, prefix, f'{prefix}_side_q_open_{r.id}')
        col_text.markdown(
            f"<div class='mo-side-sub'>{html.escape(short or '')}<br>{_due_chip(state, days)}</div>",
            unsafe_allow_html=True)
        if col_btn.button('📞', key=f'{prefix}_side_q_call_{r.id}', help=f"Call {r.fields.get('contact')} (simulated)",
                          width='stretch'):
            call_dialog(storage, r, f'{prefix}_side_q_calldlg_{r.id}')
    if len(queue) > limit:
        st.sidebar.caption(f'+{len(queue) - limit} more in Daily Priorities')


def _goal_bar(label, done, target):
    pct = min(100, round(done / target * 100)) if target else 0
    color = '#34D399' if done >= target else '#6366F1'
    return (f"<div class='mo-goal'><div style='display:flex; justify-content:space-between;'>"
            f"<span>{label}</span><span><b style='color:#F8FAFC;'>{done}</b> / {target}</span></div>"
            f"<div class='mo-goal-bar'><div class='mo-goal-fill' style='width:{pct}%; background:{color};'></div></div></div>")


def activity_goals(config, records, reference):
    targets = config.activity_targets
    end = reference.date
    counts = activity_counts(records, end - datetime.timedelta(days=6), end, lambda v: local_date(v, reference))
    st.sidebar.markdown(
        "<div class='mo-side-label'>Weekly Goals · Last 7 Days</div>"
        + _goal_bar('📞 Calls', counts['calls'], targets.calls)
        + _goal_bar('✉️ Emails', counts['emails'], targets.emails)
        + _goal_bar('📅 Meetings booked', counts['meetings'], targets.meetings),
        unsafe_allow_html=True)


def proposals_awaiting(config, records, reference, prefix, limit=5):
    rows = awaiting_decision(records, config, reference.date, lambda v: local_date(v, reference))
    total = sum(r['value'] for r in rows)
    st.sidebar.markdown(
        f"<div class='mo-side-label'>Proposals Awaiting Decision · ${total:,.0f}</div>", unsafe_allow_html=True)
    if not rows:
        st.sidebar.markdown("<div class='mo-side-empty'>No proposals out right now.</div>", unsafe_allow_html=True)
        return
    stages = {s.id: s.name for s in config.stages}
    for row in rows[:limit]:
        r, days = row['record'], row['days']
        color = '#FB7185' if (days or 0) > 14 else '#FBBF24' if (days or 0) > 10 else '#94A3B8'
        age = f"<span style='color:{color}; font-weight:700;'>{days}d out</span>" if days is not None else ''
        company_link(st.sidebar, r, prefix, f'{prefix}_side_p_open_{r.id}')
        st.sidebar.markdown(
            f"<div class='mo-side-sub'><span style='color:#34D399; font-weight:600;'>${row['value']:,.0f}</span>"
            f" · {html.escape(stages.get(r.stage_id, r.stage_id))} · {age}</div>",
            unsafe_allow_html=True)
    if len(rows) > limit:
        st.sidebar.caption(f'+{len(rows) - limit} more')


def capacity(config, records, reference, prefix):
    available = config.delivery_capacity.hours_per_month
    summary = capacity_summary(records, config, reference.date)
    committed, pending = summary['committed'], summary['pending']
    pct = round(committed / available * 100)
    projected = round((committed + pending) / available * 100)
    fill = '#FB7185' if pct > 100 else '#FBBF24' if pct >= 85 else '#34D399'
    pending_html = ''
    if pending:
        color = '#FB7185' if projected > 100 else '#94A3B8'
        pending_html = (f"<div class='sub' style='color:{color}; font-size:0.72rem; margin-top:4px;'>"
                        f"Deals in negotiation would add {pending:.0f} hrs → {projected}% of capacity</div>")
    st.sidebar.markdown(
        "<div class='mo-side-label'>Delivery Capacity · Next 30 Days</div>"
        f"<div class='mo-goal'><div style='display:flex; justify-content:space-between;'>"
        f"<span>Committed</span><span><b style='color:#F8FAFC;'>{committed:.0f}</b> / {available} hrs ({pct}%)</span></div>"
        f"<div class='mo-goal-bar'><div class='mo-goal-fill' style='width:{min(pct, 100)}%; background:{fill};'></div></div>"
        f"{pending_html}</div>",
        unsafe_allow_html=True)
    if summary['upcoming']:
        st.sidebar.markdown("<div class='mo-side-label' style='margin-top:8px;'>Upcoming Starts</div>",
                            unsafe_allow_html=True)
    for u in summary['upcoming'][:3]:
        company_link(st.sidebar, u['record'], prefix, f"{prefix}_side_s_open_{u['record'].id}")
        st.sidebar.markdown(
            f"<div class='mo-side-sub'>Starts {u['start'].strftime('%b')} {u['start'].day} · {u['hours']:.0f} hrs/mo</div>",
            unsafe_allow_html=True)


def render_sidebar_widgets(config, storage, reference, prefix):
    widgets = config.sidebar_widgets
    if not widgets:
        return
    records = storage.list_records()
    st.sidebar.markdown(WIDGET_CSS, unsafe_allow_html=True)
    for widget in widgets:
        if widget == 'call_queue':
            call_queue(config, storage, records, reference, prefix)
        elif widget == 'activity_goals':
            activity_goals(config, records, reference)
        elif widget == 'proposals_awaiting':
            proposals_awaiting(config, records, reference, prefix)
        elif widget == 'capacity':
            capacity(config, records, reference, prefix)

"""Configuration-driven public views. Imports no private workflow or provider."""
import datetime
import hashlib
import json
from pathlib import Path
import streamlit as st
from pipeline.adapters.primary.runtime import select_session
from pipeline.adapters.secondary.memory_records import MemoryRecordStorage
from pipeline.domain.records import format_field
from pipeline.domain.intelligence_service import IntelligenceService
from pipeline.domain.outreach_metrics import calculate_metrics, conversion_funnel

STAGE_STYLES = {
    # Sales Rep Stages
    'identified': {
        'bg': '#1E293B',
        'fg': '#94A3B8',
        'border': '#334155',
        'badge_bg': '#0F172A',
    },
    'qualified': {
        'bg': '#0C4A6E33',
        'fg': '#38BDF8',
        'border': '#0284C755',
        'badge_bg': '#0369A122',
    },
    'ready': {
        'bg': '#312E8133',
        'fg': '#A5B4FC',
        'border': '#4F46E555',
        'badge_bg': '#4338CA22',
    },
    'contacted': {
        'bg': '#164E6333',
        'fg': '#22D3EE',
        'border': '#0891B255',
        'badge_bg': '#0E749022',
    },
    'replied': {
        'bg': '#451A0333',
        'fg': '#FBBF24',
        'border': '#D9770655',
        'badge_bg': '#B4530922',
    },
    'meeting_booked': {
        'bg': '#064E3B33',
        'fg': '#34D399',
        'border': '#05966955',
        'badge_bg': '#04785722',
    },
    'opportunity_created': {
        'bg': '#3B076433',
        'fg': '#C084FC',
        'border': '#7C3AED55',
        'badge_bg': '#6D28D922',
    },
    'disqualified': {
        'bg': '#4C051933',
        'fg': '#FB7185',
        'border': '#E11D4855',
        'badge_bg': '#9F123922',
    },
    'no_response': {
        'bg': '#1E293B',
        'fg': '#64748B',
        'border': '#334155',
        'badge_bg': '#1E293B',
    },
    # B2B Services Stages
    'inquiry': {
        'bg': '#1E293B',
        'fg': '#94A3B8',
        'border': '#334155',
        'badge_bg': '#0F172A',
    },
    'scoping': {
        'bg': '#0C4A6E33',
        'fg': '#38BDF8',
        'border': '#0284C755',
        'badge_bg': '#0369A122',
    },
    'proposal_dev': {
        'bg': '#312E8133',
        'fg': '#A5B4FC',
        'border': '#4F46E555',
        'badge_bg': '#4338CA22',
    },
    'proposal_sent': {
        'bg': '#164E6333',
        'fg': '#22D3EE',
        'border': '#0891B255',
        'badge_bg': '#0E749022',
    },
    'negotiation': {
        'bg': '#451A0333',
        'fg': '#FBBF24',
        'border': '#D9770655',
        'badge_bg': '#B4530922',
    },
    'contract_awarded': {
        'bg': '#064E3B33',
        'fg': '#34D399',
        'border': '#05966955',
        'badge_bg': '#04785722',
    },
    'lost': {
        'bg': '#4C051933',
        'fg': '#FB7185',
        'border': '#E11D4855',
        'badge_bg': '#9F123922',
    },
}

PUBLIC_THEME_CSS = """
<style>
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    .block-container {
        padding-top: 4.25rem !important;
        padding-bottom: 2rem;
        max-width: 1360px;
    }
    .demo-main-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-top: 0;
        margin-bottom: 0.15rem;
        letter-spacing: -0.015em;
        line-height: 1.25;
    }
    .demo-sub-title {
        font-size: 0.88rem;
        color: #94A3B8;
        margin-bottom: 0.75rem;
        line-height: 1.4;
    }
    .demo-section-header {
        font-size: 1.22rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 0.2rem;
        margin-bottom: 0.15rem;
    }
    /* Compact headline KPI cards: centered labels and values */
    div[data-testid="stMetric"] {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px 6px;
        box-shadow: none;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #6366F1;
        background-color: #111C35;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        text-align: center !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] > div,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {
        font-size: 0.68rem !important;
        color: #94A3B8 !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        text-align: center !important;
        width: 100% !important;
        white-space: nowrap;
        overflow: visible !important;
        text-overflow: clip !important;
        margin: 0 auto !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        text-align: center !important;
        font-size: 1.35rem !important;
        color: #F8FAFC !important;
        font-weight: 700 !important;
        line-height: 1.2;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] > div {
        text-align: center !important;
        width: 100% !important;
    }
    /* Card expander styling */
    div[data-testid="stExpander"] {
        background-color: #0B132B;
        border: 1px solid #1E293B;
        border-radius: 8px;
        margin-bottom: 8px;
        transition: border-color 0.15s ease;
    }
    div[data-testid="stExpander"]:hover {
        border-color: #334155;
    }
    div[data-testid="stExpander"] details summary {
        padding: 8px 12px !important;
    }
    div[data-testid="stExpander"] details summary p {
        line-height: 1.45;
    }
    /* Compact form styling */
    div[data-testid="stForm"] {
        border: 1px solid #1E293B;
        border-radius: 6px;
        padding: 10px 14px;
        background-color: #0F172A;
    }
</style>
"""


def session_storage(config, workspace_key=None):
    select_session(st.session_state, 'demo')
    ws_key = workspace_key or config.pipeline_type or 'sales_rep'
    cfg_hash = hashlib.sha256(config.model_dump_json().encode()).hexdigest()[:12]
    store_key = f"{ws_key}_{cfg_hash}"
    if '_demo_workspace_stores' not in st.session_state:
        st.session_state['_demo_workspace_stores'] = {}
    stores = st.session_state['_demo_workspace_stores']
    if store_key not in stores:
        seed = []
        fixtures_dir = Path(__file__).resolve().parents[2] / 'examples/fixtures'
        if config.seed in ('b2b_prospects', 'sales_rep_prospects'):
            seed = json.loads((fixtures_dir / 'demo_prospects.json').read_text(encoding='utf-8'))
        elif config.seed == 'b2b_services_prospects':
            seed = json.loads((fixtures_dir / 'demo_b2b_services.json').read_text(encoding='utf-8'))
        stores[store_key] = MemoryRecordStorage(config, seed)
    st.session_state['_demo_store'] = stores[store_key]
    return stores[store_key]


def render_single_field(field, prefix, values, height=None, placeholder=None):
    if not field.editable:
        st.text(f'{field.label}: {format_field(field, values.get(field.key))}')
        return values.get(field.key)
    label = field.label + (' *' if field.required else '')
    key = prefix + '_' + field.key
    val = values.get(field.key)
    if field.type == 'currency':
        num_val = float(val) if val is not None and str(val).strip() != '' else None
        return st.number_input(label, min_value=0.0, value=num_val, key=key)
    elif field.type == 'date':
        val_date = val or None
        if isinstance(val_date, str):
            try:
                val_date = datetime.date.fromisoformat(val_date)
            except ValueError:
                val_date = None
        date_res = st.date_input(label, value=val_date, key=key)
        return date_res.isoformat() if date_res else None
    elif field.type == 'long_text':
        ph = placeholder or f"Enter {field.label.lower()}..."
        return st.text_area(label, value=val or '', max_chars=field.max_length, key=key, height=height or 75, placeholder=ph)
    else:
        ph = placeholder or f"Enter {field.label.lower()}..."
        return st.text_input(label, value=val or '', max_chars=field.max_length, key=key, placeholder=ph)


def input_fields(config, prefix, values=None, intake=False):
    values = values or {}
    result = {}
    fields_by_key = {f.key: f for f in config.fields if f.visible and (not intake or f.intake)}

    # Section A: Account & Contact (Two-Column Grid)
    st.markdown("<div style='font-size:0.78rem; font-weight:700; color:#818CF8; text-transform:uppercase; letter-spacing:0.5px; margin-top:2px; margin-bottom:6px;'>Account & Contact Information</div>", unsafe_allow_html=True)
    
    # Row 1: Account * | Prospect Name *
    if 'company' in fields_by_key and 'contact' in fields_by_key:
        c1, c2 = st.columns(2)
        with c1:
            result['company'] = render_single_field(fields_by_key['company'], prefix, values, placeholder="e.g. Lumina HealthTech")
        with c2:
            result['contact'] = render_single_field(fields_by_key['contact'], prefix, values, placeholder="e.g. Elena Rostova")
    elif 'company' in fields_by_key:
        result['company'] = render_single_field(fields_by_key['company'], prefix, values, placeholder="e.g. Lumina HealthTech")
    elif 'contact' in fields_by_key:
        result['contact'] = render_single_field(fields_by_key['contact'], prefix, values, placeholder="e.g. Elena Rostova")

    # Row 2: Job Title | Email
    if 'title' in fields_by_key and 'email' in fields_by_key:
        c1, c2 = st.columns(2)
        with c1:
            result['title'] = render_single_field(fields_by_key['title'], prefix, values, placeholder="e.g. VP of Revenue Operations")
        with c2:
            result['email'] = render_single_field(fields_by_key['email'], prefix, values, placeholder="e.g. elena@lumina.example.com")
    elif 'title' in fields_by_key:
        result['title'] = render_single_field(fields_by_key['title'], prefix, values, placeholder="e.g. VP of Revenue Operations")
    elif 'email' in fields_by_key:
        result['email'] = render_single_field(fields_by_key['email'], prefix, values, placeholder="e.g. elena@lumina.example.com")

    # Row 3: Phone | Website
    if 'phone' in fields_by_key and 'website' in fields_by_key:
        c1, c2 = st.columns(2)
        with c1:
            result['phone'] = render_single_field(fields_by_key['phone'], prefix, values, placeholder="e.g. (617) 555-0142")
        with c2:
            result['website'] = render_single_field(fields_by_key['website'], prefix, values, placeholder="e.g. lumina.example.com")
    elif 'phone' in fields_by_key:
        result['phone'] = render_single_field(fields_by_key['phone'], prefix, values, placeholder="e.g. (617) 555-0142")
    elif 'website' in fields_by_key:
        result['website'] = render_single_field(fields_by_key['website'], prefix, values, placeholder="e.g. lumina.example.com")

    # Row 4: Industry | Company Size
    if 'industry' in fields_by_key and 'company_size' in fields_by_key:
        c1, c2 = st.columns(2)
        with c1:
            result['industry'] = render_single_field(fields_by_key['industry'], prefix, values, placeholder="e.g. HealthTech, B2B SaaS")
        with c2:
            result['company_size'] = render_single_field(fields_by_key['company_size'], prefix, values, placeholder="e.g. 250-500")
    elif 'industry' in fields_by_key:
        result['industry'] = render_single_field(fields_by_key['industry'], prefix, values, placeholder="e.g. HealthTech, Consulting")
    elif 'company_size' in fields_by_key:
        result['company_size'] = render_single_field(fields_by_key['company_size'], prefix, values, placeholder="e.g. 250-500")

    # Tech Stack (full width)
    if 'tech_stack' in fields_by_key:
        result['tech_stack'] = render_single_field(fields_by_key['tech_stack'], prefix, values, placeholder="e.g. Salesforce · HubSpot · Gong")

    # Section B: Opportunity Context
    opp_keys = {'acv', 'icp_fit', 'opportunity_brief'} & set(fields_by_key)
    if opp_keys:
        st.markdown("<div style='font-size:0.78rem; font-weight:700; color:#818CF8; text-transform:uppercase; letter-spacing:0.5px; margin-top:10px; margin-bottom:2px;'>Opportunity Context</div>", unsafe_allow_html=True)
        st.caption("Why is this prospect worth pursuing?")
        if 'acv' in fields_by_key and 'icp_fit' in fields_by_key:
            c1, c2 = st.columns(2)
            with c1:
                result['acv'] = render_single_field(fields_by_key['acv'], prefix, values)
            with c2:
                result['icp_fit'] = render_single_field(fields_by_key['icp_fit'], prefix, values, placeholder="e.g. High, Medium, Low")
        elif 'acv' in fields_by_key:
            result['acv'] = render_single_field(fields_by_key['acv'], prefix, values)
        elif 'icp_fit' in fields_by_key:
            result['icp_fit'] = render_single_field(fields_by_key['icp_fit'], prefix, values, placeholder="e.g. High, Medium, Low")

        if 'opportunity_brief' in fields_by_key:
            result['opportunity_brief'] = render_single_field(fields_by_key['opportunity_brief'], prefix, values, height=75, placeholder="Brief opportunity thesis: scaling team, manual bottlenecks, or expansion trigger...")

    # Section C: Pipeline & Next Actions
    pipe_keys = {'source', 'opportunity_owner', 'priority', 'follow_up_status', 'next_action_date', 'next_action'} & set(fields_by_key)
    if pipe_keys:
        st.markdown("<div style='font-size:0.78rem; font-weight:700; color:#818CF8; text-transform:uppercase; letter-spacing:0.5px; margin-top:10px; margin-bottom:6px;'>Pipeline & Next Actions</div>", unsafe_allow_html=True)
        if 'source' in fields_by_key and 'opportunity_owner' in fields_by_key:
            c1, c2 = st.columns(2)
            with c1:
                result['source'] = render_single_field(fields_by_key['source'], prefix, values, placeholder="e.g. Account Research, Inbound, Referral")
            with c2:
                result['opportunity_owner'] = render_single_field(fields_by_key['opportunity_owner'], prefix, values, placeholder="e.g. Sarah Jenkins")
        elif 'source' in fields_by_key:
            result['source'] = render_single_field(fields_by_key['source'], prefix, values)
        elif 'opportunity_owner' in fields_by_key:
            result['opportunity_owner'] = render_single_field(fields_by_key['opportunity_owner'], prefix, values)

        if 'priority' in fields_by_key and 'follow_up_status' in fields_by_key:
            c1, c2 = st.columns(2)
            with c1:
                result['priority'] = render_single_field(fields_by_key['priority'], prefix, values, placeholder="e.g. High, Medium, Low")
            with c2:
                result['follow_up_status'] = render_single_field(fields_by_key['follow_up_status'], prefix, values, placeholder="e.g. Pre-outreach, Active, In Research")
        elif 'priority' in fields_by_key:
            result['priority'] = render_single_field(fields_by_key['priority'], prefix, values)
        elif 'follow_up_status' in fields_by_key:
            result['follow_up_status'] = render_single_field(fields_by_key['follow_up_status'], prefix, values)

        if 'next_action_date' in fields_by_key:
            c1, _ = st.columns(2)
            with c1:
                result['next_action_date'] = render_single_field(fields_by_key['next_action_date'], prefix, values)

        if 'next_action' in fields_by_key:
            result['next_action'] = render_single_field(fields_by_key['next_action'], prefix, values, placeholder="e.g. Schedule discovery call with decision maker")

    # Section D: Additional Qualification & Notes (Collapsed Expander)
    qual_keys = {'pain_points', 'desired_outcome', 'intent_signals', 'qualification_notes', 'notes'} & set(fields_by_key)
    if qual_keys:
        with st.expander("Additional Qualification & Notes", expanded=False):
            if 'pain_points' in fields_by_key:
                result['pain_points'] = render_single_field(fields_by_key['pain_points'], prefix, values, height=70, placeholder="Core operational friction, manual bottlenecks, or customer pain points...")
            if 'desired_outcome' in fields_by_key:
                result['desired_outcome'] = render_single_field(fields_by_key['desired_outcome'], prefix, values, height=70, placeholder="Target outcomes, business KPIs, or expected impact...")
            if 'intent_signals' in fields_by_key:
                result['intent_signals'] = render_single_field(fields_by_key['intent_signals'], prefix, values, height=60, placeholder="e.g. Hiring 6 enterprise AEs · Series B funding ($35M) · G2 review surge")
            if 'qualification_notes' in fields_by_key:
                result['qualification_notes'] = render_single_field(fields_by_key['qualification_notes'], prefix, values, height=70, placeholder="Budget confirmation, authority, timing, and ICP fit criteria...")
            if 'notes' in fields_by_key:
                result['notes'] = render_single_field(fields_by_key['notes'], prefix, values, height=70, placeholder="Account background, relationship notes, or miscellaneous context...")

    # Remaining fields (if any)
    handled_keys = {
        'company', 'contact', 'title', 'email', 'phone', 'website', 'industry', 'company_size', 'tech_stack',
        'acv', 'icp_fit', 'opportunity_brief',
        'source', 'opportunity_owner', 'priority', 'follow_up_status', 'next_action_date', 'next_action',
        'pain_points', 'desired_outcome', 'intent_signals', 'qualification_notes', 'notes'
    }
    remaining = [f for f in config.fields if f.key not in handled_keys and f.visible and (not intake or f.intake)]
    for rf in remaining:
        result[rf.key] = render_single_field(rf, prefix, values)

    return result


def intake(config, storage, prefix):
    st.subheader(config.labels.create)
    st.caption('Fields marked * are required. Use fictional information for this public demo.')
    with st.form(prefix + '_form', clear_on_submit=True):
        values = input_fields(config, prefix, intake=True)
        col_btn1, col_btn2 = st.columns([3, 7])
        with col_btn1:
            submitted = st.form_submit_button(config.labels.create, use_container_width=True)
    if submitted:
        try:
            storage.create(values)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state['_demo_flash'] = f'{config.labels.record_singular} added.'
            st.rerun()


def render_visual_conversion_funnel(funnel_rows):
    if not funnel_rows:
        return
    total_count = funnel_rows[0]['Count'] if funnel_rows else 0
    colors = ['#6366F1', '#0284C7', '#D97706', '#059669', '#7C3AED']

    bars_html = []
    for idx, row in enumerate(funnel_rows):
        color = colors[idx % len(colors)]
        label = row['Milestone']
        count = row['Count']
        prev_conv = row.get('Conversion from Previous', '—')
        overall_conv = row.get('Overall Conversion', '—')
        pct_of_total = (count / total_count * 100) if total_count > 0 else 0
        bar_width = max(3.5, pct_of_total) if count > 0 else 0

        step_badge = ""
        if prev_conv != '—':
            step_badge = f"<span style='color: {color}; font-weight: 600; font-size: 0.74rem;'>({prev_conv} step)</span>"

        bars_html.append(
            f"<div style='margin-bottom: 11px;'>"
            f"<div style='display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 3px; font-size: 0.82rem;'>"
            f"<div style='font-weight: 600; color: #F8FAFC;'>"
            f"<span style='display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: {color}; margin-right: 6px;'></span>"
            f"{label}"
            f"</div>"
            f"<div style='font-size: 0.78rem; color: #94A3B8;'>"
            f"<b style='color: #F8FAFC; font-size: 0.86rem;'>{count}</b>"
            f"&nbsp;·&nbsp; <span style='color: #CBD5E1;'>{overall_conv} of cohort</span>"
            f"&nbsp;{step_badge}"
            f"</div>"
            f"</div>"
            f"<div style='background: #1E293B; height: 10px; border-radius: 5px; overflow: hidden; width: 100%; border: 1px solid #334155;'>"
            f"<div style='background: {color}; height: 100%; width: {bar_width:.1f}%; border-radius: 4px;'></div>"
            f"</div>"
            f"</div>"
        )

    bars_content = "".join(bars_html)
    container_html = (
        f"<div style='background: #0F172A; border: 1px solid #1E293B; border-radius: 8px; padding: 14px 16px; margin-bottom: 14px;'>"
        f"<div style='font-size: 0.74rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px;'>"
        f"Conversion Pipeline Funnel"
        f"</div>"
        f"{bars_content}"
        f"</div>"
    )
    st.markdown(container_html, unsafe_allow_html=True)


def record_table(config, records):
    stages = {s.id: s.name for s in config.stages}
    rows = [{**{f.label: format_field(f, r.fields.get(f.key)) for f in config.fields if f.visible and f.table},
             config.labels.stage: stages.get(r.stage_id, r.stage_id)} for r in records]
    st.dataframe(rows, hide_index=True, width="stretch")


def pipeline_distribution_bar(config, records):
    stage_counts = {s.id: 0 for s in config.stages}
    for r in records:
        if r.stage_id in stage_counts:
            stage_counts[r.stage_id] += 1

    today_str = datetime.date.today().isoformat()
    overdue_cnt = sum(1 for r in records if r.fields.get('next_action_date') and str(r.fields.get('next_action_date')) < today_str and r.stage_id not in ('disqualified', 'no_response', 'contract_awarded', 'lost'))
    today_cnt = sum(1 for r in records if str(r.fields.get('next_action_date')) == today_str and r.stage_id not in ('disqualified', 'no_response', 'contract_awarded', 'lost'))
    replied_cnt = sum(1 for r in records if r.stage_id in ('replied', 'proposal_sent'))
    active_cnt = sum(1 for r in records if any(s.id == r.stage_id and s.active for s in config.stages))
    total_cnt = len(records)

    items_html = []
    for s in config.stages:
        cnt = stage_counts.get(s.id, 0)
        style = STAGE_STYLES.get(s.id, {'fg': '#94A3B8'})
        items_html.append(f"<span style='color: #94A3B8;'>{s.name}:</span> <b style='color: {style['fg']};'>{cnt}</b>")

    breakdown_str = " &nbsp;·&nbsp; ".join(items_html)

    # Operational Priorities Alert Row
    priority_badges = [
        f"<span style='color:#38BDF8;'><b>{active_cnt}</b> Active Opportunities</span>"
    ]
    if overdue_cnt > 0:
        priority_badges.append(f"<span style='color:#FB7185;'>⚠️ <b>{overdue_cnt}</b> Overdue Actions</span>")
    if today_cnt > 0:
        priority_badges.append(f"<span style='color:#FBBF24;'>📅 <b>{today_cnt}</b> Due Today</span>")
    if replied_cnt > 0:
        priority_badges.append(f"<span style='color:#34D399;'>💬 <b>{replied_cnt}</b> Awaiting Follow-up</span>")

    priority_str = " &nbsp;|&nbsp; ".join(priority_badges)

    st.markdown(
        f"""
        <div style='margin-top: 4px; margin-bottom: 10px; font-size: 0.82rem; color: #94A3B8; background: #0F172A; padding: 8px 14px; border-radius: 6px; border: 1px solid #334155;'>
            <div style='display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 4px;'>
                <div><span style='color: #F8FAFC; font-weight: 700; text-transform: uppercase; font-size: 0.74rem; letter-spacing: 0.5px;'>Daily Priorities:</span> &nbsp; {priority_str}</div>
                <div style='color: #64748B; font-size: 0.77rem;'>Total Tracked: {total_cnt}</div>
            </div>
            <div style='border-top: 1px solid #1E293B; padding-top: 5px; font-size: 0.79rem;'>
                <span style='color: #94A3B8; font-weight: 600;'>Stage Distribution:</span> &nbsp; {breakdown_str}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_opportunity_workspace(config, storage, record, stages, prefix):
    """Read-first opportunity workspace emphasizing decisions, context, and actions."""
    company = record.fields.get('company', '')
    contact = record.fields.get('contact', '')
    title = record.fields.get('title', '')
    email = record.fields.get('email', '')
    phone = record.fields.get('phone', '')
    website = record.fields.get('website', '')
    industry = record.fields.get('industry', '')
    company_size = record.fields.get('company_size', '')
    tech_stack = record.fields.get('tech_stack', '')
    acv = record.fields.get('acv')
    brief = record.fields.get('opportunity_brief', '')
    pain_points = record.fields.get('pain_points', '')
    desired_outcome = record.fields.get('desired_outcome', '')
    icp_fit = record.fields.get('icp_fit', '')
    intent = record.fields.get('intent_signals', '')
    qual_notes = record.fields.get('qualification_notes', '')
    owner = record.fields.get('opportunity_owner', '')
    source = record.fields.get('source', '')
    priority = record.fields.get('priority', '')
    next_action = record.fields.get('next_action', '')
    next_action_date = record.fields.get('next_action_date', '')
    follow_up_status = record.fields.get('follow_up_status', '')
    notes = record.fields.get('notes', '')
    
    # Intelligence fields
    fit_rationale = record.fields.get('fit_rationale', '')
    opp_rationale = record.fields.get('opportunity_rationale', '')
    suggested_action = record.fields.get('suggested_action', '')
    suggested_angle = record.fields.get('suggested_angle', '')
    discovery_questions = record.fields.get('discovery_questions', '')
    objections = record.fields.get('objections', '')

    def human_date(d_str):
        if not d_str:
            return ""
        try:
            dt = datetime.date.fromisoformat(str(d_str)[:10])
            return dt.strftime("%b %d, %Y")
        except Exception:
            return str(d_str)[:10]

    # --- SECTION B: OPPORTUNITY BRIEF (Prominent & Clean) ---
    if brief:
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.45); border-left: 3px solid #6366F1; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px;">
                <div style="font-size: 0.70rem; font-weight: 700; color: #818CF8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;">Opportunity Brief</div>
                <div style="font-size: 0.88rem; color: #F1F5F9; line-height: 1.45;">{brief}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- SECTION C: RECOMMENDED NEXT ACTION (Hero Callout) ---
    today = datetime.date.today()
    is_overdue = False
    is_today = False
    formatted_due = "No due date"
    if next_action_date:
        try:
            act_d = datetime.date.fromisoformat(str(next_action_date))
            days_diff = (act_d - today).days
            d_fmt = act_d.strftime("%b %d, %Y")
            if days_diff < 0 and record.stage_id not in ('disqualified', 'no_response', 'contract_awarded', 'lost'):
                is_overdue = True
                formatted_due = f"<span style='color:#FB7185; font-weight:700;'>⚠️ Due {d_fmt} ({abs(days_diff)}d overdue)</span>"
            elif days_diff == 0:
                is_today = True
                formatted_due = f"<span style='color:#FBBF24; font-weight:700;'>📅 Due Today ({d_fmt})</span>"
            elif days_diff == 1:
                formatted_due = f"<span style='color:#38BDF8; font-weight:600;'>📅 Due Tomorrow ({d_fmt})</span>"
            else:
                formatted_due = f"<span style='color:#CBD5E1;'>📅 Due {d_fmt}</span>"
        except Exception:
            formatted_due = f"<span style='color:#CBD5E1;'>📅 Due {next_action_date}</span>"

    box_bg = "rgba(239, 68, 68, 0.08)" if is_overdue else ("rgba(245, 158, 11, 0.08)" if is_today else "rgba(99, 102, 241, 0.07)")
    box_border = "rgba(239, 68, 68, 0.35)" if is_overdue else ("rgba(245, 158, 11, 0.35)" if is_today else "rgba(99, 102, 241, 0.30)")
    accent_color = "#FB7185" if is_overdue else ("#FBBF24" if is_today else "#818CF8")

    action_box_html = f"""
    <div style="background: {box_bg}; border: 1px solid {box_border}; border-radius: 6px; padding: 8px 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div style="flex: 1; min-width: 250px;">
            <div style="font-size: 0.70rem; font-weight: 700; color: {accent_color}; text-transform: uppercase; letter-spacing: 0.5px;">Recommended Next Action</div>
            <div style="font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin-top: 2px;">🎯 {next_action or 'Identify next milestone'}</div>
        </div>
        <div style="font-size: 0.80rem; text-align: right; flex-shrink: 0;">
            <div>{formatted_due}</div>
            <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 1px;">Status: <b style="color:#CBD5E1;">{follow_up_status or 'Active'}</b></div>
        </div>
    </div>
    """
    st.markdown(action_box_html, unsafe_allow_html=True)

    # Balanced Two-Column Workspace Layout (Section 2.D)
    col_left, col_right = st.columns([1, 1])

    with col_left:
        # --- 1. Account Profile (2-column key/value grid) ---
        tech_badges = ""
        if tech_stack:
            t_items = [t.strip() for t in tech_stack.split('·')]
            tech_badges = " ".join([f"<span style='background:#1E293B; border:1px solid #334155; color:#38BDF8; padding:1px 5px; border-radius:3px; font-size:0.72rem; font-weight:500;'>{t}</span>" for t in t_items])

        profile_items = [
            f'<div><span style="color:#64748B; font-weight:600;">Contact:</span> <span style="color:#F8FAFC;">{contact or "—"}</span></div>',
            f'<div><span style="color:#64748B; font-weight:600;">Job Title:</span> <span style="color:#F8FAFC;">{title or "—"}</span></div>',
            f'<div><span style="color:#64748B; font-weight:600;">Email:</span> <span style="color:#94A3B8; font-family:monospace; font-size:0.76rem;">{email or "—"}</span></div>',
        ]
        if phone:
            profile_items.append(f'<div><span style="color:#64748B; font-weight:600;">Phone:</span> <span style="color:#94A3B8; font-family:monospace; font-size:0.76rem;">{phone}</span></div>')
        profile_items.extend([
            f'<div><span style="color:#64748B; font-weight:600;">Industry:</span> <span style="color:#F8FAFC;">{industry or "—"}</span></div>',
            f'<div><span style="color:#64748B; font-weight:600;">Company Size:</span> <span style="color:#F8FAFC;">{company_size or "—"}</span></div>',
            f'<div><span style="color:#64748B; font-weight:600;">Owner:</span> <span style="color:#F8FAFC;">{owner or "—"}</span></div>',
            f'<div><span style="color:#64748B; font-weight:600;">Lead Source:</span> <span style="color:#F8FAFC;">{source or "—"}</span></div>',
            f'<div><span style="color:#64748B; font-weight:600;">Tech Stack:</span> {tech_badges or "—"}</div>',
        ])

        profile_grid_html = f"""
        <div style="font-size:0.74rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Account Profile</div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px 12px; background: #0F172A; border: 1px solid #1E293B; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; font-size: 0.80rem;">
            {''.join(profile_items)}
        </div>
        """
        st.markdown(profile_grid_html, unsafe_allow_html=True)

        # --- 2. Business Needs and Qualification ---
        st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;'>Needs & Qualification</div>", unsafe_allow_html=True)
        needs_html = "<div style='background:#0F172A; border:1px solid #1E293B; border-radius:6px; padding:8px 12px; margin-bottom:10px; font-size:0.81rem;'>"
        if pain_points:
            needs_html += f"<div style='margin-bottom:6px;'><span style='color:#FCA5A5; font-weight:600;'>Pain Points & Needs:</span> <span style='color:#E2E8F0;'>{pain_points}</span></div>"
        if desired_outcome:
            needs_html += f"<div style='margin-bottom:6px;'><span style='color:#34D399; font-weight:600;'>Desired Outcome:</span> <span style='color:#E2E8F0;'>{desired_outcome}</span></div>"
        if intent:
            signals = [s.strip() for s in intent.split('·')]
            sig_pills = " ".join([f"<span style='background:#1E293B; border:1px solid #334155; color:#FBBF24; padding:1px 6px; border-radius:3px; font-size:0.73rem; display:inline-block; margin:2px 2px;'>⚡ {s}</span>" for s in signals])
            needs_html += f"<div style='margin-top:4px;'><span style='color:#94A3B8; font-weight:600;'>Intent Signals:</span> {sig_pills}</div>"
        if qual_notes:
            needs_html += f"<div style='margin-top:6px; border-top:1px solid #1E293B; padding-top:4px; font-size:0.77rem; color:#94A3B8;'><b>Qualification Note:</b> {qual_notes}</div>"
        needs_html += "</div>"
        st.markdown(needs_html, unsafe_allow_html=True)

        # --- 3. Immediately Visible Account Intelligence ---
        if fit_rationale or opp_rationale or suggested_angle:
            st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#818CF8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;'>Account Intelligence</div>", unsafe_allow_html=True)
            intel_html = "<div style='background:#0F172A; border:1px solid #1E293B; border-radius:6px; padding:8px 12px; margin-bottom:8px; font-size:0.81rem;'>"
            if fit_rationale:
                intel_html += f"<div style='margin-bottom:6px; border-left:2px solid #38BDF8; padding-left:8px;'><span style='color:#38BDF8; font-weight:600;'>Why This Account:</span> <span style='color:#E2E8F0;'>{fit_rationale}</span></div>"
            if opp_rationale:
                intel_html += f"<div style='margin-bottom:6px; border-left:2px solid #FBBF24; padding-left:8px;'><span style='color:#FBBF24; font-weight:600;'>Why Now:</span> <span style='color:#E2E8F0;'>{opp_rationale}</span></div>"
            if suggested_angle:
                intel_html += f"<div style='border-top:1px solid #1E293B; padding-top:6px;'><span style='color:#818CF8; font-weight:600;'>Suggested Outreach Angle:</span><div style='color:#F8FAFC; background:#1E293B; border-radius:4px; padding:6px 8px; margin-top:3px; line-height:1.4;'>{suggested_angle}</div></div>"
            intel_html += "</div>"
            st.markdown(intel_html, unsafe_allow_html=True)

        # --- 4. Secondary Intelligence (Discovery Preparation & Objections) ---
        if discovery_questions or objections:
            with st.expander("Discovery Preparation & Potential Objections", expanded=False):
                if discovery_questions:
                    st.markdown(f"<div style='font-size:0.80rem; color:#CBD5E1; margin-bottom:6px;'><b style='color:#38BDF8;'>Discovery Questions:</b><br>{discovery_questions}</div>", unsafe_allow_html=True)
                if objections:
                    st.markdown(f"<div style='font-size:0.80rem; color:#CBD5E1;'><b style='color:#FB7185;'>Potential Objections & Handling:</b><br>{objections}</div>", unsafe_allow_html=True)

    with col_right:
        # --- 1. Pipeline Stage & Quick Movement ---
        st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;'>Pipeline Stage</div>", unsafe_allow_html=True)
        with st.form(f"{prefix}_stage_form_{record.id}"):
            col_st1, col_st2 = st.columns([7, 3])
            with col_st1:
                new_stage = st.selectbox(
                    config.labels.stage,
                    list(stages),
                    index=list(stages).index(record.stage_id) if record.stage_id in stages else 0,
                    format_func=stages.get,
                    key=f"{prefix}_stage_{record.id}",
                    label_visibility="collapsed"
                )
            with col_st2:
                save_stage = st.form_submit_button(config.labels.save, use_container_width=True)
            if save_stage:
                try:
                    storage.update(record.id, {}, new_stage)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.session_state['_demo_flash'] = f'Moved to {stages.get(new_stage, new_stage)}.'
                    st.rerun()

        # --- 2. Activity Logging ---
        if config.features.activities:
            st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-top:8px; margin-bottom:4px;'>Log Activity</div>", unsafe_allow_html=True)
            with st.form(f"{prefix}_activity_{record.id}", clear_on_submit=True):
                text = st.text_area('Activity Summary / Note', max_chars=2000, key=f"{prefix}_note_{record.id}", height=60, label_visibility="collapsed", placeholder="Enter call notes, email summary, or next step details...")
                col_act1, col_act2 = st.columns([3, 2])
                with col_act1:
                    kind = st.selectbox(
                        'Activity Type',
                        ['call', 'email', 'contacted', 'replied', 'meeting', 'note', 'follow_up'],
                        format_func=lambda v: {'call': '📞 Call', 'email': '✉️ Email', 'contacted': '📤 Contacted', 'replied': '💬 Replied', 'meeting': '📅 Meeting', 'note': '📝 Note', 'follow_up': '🔄 Follow-up'}.get(v, v.title()),
                        key=f"{prefix}_kind_{record.id}",
                        label_visibility="collapsed"
                    )
                with col_act2:
                    add = st.form_submit_button(config.labels.add_note, use_container_width=True)
                if add and text.strip():
                    try:
                        storage.add_activity(record.id, kind, text.strip())
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.rerun()

        # --- 3. Unified Reverse-Chronological Activity Timeline ---
        st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-top:8px; margin-bottom:6px;'>Activity & Progression Timeline</div>", unsafe_allow_html=True)
        
        events = []
        for act in getattr(record, 'activities', []):
            events.append({
                'time': act.occurred_at or '',
                'kind': act.kind,
                'title': act.kind.replace('_', ' ').title(),
                'text': act.text,
                'is_stage': False
            })
        for stg in getattr(record, 'stage_history', []):
            events.append({
                'time': stg.entered_at or '',
                'kind': 'stage_change',
                'title': f"Moved to {stages.get(stg.stage_id, stg.stage_id)}",
                'text': '',
                'is_stage': True
            })
        events.sort(key=lambda e: e['time'], reverse=True)

        if events:
            kind_icons = {
                'call': '📞', 'email': '✉️', 'contacted': '📤', 'replied': '💬',
                'meeting': '📅', 'opportunity': '🏆', 'note': '📝', 'follow_up': '🔄',
                'stage_change': '🚀'
            }
            timeline_html = "<div style='max-height: 250px; overflow-y: auto; padding-right: 4px;'>"
            for ev in events:
                icon = kind_icons.get(ev['kind'], '•')
                t_str = human_date(ev['time'][:10]) if ev['time'] else 'Initial'
                border_color = "#6366F1" if ev['is_stage'] else "#334155"
                text_block = f"<div style='color: #CBD5E1; margin-top: 2px;'>{ev['text']}</div>" if ev['text'] else ""
                timeline_html += (
                    f"<div style='border-left: 2px solid {border_color}; padding-left: 10px; margin-bottom: 8px; font-size: 0.80rem;'>"
                    f"<div style='color: #94A3B8; font-size: 0.72rem;'>{icon} <b style='color:#F1F5F9;'>{ev['title']}</b> &nbsp;·&nbsp; {t_str}</div>"
                    f"{text_block}"
                    f"</div>"
                )
            timeline_html += "</div>"
            st.markdown(timeline_html, unsafe_allow_html=True)
        else:
            st.caption("No activities recorded yet.")


def pipeline(config, storage, prefix):
    records = storage.list_records()
    if 'metrics' in config.dashboard_modules:
        metric_cards(config, records)
    pipeline_distribution_bar(config, records)

    # Inline quick add
    with st.expander(f"+ {config.labels.create}", expanded=False):
        intake(config, storage, prefix + '_inline')

    stages = {s.id: s.name for s in config.stages}

    # Compact multi-column Search, Filter & Page selector
    col_search, col_filter, col_page = st.columns([6, 3, 2])
    with col_search:
        search = st.text_input(
            f'Search {config.labels.record_plural.lower()}',
            placeholder=f'Search {config.labels.record_plural.lower()} by company, contact, or keywords...',
            key=prefix + '_search'
        ).lower().strip()
    with col_filter:
        stage_filter = st.selectbox(
            config.labels.stage,
            ['all', *stages],
            format_func=lambda value: 'All stages' if value == 'all' else stages[value],
            key=prefix + '_filter'
        )

    visible = [r for r in records if (stage_filter == 'all' or stage_filter == r.stage_id)
               and (not search or search in ' '.join(str(v) for v in r.fields.values()).lower())]

    total_pages = max(1, (len(visible) + 9) // 10)
    with col_page:
        page = st.selectbox(
            'Page',
            list(range(1, total_pages + 1)),
            format_func=lambda p: f'Page {p} of {total_pages}',
            key=prefix + '_page'
        )

    st.markdown(
        f"<div style='font-size: 0.82rem; color: #94A3B8; margin-top: -6px; margin-bottom: 8px;'>"
        f"Showing <b>{len(visible)}</b> of {len(records)} {config.labels.record_plural.lower()} &nbsp;·&nbsp; Page {page} of {total_pages}"
        f"</div>",
        unsafe_allow_html=True
    )

    if not visible:
        st.info(f'No {config.labels.record_plural.lower()} match. Add a record or change the filters.')
        return

    if 'table' in config.dashboard_modules:
        with st.expander('Table'):
            record_table(config, visible)

    for record in visible[(page - 1) * 10:page * 10]:
        company = record.fields.get('company', '')
        contact = record.fields.get('contact', '')
        title = record.fields.get('title', '')
        acv = record.fields.get('acv')
        industry = record.fields.get('industry', '')
        source = record.fields.get('source', '')
        stage_name = stages.get(record.stage_id, record.stage_id)
        brief = record.fields.get('opportunity_brief') or record.fields.get('notes', '')
        icp_fit = record.fields.get('icp_fit', '')
        tech_stack = record.fields.get('tech_stack', '')
        intent = record.fields.get('intent_signals', '')
        next_action = record.fields.get('next_action', '')
        next_action_date = record.fields.get('next_action_date', '')
        priority = record.fields.get('priority', '')

        phone = record.fields.get('phone', '')

        # Line 1: Header (Company — Contact (Title) · Phone · Stage)
        header_text = f"**{company}**"
        if contact:
            header_text += f" — {contact}" + (f" ({title})" if title else "")
        if phone:
            header_text += f" &nbsp;·&nbsp; `{phone}`"
        header_text += f" &nbsp;·&nbsp; `{stage_name}`"

        # Line 2: Opportunity Brief (Clean, readable text, no blockquote clipping)
        clean_brief = brief.strip()
        if len(clean_brief) > 130:
            clean_brief = clean_brief[:127] + "..."

        # Line 3: Badges + Action Footer
        badges = []
        if icp_fit:
            badges.append(f"🎯 {icp_fit} Fit")
        if intent:
            top_intent = intent.split('·')[0].strip()
            if len(top_intent) > 28:
                top_intent = top_intent[:25] + "..."
            badges.append(f"⚡ {top_intent}")
        if tech_stack:
            top_tech = tech_stack.split('·')[0].strip()
            badges.append(f"🛠️ {top_tech}")
        badges_str = " &nbsp;·&nbsp; ".join(badges)

        footer_items = []
        if next_action:
            short_na = next_action if len(next_action) <= 46 else next_action[:43] + "..."
            footer_items.append(f"**Next:** {short_na}")
        if next_action_date:
            try:
                d = datetime.date.fromisoformat(str(next_action_date))
                diff = (d - datetime.date.today()).days
                if diff < 0 and record.stage_id not in ('disqualified', 'no_response', 'contract_awarded', 'lost'):
                    footer_items.append(f":red[⚠️ Due {d.strftime('%b %d')} ({abs(diff)}d overdue)]")
                elif diff == 0:
                    footer_items.append(":orange[📅 Due Today]")
                else:
                    footer_items.append(f"📅 {d.strftime('%b %d')}")
            except Exception:
                footer_items.append(f"📅 {next_action_date}")
        if acv is not None:
            try:
                footer_items.append(f":green[${float(acv):,.0f} ACV]")
            except Exception:
                footer_items.append(f":green[{acv}]")

        footer_str = " &nbsp;·&nbsp; ".join(footer_items)

        card_header = f"{header_text}\n\n{clean_brief}\n\n{badges_str} &nbsp;|&nbsp; {footer_str}"

        with st.expander(card_header):
            is_editing = st.session_state.get(f'{prefix}_editing_{record.id}', False)

            # Top Header Bar with Edit Action (Section 2.A)
            contact_info = f"{contact}" + (f", {title}" if title else "") if contact else ""
            st_style = STAGE_STYLES.get(record.stage_id, {'bg': '#1E293B', 'fg': '#CBD5E1', 'border': '#334155'})
            pills = [
                f"<span style='background:{st_style['bg']}; color:{st_style['fg']}; border:1px solid {st_style['border']}; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700;'>{stage_name}</span>"
            ]
            if acv is not None:
                try:
                    pills.append(f"<span style='background:#064E3B33; color:#34D399; border:1px solid #05966955; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700;'>${float(acv):,.0f} ACV</span>")
                except Exception:
                    pass
            if icp_fit:
                icp_color = '#38BDF8' if icp_fit == 'High' else '#FBBF24'
                pills.append(f"<span style='background:#0F172A; color:{icp_color}; border:1px solid #334155; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600;'>🎯 {icp_fit} Fit</span>")
            if priority:
                pills.append(f"<span style='background:#0F172A; color:#E2E8F0; border:1px solid #334155; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:500;'>⚡ {priority} Priority</span>")

            pills_str = " ".join(pills)

            col_bar1, col_bar2 = st.columns([5, 1])
            with col_bar1:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px; margin-bottom: 6px;">
                        <span style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC;">{company}</span>
                        <span style="font-size: 0.83rem; color: #94A3B8;">{contact_info}</span>
                        <div style="display: inline-flex; align-items: center; gap: 5px; margin-left: 4px;">{pills_str}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_bar2:
                if st.button("✏️ Edit" if not is_editing else "✖️ View", key=f"{prefix}_btn_toggle_{record.id}", use_container_width=True):
                    st.session_state[f'{prefix}_editing_{record.id}'] = not is_editing
                    st.rerun()

            if is_editing:
                # Section F: Edit Mode
                st.markdown("<div style='font-size:0.78rem; font-weight:700; color:#818CF8; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:6px;'>✏️ Edit Opportunity Details</div>", unsafe_allow_html=True)
                with st.form(f"{prefix}_edit_{record.id}"):
                    values = input_fields(config, f"{prefix}_{record.id}", record.fields)
                    stage = st.selectbox(
                        config.labels.stage,
                        list(stages),
                        index=list(stages).index(record.stage_id) if record.stage_id in stages else 0,
                        format_func=stages.get,
                        key=f"{prefix}_stage_{record.id}"
                    )
                    col_save, col_cancel = st.columns([1, 1])
                    with col_save:
                        save = st.form_submit_button(config.labels.save, use_container_width=True)
                    with col_cancel:
                        cancel = st.form_submit_button("Cancel", use_container_width=True)
                if save:
                    try:
                        storage.update(record.id, values, stage)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.session_state[f'{prefix}_editing_{record.id}'] = False
                        st.session_state['_demo_flash'] = 'Changes saved.'
                        st.rerun()
                if cancel:
                    st.session_state[f'{prefix}_editing_{record.id}'] = False
                    st.rerun()
            else:
                # Read-First Opportunity Workspace
                render_opportunity_workspace(config, storage, record, stages, prefix)


def intelligence(config):
    heading = config.labels.intelligence
    st.subheader(heading)
    if config.pipeline_type == 'sales_rep_outbound':
        st.caption('Reusable discovery guides, buying signals, outreach angles, and objection-handling resources for common sales scenarios.')
    else:
        st.caption('Commercial discovery guides, client requirements, and conversation frameworks for consultative engagements.')

    items = IntelligenceService.load_intel(Path(__file__).resolve().parents[3] / 'intel.json.example')
    query = st.text_input(
        f"Find {heading.lower()}",
        placeholder='Search by scenario, pain point, sector, or keyword...',
        key='public_intelligence_search'
    )
    cards = IntelligenceService.get_cue_cards(items, query)
    if not cards:
        st.info(f'No matching playbooks. Try another search.')
        return

    for item in cards:
        with st.expander(f"📘 {item.title}", expanded=True):
            st.markdown(
                f"""
                <div style="background:#0F172A; border-left:4px solid #6366F1; border-radius:6px; padding:10px 14px; margin-bottom:12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="color:#818CF8; font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">{' · '.join(item.tags)}</span>
                        <span style="background:#1E293B; border:1px solid #334155; color:#94A3B8; padding:1px 6px; border-radius:3px; font-size:0.68rem; font-weight:600;">SYNTHETIC PLAYBOOK</span>
                    </div>
                    <div style="color:#F8FAFC; font-size:0.90rem; font-weight:600; line-height:1.4;">{item.summary}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if item.context:
                st.markdown(
                    f"""
                    <div style="background:#0F172A; border:1px solid #1E293B; border-radius:6px; padding:8px 12px; margin-bottom:10px; font-size:0.82rem;">
                        <span style="color:#38BDF8; font-weight:700; text-transform:uppercase; font-size:0.70rem; letter-spacing:0.4px;">Context & Business Scenario</span>
                        <div style="color:#CBD5E1; margin-top:2px; line-height:1.4;">{item.context}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            col_p1, col_p2 = st.columns([1, 1])
            with col_p1:
                if item.pain_points:
                    st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#FCA5A5; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:4px;'>Common Pain Points</div>", unsafe_allow_html=True)
                    pts_html = "".join([f"<div style='font-size:0.80rem; color:#E2E8F0; margin-bottom:4px; line-height:1.35;'>• {p}</div>" for p in item.pain_points])
                    st.markdown(f"<div style='background:#0F172A; border:1px solid #1E293B; border-radius:6px; padding:8px 12px; margin-bottom:10px;'>{pts_html}</div>", unsafe_allow_html=True)
            with col_p2:
                if item.signals:
                    st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#FBBF24; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:4px;'>Signals to Investigate</div>", unsafe_allow_html=True)
                    sigs_html = "".join([f"<div style='font-size:0.80rem; color:#E2E8F0; margin-bottom:4px; line-height:1.35;'>⚡ {s}</div>" for s in item.signals])
                    st.markdown(f"<div style='background:#0F172A; border:1px solid #1E293B; border-radius:6px; padding:8px 12px; margin-bottom:10px;'>{sigs_html}</div>", unsafe_allow_html=True)

            if item.questions:
                st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#38BDF8; text-transform:uppercase; letter-spacing:0.4px; margin-top:4px; margin-bottom:4px;'>Discovery Questions</div>", unsafe_allow_html=True)
                for q in item.questions:
                    st.code(q, language=None)

            if item.outreach_angles:
                st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#34D399; text-transform:uppercase; letter-spacing:0.4px; margin-top:6px; margin-bottom:4px;'>Suggested Outreach Angles</div>", unsafe_allow_html=True)
                for angle in item.outreach_angles:
                    st.code(angle, language=None)

            if item.objections:
                st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#FB7185; text-transform:uppercase; letter-spacing:0.4px; margin-top:6px; margin-bottom:4px;'>Potential Objections & Handling</div>", unsafe_allow_html=True)
                for obj in item.objections:
                    st.markdown(f"<div style='background:#1E293B; border-left:3px solid #FB7185; border-radius:4px; padding:6px 10px; margin-bottom:4px; font-size:0.80rem; color:#CBD5E1; line-height:1.35;'>{obj}</div>", unsafe_allow_html=True)


def metric_cards(config, records):
    metrics = calculate_metrics(records, config)
    if not metrics:
        return
    col_count = len(metrics) if len(metrics) <= 6 else 6
    columns = st.columns(col_count)
    for index, (key, metric) in enumerate(metrics.items()):
        value = metric['value']
        display = '—' if value is None else (f'{value:.1f}%' if metric['format'] == 'percent' else
                                           f'${value:,.0f}' if metric['format'] == 'currency' else str(value))
        label = config.labels.record_plural if key == 'total' else metric['label']
        target_col = columns[index % col_count]
        target_col.metric(label, display)
        if 'denominator' in metric:
            target_col.caption(f"{metric['numerator']} / {metric['denominator']} unique prospects")


def render_public(config):
    import os
    workspace_options = {
        'sales_rep': 'Sales Rep (Outbound Prospecting)',
        'b2b_services': 'B2B Services (Client Opportunities)',
    }
    default_ws = 'b2b_services' if config.pipeline_type == 'b2b_services' else 'sales_rep'
    active_ws = st.session_state.get('demo_workspace_selector', default_ws)

    # Dynamically load selected workspace configuration if user switched workspaces
    if not os.environ.get('PIPELINE_INSTANCE_CONFIG'):
        if active_ws == 'b2b_services' and config.pipeline_type != 'b2b_services':
            from pipeline.domain.instance_loader import load_demo_config
            b2b_path = Path(__file__).resolve().parents[3] / 'config' / 'demo_b2b_services.json'
            config = load_demo_config(b2b_path)
        elif active_ws == 'sales_rep' and config.pipeline_type == 'b2b_services':
            from pipeline.domain.instance_loader import load_demo_config
            sales_path = Path(__file__).resolve().parents[3] / 'config' / 'demo_sales_rep.json'
            config = load_demo_config(sales_path)

    try:
        storage = session_storage(config, active_ws)
    except (OSError, ValueError):
        st.error('Demo data does not match its configuration. No integrations were started.')
        return

    # Sidebar Brand Header
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px; padding: 2px 0px;">
            <div style="
                width: 36px;
                height: 36px;
                background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                font-size: 15px;
                color: #FFFFFF;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25);
                flex-shrink: 0;
            ">MO</div>
            <div style="line-height: 1.25;">
                <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC; letter-spacing: -0.2px;">More Outbound</div>
                <div style="font-size: 0.70rem; font-weight: 600; color: #818CF8; text-transform: uppercase; letter-spacing: 0.6px;">Pipeline Intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Demo Workspace Selector (Section 2)
    st.sidebar.markdown(
        "<div style='font-size:0.72rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;'>Demo Workspace</div>",
        unsafe_allow_html=True
    )
    selected_ws = st.sidebar.selectbox(
        'Demo Workspace',
        list(workspace_options.keys()),
        index=0 if active_ws == 'sales_rep' else 1,
        format_func=workspace_options.get,
        key='demo_workspace_selector',
        label_visibility='collapsed'
    )
    st.sidebar.caption("More Outbound adapts pipeline stages, fields, and workflows via configuration.")

    if selected_ws != active_ws:
        st.rerun()

    st.markdown(PUBLIC_THEME_CSS, unsafe_allow_html=True)

    # Main Page Title & Subtitle with custom classes
    st.markdown(f'<div class="demo-main-title">{config.page_title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="demo-sub-title">{config.page_subtitle}</div>', unsafe_allow_html=True)

    # Subtle Demo Sandbox Indicator (Section 7)
    st.sidebar.markdown(
        """
        <div style="background: #0F172A; border: 1px solid #1E293B; border-left: 3px solid #6366F1; border-radius: 6px; padding: 7px 10px; margin-bottom: 12px; font-size: 0.77rem; color: #94A3B8; line-height: 1.35;">
            <strong style="color: #F8FAFC;">Demo Sandbox</strong><br>
            Isolated visitor session. No live integrations or messages are sent.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Sidebar Navigation
    st.sidebar.markdown("<div style='font-size:0.72rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;'>Navigation</div>", unsafe_allow_html=True)
    nav = {n.id: n.label for n in config.navigation}
    destination = st.sidebar.radio('Navigate', list(nav), format_func=nav.get, key='public_navigation')

    st.sidebar.caption(f"**{config.display_name}** · Public Demo")

    if '_demo_flash' in st.session_state:
        st.success(st.session_state.pop('_demo_flash'))

    prefix = 'public_' + str(st.session_state.get('_demo_epoch', 0))

    if destination == 'intake':
        intake(config, storage, prefix + '_intake')
    elif destination == 'pipeline':
        pipeline(config, storage, prefix)
    elif destination == 'intelligence':
        intelligence(config)
    else:
        st.subheader(nav[destination])
        records = storage.list_records()
        if 'metrics' in config.dashboard_modules:
            metric_cards(config, records)
        if 'funnel' in config.dashboard_modules:
            st.subheader('Historical Conversion Funnel')
            funnel_rows = conversion_funnel(records, config)
            render_visual_conversion_funnel(funnel_rows)
            with st.expander('Conversion Funnel Data Table', expanded=True):
                st.dataframe(funnel_rows, hide_index=True, width="stretch")
            st.caption('Each step counts unique records that achieved every preceding milestone. Later stage moves retain earlier achievements.')
        if 'table' in config.dashboard_modules:
            record_table(config, records)
        st.caption('Booking counts any recorded booking, including a later cancellation. Closed and disqualified prospects retain their history. Missing evidence is not inferred; a zero denominator displays —.')

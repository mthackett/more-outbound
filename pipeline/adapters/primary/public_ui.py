"""Configuration-driven views for the sales prospecting and pipeline intelligence UI."""
import datetime
import hashlib
import html
import json
from pathlib import Path
import re
import streamlit as st
from pipeline.adapters.primary.demo_widgets import SYNTHETIC_NOTE, contact_action_buttons, render_sidebar_widgets
from pipeline.adapters.primary.runtime import select_session
from pipeline.adapters.secondary.memory_records import MemoryRecordStorage
from pipeline.domain.demo_dates import local_date, session_reference
from pipeline.domain.records import due_state, format_field, open_next_action
from pipeline.domain.intelligence_service import IntelligenceService
from pipeline.domain.outreach_metrics import (
    METRIC_REGISTRY, calculate_metrics, conversion_funnel, milestone_labels, stage_breakdown,
    trailing_periods, weekly_series,
)


def escape_markdown(text):
    """Escape dollar signs in Markdown strings to prevent accidental KaTeX math rendering."""
    if not text:
        return ""
    return re.sub(r'(?<!\\)\$', r'\$', str(text))

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
    div[data-testid="stMetric"] > div {
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
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
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] div,
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
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
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
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] div,
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] p {
        text-align: center !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 auto !important;
    }
    /* Tooltips dismiss themselves. A click that reruns the script can replace the hovered
       button before its mouse-out fires, orphaning the tooltip; rapid clicks stacked several.
       Each tooltip mounts fresh, so this animation restarts on every hover. */
    @keyframes mo-tooltip-autohide {
        0% { opacity: 0; visibility: visible; }
        10% { opacity: 1; }
        75% { opacity: 1; }
        100% { opacity: 0; visibility: hidden; }
    }
    div[role="tooltip"]:has([data-testid="stTooltipContent"]) {
        animation: mo-tooltip-autohide 1.8s ease-in-out forwards;
        pointer-events: none;
    }
    /* Only the newest tooltip is ever shown: hide any that a later one has superseded. */
    div[data-overlay-container]:has(~ div[data-overlay-container] [data-testid="stTooltipContent"])
        div[role="tooltip"]:has([data-testid="stTooltipContent"]) {
        display: none !important;
    }
    /* Phones: KPI cards two per row instead of one tall stack */
    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] [data-testid="stMetric"]) {
            flex-wrap: wrap !important;
            gap: 8px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] [data-testid="stMetric"]) > div[data-testid="stColumn"] {
            flex: 1 1 calc(50% - 8px) !important;
            min-width: calc(50% - 8px) !important;
            width: calc(50% - 8px) !important;
        }
    }
    /* Record header pills wrap as whole pills; profile values wrap inside their grid cell */
    .mo-pills > span { white-space: nowrap; }
    .mo-profile-grid > div { min-width: 0; overflow-wrap: anywhere; }
    /* Shared panel + uppercase section label used by analytics and widgets */
    .mo-panel {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 14px 16px;
    }
    .mo-label {
        font-size: 0.74rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }
    /* Side-by-side panels that always share one height; stack on narrow screens */
    .mo-grid-2 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        align-items: stretch;
        margin-bottom: 14px;
    }
    @media (max-width: 900px) {
        .mo-grid-2 { grid-template-columns: 1fr; }
    }
    /* Trailing-period comparison tiles */
    .mo-tiles {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
        gap: 10px;
        margin-bottom: 14px;
    }
    .mo-tile {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 10px 12px;
    }
    .mo-tile-label {
        font-size: 0.68rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        min-height: 1.9em;
    }
    .mo-tile-value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.25;
    }
    .mo-delta { font-size: 0.72rem; font-weight: 600; }
    .mo-delta-up { color: #34D399; }
    .mo-delta-down { color: #FB7185; }
    .mo-delta-flat { color: #94A3B8; }
    .mo-delta-prior { color: #64748B; font-weight: 500; margin-top: 1px; }
    .mo-table { width: 100%; border-collapse: collapse; font-size: 0.81rem; }
    .mo-table th {
        text-align: right; color: #94A3B8; font-weight: 700; font-size: 0.68rem;
        text-transform: uppercase; letter-spacing: 0.3px; padding: 6px 8px; border-bottom: 1px solid #1E293B;
    }
    .mo-table th:first-child, .mo-table td:first-child { text-align: left; }
    .mo-table td { text-align: right; color: #F1F5F9; padding: 7px 8px; border-bottom: 1px solid #1E293B; }
    .mo-table tr:last-child td { border-bottom: none; }
    .mo-table td .mo-delta { display: block; font-size: 0.68rem; }
    .mo-table-wrap { overflow-x: auto; }
    /* Section headings: consistent, compact hierarchy */
    [data-testid="stHeading"] h3 {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        padding-top: 0.6rem !important;
        padding-bottom: 0.35rem !important;
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
    /* Pipeline Card Company Names: MO Brand Blue */
    div[data-testid="stExpander"] details summary p > strong:first-child,
    div[data-testid="stExpander"] summary p > strong:first-child,
    div[data-testid="stExpander"] summary span[style*="blue"] strong,
    div[data-testid="stExpander"] summary span[style*="rgb(28, 131, 225)"] strong,
    div[data-testid="stExpander"] summary span[style*="rgb(0, 104, 201)"] strong {
        color: #818CF8 !important;
    }
    div[data-testid="stExpander"]:hover summary p > strong:first-child,
    div[data-testid="stExpander"]:hover summary span[style*="blue"] strong {
        color: #A5B4FC !important;
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


def session_storage(config, workspace_key=None, reference=None):
    select_session(st.session_state, 'demo')
    ws_key = workspace_key or config.pipeline_type or 'sales_rep'
    cfg_hash = hashlib.sha256(config.model_dump_json().encode()).hexdigest()[:12]
    store_key = f"{ws_key}_{cfg_hash}"
    if '_demo_workspace_stores' not in st.session_state:
        st.session_state['_demo_workspace_stores'] = {}
    stores = st.session_state['_demo_workspace_stores']
    ref = reference or st.session_state.get('_demo_reference') or session_reference()
    if store_key not in stores:
        seed = []
        fixtures_dir = Path(__file__).resolve().parents[2] / 'examples/fixtures'
        if config.seed in ('b2b_prospects', 'sales_rep_prospects'):
            seed = json.loads((fixtures_dir / 'demo_prospects.json').read_text(encoding='utf-8'))
        elif config.seed == 'b2b_services_prospects':
            seed = json.loads((fixtures_dir / 'demo_b2b_services.json').read_text(encoding='utf-8'))
        stores[store_key] = MemoryRecordStorage(config, seed, reference=ref)
    st.session_state['_demo_store'] = stores[store_key]
    return stores[store_key]


def render_single_field(field, prefix, values, height=None, placeholder=None):
    if not field.editable:
        st.text(f'{field.label}: {format_field(field, values.get(field.key))}')
        return values.get(field.key)
    label = field.label + (' *' if field.required else '')
    key = prefix + '_' + field.key
    val = values.get(field.key)
    if field.type in ('currency', 'number'):
        num_val = float(val) if val is not None and str(val).strip() != '' else None
        step = 1.0 if field.type == 'number' else 100.0
        return st.number_input(label, min_value=0.0, value=num_val, step=step, key=key)
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
            submitted = st.form_submit_button(config.labels.create, width='stretch')
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


def value_suffix(config):
    """How a record's value reads on cards: annual contract value for SaaS, a contract for services."""
    return 'contract' if config.pipeline_type == 'b2b_services' else 'ACV'


def awaiting_stage_ids(config):
    """Stages where the counterpart has responded and the ball is in our court."""
    return {s.id for s in config.stages if 'replied' in s.milestones and s.active}


def daily_priority_sets(config, records, reference=None):
    """Record ids per Daily Priority bucket, shared by the summary bar and filter."""
    today = reference.date if reference else datetime.date.today()
    active = {s.id for s in config.stages if s.active}
    awaiting = awaiting_stage_ids(config)
    sets = {'overdue': set(), 'due_today': set(), 'awaiting_reply': set(), 'active': set()}
    for r in records:
        if r.stage_id in awaiting:
            sets['awaiting_reply'].add(r.id)
        if r.stage_id not in active:
            continue
        sets['active'].add(r.id)
        state, _ = due_state(open_next_action(r)[1], today)
        if state == 'overdue':
            sets['overdue'].add(r.id)
        elif state == 'today':
            sets['due_today'].add(r.id)
    return sets


def pipeline_distribution_bar(config, records, reference=None):
    stage_counts = {s.id: 0 for s in config.stages}
    for r in records:
        if r.stage_id in stage_counts:
            stage_counts[r.stage_id] += 1

    priority_sets = daily_priority_sets(config, records, reference)
    overdue_cnt = len(priority_sets['overdue'])
    today_cnt = len(priority_sets['due_today'])
    replied_cnt = len(priority_sets['awaiting_reply'])
    active_cnt = len(priority_sets['active'])
    total_cnt = len(records)

    items_html = []
    for s in config.stages:
        cnt = stage_counts.get(s.id, 0)
        style = STAGE_STYLES.get(s.id, {'fg': '#94A3B8'})
        items_html.append(f"<span style='white-space: nowrap;'><span style='color: #94A3B8;'>{s.name}:</span> <b style='color: {style['fg']};'>{cnt}</b></span>")

    breakdown_str = " &nbsp;·&nbsp; ".join(items_html)

    # Operational Priorities Alert Row
    priority_badges = [
        f"<span style='color:#38BDF8;'><b>{active_cnt}</b> Active {config.labels.record_plural}</span>"
    ]
    if overdue_cnt > 0:
        priority_badges.append(f"<span style='color:#FB7185;'>⚠️ <b>{overdue_cnt}</b> Overdue</span>")
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
    return (overdue_cnt, today_cnt, replied_cnt, active_cnt)


def render_opportunity_workspace(config, storage, record, stages, prefix, reference=None):
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
        clean_brief_html = html.escape(str(brief))
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.45); border-left: 3px solid #6366F1; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px;">
                <div style="font-size: 0.70rem; font-weight: 700; color: #818CF8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;">Opportunity Brief</div>
                <div style="font-size: 0.88rem; color: #F1F5F9; line-height: 1.45;">{clean_brief_html}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- SECTION C: SCHEDULED NEXT ACTION LIFECYCLE ---
    today = reference.date if reference else datetime.date.today()
    active_stage_ids = {s.id for s in config.stages if s.active}

    act_desc, act_due_str = open_next_action(record)
    has_open_action = bool(act_desc or act_due_str)
    latest = record.latest_action
    act_status = 'open' if has_open_action else (latest.status if latest else 'none')
    if not has_open_action and latest:
        act_desc = latest.description

    is_overdue = False
    is_today = False
    formatted_due = "No due date"
    state, days_diff = due_state(act_due_str, today)
    if state and has_open_action:
        d_fmt = datetime.date.fromisoformat(str(act_due_str)[:10]).strftime("%b %d, %Y")
        is_active = record.stage_id in active_stage_ids
        if state == 'overdue' and is_active:
            is_overdue = True
            formatted_due = f"<span style='color:#FB7185; font-weight:700;'>⚠️ Due {d_fmt} ({abs(days_diff)}d overdue)</span>"
        elif state == 'today' and is_active:
            is_today = True
            formatted_due = f"<span style='color:#FBBF24; font-weight:700;'>📅 Due Today ({d_fmt})</span>"
        elif state == 'tomorrow' and is_active:
            formatted_due = f"<span style='color:#38BDF8; font-weight:600;'>📅 Due Tomorrow ({d_fmt})</span>"
        else:
            formatted_due = f"<span style='color:#CBD5E1;'>📅 Due {d_fmt}</span>"
    elif act_status == 'completed':
        formatted_due = "<span style='color:#34D399; font-weight:600;'>✓ Completed</span>"

    box_bg = "rgba(239, 68, 68, 0.08)" if is_overdue else ("rgba(245, 158, 11, 0.08)" if is_today else "rgba(99, 102, 241, 0.07)")
    box_border = "rgba(239, 68, 68, 0.35)" if is_overdue else ("rgba(245, 158, 11, 0.35)" if is_today else "rgba(99, 102, 241, 0.30)")
    accent_color = "#FB7185" if is_overdue else ("#FBBF24" if is_today else "#818CF8")

    status_pill = (
        "<span style='background:#064E3B44; color:#34D399; border:1px solid #05966966; padding:1px 6px; border-radius:3px; font-weight:600; font-size:0.72rem;'>OPEN</span>"
        if has_open_action else
        ("<span style='background:#1E293B; color:#94A3B8; border:1px solid #334155; padding:1px 6px; border-radius:3px; font-weight:600; font-size:0.72rem;'>COMPLETED</span>"
         if act_status == 'completed' else
         "<span style='background:#1E293B; color:#64748B; border:1px solid #334155; padding:1px 6px; border-radius:3px; font-weight:500; font-size:0.72rem;'>NONE</span>")
    )

    action_box_html = f"""
    <div style="background: {box_bg}; border: 1px solid {box_border}; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div style="flex: 1; min-width: 250px;">
            <div style="font-size: 0.70rem; font-weight: 700; color: {accent_color}; text-transform: uppercase; letter-spacing: 0.5px;">Scheduled Next Action</div>
            <div style="font-size: 0.92rem; font-weight: 600; color: #F8FAFC; margin-top: 2px;">🎯 {html.escape(str(act_desc or ('Action completed' if act_status == 'completed' else 'No outstanding action')))}</div>
        </div>
        <div style="font-size: 0.80rem; text-align: right; flex-shrink: 0;">
            <div>{formatted_due}</div>
            <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 2px;">Status: {status_pill}</div>
        </div>
    </div>
    """
    st.markdown(action_box_html, unsafe_allow_html=True)

    # Action Lifecycle Controls
    if has_open_action:
        tab_comp, tab_resched, tab_new = st.tabs(["✓ Complete Action", "📅 Reschedule", "🎯 Replace / Schedule Next"])
        with tab_comp:
            with st.form(f"{prefix}_complete_form_{record.id}"):
                st.caption(f"Mark **{html.escape(str(act_desc))}** as completed. You may optionally specify the next action.")
                col_c1, col_c2 = st.columns([7, 3])
                with col_c1:
                    new_act_desc = st.text_input("Following Action (optional)", placeholder="e.g. Schedule discovery demo with revenue leadership...", key=f"{prefix}_na_desc_{record.id}")
                with col_c2:
                    new_act_due = st.date_input("Due Date", value=today + datetime.timedelta(days=3), key=f"{prefix}_na_due_{record.id}")
                comp_note = st.text_input("Completion Note (optional)", placeholder="e.g. Call completed, prospect requested technical overview...", key=f"{prefix}_comp_note_{record.id}")
                col_btn, _ = st.columns([3, 7])
                with col_btn:
                    complete_submit = st.form_submit_button("✓ Complete Action", width='stretch')
                if complete_submit:
                    try:
                        storage.complete_action(
                            record.id,
                            note=comp_note,
                            new_next_action=new_act_desc if new_act_desc.strip() else None,
                            new_next_action_date=new_act_due if new_act_desc.strip() else None
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.session_state['_demo_flash'] = 'Action completed.'
                        st.rerun()

        with tab_resched:
            with st.form(f"{prefix}_resched_form_{record.id}"):
                default_resched = today + datetime.timedelta(days=2)
                if act_due_str:
                    try:
                        parsed_curr = datetime.date.fromisoformat(str(act_due_str)[:10])
                        if parsed_curr < today:
                            default_resched = today + datetime.timedelta(days=1)
                    except Exception:
                        pass
                col_r1, col_r2 = st.columns([3, 7])
                with col_r1:
                    resched_due = st.date_input("New Due Date", value=default_resched, key=f"{prefix}_resched_due_{record.id}")
                with col_r2:
                    resched_reason = st.text_input("Reason (optional)", placeholder="e.g. Contact requested follow-up next week...", key=f"{prefix}_resched_reason_{record.id}")
                col_btn, _ = st.columns([3, 7])
                with col_btn:
                    resched_submit = st.form_submit_button("📅 Reschedule Action", width='stretch')
                if resched_submit:
                    try:
                        storage.reschedule_action(record.id, resched_due, reason=resched_reason)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.session_state['_demo_flash'] = 'Action rescheduled.'
                        st.rerun()

        with tab_new:
            with st.form(f"{prefix}_replace_form_{record.id}"):
                col_n1, col_n2 = st.columns([7, 3])
                with col_n1:
                    sched_desc = st.text_input("New Action Description *", placeholder="e.g. Follow up on renewal proposal...", key=f"{prefix}_sched_desc_{record.id}")
                with col_n2:
                    sched_due = st.date_input("Due Date", value=today + datetime.timedelta(days=3), key=f"{prefix}_sched_due_{record.id}")
                col_btn, _ = st.columns([3, 7])
                with col_btn:
                    sched_submit = st.form_submit_button("🎯 Save Action", width='stretch')
                if sched_submit and sched_desc.strip():
                    try:
                        storage.schedule_action(record.id, sched_desc.strip(), sched_due)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.session_state['_demo_flash'] = 'New action scheduled.'
                        st.rerun()
    else:
        with st.expander("🎯 Schedule Next Action", expanded=True):
            with st.form(f"{prefix}_new_action_form_{record.id}"):
                col_n1, col_n2 = st.columns([7, 3])
                with col_n1:
                    sched_desc = st.text_input("Action Description *", placeholder="e.g. Follow up on proposal...", key=f"{prefix}_sched_desc_{record.id}")
                with col_n2:
                    sched_due = st.date_input("Due Date", value=today + datetime.timedelta(days=3), key=f"{prefix}_sched_due_{record.id}")
                col_btn, _ = st.columns([3, 7])
                with col_btn:
                    sched_submit = st.form_submit_button("🎯 Schedule Action", width='stretch')
                if sched_submit and sched_desc.strip():
                    try:
                        storage.schedule_action(record.id, sched_desc.strip(), sched_due)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.session_state['_demo_flash'] = 'Next action scheduled.'
                        st.rerun()

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
        <div class="mo-profile-grid" style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 5px 12px; background: #0F172A; border: 1px solid #1E293B; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; font-size: 0.80rem;">
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
            col_st1, col_st2 = st.columns([3, 2])
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
                save_stage = st.form_submit_button(config.labels.save, width='stretch')
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
                complete_at_same_time = False
                if has_open_action:
                    complete_at_same_time = st.checkbox("✓ Complete scheduled action at the same time", value=False, key=f"{prefix}_chk_comp_{record.id}")
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
                    add = st.form_submit_button(config.labels.add_note, width='stretch')
                if add and text.strip():
                    try:
                        storage.add_activity(record.id, kind, text.strip(), complete_action=complete_at_same_time)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        if complete_at_same_time:
                            st.session_state['_demo_flash'] = 'Activity logged and scheduled action completed.'
                        st.rerun()

        # --- 3. Unified Reverse-Chronological Activity Timeline ---
        st.markdown("<div style='font-size:0.74rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-top:8px; margin-bottom:6px;'>Activity & Progression Timeline</div>", unsafe_allow_html=True)
        
        events = []
        for act in getattr(record, 'activities', []):
            is_comp = act.text and 'Completed action:' in act.text
            is_resched = act.text and 'Rescheduled action' in act.text
            is_sched = act.text and 'Scheduled next action' in act.text
            title = (
                'Action Completed' if is_comp else
                'Action Rescheduled' if is_resched else
                'Action Scheduled' if is_sched else
                act.kind.replace('_', ' ').title()
            )
            events.append({
                'time': act.occurred_at or '',
                'kind': act.kind,
                'title': title,
                'text': act.text,
                'is_stage': False,
                'is_comp': is_comp,
                'is_action': (is_comp or is_resched or is_sched)
            })
        for stg in getattr(record, 'stage_history', []):
            events.append({
                'time': stg.entered_at or '',
                'kind': 'stage_change',
                'title': f"Moved to {stages.get(stg.stage_id, stg.stage_id)}",
                'text': '',
                'is_stage': True,
                'is_comp': False,
                'is_action': False
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
                icon = '✅' if ev.get('is_comp') else ('📅' if ev.get('title') == 'Action Rescheduled' else ('🎯' if ev.get('title') == 'Action Scheduled' else kind_icons.get(ev['kind'], '•')))
                t_str = human_date(ev['time'][:10]) if ev['time'] else 'Initial'
                border_color = "#34D399" if ev.get('is_comp') else ("#6366F1" if ev['is_stage'] else "#334155")
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


def pipeline(config, storage, prefix, reference=None):
    records = storage.list_records()
    if 'metrics' in config.dashboard_modules:
        metric_cards(config, records)
    counts = pipeline_distribution_bar(config, records, reference=reference)
    overdue_cnt, today_cnt, replied_cnt, active_cnt = counts if counts else (0, 0, 0, 0)

    # Guided Demo Walkthrough (P2 - dismissible, lightweight)
    if not st.session_state.get('_demo_hide_walkthrough', False):
        col_wt_text, col_wt_btn = st.columns([11, 1])
        with col_wt_text:
            st.markdown(
                f"""
                <div style="background: linear-gradient(90deg, rgba(99, 102, 241, 0.12) 0%, rgba(30, 41, 59, 0.4) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 6px; padding: 8px 12px; margin-bottom: 10px;">
                    <div style="font-size: 0.72rem; font-weight: 700; color: #818CF8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;">
                        💡 Demo Workflow
                    </div>
                    <div style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.4;">
                        <strong style="color: #38BDF8;">Account Intelligence</strong> →
                        <strong style="color: #A5B4FC;">Recommended Actions</strong> →
                        <strong style="color: #FBBF24;">Activity Tracking</strong> →
                        <strong style="color: #34D399;">Pipeline Progression</strong> →
                        <strong style="color: #C084FC;">Historical Analytics</strong>.
                        Click any {html.escape(config.labels.record_singular.lower())} below to view intelligence, log notes, or change stage.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_wt_btn:
            if st.button("✕", key=prefix + "_dismiss_guide", help="Dismiss guide"):
                st.session_state['_demo_hide_walkthrough'] = True
                st.rerun()

    # Inline quick add
    with st.expander(f"+ {config.labels.create}", expanded=False):
        intake(config, storage, prefix + '_inline')

    stages = {s.id: s.name for s in config.stages}

    # Compact multi-column Search, Priority, Stage Filter & Page selector
    col_search, col_prio, col_filter, col_page = st.columns([5, 3, 3, 2])
    with col_search:
        search = st.text_input(
            f'Search {config.labels.record_plural.lower()}',
            placeholder=f'Search by company, contact, or keywords...',
            key=prefix + '_search'
        ).lower().strip()
    with col_prio:
        priority_options = ['all', 'due_today', 'overdue', 'awaiting_reply', 'active']
        prio_key = prefix + '_priority_filter'
        if st.session_state.get(prio_key) not in priority_options:
            st.session_state[prio_key] = 'all'
        priority_labels = {
            'all': 'All Priorities',
            'due_today': f'📅 Due Today ({today_cnt})',
            'overdue': f'⚠️ Overdue ({overdue_cnt})',
            'awaiting_reply': f'💬 Awaiting Follow-up ({replied_cnt})',
            'active': f'⚡ Active {config.labels.record_plural} ({active_cnt})'
        }
        priority_filter = st.selectbox(
            'Daily Priority',
            priority_options,
            format_func=lambda val: priority_labels.get(val, val),
            key=prio_key
        )
    with col_filter:
        valid_stages = ['all', *stages]
        filter_key = prefix + '_filter'
        if st.session_state.get(filter_key) not in valid_stages:
            st.session_state[filter_key] = 'all'
        stage_filter = st.selectbox(
            config.labels.stage,
            valid_stages,
            format_func=lambda value: 'All stages' if value == 'all' else stages[value],
            key=filter_key
        )

    ref_date = reference.date if reference else datetime.date.today()
    active_stage_ids = {s.id for s in config.stages if s.active}
    priority_ids = daily_priority_sets(config, records, reference).get(priority_filter)

    visible = [r for r in records if (priority_ids is None or r.id in priority_ids)
               and (stage_filter == 'all' or stage_filter == r.stage_id)
               and (not search or search in ' '.join(str(v) for v in r.fields.values()).lower())]

    page_size = 10
    total_count = len(visible)
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    page_key = prefix + '_page'
    saved_page_key = f"_saved_page_{prefix}"
    if page_key not in st.session_state and saved_page_key in st.session_state:
        st.session_state[page_key] = st.session_state[saved_page_key]

    raw_page = st.session_state.get(page_key, 1)
    try:
        current_page = int(raw_page)
    except (ValueError, TypeError):
        current_page = 1
        st.session_state[page_key] = 1

    if current_page > total_pages or current_page < 1:
        current_page = 1
        st.session_state[page_key] = 1

    page_options = list(range(1, total_pages + 1))
    if st.session_state.get(page_key) not in page_options:
        st.session_state[page_key] = 1

    with col_page:
        page = st.selectbox(
            'Page',
            page_options,
            format_func=str,
            key=page_key
        )
    st.session_state[saved_page_key] = page

    # Accurate range display: e.g. "Showing 1–10 of 40 prospects · Page 1 of 4"
    if total_count == 0:
        range_str = f"Showing 0 of {len(records)} {config.labels.record_plural.lower()}"
    else:
        start_idx = (page - 1) * page_size + 1
        end_idx = min(page * page_size, total_count)
        if total_count < len(records):
            range_str = f"Showing <b>{start_idx}–{end_idx}</b> of {total_count} (out of {len(records)} total) &nbsp;·&nbsp; Page {page} of {total_pages}"
        else:
            range_str = f"Showing <b>{start_idx}–{end_idx}</b> of {len(records)} {config.labels.record_plural.lower()} &nbsp;·&nbsp; Page {page} of {total_pages}"

    st.markdown(
        f"<div style='font-size: 0.82rem; color: #94A3B8; margin-top: -6px; margin-bottom: 8px;'>"
        f"{range_str}"
        f"</div>",
        unsafe_allow_html=True
    )

    if not visible:
        st.info(f'No {config.labels.record_plural.lower()} match. Add a record or change the filters.')
        return

    if 'table' in config.dashboard_modules:
        with st.expander('Table'):
            record_table(config, visible)

    for record in visible[(page - 1) * page_size:page * page_size]:
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
        priority = record.fields.get('priority', '')
        phone = record.fields.get('phone', '')

        # Row 1: Company, contact, stage
        r1_parts = [f":blue[**{escape_markdown(company)}**]"]
        if contact:
            r1_parts.append(f"{escape_markdown(contact)}" + (f" ({escape_markdown(title)})" if title else ""))
        if phone:
            r1_parts.append(f"`{phone}`")
        r1_parts.append(f"`{stage_name}`")
        row1 = " — ".join(r1_parts[:2])
        if len(r1_parts) > 2:
            row1 += " · " + " · ".join(r1_parts[2:])

        # Row 2: Account summary
        clean_brief = brief.strip() if brief else "No account brief provided."
        if len(clean_brief) > 130:
            clean_brief = clean_brief[:127] + "..."
        row2 = escape_markdown(clean_brief)

        # Row 3: Fit, intent signals, technology
        badges = []
        if icp_fit:
            badges.append(f"🎯 {escape_markdown(icp_fit)} Fit")
        if intent:
            top_intent = intent.split('·')[0].strip()
            badges.append(f"⚡ {escape_markdown(top_intent)}")
        if tech_stack:
            top_tech = tech_stack.split('·')[0].strip()
            badges.append(f"🛠️ {escape_markdown(top_tech)}")
        row3 = " · ".join(badges) if badges else "🎯 Account Intelligence Ready"

        # Row 4: Next action, due date, ACV
        footer_items = []
        act_d, act_due = open_next_action(record)
        latest = record.latest_action

        if act_d:
            short_na = act_d if len(act_d) <= 44 else act_d[:41] + "..."
            footer_items.append(f"**Next:** {escape_markdown(short_na)}")
        elif latest and latest.status == 'completed':
            footer_items.append("✅ **Next:** Completed")
        else:
            footer_items.append("— No next action scheduled")

        state, diff = due_state(act_due, ref_date)
        if state:
            d_label = datetime.date.fromisoformat(str(act_due)[:10]).strftime('%b %d')
            is_active = record.stage_id in active_stage_ids
            if state == 'overdue' and is_active:
                footer_items.append(f":red[⚠️ Due {d_label} ({abs(diff)}d overdue)]")
            elif state == 'today' and is_active:
                footer_items.append(":orange[📅 Due Today]")
            elif state == 'tomorrow' and is_active:
                footer_items.append(f"📅 Due Tomorrow ({d_label})")
            else:
                footer_items.append(f"📅 Due {d_label}")

        if acv is not None:
            try:
                footer_items.append(f":green[\\${float(acv):,.0f} {value_suffix(config)}]")
            except Exception:
                footer_items.append(f":green[{escape_markdown(str(acv))}]")

        row4 = " · ".join(footer_items)

        card_header = f"{row1}\n\n{row2}\n\n{row3}\n\n{row4}"

        with st.expander(card_header, expanded=st.session_state.get(f'{prefix}_focus') == record.id):
            is_editing = st.session_state.get(f'{prefix}_editing_{record.id}', False)

            # Top Header Bar with Edit Action (Section 2.A)
            contact_info = f"{contact}" + (f", {title}" if title else "") if contact else ""
            st_style = STAGE_STYLES.get(record.stage_id, {'bg': '#1E293B', 'fg': '#CBD5E1', 'border': '#334155'})
            pills = [
                f"<span style='background:{st_style['bg']}; color:{st_style['fg']}; border:1px solid {st_style['border']}; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700;'>{stage_name}</span>"
            ]
            if acv is not None:
                try:
                    pills.append(f"<span style='background:#064E3B33; color:#34D399; border:1px solid #05966955; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700;'>${float(acv):,.0f} {value_suffix(config)}</span>")
                except Exception:
                    pass
            if icp_fit:
                icp_color = '#38BDF8' if icp_fit == 'High' else '#FBBF24'
                pills.append(f"<span style='background:#0F172A; color:{icp_color}; border:1px solid #334155; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600;'>🎯 {icp_fit} Fit</span>")
            if priority:
                pills.append(f"<span style='background:#0F172A; color:#E2E8F0; border:1px solid #334155; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:500;'>⚡ {priority} Priority</span>")

            pills_str = " ".join(pills)

            col_bar1, col_actions, col_bar2 = st.columns([5, 3, 1.4], vertical_alignment='center')
            with col_bar1:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px; margin-bottom: 6px;">
                        <span style="font-size: 1.15rem; font-weight: 700; color: #818CF8;">{company}</span>
                        <span style="font-size: 0.83rem; color: #94A3B8;">{contact_info}</span>
                        <div class="mo-pills" style="display: inline-flex; flex-wrap: wrap; align-items: center; gap: 5px; margin-left: 4px;">{pills_str}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_actions:
                contact_action_buttons(storage, record, prefix)
            with col_bar2:
                if st.button("✏️ Edit" if not is_editing else "✖️ View", key=f"{prefix}_btn_toggle_{record.id}", width='stretch'):
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
                        save = st.form_submit_button(config.labels.save, width='stretch')
                    with col_cancel:
                        cancel = st.form_submit_button("Cancel", width='stretch')
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
                render_opportunity_workspace(config, storage, record, stages, prefix, reference=reference)


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
        with st.expander(f"📘 {item.title}", expanded=False):
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


def format_metric_currency(val):
    if val is None:
        return '—'
    abs_val = abs(val)
    sign = '-' if val < 0 else ''
    if abs_val >= 1_000_000_000:
        formatted = f"{abs_val / 1_000_000_000:.2f}".rstrip('0').rstrip('.')
        return f"{sign}${formatted}B"
    if abs_val >= 1_000_000:
        formatted = f"{abs_val / 1_000_000:.2f}".rstrip('0').rstrip('.')
        return f"{sign}${formatted}M"
    return f"{sign}${abs_val:,.0f}"


def metric_cards(config, records):
    metrics = calculate_metrics(records, config)
    if not metrics:
        return
    col_count = len(metrics) if len(metrics) <= 6 else 6
    columns = st.columns(col_count)
    custom_labels = getattr(getattr(config, 'labels', None), 'metric_labels', {}) or {}
    for index, (key, metric) in enumerate(metrics.items()):
        value = metric['value']
        display = '—' if value is None else (f'{value:.1f}%' if metric['format'] == 'percent' else
                                           format_metric_currency(value) if metric['format'] == 'currency' else str(value))
        label = custom_labels.get(key, config.labels.record_plural if key == 'total' else metric['label'])
        columns[index % col_count].metric(label, display)


def render_public(config):
    import os
    workspace_options = {
        'sales_rep': 'Sales Rep · Outbound',
        'b2b_services': 'B2B Services · Client Deals',
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

    if '_demo_reference' not in st.session_state:
        tz_name = None
        tz_offset = None
        ctx = getattr(st, 'context', None)
        if ctx is not None:
            tz_name = getattr(ctx, 'timezone', None)
            tz_offset = getattr(ctx, 'timezone_offset', None)
        st.session_state['_demo_reference'] = session_reference(tz_name=tz_name, offset_minutes=tz_offset)
    reference = st.session_state['_demo_reference']

    try:
        storage = session_storage(config, active_ws, reference=reference)
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
            <strong style="color: #F8FAFC;">Demo Sandbox · Synthetic Data</strong><br>
            All companies, contacts and figures are fictitious. Calls and emails are simulated; nothing is sent.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Sidebar Navigation
    st.sidebar.markdown("<div style='font-size:0.72rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;'>Navigation</div>", unsafe_allow_html=True)
    nav = {n.id: n.label for n in config.navigation}
    destination = st.sidebar.radio('Navigate', list(nav), format_func=nav.get, key='public_navigation', label_visibility='collapsed')

    # Widget keys are scoped per workspace so filters, pages and open forms never leak across workspaces.
    prefix = f"public_{st.session_state.get('_demo_epoch', 0)}_{active_ws}"
    render_sidebar_widgets(config, storage, reference, prefix)
    st.sidebar.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
    st.sidebar.caption(f"**{config.display_name}** · Public Demo  \nAll demo data is synthetic.")

    if '_demo_flash' in st.session_state:
        st.success(st.session_state.pop('_demo_flash'))

    if destination == 'intake':
        intake(config, storage, prefix + '_intake')
    elif destination == 'pipeline':
        pipeline(config, storage, prefix, reference=reference)
    elif destination == 'intelligence':
        intelligence(config)
    else:
        analytics(config, storage, nav[destination], reference=reference)

    st.markdown(f"<div style='margin-top:28px; padding-top:10px; border-top:1px solid #1E293B; font-size:0.75rem; "
                f"color:#64748B; text-align:center;'>🧪 {SYNTHETIC_NOTE} No calls, emails or messages are sent.</div>",
                unsafe_allow_html=True)


def stage_breakdown_html(config, rows):
    """Current count and value per stage; closed stages are dimmed.

    Lost/disqualified value is not pipeline, so closed stages show counts only and
    bars scale to open and won stages.
    """
    max_value = max((r['Value'] for r in rows if not r['Closed']), default=0) or 1
    has_values = any(r['Value'] for r in rows if not r['Closed'])
    lines = []
    divider_done = False
    for r in rows:
        style = STAGE_STYLES.get(r['stage_id'], {'fg': '#94A3B8'})
        opacity = '1' if r['Active'] else '0.55'
        if not r['Active'] and not divider_done:
            divider_done = True
            lines.append("<div style='font-size:0.66rem; font-weight:700; color:#64748B; text-transform:uppercase; "
                         "letter-spacing:0.5px; border-top:1px solid #1E293B; padding-top:6px; margin:8px 0 6px;'>"
                         "Closed / converted · not in active pipeline</div>")
        shown = 0 if r['Closed'] else r['Value']
        width = shown / max_value * 100 if shown else 0
        value_str = format_metric_currency(shown) if shown else '—'
        bar = (f"<div style='flex:1; min-width:60px; background:#1E293B; height:8px; border-radius:4px; overflow:hidden;'>"
               f"<div style='background:{style['fg']}; width:{width:.1f}%; height:100%;'></div></div>"
               f"<div style='width:68px; text-align:right; color:#34D399; font-weight:600;'>{value_str}</div>") if has_values else ""
        lines.append(
            f"<div style='display:flex; align-items:center; gap:10px; margin-bottom:7px; font-size:0.81rem; opacity:{opacity};'>"
            f"<div style='width:170px; flex-shrink:0; color:#E2E8F0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>"
            f"<span style='display:inline-block; width:8px; height:8px; border-radius:50%; background:{style['fg']}; margin-right:6px;'></span>"
            f"{html.escape(r['Stage'])}</div>"
            f"<div style='width:28px; text-align:right; color:#F8FAFC; font-weight:700;'>{r['Count']}</div>"
            f"{bar}</div>"
        )
    return (f"<div class='mo-panel'><div class='mo-label'>Current {html.escape(config.labels.record_plural)} by Stage</div>"
            + "".join(lines) + "</div>")


def top_open_html(config, records, reference=None, limit=5):
    """Largest active records by value, with their next action and due date."""
    active = {s.id for s in config.stages if s.active and not s.terminal}
    stages = {s.id: s.name for s in config.stages}
    today = reference.date if reference else datetime.date.today()

    def value(r):
        v = r.fields.get('acv')
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0

    top = sorted((r for r in records if r.stage_id in active and value(r)), key=value, reverse=True)[:limit]
    due_styles = {'overdue': '#FB7185', 'today': '#FBBF24'}
    lines = []
    for r in top:
        desc, due = open_next_action(r)
        state, diff = due_state(due, today)
        due_html = ''
        if state:
            text = f"{abs(diff)}d overdue" if state == 'overdue' else ('Due today' if state == 'today' else f"Due in {diff}d")
            due_html = f"<span style='color:{due_styles.get(state, '#94A3B8')}; font-weight:600;'>{text}</span>"
        style = STAGE_STYLES.get(r.stage_id, {'fg': '#94A3B8'})
        lines.append(
            "<div style='padding:7px 0; border-bottom:1px solid #1E293B; font-size:0.81rem;'>"
            "<div style='display:flex; justify-content:space-between; gap:8px;'>"
            f"<span style='color:#818CF8; font-weight:700;'>{html.escape(str(r.fields.get('company') or r.fields.get('contact') or '—'))}</span>"
            f"<span style='color:#34D399; font-weight:700;'>{format_metric_currency(value(r))}</span></div>"
            "<div style='display:flex; justify-content:space-between; gap:8px; color:#94A3B8; font-size:0.76rem; margin-top:2px;'>"
            f"<span><span style='color:{style['fg']};'>{html.escape(stages.get(r.stage_id, r.stage_id))}</span>"
            f"{' · ' + html.escape(desc[:60] + ('…' if len(desc) > 60 else '')) if desc else ''}</span>"
            f"<span style='white-space:nowrap;'>{due_html}</span></div></div>"
        )
    body = "".join(lines) or "<div style='color:#64748B; font-size:0.81rem;'>No open records with a value yet.</div>"
    return (f"<div class='mo-panel'><div class='mo-label'>Largest Open {html.escape(config.labels.record_plural)}</div>"
            + body + "</div>")


# Trend views per workspace: which period metrics to show and what to call them.
TREND_VIEWS = {
    'b2b_services': {
        'new_label': 'New Inquiries', 'value_label': 'Value Won',
        'tiles': ['new', 'replied', 'meeting', 'opportunity', 'won_value', 'win_rate'],
        'chart': ['new', 'replied', 'opportunity'],
    },
    'default': {
        'new_label': 'New Prospects', 'value_label': 'Opportunity Value',
        'tiles': ['new', 'contacted', 'replied', 'meeting', 'opportunity', 'reply_rate', 'meeting_booking_rate'],
        'chart': ['new', 'contacted', 'replied'],
    },
}
# Categorical series colors, fixed order; validated for CVD separation on the #0F172A surface.
TREND_COLORS = ['#3987e5', '#d95926', '#199e70']
PERIOD_DAYS = 30


def trend_view(config):
    return TREND_VIEWS.get(config.pipeline_type, TREND_VIEWS['default'])


def trend_labels(config):
    view = trend_view(config)
    custom = config.labels.metric_labels or {}
    labels = {'new': view['new_label'], 'won_value': view['value_label'], **milestone_labels(config)}
    for key in ('reply_rate', 'meeting_booking_rate', 'reply_to_meeting_rate', 'win_rate'):
        labels[key] = custom.get(key, METRIC_REGISTRY[key][0])
    return labels


def format_trend_value(key, value):
    if value is None:
        return '—'
    if key == 'won_value':
        return format_metric_currency(value)
    if key.endswith('_rate'):
        return f'{value:.1f}%'
    return f'{value:,}'


def delta_html(key, current, prior, show_prior=True):
    """Change vs the prior period: percent for counts, points for rates."""
    if current is None or prior is None:
        return "<span class='mo-delta mo-delta-flat'>—</span>"
    if key.endswith('_rate'):
        diff = current - prior
        text = f'{abs(diff):.1f} pts'
    elif prior == 0:
        diff = current
        text = 'new' if current else 'no change'
    elif prior < 5 and key != 'won_value':
        # Percentages on tiny bases read as noise ("+500%"); show the absolute change.
        diff = current - prior
        text = f'{abs(diff):,}'
    else:
        diff = current - prior
        text = f'{abs(diff) / prior * 100:.0f}%'
    if abs(diff) < 0.05:
        cls, arrow, text = 'flat', '→', 'no change'
    else:
        cls, arrow = ('up', '▲') if diff > 0 else ('down', '▼')
    prior_html = (f"<div class='mo-delta mo-delta-prior'>prior 30d: {format_trend_value(key, prior)}</div>"
                  if show_prior else '')
    return f"<span class='mo-delta mo-delta-{cls}'>{arrow} {text}</span>{prior_html}"


def trend_tiles_html(config, periods):
    current, prior = periods[0], periods[1]
    labels = trend_labels(config)
    tiles = []
    for key in trend_view(config)['tiles']:
        tiles.append(
            "<div class='mo-tile'>"
            f"<div class='mo-tile-label'>{html.escape(labels[key])}</div>"
            f"<div class='mo-tile-value'>{format_trend_value(key, current[key])}</div>"
            f"{delta_html(key, current[key], prior[key])}"
            "</div>"
        )
    return "<div class='mo-tiles'>" + "".join(tiles) + "</div>"


def period_label(period):
    start, end = period['start'], period['end']
    return f"{start.strftime('%b')} {start.day} – {end.strftime('%b')} {end.day}"


def period_table_html(config, periods):
    """Trailing 30-day periods, newest first, each compared with the one before it."""
    labels = trend_labels(config)
    keys = trend_view(config)['tiles']
    head = "<tr><th>Period</th>" + "".join(f"<th>{html.escape(labels[k])}</th>" for k in keys) + "</tr>"
    rows = []
    for i, period in enumerate(periods):
        older = periods[i + 1] if i + 1 < len(periods) else None
        name = 'Last 30 days' if i == 0 else f'{i * PERIOD_DAYS + 1}–{(i + 1) * PERIOD_DAYS} days ago'
        cells = [f"<td><b>{name}</b><span class='mo-delta mo-delta-prior' style='display:block;'>"
                 f"{period_label(period)}</span></td>"]
        for k in keys:
            delta = delta_html(k, period[k], older[k], show_prior=False) if older else ''
            cells.append(f"<td>{format_trend_value(k, period[k])}{delta}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return ("<div class='mo-panel' style='margin-bottom:14px;'>"
            "<div class='mo-label'>Month over Month · Trailing 30-Day Periods</div>"
            f"<div class='mo-table-wrap'><table class='mo-table'>{head}{''.join(rows)}</table></div></div>")


ROLLING_WEEKS = 4


def weekly_trend_chart(config, weeks):
    """Rolling four-week totals: weekly counts for one person are too small to read raw."""
    import altair as alt
    labels = trend_labels(config)
    keys = trend_view(config)['chart']
    names = [labels[k] for k in keys]
    data = []
    for i in range(ROLLING_WEEKS - 1, len(weeks)):
        window = weeks[i - ROLLING_WEEKS + 1:i + 1]
        for k in keys:
            data.append({'Week': weeks[i]['end'].isoformat(), 'Series': labels[k],
                         'Count': sum(w[k] for w in window)})
    axis = dict(labelColor='#94A3B8', labelFontSize=11, domainColor='#334155', tickColor='#334155')
    chart = (
        alt.Chart(alt.Data(values=data))
        .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=64, filled=True))
        .encode(
            x=alt.X('Week:T', title=None, axis=alt.Axis(format='%b %d', grid=False, tickCount=7, **axis)),
            y=alt.Y('Count:Q', title=None, axis=alt.Axis(gridColor='#1E293B', tickMinStep=1, **axis)),
            color=alt.Color('Series:N', sort=names, scale=alt.Scale(domain=names, range=TREND_COLORS[:len(keys)]),
                            legend=alt.Legend(orient='top', title=None, labelColor='#CBD5E1', labelFontSize=12,
                                              symbolType='circle')),
            tooltip=[alt.Tooltip('Week:T', title='4 weeks ending', format='%b %d'),
                     alt.Tooltip('Series:N', title='Metric'), alt.Tooltip('Count:Q', title='Total')],
        )
        .properties(height=240)
        .configure_view(strokeWidth=0)
        .configure(background='transparent')
    )
    st.markdown("<div class='mo-label' style='margin-top:4px;'>Trend · Rolling 4-Week Totals, Updated Weekly</div>",
                unsafe_allow_html=True)
    st.altair_chart(chart, width='stretch', theme=None)


def render_trends(config, records, reference=None):
    today = reference.date if reference else datetime.date.today()
    tz_ref = reference or session_reference()

    def to_date(value):
        return local_date(value, tz_ref)

    periods = trailing_periods(records, config, today, to_date, days=PERIOD_DAYS, count=3)
    st.subheader('Last 30 Days')
    st.caption('Compared with the prior 30 days. Each count is the first time a record reached that milestone.')
    st.markdown(trend_tiles_html(config, periods), unsafe_allow_html=True)
    weekly_trend_chart(config, weekly_series(records, config, today, to_date, weeks=13))
    st.markdown(period_table_html(config, periods), unsafe_allow_html=True)


def analytics(config, storage, heading, reference=None):
    st.subheader(heading)
    records = storage.list_records()
    if 'metrics' in config.dashboard_modules:
        metric_cards(config, records)
    render_trends(config, records, reference=reference)
    st.subheader('Current Pipeline')
    # One grid so both panels always render at the same height.
    st.markdown(
        "<div class='mo-grid-2'>"
        + stage_breakdown_html(config, stage_breakdown(records, config))
        + top_open_html(config, records, reference=reference)
        + "</div>",
        unsafe_allow_html=True
    )
    if 'funnel' in config.dashboard_modules:
        st.subheader('Historical Conversion Funnel')
        funnel_rows = conversion_funnel(records, config)
        render_visual_conversion_funnel(funnel_rows)
        with st.expander('Conversion Funnel Data Table', expanded=False):
            st.dataframe(funnel_rows, hide_index=True, width="stretch")
        st.caption('Each step counts unique records that achieved every preceding milestone. Later stage moves retain '
                   'earlier achievements, and closed records keep their history. A zero denominator displays —.')
    if 'table' in config.dashboard_modules:
        with st.expander(f'All {config.labels.record_plural}', expanded=False):
            record_table(config, records)

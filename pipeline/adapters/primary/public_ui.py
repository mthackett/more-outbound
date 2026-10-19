"""Configuration-driven public views. Imports no private workflow or provider."""
import hashlib
import json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from pipeline.adapters.primary.runtime import select_session
from pipeline.adapters.secondary.memory_records import MemoryRecordStorage
from pipeline.domain.records import format_field
from pipeline.domain.intelligence_service import IntelligenceService
from pipeline.domain.outreach_metrics import calculate_metrics, conversion_funnel

STAGE_STYLES = {
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
}

PUBLIC_THEME_CSS = """
<style>
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 2rem;
    }
    .demo-main-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 0.15rem;
        letter-spacing: -0.015em;
    }
    .demo-sub-title {
        font-size: 0.90rem;
        color: #94A3B8;
        margin-bottom: 0.85rem;
        line-height: 1.4;
    }
    /* Compact headline 6-metric KPI cards: centered labels and values */
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
    /* Compact two-line pipeline card styling */
    div[data-testid="stExpander"] details {
        border-radius: 8px;
        border: 1px solid #334155;
        background-color: #0B1120;
        margin-bottom: 6px;
        transition: border-color 0.15s ease;
    }
    div[data-testid="stExpander"] details:hover {
        border-color: #475569;
    }
    div[data-testid="stExpander"] details summary {
        padding: 8px 12px;
        cursor: pointer;
    }
    div[data-testid="stExpander"] details summary p {
        margin-top: 0px !important;
        margin-bottom: 2px !important;
        line-height: 1.32;
    }
    /* Form & Container styling */
    div[data-testid="stForm"] {
        border: 1px solid #334155;
        border-radius: 8px;
        background-color: #0F172A44;
        padding: 14px;
    }
    /* Subtle custom Reset button in sidebar */
    div.st-key-public_reset button {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        color: #E2E8F0 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-public_reset button:hover {
        background-color: #7F1D1D33 !important;
        border-color: #DC2626 !important;
        color: #FCA5A5 !important;
    }
</style>
"""


def render_outreach_resources_sidebar():
    sections = [
        {
            "category": "Target ICP Profiles",
            "items": [
                ("VP RevOps", "ICP Target: VP of Revenue Operations. Primary pain: disparate CRM data, siloed outbound tooling, manual pipeline hygiene. Value angle: automated pipeline intelligence and unified qualification."),
                ("Head of Sales", "ICP Target: Head of Sales / VP Sales. Primary pain: low SDR conversion, slow lead response times, missed targets. Value angle: multi-channel sequence cadence and verified account insights."),
                ("Dir Growth", "ICP Target: Director of Growth. Primary pain: scaling outbound pipeline without proportional rep headcount. Value angle: automated lead qualification rules and instant response workflows."),
                ("CRO", "ICP Target: Chief Revenue Officer. Primary pain: unpredictable forecast, pipeline leakage, unmonitored deal velocity. Value angle: executive pipeline visibility and conversion telemetry."),
            ]
        },
        {
            "category": "Campaign Playbooks",
            "items": [
                ("Executive Sequence", "Subject: Quick question regarding outbound infrastructure\\n\\nHi - Noticed your team expanding your sales footprint. Revenue teams often hit a bottleneck when qualification data stays scattered across sheets. We automated full-funnel intelligence so reps focus solely on high-fit accounts. Open to a brief 5-minute preview this week?"),
                ("Value Trigger", "Subject: Scaling pipeline velocity\\n\\nHi - Following up on recent market signals in your space. Our partners typically see booking rates improve by 30%+ in 14 days without modifying their existing CRM stack. Would you be open to seeing the benchmark playbook?"),
                ("Tech Stack Audit", "Subject: Quick audit on outbound tech stack\\n\\nHi - We completed a synthetic benchmark on outreach conversion across B2B platforms. Would you like a 1-page summary of findings for your team?"),
                ("Breakup Touchpoint", "Subject: Closing the loop\\n\\nHi - Haven't heard back, so I assume pipeline automation isn't top of mind right now. I'll pause outreach for now. If anything changes down the line, feel free to reach back out anytime."),
            ]
        },
        {
            "category": "Objection Scripts",
            "items": [
                ("Timing / Budget", "Talk track: Understood on the budget pause. Our architecture requires zero upfront commitments and runs alongside your existing CRM in an isolated sandbox. Let's run a 14-day zero-risk trial to prove ROI before budget cycles open."),
                ("Already Have Tool", "Talk track: Completely expected. Most teams we work with already use HubSpot, Salesforce, or Apollo. We sit on top of your existing CRM to score opportunities before reps spend time on low-fit prospects."),
                ("Send by Email", "Talk track: Happy to! To make sure I share what's most relevant to your team, are you primarily looking to improve response rates or automate lead qualification?"),
                ("Not a Priority", "Talk track: Understood. What is the single biggest initiative your revenue team is tackling this quarter? Let's stay in touch when pipeline expansion moves up the queue."),
            ]
        }
    ]

    html_sections = ""
    total_rows = 0
    for sec in sections:
        cat_name = sec["category"]
        links = sec["items"]
        total_rows += (len(links) + 1) // 2
        html_sections += f'<div class="res-category-title">{cat_name}</div><div class="res-grid">'
        for label, snippet in links:
            safe_text = json.dumps(snippet)
            html_sections += f'<button type="button" class="res-btn" title="Click to copy playbook reference" onclick=\'copyText({safe_text}, this, event)\'>{label}</button>'
        html_sections += '</div>'

    doc_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            padding: 2px 2px 6px 2px;
            background: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #F8FAFC;
            overflow-x: hidden;
        }}
        .res-category-title {{
            font-size: 0.70rem;
            font-weight: 700;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 8px 0 4px 0;
            padding-bottom: 2px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.15);
        }}
        .res-category-title:first-child {{
            margin-top: 1px;
        }}
        .res-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 4px;
            margin-bottom: 6px;
        }}
        .res-btn {{
            background: #1E293B;
            color: #E2E8F0;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 5px 6px;
            font-size: 0.76rem;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: all 0.15s ease;
            user-select: none;
            width: 100%;
            box-sizing: border-box;
        }}
        .res-btn:hover {{
            background: #334155;
            color: #FFFFFF;
            border-color: #6366F1;
        }}
        .res-btn:active {{
            transform: scale(0.97);
        }}
    </style>
    </head>
    <body>
        {html_sections}
        <script>
        function copyText(text, btn, e) {{
            if (e) {{
                e.preventDefault();
                e.stopPropagation();
            }}
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(text).then(() => onSuccess(btn)).catch(() => fallback(text, btn));
            }} else {{
                fallback(text, btn);
            }}
        }}
        function fallback(text, btn) {{
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.focus();
            ta.select();
            try {{
                document.execCommand('copy');
                onSuccess(btn);
            }} catch(e) {{
                console.error(e);
            }}
            document.body.removeChild(ta);
        }}
        function onSuccess(btn) {{
            var orig = btn.innerText;
            btn.innerText = 'Copied';
            btn.style.background = '#065F46';
            btn.style.borderColor = '#10B981';
            btn.style.color = '#A7F3D0';
            setTimeout(() => {{
                btn.innerText = orig;
                btn.style.background = '#1E293B';
                btn.style.borderColor = '#334155';
                btn.style.color = '#E2E8F0';
            }}, 1200);
        }}
        </script>
    </body>
    </html>
    """
    iframe_height = max(50, len(sections) * 26 + total_rows * 32 + 16)
    if hasattr(st, "html"):
        st.html(doc_html, unsafe_allow_javascript=True)
    else:
        components.html(doc_html, height=iframe_height, scrolling=False)


def session_storage(config):
    identity = 'demo:' + hashlib.sha256(config.model_dump_json().encode()).hexdigest()
    select_session(st.session_state, identity)
    if '_demo_store' not in st.session_state:
        seed = []
        if config.seed == 'b2b_prospects':
            seed = json.loads((Path(__file__).resolve().parents[2] / 'examples/fixtures/demo_prospects.json').read_text(encoding='utf-8'))
        st.session_state['_demo_store'] = MemoryRecordStorage(config, seed)
    return st.session_state['_demo_store']


def input_fields(config, prefix, values=None, intake=False):
    values = values or {}
    result = {}
    for field in config.fields:
        if not field.visible or (intake and not field.intake):
            continue
        if not field.editable:
            st.text(f'{field.label}: {format_field(field, values.get(field.key))}')
            continue
        label = field.label + (' *' if field.required else '')
        key = prefix + '_' + field.key
        value = values.get(field.key)
        if field.type == 'currency':
            result[field.key] = st.number_input(label, min_value=0.0, value=float(value) if value is not None else None, key=key)
        elif field.type == 'date':
            value = st.date_input(label, value=value or None, key=key)
            result[field.key] = value.isoformat() if value else None
        elif field.type == 'long_text':
            result[field.key] = st.text_area(label, value=value or '', max_chars=field.max_length, key=key)
        else:
            result[field.key] = st.text_input(label, value=value or '', max_chars=field.max_length, key=key)
    return result


def intake(config, storage, prefix):
    st.subheader(config.labels.create)
    st.caption('Fields marked * are required. Use fictional information for this public demo.')
    with st.form(prefix + '_form', clear_on_submit=True):
        values = input_fields(config, prefix, intake=True)
        submitted = st.form_submit_button(config.labels.create)
    if submitted:
        try:
            storage.create(values)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state['_demo_flash'] = f'{config.labels.record_singular} added.'
            st.rerun()


def record_table(config, records):
    stages = {s.id: s.name for s in config.stages}
    rows = [{**{f.label: format_field(f, r.fields.get(f.key)) for f in config.fields if f.visible and f.table},
             config.labels.stage: stages[r.stage_id]} for r in records]
    st.dataframe(rows, hide_index=True, width="stretch")


def pipeline_distribution_bar(config, records):
    stage_counts = {s.id: 0 for s in config.stages}
    for r in records:
        if r.stage_id in stage_counts:
            stage_counts[r.stage_id] += 1

    items_html = []
    for s in config.stages:
        cnt = stage_counts.get(s.id, 0)
        style = STAGE_STYLES.get(s.id, {'fg': '#94A3B8'})
        items_html.append(f"<span style='color: #94A3B8;'>{s.name}:</span> <b style='color: {style['fg']};'>{cnt}</b>")

    breakdown_str = " &nbsp;·&nbsp; ".join(items_html)
    active_cnt = sum(stage_counts[s.id] for s in config.stages if s.active)
    total_cnt = len(records)

    st.markdown(
        f"<div style='margin-top: 4px; margin-bottom: 12px; font-size: 0.82rem; color: #94A3B8; background: #0F172A; padding: 7px 14px; border-radius: 6px; border: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;'>"
        f"<div><span style='color: #F8FAFC; font-weight: 600;'>Pipeline Distribution:</span> &nbsp; {breakdown_str}</div>"
        f"<div style='color: #64748B; font-size: 0.78rem;'>Active: {active_cnt} of {total_cnt}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


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

        # Line 1: Company — Contact (Title)
        if company and contact:
            line1 = f"**{company}** — {contact}" + (f" ({title})" if title else "")
        elif company:
            line1 = f"**{company}**" + (f" — {title}" if title else "")
        elif contact:
            line1 = f"**{contact}**" + (f" ({title})" if title else "")
        else:
            line1 = f"**{config.labels.record_singular} #{record.id}**"

        # Line 2: Stage pill · Industry · Source · ACV
        line2_items = [f"`{stage_name}`"]
        if industry:
            line2_items.append(f"`{industry}`")
        if source:
            line2_items.append(f"`{source}`")
        if acv is not None:
            try:
                acv_val = float(acv)
                line2_items.append(f":green[${acv_val:,.0f} ACV]")
            except (ValueError, TypeError):
                line2_items.append(f":green[{acv}]")

        line2_str = " · ".join(line2_items)
        card_header = f"{line1}\n\n{line2_str}"

        with st.expander(card_header):
            st_style = STAGE_STYLES.get(record.stage_id, {'bg': '#1E293B', 'fg': '#CBD5E1', 'border': '#334155'})
            pills_html = [
                f"<span style='background:{st_style['bg']}; color:{st_style['fg']}; border:1px solid {st_style['border']}; padding:3px 10px; border-radius:9999px; font-size:0.78rem; font-weight:600;'>{stage_name}</span>"
            ]
            if industry:
                pills_html.append(f"<span style='background:#0F172A; color:#94A3B8; border:1px solid #334155; padding:3px 10px; border-radius:9999px; font-size:0.78rem; font-weight:500;'>{industry}</span>")
            if source:
                pills_html.append(f"<span style='background:#0F172A; color:#94A3B8; border:1px solid #334155; padding:3px 10px; border-radius:9999px; font-size:0.78rem; font-weight:500;'>{source}</span>")
            if acv is not None:
                try:
                    pills_html.append(f"<span style='background:#064E3B22; color:#34D399; border:1px solid #05966944; padding:3px 10px; border-radius:9999px; font-size:0.78rem; font-weight:600;'>${float(acv):,.0f} ACV</span>")
                except (ValueError, TypeError):
                    pass

            st.markdown(f"<div style='margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 6px;'>{''.join(pills_html)}</div>", unsafe_allow_html=True)

            col_detail, col_activity = st.columns([1, 1])

            with col_detail:
                st.markdown("<div style='font-size:0.80rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:6px;'>Record Details</div>", unsafe_allow_html=True)
                if config.features.edit_records:
                    with st.form(prefix + '_edit_' + record.id):
                        values = input_fields(config, prefix + '_' + record.id, record.fields)
                        stage = st.selectbox(config.labels.stage, list(stages), index=list(stages).index(record.stage_id),
                                             format_func=stages.get, key=prefix + '_stage_' + record.id)
                        save = st.form_submit_button(config.labels.save)
                    if save:
                        try:
                            storage.update(record.id, values, stage)
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            st.session_state['_demo_flash'] = 'Changes saved.'
                            st.rerun()
                else:
                    for field in config.fields:
                        if field.visible:
                            st.text(f'{field.label}: {format_field(field, record.fields.get(field.key))}')

            with col_activity:
                st.markdown("<div style='font-size:0.80rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:6px;'>Activity & Timeline</div>", unsafe_allow_html=True)
                if config.features.activities:
                    with st.form(prefix + '_activity_' + record.id, clear_on_submit=True):
                        text = st.text_area('Activity / Note', max_chars=2000, key=prefix + '_note_' + record.id)
                        kind = st.selectbox('Activity Type', ['note', 'contacted', 'replied', 'meeting', 'meeting_canceled', 'opportunity'],
                                            format_func=lambda value: value.replace('_', ' ').title(), key=prefix + '_kind_' + record.id)
                        add = st.form_submit_button(config.labels.add_note)
                    if add:
                        try:
                            storage.add_activity(record.id, kind, text)
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            st.rerun()
                if record.activities:
                    st.caption('Activity History')
                    st.dataframe([a.model_dump(exclude={'id'}) for a in record.activities], hide_index=True, width="stretch")
                st.caption('Stage History')
                st.dataframe([{'Stage': stages[e.stage_id], 'Entered': e.entered_at} for e in record.stage_history], hide_index=True, width="stretch")


def intelligence(config):
    st.subheader(config.labels.intelligence)
    st.caption('Synthetic account research and conversation guides. No enrichment services are connected.')
    items = IntelligenceService.load_intel(Path(__file__).resolve().parents[3] / 'intel.json.example')
    query = st.text_input('Find intelligence', placeholder='Search by sector, keyword, or company profile...', key='public_intelligence_search')
    cards = IntelligenceService.get_cue_cards(items, query)
    if not cards:
        st.info('No matching intelligence. Try another search.')
    for item in cards:
        with st.expander(item.title, expanded=True):
            st.markdown(
                f"""
                <div style="background:#0F172A; border-left:4px solid #6366F1; border-radius:6px; padding:10px 14px; margin-bottom:10px;">
                    <div style="color:#F8FAFC; font-size:0.92rem; font-weight:600; line-height:1.4; margin-bottom:6px;">{item.summary}</div>
                    <div style="color:#818CF8; font-size:0.76rem; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">{' · '.join(item.tags)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if item.signals:
                st.markdown("<div style='font-size:0.80rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:4px;'>Account Signals</div>", unsafe_allow_html=True)
                for signal in item.signals:
                    st.markdown(f"<div style='font-size:0.85rem; color:#E2E8F0; margin-bottom:3px;'>• {signal}</div>", unsafe_allow_html=True)
            if item.questions:
                st.markdown("<div style='font-size:0.80rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.4px; margin-top:8px; margin-bottom:4px;'>Conversation Prompts</div>", unsafe_allow_html=True)
                for question in item.questions:
                    st.markdown(f"<div style='background:#1E293B; border-radius:6px; padding:6px 10px; margin-bottom:4px; font-size:0.84rem; color:#CBD5E1;'><b>Prompt:</b> {question}</div>", unsafe_allow_html=True)


def render_public(config):
    try:
        storage = session_storage(config)
    except (OSError, ValueError):
        st.error('Demo data does not match its configuration. No integrations were started.')
        return

    st.markdown(PUBLIC_THEME_CSS, unsafe_allow_html=True)

    # Main Page Title & Subtitle with custom classes
    st.markdown(f'<div class="demo-main-title">{config.page_title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="demo-sub-title">{config.page_subtitle}</div>', unsafe_allow_html=True)

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

    # Sidebar Outreach Resources (collapsible playbook)
    with st.sidebar.expander("Outreach Resources", expanded=False):
        render_outreach_resources_sidebar()

    # Sidebar Session Controls
    st.sidebar.markdown("<div style='font-size:0.72rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-top:14px; margin-bottom:6px;'>Session Controls</div>", unsafe_allow_html=True)
    if config.features.reset_demo_data and st.sidebar.button(config.labels.reset, key='public_reset', use_container_width=True):
        storage.reset()
        st.session_state['_demo_epoch'] = st.session_state.get('_demo_epoch', 0) + 1
        for key in list(st.session_state):
            if key.startswith('public_') and key not in ('public_navigation', 'public_reset'):
                del st.session_state[key]
        st.session_state['_demo_flash'] = 'Demo data reset for this session.'
        st.rerun()

    # Sidebar Sandbox Architecture Details
    with st.sidebar.expander("Sandbox Architecture", expanded=False):
        st.markdown(
            """
            <div style="font-size: 0.77rem; color: #94A3B8; line-height: 1.6;">
                <div><span style="color: #34D399; font-weight: 800;">●</span> <b style="color: #F8FAFC;">Storage:</b> Ephemeral In-Memory</div>
                <div><span style="color: #38BDF8; font-weight: 800;">●</span> <b style="color: #F8FAFC;">Network:</b> Zero External I/O</div>
                <div><span style="color: #A5B4FC; font-weight: 800;">●</span> <b style="color: #F8FAFC;">Dataset:</b> 40 Synthetic Accounts</div>
                <div><span style="color: #FBBF24; font-weight: 800;">●</span> <b style="color: #F8FAFC;">Isolation:</b> Per-Visitor Session</div>
            </div>
            """,
            unsafe_allow_html=True
        )

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
            st.dataframe(conversion_funnel(records, config), hide_index=True, width="stretch")
            st.caption('Each step counts unique records that achieved every preceding milestone. Later stage moves retain earlier achievements.')
        if 'table' in config.dashboard_modules:
            record_table(config, records)
        st.caption('Booking counts any recorded booking, including a later cancellation. Closed and disqualified prospects retain their history. Missing evidence is not inferred; a zero denominator displays —.')


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

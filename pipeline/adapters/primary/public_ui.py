"""Configuration-driven public views. Imports no private workflow or provider."""
import hashlib
import json
from pathlib import Path
import streamlit as st
from pipeline.adapters.primary.runtime import select_session
from pipeline.adapters.secondary.memory_records import MemoryRecordStorage
from pipeline.domain.records import format_field
from pipeline.domain.intelligence_service import IntelligenceService
from pipeline.domain.outreach_metrics import calculate_metrics, conversion_funnel


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
    st.dataframe(rows, hide_index=True, use_container_width=True)


def pipeline(config, storage, prefix):
    records = storage.list_records()
    if 'metrics' in config.dashboard_modules:
        metric_cards(config, records)
    stages = {s.id: s.name for s in config.stages}
    search = st.text_input(f'Search {config.labels.record_plural.lower()}', key=prefix + '_search').lower().strip()
    stage_filter = st.selectbox(config.labels.stage, ['all', *stages],
                                format_func=lambda value: 'All stages' if value == 'all' else stages[value], key=prefix + '_filter')
    visible = [r for r in records if (stage_filter == 'all' or stage_filter == r.stage_id)
               and (not search or search in ' '.join(str(v) for v in r.fields.values()).lower())]
    st.caption(f'{len(visible)} of {len(records)} {config.labels.record_plural.lower()}')
    if not visible:
        st.info(f'No {config.labels.record_plural.lower()} match. Add a record or change the filters.')
        return
    page = st.selectbox('Page', list(range(1, (len(visible) + 9) // 10 + 1)), key=prefix + '_page')
    if 'table' in config.dashboard_modules:
        with st.expander('Table'):
            record_table(config, visible)
    for record in visible[(page - 1) * 10:page * 10]:
        summary = ' · '.join(format_field(f, record.fields.get(f.key)) for f in config.fields if f.visible and f.card)
        with st.expander(f'{summary} | {stages[record.stage_id]}'):
            st.caption(f'{config.labels.stage}: {stages[record.stage_id]}')
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
                st.write('Activity History')
                st.dataframe([a.model_dump(exclude={'id'}) for a in record.activities], hide_index=True)
            st.write('Stage History')
            st.dataframe([{'Stage': stages[e.stage_id], 'Entered': e.entered_at} for e in record.stage_history], hide_index=True)


def intelligence(config):
    st.subheader(config.labels.intelligence)
    st.caption('Synthetic account research and conversation guides. No enrichment services are connected.')
    items = IntelligenceService.load_intel(Path(__file__).resolve().parents[3] / 'intel.json.example')
    query = st.text_input('Find intelligence', key='public_intelligence_search')
    cards = IntelligenceService.get_cue_cards(items, query)
    if not cards:
        st.info('No matching intelligence. Try another search.')
    for item in cards:
        with st.expander(item.title, expanded=True):
            st.write(item.summary)
            st.caption(' · '.join(item.tags))
            for signal in item.signals:
                st.write('• ' + signal)
            for question in item.questions:
                st.write('Conversation prompt: ' + question)


def render_public(config):
    try:
        storage = session_storage(config)
    except (OSError, ValueError):
        st.error('Demo data does not match its configuration. No integrations were started.')
        return
    st.title(config.page_title)
    st.caption(config.page_subtitle)
    st.sidebar.title(config.display_name)
    st.sidebar.info('Fictional demo · Changes stay in this visitor session. No messages are sent.')
    nav = {n.id: n.label for n in config.navigation}
    destination = st.sidebar.radio('Navigate', list(nav), format_func=nav.get, key='public_navigation')
    if config.features.reset_demo_data and st.sidebar.button(config.labels.reset, key='public_reset'):
        storage.reset()
        st.session_state['_demo_epoch'] = st.session_state.get('_demo_epoch', 0) + 1
        for key in list(st.session_state):
            if key.startswith('public_') and key not in ('public_navigation', 'public_reset'):
                del st.session_state[key]
        st.session_state['_demo_flash'] = 'Demo data reset for this session.'
        st.rerun()
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
            st.dataframe(conversion_funnel(records, config), hide_index=True, use_container_width=True)
            st.caption('Each step counts unique records that achieved every preceding milestone. Later stage moves retain earlier achievements.')
        if 'table' in config.dashboard_modules:
            record_table(config, records)
        st.caption('Booking counts any recorded booking, including a later cancellation. Closed and disqualified prospects retain their history. Missing evidence is not inferred; a zero denominator displays —.')


def metric_cards(config, records):
    metrics = calculate_metrics(records, config)
    if not metrics:
        return
    columns = st.columns(min(3, len(metrics)))
    for index, (key, metric) in enumerate(metrics.items()):
        value = metric['value']
        display = '—' if value is None else (f'{value:.1f}%' if metric['format'] == 'percent' else
                                           f'${value:,.0f}' if metric['format'] == 'currency' else str(value))
        label = config.labels.record_plural if key == 'total' else metric['label']
        columns[index % len(columns)].metric(label, display)
        if 'denominator' in metric:
            columns[index % len(columns)].caption(f"{metric['numerator']} / {metric['denominator']} unique prospects")

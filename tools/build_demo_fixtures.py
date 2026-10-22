"""Build the public-demo fixtures: 13 weeks of synthetic, relative-dated history.

Simulates one sales rep's outbound prospecting and one independent consultant's
deal flow, day by day, so stage histories, activities, conversion rates and
month-over-month trends are internally consistent. Output is deterministic.

Writes:
  pipeline/examples/fixtures/demo_prospects.json      (Sales Rep workspace)
  pipeline/examples/fixtures/demo_b2b_services.json   (B2B Services workspace)

Workspace configs in config/ are maintained by hand and are not touched.

Usage:
  python tools/build_demo_fixtures.py           # rewrite fixtures and print stats
  python tools/build_demo_fixtures.py --check   # print stats only
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import demo_fixture_content as C  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'pipeline' / 'examples' / 'fixtures'
# Chosen with --search: steady month-over-month growth and realistic conversion rates.
SALES_SEED = 20264736
B2B_SEED = 20263130
WINDOW_DAYS = 91          # 13 weeks of history
LAST_EVENT_DAY = -1       # history ends yesterday; today only holds scheduled actions
MAX_DUE_DAY = 10
GENERIC_WORDS = {'group', 'co', 'inc', 'partners', 'services', 'solutions', 'systems', 'the', '&'}


# --------------------------------------------------------------------------- helpers

def date_token(day):
    return f'today{day:+d}'


def datetime_token(day, minutes):
    return f'today{day:+d}T{minutes // 60:02d}:{minutes % 60:02d}'


def lower_first(text):
    return text[:1].lower() + text[1:] if text else text


def weighted(rng, pairs):
    items, weights = zip(*pairs)
    return rng.choices(items, weights=weights, k=1)[0]


def slug(text, words=2):
    parts = [w for w in re.split(r'[^a-z0-9]+', text.lower()) if w and w not in GENERIC_WORDS]
    return ''.join(parts[:words]) or 'example'


def email_for(first, last, company):
    local = re.sub(r'[^a-z.-]', '', f'{first}.{last}'.lower())
    return f'{local}@{slug(company)}.example.com'


class People:
    """Unique fictional full names."""

    def __init__(self, rng, reserved=()):
        pairs = [(f, l) for f in C.FIRST_NAMES for l in C.LAST_NAMES]
        rng.shuffle(pairs)
        self._pairs = iter(pairs)
        self._used_first = {}
        self._used_last = {last: 1 for _, last in reserved}
        self._used = set(reserved)

    def next(self):
        for first, last in self._pairs:
            # Spread first names so the list doesn't read as twelve Elenas.
            if ((first, last) in self._used or self._used_first.get(first, 0) >= 2
                    or self._used_last.get(last, 0) >= 2):
                continue
            self._used.add((first, last))
            self._used_first[first] = self._used_first.get(first, 0) + 1
            self._used_last[last] = self._used_last.get(last, 0) + 1
            return first, last
        raise RuntimeError('Name pool exhausted')


class Phones:
    """Numbers from the reserved fictional (NNN) 555-0100..0199 block."""

    def __init__(self, rng, reserved=()):
        self._rng = rng
        self._free = {}
        self._reserved = set(reserved)

    def next(self, area):
        if area not in self._free:
            pool = [n for n in range(100, 200) if f'({area}) 555-{n:04d}' not in self._reserved]
            self._rng.shuffle(pool)
            self._free[area] = pool
        return f'({area}) 555-{self._free[area].pop():04d}'


class Timeline:
    """Collects stage changes and activities for one record."""

    def __init__(self, rng, record_id):
        self.rng = rng
        self.record_id = record_id
        self.stages = []
        self.activities = []
        self.last_minutes = {}
        self.used_text = set()

    def pick(self, pool):
        """Choose a template not yet used on this record, so timelines don't repeat themselves."""
        fresh = [t for t in pool if t not in self.used_text] or list(pool)
        choice = self.rng.choice(fresh)
        self.used_text.add(choice)
        return choice

    def clock(self, day, earliest=8 * 60, latest=17 * 60):
        start = max(earliest, self.last_minutes.get(day, earliest - 15) + 15)
        if start > latest:
            start = latest
        minutes = self.rng.randrange(start, latest + 1, 15) if start < latest else start
        self.last_minutes[day] = minutes
        return minutes

    def stage(self, stage_id, day):
        self.stages.append({'stage_id': stage_id, 'entered_at': datetime_token(day, self.clock(day))})

    def act(self, kind, text, day):
        n = len(self.activities) + 1
        self.activities.append({'id': f'act-{self.record_id}-{n:02d}', 'kind': kind, 'text': text,
                                'occurred_at': datetime_token(day, self.clock(day))})

    def count(self, kinds, first_day, last_day):
        days = [int(re.match(r'today([+-]\d+)', a['occurred_at']).group(1)) for a in self.activities
                if a['kind'] in kinds]
        return sum(first_day <= d <= last_day for d in days)


class Horizon(Exception):
    """Raised when the next simulated step would happen today or later."""

    def __init__(self, due_day, action):
        super().__init__(action)
        self.due_day = due_day
        self.action = action


def advance(day, gap, action):
    """Move the simulation forward, or stop with a scheduled next action."""
    nxt = day + gap
    if nxt > LAST_EVENT_DAY:
        raise Horizon(max(0, nxt), action)
    return nxt


def created_days(rng, weekly_counts):
    days = []
    for week, count in enumerate(weekly_counts):
        start = -WINDOW_DAYS + week * 7
        days.extend(min(LAST_EVENT_DAY, start + rng.randint(0, 6)) for _ in range(count))
    return sorted(days)


# --------------------------------------------------------------------------- sales rep

SALES_WEEKLY_NEW = [5, 5, 6, 6, 7, 7, 8, 4, 8, 8, 9, 9, 9]   # dip in week 8 (rep out at a conference)
SALES_FIT = [('High', 50), ('Medium', 37), ('Low', 13)]
SEQUENCE_PATTERN = [('call', 'email'), ('email',), ('call',), ('call', 'email'), ('email',), ('call',), ('call', 'email')]
SALES_FIT_MULT = {'High': 1.0, 'Medium': 0.8, 'Low': 0.5}
SALES_STATUS = {
    'identified': 'In Research', 'qualified': 'Qualified', 'ready': 'Ready for Sequence',
    'meeting_booked': 'Meeting Booked', 'opportunity_created': 'Opportunity Created',
    'disqualified': 'Disqualified', 'no_response': 'No Response - Cooldown',
}
SALES_REPLY_STATUS = {'positive': 'Replied - Positive', 'pricing': 'Replied - Pricing Request',
                      'referral': 'Replied - Referral', 'later': 'Replied - Follow Up Later'}


def sales_profile(rng, people, phones, industry, company):
    ind = C.SALES_INDUSTRIES[industry]
    band, _, rep_range, acv_range = rng.choices(C.SALES_SIZES, weights=[s[1] for s in C.SALES_SIZES])[0]
    reps = rng.randint(*rep_range)
    first, last = people.next()
    _, area = rng.choice(C.CITIES)
    crm = rng.choice(C.SALES_CRMS)
    hires = rng.randint(3, 12)
    signals = [s.format(hires=hires) for s in rng.sample(ind['signals'], 3)]
    ctx = {'reps': reps, 'crm': crm, 'first': first, 'contact_first': first, 'company': company,
           'industry': industry, 'size': band, 'signal': signals[0], 'signal_lower': lower_first(signals[0]),
           'peer': rng.choice(ind['peers'])}
    small = band in ('50-100', '100-250')
    return {
        'ind': ind, 'ctx': ctx, 'first': first, 'last': last, 'reps': reps, 'crm': crm,
        'fit': weighted(rng, SALES_FIT),
        'fields': {
            'company': company, 'contact': f'{first} {last}',
            'title': rng.choice(C.SALES_TITLES['small' if small else 'mid']),
            'email': email_for(first, last, company), 'phone': phones.next(area),
            'website': f'https://{slug(company)}.example.com', 'industry': industry, 'company_size': band,
            'tech_stack': ' · '.join([crm] + rng.sample(C.SALES_TOOLS, 2)),
            'acv': round(rng.uniform(*acv_range) / 500) * 500,
            'opportunity_brief': rng.choice(ind['briefs']).format(**ctx),
            'pain_points': rng.choice(ind['pains']), 'desired_outcome': rng.choice(ind['outcomes']),
            'intent_signals': ' · '.join(signals),
            'opportunity_owner': C.SALES_REP, 'source': weighted(rng, C.SALES_SOURCES),
            'notes': rng.choice(C.SALES_NOTES).format(**ctx),
            'fit_rationale': rng.choice(C.SALES_FIT_RATIONALE).format(**ctx),
            'opportunity_rationale': rng.choice(C.SALES_WHY_NOW).format(**ctx),
            'suggested_action': rng.choice(C.SALES_ACTIONS).format(**ctx),
            'suggested_angle': rng.choice(C.SALES_ANGLES),
            'discovery_questions': rng.choice(C.SALES_QUESTIONS),
            'objections': rng.choice(C.SALES_OBJECTIONS).format(**ctx),
        },
    }


def simulate_sales(rng, tl, p, created, people):
    """Walk one prospect through the funnel. Returns (stage, status, next_action, due_day)."""
    ctx, first, fit = p['ctx'], p['first'], p['fit']
    t = (created + WINDOW_DAYS) / WINDOW_DAYS          # 0 = oldest, 1 = newest: the rep improves
    mult = SALES_FIT_MULT[fit]
    stage, status = 'identified', SALES_STATUS['identified']
    try:
        tl.stage('identified', created)
        tl.act('note', f"Account identified via {p['fields']['source']}. {ctx['signal']}.", created)

        day = advance(created, rng.randint(1, 3), f"Research {first}'s team and confirm ICP fit")
        if rng.random() < {'High': 0.03, 'Medium': 0.10, 'Low': 0.45}[fit]:
            tl.stage('disqualified', day)
            tl.act('note', rng.choice(C.SALES_DQ_EARLY), day)
            return 'disqualified', SALES_STATUS['disqualified'], None, None
        tl.stage('qualified', day)
        stage, status = 'qualified', SALES_STATUS['qualified']
        tl.act('note', f"Qualified: {fit.lower()} fit — {p['reps']} reps on {p['crm']}.", day)

        day = advance(day, rng.randint(1, 2), f'Finalize outreach angle and build sequence for {first}')
        tl.stage('ready', day)
        stage, status = 'ready', SALES_STATUS['ready']

        day = advance(day, rng.randint(1, 3), f'Launch sequence: step 1 email to {first}')
        tl.stage('contacted', day)
        stage = 'contacted'
        subject = rng.choice(p['ind']['subjects']).format(**ctx)
        tl.act('contacted', f'Sequence step 1: personalized email to {first} — "{subject}".', day)

        # Multi-touch sequence (email, call + email, call, ...) until a reply or the sequence ends.
        p_reply = (0.065 + 0.040 * t) * mult
        replied_day = None
        touches = 1
        if rng.random() < p_reply:
            replied_day = advance(day, rng.randint(1, 2), f'Sequence step 2: call + email {first}')
        for touch in range(2, 9):
            if replied_day is not None:
                break
            status = f'In Sequence - Touch {touch - 1}'
            kinds = SEQUENCE_PATTERN[touch - 2]
            day = advance(day, rng.choice([2, 2, 3, 3, 4]), f"Sequence step {touch}: {' + '.join(kinds)} {first}")
            for kind in kinds:
                pool = C.SALES_TOUCH_CALL if kind == 'call' else C.SALES_TOUCH_EMAIL
                tl.act(kind, tl.pick(pool).format(n=touch, **ctx), day)
            touches = touch
            if rng.random() < p_reply:
                replied_day = advance(day, rng.randint(0, 1), f'Sequence step {touch + 1}: follow up with {first}'
                                      if touch < 8 else f'Final breakup email to {first}')
        if replied_day is None:
            day = advance(day, rng.randint(3, 5), f'Final breakup email to {first}')
            tl.stage('no_response', day)
            weeks = max(2, round((day - created) / 7))
            tl.act('note', f'Sequence complete: {touches} touches over {weeks} weeks with no response. '
                           'Moved to cooldown; revisit next quarter.', day)
            return 'no_response', SALES_STATUS['no_response'], None, None

        # Reply
        day = replied_day
        kind_of_reply = weighted(rng, [('positive', 50), ('pricing', 18), ('referral', 14), ('later', 18)])
        ref_first, ref_last = people.next()
        reply = rng.choice(C.SALES_REPLIES[kind_of_reply]).format(
            ref=f'{ref_first} {ref_last}', ref_title=rng.choice(C.SALES_REFERRAL_TITLES), **ctx)
        tl.stage('replied', day)
        stage, status = 'replied', SALES_REPLY_STATUS[kind_of_reply]
        tl.act('replied', f'{first} replied: "{reply}"', day)
        next_by_type = {
            'positive': f'Propose discovery times to {first}',
            'pricing': f"Send pricing overview for {p['reps']} seats",
            'referral': f'Reach out to {ref_first} {ref_last} (referred by {first})',
            'later': f'Check back in with {first}',
        }
        day = advance(day, 1 if kind_of_reply != 'later' else rng.randint(10, 14), next_by_type[kind_of_reply])
        tl.act('email', {'positive': f'Sent {first} three discovery time options.',
                         'pricing': f'Sent pricing overview and a short ROI summary to {first}.',
                         'referral': f'Emailed {ref_first} {ref_last} with context from {first}.',
                         'later': f'Checked back in with {first} as requested.'}[kind_of_reply], day)

        p_meet = {'positive': 0.80, 'pricing': 0.60, 'referral': 0.55, 'later': 0.40}[kind_of_reply]
        p_meet = min(0.95, p_meet * (0.85 + 0.3 * t) * (1.0 if fit == 'High' else 0.85 if fit == 'Medium' else 0.6))
        if rng.random() >= p_meet:
            day = advance(day, rng.randint(4, 7), f'Follow up with {first} on next steps')
            tl.act(rng.choice(['email', 'call']), f'Followed up with {first}; no commitment yet.', day)
            day = advance(day, rng.randint(5, 9), f'Last follow-up to {first} before cooldown')
            if rng.random() < 0.5:
                tl.stage('no_response', day)
                tl.act('note', rng.choice(C.SALES_DARK_AFTER_REPLY), day)
                return 'no_response', SALES_STATUS['no_response'], None, None
            tl.stage('disqualified', day)
            tl.act('note', rng.choice(C.SALES_DQ_LATE), day)
            return 'disqualified', SALES_STATUS['disqualified'], None, None

        # Meeting booked, then held
        day = advance(day, rng.randint(1, 3), f'Confirm discovery call with {first}')
        tl.stage('meeting_booked', day)
        stage, status = 'meeting_booked', 'Meeting Booked'
        tl.act('meeting', f"Discovery call booked with {first} ({p['fields']['title']}).", day)
        day = advance(day, rng.randint(3, 6), f'Run discovery call with {first}')
        tl.act('call', f"Discovery call held: {rng.choice(C.SALES_MEETING_FINDINGS).format(**ctx)}", day)
        status = 'Discovery Held'
        day = advance(day, 1, f'Send discovery recap and proposal to {first}')
        tl.act('email', f'Sent {first} a recap, success criteria and a proposed pilot plan.', day)

        p_opp = (0.55 + 0.15 * t) * (1.0 if fit == 'High' else 0.8 if fit == 'Medium' else 0.5)
        if rng.random() < p_opp:
            day = advance(day, rng.randint(3, 7), f'Align on pilot scope with {first}')
            tl.stage('opportunity_created', day)
            seats = p['reps']
            step = rng.choice(C.SALES_OPP_STEPS)
            tl.act('opportunity', f"Opportunity created: ${p['fields']['acv']:,.0f} ACV for {seats} seats. "
                                  f'Next step: {step}.', day)
            return 'opportunity_created', SALES_STATUS['opportunity_created'], None, None
        day = advance(day, rng.randint(6, 12), f'Follow up on proposal with {first}')
        tl.stage('disqualified', day)
        tl.act('note', rng.choice(C.SALES_DQ_LATE), day)
        return 'disqualified', SALES_STATUS['disqualified'], None, None
    except Horizon as pending:
        return stage, status, pending.action, pending.due_day


def sales_record(record_id, p, stage, status, action, due):
    fields = dict(p['fields'])
    fit = p['fit']
    fields['icp_fit'] = fit
    fields['qualification_notes'] = (f"{fit} fit: {p['reps']} quota-carrying reps on {p['crm']}, "
                                     f"{fields['company_size']} employees.")
    fields['priority'] = ('High' if fit == 'High' and (stage in ('replied', 'meeting_booked') or fields['acv'] >= 35000)
                          else 'Low' if fit == 'Low' else 'Medium')
    fields['follow_up_status'] = status
    fields['next_action'] = action or ''
    fields['next_action_date'] = date_token(due) if action else None
    return fields


def build_sales(rng):
    people = People(rng, reserved={('Elena', 'Rostova')})
    phones = Phones(rng, reserved={C.SALES_HERO['phone']})
    pool = [(industry, company) for industry, data in C.SALES_INDUSTRIES.items() for company in data['companies']]
    days = created_days(rng, SALES_WEEKLY_NEW)
    picks = rng.sample(pool, len(days))
    rows, timelines = [], {}
    for n, (created, (industry, company)) in enumerate(zip(days, picks), start=2):
        record_id = f'demo-{n:03d}'
        p = sales_profile(rng, people, phones, industry, company)
        tl = Timeline(rng, record_id)
        stage, status, action, due = simulate_sales(rng, tl, p, created, people)
        rows.append({'id': record_id, 'stage_id': stage, 'created_at': tl.stages[0]['entered_at'],
                     'fields': sales_record(record_id, p, stage, status, action, due),
                     'stage_history': tl.stages, 'activities': tl.activities})
        timelines[record_id] = tl

    # Hero record: freshly identified, research due today.
    tl = Timeline(rng, 'demo-001')
    tl.stage('identified', -2)
    tl.act('note', 'Account identified via account research. Hiring 6 enterprise AEs after a $35M Series B.', -2)
    tl.act('note', 'Research: Elena joined recently and is reviewing the sales tech stack.', -1)
    hero_fields = dict(C.SALES_HERO, opportunity_owner=C.SALES_REP, next_action_date=date_token(0))
    rows.insert(0, {'id': 'demo-001', 'stage_id': 'identified', 'created_at': tl.stages[0]['entered_at'],
                    'fields': hero_fields, 'stage_history': tl.stages, 'activities': tl.activities})
    timelines['demo-001'] = tl
    calibrate_due_dates(rng, rows, overdue=2, due_today=(6, 7), overdue_stages=('contacted',))
    return order_by_urgency(rows, hero='demo-001'), timelines


# --------------------------------------------------------------------------- consultant

B2B_WEEKLY_NEW = [2, 2, 2, 3, 2, 3, 2, 2, 3, 3, 3, 3, 3]
B2B_ENGAGEMENT_MIX = [('hubspot_impl', 18), ('sfdc_cleanup', 12), ('revops_audit', 16), ('sales_process', 12),
                      ('forecast_dash', 12), ('fractional', 12), ('marketing_auto', 10), ('comp_territory', 8)]


def b2b_profile(rng, people, phones, client):
    company, industry, employees = client
    key = weighted(rng, B2B_ENGAGEMENT_MIX)
    eng = C.B2B_ENGAGEMENTS[key]
    first, last = people.next()
    _, area = rng.choice(C.CITIES)
    months = rng.randint(*eng['months'])
    value = round(rng.uniform(*eng['value']) / 500) * 500
    hours = round(rng.randint(*eng['hours']) / 5) * 5
    source = weighted(rng, C.B2B_SOURCES)
    brief = f"{eng['label']}. " + rng.choice(eng['briefs']).format(size=employees)
    return {
        'key': key, 'eng': eng, 'first': first, 'months': months, 'value': value, 'hours': hours,
        'company': company,
        'fields': {
            'company': company, 'contact': f'{first} {last}', 'title': rng.choice(C.B2B_TITLES),
            'email': email_for(first, last, company), 'phone': phones.next(area), 'industry': industry,
            'acv': value, 'opportunity_brief': brief, 'pain_points': rng.choice(eng['pains']),
            'desired_outcome': rng.choice(eng['outcomes']), 'tech_stack': eng['tech'],
            'opportunity_owner': C.CONSULTANT, 'source': source,
            'notes': f'{employees} employees. Came in via {source.lower()}.',
        },
    }


def simulate_b2b(rng, tl, p, created):
    """Walk one inquiry through the consultant's sales cycle."""
    first, eng, t = p['first'], p['eng'], (created + WINDOW_DAYS) / WINDOW_DAYS
    stage = 'inquiry'
    try:
        tl.stage('inquiry', created)
        tl.act('note', f"New inquiry via {p['fields']['source'].lower()} — {p['fields']['opportunity_brief']}", created)
        day = advance(created, rng.randint(1, 3), f'Intro call with {first}')
        tl.act('call', f"Intro call with {first}: {rng.choice(C.B2B_INTRO_FINDINGS).format(first=first)}.", day)
        if rng.random() < 0.10:
            day = advance(day, rng.randint(1, 3), f'Send scoping notes to {first}')
            tl.stage('lost', day)
            tl.act('note', rng.choice(C.B2B_LOST_EARLY), day)
            return 'lost', None, None

        day = advance(day, rng.randint(1, 3), f'Book requirements session with {first}')
        tl.stage('scoping', day)
        stage = 'scoping'
        tl.act('email', f'Sent {first} a scoping questionnaire and two session times.', day)
        day = advance(day, rng.randint(2, 5), f"Requirements session with {first}'s team")
        tl.act('call', f'Requirements session with {first} and {rng.randint(2, 4)} stakeholders; '
                       f'documented {rng.randint(5, 9)} must-haves.', day)
        if rng.random() < 0.06:
            day = advance(day, rng.randint(3, 6), f'Check in with {first} on scope')
            tl.stage('lost', day)
            tl.act('note', rng.choice(C.B2B_LOST_EARLY), day)
            return 'lost', None, None

        day = advance(day, rng.randint(1, 2), f"Draft proposal & SOW for {p['company']}")
        tl.stage('proposal_dev', day)
        stage = 'proposal_dev'
        tl.act('note', f"Drafting proposal: {eng['label']}, {p['months']}-month timeline.", day)

        day = advance(day, rng.randint(2, 5), f'Send proposal to {first}')
        tl.stage('proposal_sent', day)
        stage = 'proposal_sent'
        if p['key'] == 'fractional':
            terms = f"${p['value'] / p['months']:,.0f}/month for {p['months']} months"
        else:
            terms = f"${p['value']:,.0f} fixed fee over {p['months']} month{'s' if p['months'] > 1 else ''}"
        tl.act('email', f"Proposal sent to {first}: {eng['label']}, {terms}.", day)

        negotiate = rng.random() < 0.62 + 0.20 * t
        decision_gap = rng.randint(8, 16) if negotiate else rng.randint(14, 24)
        decision_day = day + decision_gap
        while day + 5 < decision_day:
            day = advance(day, rng.randint(4, 6), f'Follow up on proposal with {first}')
            kind = rng.choice(['email', 'call'])
            tl.act(kind, f'Followed up on the proposal; {first} is reviewing it with the leadership team.'
                   if kind == 'email' else f'Call with {first}: answered questions on timeline and deliverables.', day)
        day = advance(day, max(1, decision_day - day), f'Follow up on proposal with {first}')
        if not negotiate:
            tl.stage('lost', day)
            tl.act('note', rng.choice(C.B2B_LOST_LATE), day)
            return 'lost', None, None

        tl.stage('negotiation', day)
        stage = 'negotiation'
        tl.act('call', f'Negotiation call: {first} {rng.choice(C.B2B_NEGOTIATION_ASKS)}.', day)
        won = rng.random() < 0.78
        day = advance(day, rng.randint(5, 10) if won else rng.randint(8, 14), f'Send revised SOW to {first}')
        if not won:
            tl.stage('lost', day)
            tl.act('note', rng.choice(C.B2B_LOST_LATE), day)
            return 'lost', None, None
        tl.stage('contract_awarded', day)
        tl.act('note', f"Signed SOW received: ${p['value']:,.0f}. Kickoff scheduled.", day)
        return 'contract_awarded', day, None
    except Horizon as pending:
        return stage, None, pending


def build_b2b(rng):
    people = People(rng)
    phones = Phones(rng)
    days = created_days(rng, B2B_WEEKLY_NEW)
    clients = rng.sample(C.B2B_CLIENTS, len(days))
    rows, timelines = [], {}
    for n, (created, client) in enumerate(zip(days, clients), start=1):
        record_id = f'b2b-{n:03d}'
        p = b2b_profile(rng, people, phones, client)
        tl = Timeline(rng, record_id)
        stage, won_day, pending = simulate_b2b(rng, tl, p, created)
        fields = dict(p['fields'])
        fields['priority'] = 'High' if p['value'] >= 30000 else 'Medium'
        fields['qualification_notes'] = ('Budget confirmed; decision maker engaged.'
                                         if stage not in ('inquiry', 'lost') else
                                         'Qualification in progress.' if stage == 'inquiry' else
                                         'Closed; notes kept for future outreach.')
        fields['next_action'], fields['next_action_date'] = '', None
        if pending:
            fields['next_action'], fields['next_action_date'] = pending.action, date_token(pending.due_day)
        if stage == 'contract_awarded':
            start = won_day + rng.randint(7, 14)
            end = start + p['months'] * 30 - 1
            fields.update(engagement_start=date_token(start), engagement_end=date_token(end),
                          monthly_hours=p['hours'])
            if start >= 0:
                fields['next_action'], fields['next_action_date'] = f"Project kickoff with {p['first']}", date_token(start)
        elif stage == 'negotiation':
            start = pending.due_day + rng.randint(14, 21)
            fields.update(engagement_start=date_token(start),
                          engagement_end=date_token(start + p['months'] * 30 - 1), monthly_hours=p['hours'])
        rows.append({'id': record_id, 'stage_id': stage, 'created_at': tl.stages[0]['entered_at'],
                     'fields': fields, 'stage_history': tl.stages, 'activities': tl.activities})
        timelines[record_id] = tl
    calibrate_due_dates(rng, rows, overdue=1, due_today=(2, 3), overdue_stages=('proposal_sent',),
                        active={'inquiry', 'scoping', 'proposal_dev', 'proposal_sent', 'negotiation'})
    return order_by_urgency(rows), timelines


# --------------------------------------------------------------------------- shared post-processing

SALES_ACTIVE = {'identified', 'qualified', 'ready', 'contacted', 'replied', 'meeting_booked'}


def due_day(row):
    value = row['fields'].get('next_action_date')
    return int(value[len('today'):]) if value else None


def calibrate_due_dates(rng, rows, overdue, due_today, overdue_stages, active=SALES_ACTIVE):
    """Make the Daily Priorities believable: a couple overdue, a handful due today."""
    open_rows = [r for r in rows if r['stage_id'] in active and r['fields'].get('next_action')]
    for r in open_rows:
        if due_day(r) > MAX_DUE_DAY:
            r['fields']['next_action_date'] = date_token(rng.randint(5, MAX_DUE_DAY))
    candidates = [r for r in open_rows if r['stage_id'] in overdue_stages and r['id'] != 'demo-001']
    for r, day in zip(rng.sample(candidates, min(overdue, len(candidates))), [-1, -2, -3]):
        r['fields']['next_action_date'] = date_token(day)
    today = [r for r in open_rows if due_day(r) == 0]
    low, high = due_today
    if len(today) > high:
        for r in rng.sample([r for r in today if r['id'] != 'demo-001'], len(today) - high):
            r['fields']['next_action_date'] = date_token(rng.randint(1, 3))
    elif len(today) < low:
        soon = [r for r in open_rows if due_day(r) in (1, 2)]
        for r in rng.sample(soon, min(low - len(today), len(soon))):
            r['fields']['next_action_date'] = date_token(0)


def order_by_urgency(rows, hero=None):
    """Open work first (most urgent at the top), then closed records, newest activity first."""
    def key(r):
        due = due_day(r)
        last = max(int(re.match(r'today([+-]\d+)', e['entered_at']).group(1)) for e in r['stage_history'])
        if due is None:
            return (1, -last, 0, r['id'])
        return (0, due, 0 if r['id'] == hero else 1, -(r['fields'].get('acv') or 0))
    return sorted(rows, key=key)


# --------------------------------------------------------------------------- stats & seed selection

WINDOWS = [('days -89..-60', (-89, -60)), ('days -59..-30', (-59, -30)), ('last 30 days', (-29, 0))]
SALES_MILESTONES = {'contacted': {'contacted'}, 'replied': {'replied'}, 'meeting': {'meeting_booked'},
                    'opportunity': {'opportunity_created'}}
B2B_MILESTONES = {'proposals': {'proposal_sent'}, 'negotiation': {'negotiation'}, 'won': {'contract_awarded'},
                  'lost': {'lost'}}
B2B_ACTIVE = {'inquiry', 'scoping', 'proposal_dev', 'proposal_sent', 'negotiation'}


def day_of(token):
    return int(re.match(r'today([+-]\d+)', token).group(1))


def window_counts(rows, milestones, window):
    lo, hi = window
    out = {'new': sum(1 for r in rows if lo <= day_of(r['created_at']) <= hi)}
    for name, ids in milestones.items():
        firsts = (next((e for e in r['stage_history'] if e['stage_id'] in ids), None) for r in rows)
        out[name] = sum(1 for e in firsts if e and lo <= day_of(e['entered_at']) <= hi)
    return out


def compute_stats(sales, sales_tl, b2b):
    s_active = [r for r in sales if r['stage_id'] in SALES_ACTIVE]
    b_active = [r for r in b2b if r['stage_id'] in B2B_ACTIVE]
    won = [r for r in b2b if r['stage_id'] == 'contract_awarded']
    stats = {
        'sales_windows': [window_counts(sales, SALES_MILESTONES, w) for _, w in WINDOWS],
        'sales_active': len(s_active),
        'sales_pipeline': sum(r['fields']['acv'] for r in s_active),
        'sales_stages': {k: sum(1 for r in sales if r['stage_id'] == k) for k in sorted({r['stage_id'] for r in sales})},
        'calls_7d': sum(tl.count({'call'}, -6, 0) for tl in sales_tl.values()),
        'emails_7d': sum(tl.count({'email', 'contacted'}, -6, 0) for tl in sales_tl.values()),
        'meetings_7d': sum(tl.count({'meeting'}, -6, 0) for tl in sales_tl.values()),
        'b2b_windows': [window_counts(b2b, B2B_MILESTONES, w) for _, w in WINDOWS],
        'b2b_won_value': [sum(r['fields']['acv'] for r in won
                              if lo <= day_of(next(e for e in r['stage_history']
                                                   if e['stage_id'] == 'contract_awarded')['entered_at']) <= hi)
                          for _, (lo, hi) in WINDOWS],
        'b2b_active': len(b_active),
        'b2b_pipeline': sum(r['fields']['acv'] for r in b_active),
        'b2b_stages': {k: sum(1 for r in b2b if r['stage_id'] == k) for k in sorted({r['stage_id'] for r in b2b})},
        'committed_hours': sum(r['fields']['monthly_hours'] for r in won
                               if day_of(r['fields']['engagement_start']) <= 30
                               and day_of(r['fields']['engagement_end']) >= 0),
        'negotiation_hours': sum(r['fields']['monthly_hours'] for r in b2b if r['stage_id'] == 'negotiation'),
    }
    return stats


class Penalty:
    """Accumulates how far stats fall outside believable ranges (lower is better)."""

    def __init__(self):
        self.total = 0.0

    def band(self, value, lo, hi, weight=1.0):
        if value < lo:
            self.total += weight * (lo - value) / max(lo, 1)
        elif value > hi:
            self.total += weight * (value - hi) / max(hi, 1)

    def rising(self, values, weight=1.0):
        for a, b in zip(values, values[1:]):
            if b < a:
                self.total += weight * (a - b) / max(a, 1)


def score_sales(stats):
    p, sw = Penalty(), stats['sales_windows']
    for key in ('new', 'contacted', 'replied', 'meeting', 'opportunity'):
        p.rising([w[key] for w in sw], 2.0)
    reply = [w['replied'] / w['contacted'] if w['contacted'] else 0 for w in sw]
    booking = [w['meeting'] / w['contacted'] if w['contacted'] else 0 for w in sw]
    p.rising(reply, 2.0)
    p.rising(booking, 2.0)
    for rate, (lo, hi) in zip(reply, [(0.18, 0.28), (0.24, 0.34), (0.30, 0.40)]):
        p.band(rate, lo, hi, 4.0)
    for rate, (lo, hi) in zip(booking, [(0.07, 0.14), (0.11, 0.18), (0.15, 0.22)]):
        p.band(rate, lo, hi, 4.0)
    p.band(sum(w['opportunity'] for w in sw), 6, 9, 2.0)
    p.band(stats['sales_active'], 34, 46)
    p.band(stats['sales_pipeline'], 900_000, 1_300_000)
    p.band(stats['calls_7d'], 24, 30, 2.0)
    p.band(stats['emails_7d'], 30, 38, 2.0)
    p.band(stats['meetings_7d'], 2, 3, 2.0)
    return p.total


def score_b2b(stats):
    p, bw = Penalty(), stats['b2b_windows']
    p.rising([w['new'] for w in bw], 2.0)
    p.rising([w['won'] for w in bw], 2.0)
    p.rising(stats['b2b_won_value'], 2.0)
    p.band(stats['b2b_active'], 11, 15, 2.0)
    p.band(stats['b2b_stages'].get('negotiation', 0), 2, 3, 2.0)
    p.band(stats['b2b_stages'].get('lost', 0), 8, 12, 2.0)
    p.band(stats['b2b_stages'].get('contract_awarded', 0), 5, 8, 2.0)
    p.band(stats['committed_hours'], 85, 105, 3.0)
    p.band(stats['negotiation_hours'], 40, 70, 2.0)
    return p.total


def print_stats(stats):
    print('\nSALES')
    for (label, _), w in zip(WINDOWS, stats['sales_windows']):
        rr = w['replied'] / w['contacted'] * 100 if w['contacted'] else 0
        br = w['meeting'] / w['contacted'] * 100 if w['contacted'] else 0
        print(f"  {label:>14}: new {w['new']:3}  contacted {w['contacted']:3}  replied {w['replied']:3}  "
              f"meetings {w['meeting']:3}  opps {w['opportunity']:3}   reply {rr:4.1f}%  booking {br:4.1f}%")
    print('  stages:', stats['sales_stages'])
    print(f"  active {stats['sales_active']}  pipeline ${stats['sales_pipeline']:,.0f}")
    print(f"  last 7 days: calls {stats['calls_7d']}  emails {stats['emails_7d']}  meetings booked {stats['meetings_7d']}")
    print('\nB2B')
    for (label, _), w, value in zip(WINDOWS, stats['b2b_windows'], stats['b2b_won_value']):
        print(f"  {label:>14}: new {w['new']:3}  proposals {w['proposals']:3}  negotiation {w['negotiation']:3}  "
              f"won {w['won']:3} (${value:,.0f})  lost {w['lost']:3}")
    print('  stages:', stats['b2b_stages'])
    print(f"  active {stats['b2b_active']}  pipeline ${stats['b2b_pipeline']:,.0f}")
    print(f"  capacity: committed {stats['committed_hours']} / {C.CONSULTANT_CAPACITY_HOURS} hrs, "
          f"negotiation would add {stats['negotiation_hours']}")


def build(sales_seed=SALES_SEED, b2b_seed=B2B_SEED):
    sales, sales_tl = build_sales(random.Random(sales_seed))
    b2b, _ = build_b2b(random.Random(b2b_seed))
    return sales, b2b, compute_stats(sales, sales_tl, b2b)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='print stats without writing fixtures')
    parser.add_argument('--search', type=int, metavar='N',
                        help='score N candidate seeds per workspace and report the best (does not write)')
    args = parser.parse_args()
    if args.search:
        best_sales = min((score_sales(build(seed, B2B_SEED)[2]), seed) for seed in range(SALES_SEED, SALES_SEED + args.search))
        best_b2b = min((score_b2b(build(SALES_SEED, seed)[2]), seed) for seed in range(B2B_SEED, B2B_SEED + args.search))
        print(f'best SALES_SEED = {best_sales[1]} (penalty {best_sales[0]:.3f})')
        print(f'best B2B_SEED = {best_b2b[1]} (penalty {best_b2b[0]:.3f})')
        print_stats(build(best_sales[1], best_b2b[1])[2])
        return
    sales, b2b, stats = build()
    print_stats(stats)
    print(f'\npenalty: sales {score_sales(stats):.3f}, b2b {score_b2b(stats):.3f}')
    if not args.check:
        for name, rows in (('demo_prospects.json', sales), ('demo_b2b_services.json', b2b)):
            (FIXTURES / name).write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            print(f'Wrote {len(rows)} records to {FIXTURES / name}')


if __name__ == '__main__':
    main()

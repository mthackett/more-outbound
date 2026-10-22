"""Narrative pools for the synthetic public-demo fixtures.

Everything here is fictional. Companies and people are invented; phone numbers
use the reserved (NNN) 555-01NN range and every email/website lives on
*.example.com. Text uses {placeholders} filled per record by
build_demo_fixtures.py.
"""

FIRST_NAMES = [
    'Elena', 'Marcus', 'Priya', 'Daniel', 'Hannah', 'Tomas', 'Aisha', 'Owen', 'Mei', 'Rafael',
    'Grace', 'Nikhil', 'Sofia', 'Caleb', 'Ines', 'Jonah', 'Leah', 'Mateo', 'Nadia', 'Ethan',
    'Yara', 'Felix', 'Camila', 'Dmitri', 'Harper', 'Kenji', 'Lauren', 'Andre', 'Maya', 'Quentin',
    'Rosa', 'Samir', 'Tessa', 'Victor', 'Wendy', 'Xavier', 'Zoe', 'Bianca', 'Colin', 'Delia',
    'Emeka', 'Fiona', 'Gavin', 'Helena', 'Imran', 'Julia', 'Kofi', 'Lena', 'Malik', 'Nora',
    'Oscar', 'Paloma', 'Reid', 'Sana', 'Theo', 'Uma', 'Vera', 'Wesley', 'Ximena', 'Yusuf',
    'Adele', 'Bruno', 'Clara', 'Dev', 'Esther', 'Farah', 'Gideon', 'Ivy', 'Joel', 'Kira',
]

LAST_NAMES = [
    'Rostova', 'Okafor', 'Lindqvist', 'Moreau', 'Achterberg', 'Castellano', 'Brennan', 'Takeda',
    'Haddad', 'Novak', 'Delacroix', 'Iyer', 'Whitcombe', 'Varga', 'Esposito', 'Kowalczyk',
    'Mbeki', 'Sorensen', 'Petrakis', 'Quintero', 'Halvorsen', 'Abernathy', 'Nakamura', 'Ferreira',
    'Ostrowski', 'Calloway', 'Ruiz-Benton', 'Thakkar', 'Vasquez', 'Hollander', 'Adeyemi', 'Lockhart',
    'Marchetti', 'Szabo', 'Fairbanks', 'Oyelaran', 'Kaplan', 'Bergstrom', 'Duarte', 'Ellingsen',
    'Grummond', 'Hakimi', 'Ivanova', 'Jablonski', 'Kettering', 'Larkspur', 'Mendelsohn', 'Northcott',
    'Pellegrino', 'Ravensworth', 'Strand', 'Tolliver', 'Underhill', 'Valdivia', 'Wexford', 'Yilmaz',
    'Zaragoza', 'Ashdown', 'Blackwood', 'Cordero', 'Dunmore', 'Everly', 'Galloway', 'Hartigan',
    'Ingersoll', 'Jaramillo', 'Kirchner', 'Lattimore', 'Montague', 'Nygaard',
]

# (city, area code) — numbers are always drawn from the reserved 555-0100..0199 block.
CITIES = [
    ('Boston', '617'), ('Chicago', '312'), ('San Francisco', '415'), ('New York', '212'),
    ('Austin', '512'), ('Denver', '303'), ('Seattle', '206'), ('Atlanta', '404'),
    ('Dallas', '214'), ('Minneapolis', '612'), ('Phoenix', '602'), ('Nashville', '615'),
    ('Raleigh', '919'), ('Columbus', '614'), ('Salt Lake City', '801'), ('Portland', '503'),
    ('Philadelphia', '215'), ('San Diego', '619'),
]

# ---------------------------------------------------------------------------
# Sales Rep workspace: one mid-market AE (Sarah Jenkins) selling an account
# intelligence and pipeline-discipline platform to revenue teams.
# ---------------------------------------------------------------------------

SALES_REP = 'Sarah Jenkins'

SALES_SIZES = [  # (band, weight, (min reps, max reps), (min ACV, max ACV))
    ('50-100', 10, (6, 10), (9000, 15000)),
    ('100-250', 30, (10, 24), (13000, 24000)),
    ('250-500', 32, (20, 45), (20000, 36000)),
    ('500-1000', 20, (40, 80), (30000, 52000)),
    ('1000+', 8, (80, 150), (46000, 68000)),
]

SALES_TITLES = {
    'small': ['VP of Sales', 'Head of Sales', 'Director of Sales', 'Co-founder & CRO'],
    'mid': ['VP of Sales', 'VP of Revenue Operations', 'Director of Sales Development',
            'Head of Sales Enablement', 'Director of Revenue Operations', 'Chief Revenue Officer'],
}

SALES_REFERRAL_TITLES = ['Director of Sales Operations', 'Revenue Operations Manager',
                         'Head of Sales Development', 'Sales Enablement Lead']

SALES_SOURCES = [
    ('Account Research', 22), ('LinkedIn Sales Navigator', 18), ('Intent Data (G2)', 12),
    ('Webinar Attendee', 10), ('Inbound Demo Request', 8), ('Customer Referral', 8),
    ('Industry Event', 8), ('Partner Referral', 6), ('Outbound Campaign', 8),
]

SALES_CRMS = ['Salesforce', 'HubSpot', 'Salesforce', 'HubSpot', 'Salesforce', 'Pipedrive']
SALES_TOOLS = ['Gong', 'Outreach', 'Salesloft', 'ZoomInfo', 'Apollo', 'Clari', 'Highspot', 'Chorus']

SALES_INDUSTRIES = {
    'HealthTech': {
        'companies': ['Meridian Care Analytics', 'Cobalt Health Systems', 'Brightwell Clinical',
                      'Wrenfield Health Data', 'Solace Diagnostics', 'Harborview MedTech',
                      'Pulsepoint Health', 'Evergreen Care Network',
                      'Tidewater Health Partners', 'Larchmont Clinical Systems'],
        'briefs': [
            'Field sales team of {reps} selling into hospital systems; pipeline reviews still run off spreadsheets and rep memory.',
            'Expanding from regional clinics into health-system accounts; reps lack a consistent account brief before first calls.',
            'Clinical analytics vendor adding an enterprise segment; leadership wants forecastable pipeline before the next board cycle.',
        ],
        'pains': [
            'Reps spend hours researching each health system before outreach, and context is lost when accounts change hands.',
            'Long buying committees stall deals; nobody can see which stakeholder was last engaged or what was promised.',
            'Stage 1 to Stage 2 conversion has slipped for two quarters and managers cannot pinpoint where deals stall.',
        ],
        'outcomes': [
            'Standardized pre-call briefs, cleaner hand-offs between reps, and a pipeline review the CRO trusts.',
            'Shorter ramp for new reps and visible next actions on every open health-system opportunity.',
        ],
        'signals': ['Hiring {hires} enterprise AEs', 'Series B announced', 'New VP of Sales started this quarter',
                    'Expanding into two new states', 'G2 research activity on sales engagement tools',
                    'Posted a Sales Operations Manager role'],
        'subjects': ['Pre-call prep for health-system deals', 'Idea for your clinical sales ramp',
                     'How {peer} cut research time for hospital accounts'],
        'peers': ['a 40-rep clinical analytics team', 'another health-data vendor'],
    },
    'Logistics': {
        'companies': ['Ironbridge Freight', 'Bluewater Intermodal', 'Crosspoint Logistics',
                      'Summit Fleet Services', 'Arrowline Carriers', 'Keystone Distribution',
                      'Northgate Supply Chain', 'Redline Courier Group',
                      'Veloce Logistics', 'Prairieline Transport'],
        'briefs': [
            'Freight brokerage with {reps} reps pushing into mid-market shippers; outbound is high volume but poorly targeted.',
            'Carrier sales team juggling hundreds of shipper accounts; follow-ups slip whenever lanes get busy.',
            '3PL growing its dedicated-fleet business; wants reps focused on accounts that actually match lane coverage.',
        ],
        'pains': [
            'Reps chase stale shipper lists and duplicate each other\'s outreach across territories.',
            'Quote follow-ups fall through the cracks during peak season, costing winnable freight.',
            'No shared view of which shippers are expanding, so outreach timing is guesswork.',
        ],
        'outcomes': [
            'Prioritized shipper lists with clear next actions so every rep works the right accounts each morning.',
            'Consistent follow-up cadence through peak season and visibility into quote-to-win by rep.',
        ],
        'signals': ['Opened a new cross-dock facility', 'Hiring {hires} freight sales reps', 'Added refrigerated lanes',
                    'Acquired a regional carrier', 'Leadership posted about outbound efficiency',
                    'Attended our logistics revenue webinar'],
        'subjects': ['Freight reps and follow-up discipline', 'Idea for your shipper outbound',
                     'How {peer} stopped losing quotes in peak season'],
        'peers': ['a 25-rep brokerage in the Midwest', 'another 3PL sales team'],
    },
    'Financial Services': {
        'companies': ['Halcyon Payments', 'Ledgerwise', 'Sterling Ridge Capital', 'Clearpath Lending',
                      'Granite Peak Wealth', 'Fairmount Insurance Group', 'Atlas Credit Partners',
                      'Quillon Pay', 'Crestline Financial', 'Bayview Mutual Group'],
        'briefs': [
            'Payments company scaling a {reps}-person mid-market team; compliance reviews slow every deal cycle.',
            'Commercial lender building an outbound motion for the first time; reps came from relationship banking.',
            'Insurance group consolidating three sales teams onto one CRM and one playbook.',
        ],
        'pains': [
            'Compliance-heavy deals stall because reps cannot see where each stakeholder stands.',
            'New outbound reps lack research habits; messaging is generic and reply rates are low.',
            'Three teams, three processes: forecast calls turn into reconciliation exercises.',
        ],
        'outcomes': [
            'One playbook, consistent account research, and a forecast leadership can defend to the board.',
            'Faster time-to-first-meeting for new reps and fewer deals stuck in compliance review.',
        ],
        'signals': ['Hiring {hires} account executives', 'Launched a mid-market product line',
                    'New CRO from a high-growth fintech', 'Raised a growth round', 'Consolidating CRM vendors',
                    'Downloaded our sales-process benchmark report'],
        'subjects': ['Outbound playbook for a regulated sale', 'Idea for your new outbound team',
                     'How {peer} unified three sales teams'],
        'peers': ['a regional payments provider', 'a 30-rep commercial lending team'],
    },
    'Cybersecurity': {
        'companies': ['Bastion Cyber', 'Ironvale Identity', 'Vigilant Networks', 'Cipherline Security',
                      'Watchtower Labs', 'Palisade Defense Systems', 'Keyward Security', 'Sentry Risk',
                      'Moatline Security', 'Tessera Threat Labs'],
        'briefs': [
            'Security vendor with {reps} reps selling to IT leaders; long cycles and many technical stakeholders.',
            'Identity platform moving upmarket; reps need sharper account research to reach security leadership.',
            'MDR provider expanding channel and direct sales; deal hand-offs between SDRs and AEs are messy.',
        ],
        'pains': [
            'Technical evaluations drag on and deals go dark between security reviews.',
            'SDR-to-AE hand-offs lose context, so first meetings repeat discovery.',
            'Reps cannot tell which accounts are actively evaluating versus just reading content.',
        ],
        'outcomes': [
            'Clean SDR-to-AE hand-offs and a visible next step on every technical evaluation.',
            'Outreach timed to real buying signals instead of static lists.',
        ],
        'signals': ['Hiring {hires} enterprise AEs', 'Published a new compliance certification',
                    'Spoke at a regional security summit', 'G2 research activity on revenue intelligence',
                    'New VP of Sales hired from a public security company', 'Expanding into the public sector'],
        'subjects': ['Hand-offs between SDRs and AEs', 'Idea for long security evaluations',
                     'How {peer} kept technical deals from going dark'],
        'peers': ['an identity security vendor', 'a 20-rep MDR team'],
    },
    'Manufacturing': {
        'companies': ['Beacon Robotics', 'Forgeline Manufacturing', 'Precision Axis Industries',
                      'Tristate Fabrication', 'Kinetic Automation', 'Steelhead Components',
                      'Apex Motion Controls', 'Riverbend Industrial',
                      'Hollis Precision Works', 'Cindervale Fabricators'],
        'briefs': [
            'Industrial automation OEM transitioning from founder-led sales to a {reps}-person outbound team.',
            'Component manufacturer pursuing new OEM accounts; reps rely on trade-show leads that go cold quickly.',
            'Equipment maker selling through distributors and direct; wants direct reps focused on expansion accounts.',
        ],
        'pains': [
            'Trade-show leads are never followed up consistently; most go cold within two weeks.',
            'Founder still holds key relationships, and new reps have no account history to work from.',
            'Long engineering-led sales cycles make it hard to know which deals are actually progressing.',
        ],
        'outcomes': [
            'A repeatable outbound process that new reps can run without founder involvement.',
            'Every trade-show lead worked within 48 hours with a clear owner and next step.',
        ],
        'signals': ['Hiring {hires} territory sales managers', 'Exhibiting at an automation trade show',
                    'Opened a second production facility', 'Announced a new product line',
                    'Founder posted about building a sales team', 'Downloaded our outbound playbook'],
        'subjects': ['After the trade show', 'Moving beyond founder-led sales',
                     'How {peer} worked every show lead in 48 hours'],
        'peers': ['an automation OEM', 'a 15-rep industrial sales team'],
    },
    'B2B Software': {
        'companies': ['Syntropy Analytics', 'Clearbrook Software', 'Brightpath Systems', 'Quantra Data',
                      'Signalwise', 'Fieldnote Software', 'Northbeam Apps', 'Tandem Workflow',
                      'Lattice Point Software', 'Driftline Data'],
        'briefs': [
            'SaaS company with {reps} reps adding an outbound motion on top of strong inbound demand.',
            'Analytics platform moving from SMB to mid-market; deal sizes doubling and cycles lengthening.',
            'Workflow vendor rebuilding its SDR team after a reorg; leadership wants consistency fast.',
        ],
        'pains': [
            'Inbound is plateauing, and the new outbound team has no research or sequencing discipline.',
            'Mid-market deals need multi-threading, but reps still single-thread through one champion.',
            'Ramp time for new SDRs is over four months and meeting quality is inconsistent.',
        ],
        'outcomes': [
            'Outbound that reliably adds pipeline alongside inbound, with consistent research on every account.',
            'Multi-threaded mid-market deals and SDR ramp under 60 days.',
        ],
        'signals': ['Hiring {hires} SDRs', 'Raised a Series B', 'Launched a mid-market tier',
                    'New VP of Sales started recently', 'Viewed our pricing page twice this week',
                    'Attended our pipeline-discipline webinar'],
        'subjects': ['Adding outbound on top of inbound', 'Multi-threading mid-market deals',
                     'How {peer} cut SDR ramp in half'],
        'peers': ['a Series B analytics company', 'a 35-rep SaaS sales team'],
    },
    'Construction': {
        'companies': ['Cornerstone Building Group', 'Ridgeline Roofing Supply', 'Bedrock Commercial Services',
                      'Trussworks Construction', 'Overland Equipment Rental', 'Granite State Builders',
                      'Ironwood Site Services', 'Copperline Electrical Supply',
                      'Stonebridge Contractors Supply', 'Millrace Builders'],
        'briefs': [
            'Commercial supplier with {reps} outside reps covering contractors across three states.',
            'Equipment rental company growing its national accounts team; relationships live in reps\' phones.',
            'Building-materials distributor adding inside sales to cover smaller contractors.',
        ],
        'pains': [
            'Account knowledge leaves when reps leave; there is no shared record of contractor relationships.',
            'Bid timelines are tracked in spreadsheets, so follow-ups are missed during busy season.',
            'Inside reps have no prioritized call list, so they work alphabetically.',
        ],
        'outcomes': [
            'Contractor relationships captured in one place with clear next actions per rep.',
            'A daily prioritized call list driven by bid timelines and project signals.',
        ],
        'signals': ['Won a large municipal contract', 'Hiring {hires} inside sales reps', 'Opened a new branch',
                    'Expanding into commercial roofing', 'Posted about CRM adoption challenges',
                    'Attended a construction technology expo'],
        'subjects': ['Contractor follow-ups in busy season', 'An idea for your inside sales team',
                     'How {peer} kept bid follow-ups on track'],
        'peers': ['a regional building-materials distributor', 'a national rental company'],
    },
    'Life Sciences': {
        'companies': ['Auralis Biosciences', 'Helix Path Bio', 'Verdant Genomics', 'Orion Life Sciences',
                      'Clarity Biologics', 'Novis Therapeutics', 'Kestrel BioTherapeutics', 'Lumen Assay Labs',
                      'Pellucid Bioworks', 'Riverstone Genomics'],
        'briefs': [
            'Research-tools company with {reps} reps selling to labs and biotech procurement teams.',
            'CRO business development team pursuing mid-size biotech sponsors; long, relationship-driven cycles.',
            'Lab instruments vendor launching a new platform and building a dedicated hunter team.',
        ],
        'pains': [
            'Scientific buyers ignore generic outreach; reps need context on each lab\'s research focus.',
            'BD pipeline lives in individual inboxes, so leadership cannot forecast sponsor wins.',
            'Launch accounts are not prioritized, and reps spread effort too thin.',
        ],
        'outcomes': [
            'Research-informed outreach that earns replies from scientific buyers.',
            'A shared BD pipeline with stage discipline and a credible sponsor forecast.',
        ],
        'signals': ['Hiring {hires} business development managers', 'Announced a new platform launch',
                    'Received new grant funding', 'Presented at a biotech partnering forum',
                    'New Chief Commercial Officer appointed', 'Expanding lab capacity'],
        'subjects': ['Outreach scientists actually answer', 'Forecasting sponsor wins',
                     'How {peer} prioritized launch accounts'],
        'peers': ['a lab instruments company', 'a mid-size CRO'],
    },
    'Energy & CleanTech': {
        'companies': ['Brightfield Solar', 'Windward Energy Services', 'Gridline Power', 'Voltaic Systems',
                      'Sunvale Renewables', 'Coastal Grid Services', 'Helios Field Services', 'Terravolt Storage',
                      'Kilowatt Commons', 'Brightwater Microgrid'],
        'briefs': [
            'Commercial solar installer with {reps} reps pursuing facilities and property managers.',
            'Energy services firm selling efficiency retrofits; incentive deadlines drive buying windows.',
            'Battery storage company building its first enterprise sales team.',
        ],
        'pains': [
            'Incentive deadlines create urgency, but reps miss the windows because follow-ups are manual.',
            'Property-manager buyers have long approval chains that reps lose track of.',
            'No consistent qualification, so engineers spend time on proposals that never close.',
        ],
        'outcomes': [
            'Follow-ups timed to incentive windows and fewer wasted engineering proposals.',
            'Clear qualification gates before proposals, with visible approval progress per deal.',
        ],
        'signals': ['New state incentive program announced', 'Hiring {hires} commercial sales reps',
                    'Completed a large community-solar project', 'Raised project financing',
                    'Expanding into commercial storage', 'Attended our clean-energy sales webinar'],
        'subjects': ['Timing outreach to incentive windows', 'Qualifying before the proposal',
                     'How {peer} stopped wasting engineering hours'],
        'peers': ['a commercial solar installer', 'an energy-efficiency contractor'],
    },
    'Retail & Consumer': {
        'companies': ['Northstar Retail', 'Maple & Main Retail Group', 'Coastline Outfitters', 'Brightcart Commerce',
                      'Hearthstone Home Goods', 'Peakside Apparel', 'Urban Basket Co', 'Fernway Brands',
                      'Saltmarsh Provisions', 'Goldfinch Goods'],
        'briefs': [
            'Consumer brand with {reps} wholesale reps selling into regional retail chains.',
            'Retail tech company selling to store-operations leaders; outreach is mostly cold email blasts.',
            'Wholesale team expanding from independents into national accounts.',
        ],
        'pains': [
            'Buyer meetings cluster around line reviews, and reps miss the windows to get on calendars.',
            'Cold email blasts produce unsubscribes, not meetings.',
            'National-account deals need multi-department buy-in that reps are not tracking.',
        ],
        'outcomes': [
            'Outreach timed to line-review calendars and more first meetings with buyers.',
            'Account-based outreach with tracked stakeholders for every national account.',
        ],
        'signals': ['Expanding into 40 new store locations', 'Hiring {hires} wholesale account managers',
                    'New Head of Sales from a national brand', 'Launched a private-label line',
                    'Attended a retail technology summit', 'Viewed our case study page'],
        'subjects': ['Timing outreach to line reviews', 'Moving into national accounts',
                     'How {peer} replaced email blasts'],
        'peers': ['a regional consumer brand', 'a retail-ops software company'],
    },
}

SALES_FIT_RATIONALE = [
    'Strong ICP match: {reps} quota-carrying reps on {crm}, with an active outbound motion.',
    'Team size and {crm} footprint fit our sweet spot; leadership is publicly focused on sales efficiency.',
    'Matches our best customers: {size} employees, {reps} reps, and a growing outbound function.',
]
SALES_WHY_NOW = [
    '{signal} — a classic trigger for revisiting sales tooling.',
    '{contact_first} joined recently and is reviewing the sales tech stack.',
    'Budget planning for next half starts soon; {signal_lower} suggests headcount growth.',
]
SALES_ANGLES = [
    'Lead with time saved on account research: reps get a ready brief before every first call.',
    'Frame around forecast confidence: every open deal has a visible next action and owner.',
    'Open with ramp time: new reps inherit full account history instead of starting cold.',
    'Anchor on follow-up discipline: no deal goes dark without an alert.',
]
SALES_ACTIONS = [
    'Send the {industry} benchmark report with a personalized note.',
    'Share a two-minute teardown of their current outbound sequence.',
    'Offer a 20-minute pipeline review using their own deal data.',
]
SALES_QUESTIONS = [
    'How do reps prepare for a first call today, and how long does it take? · Where do deals most often stall between stages?',
    'What happens to account history when a rep leaves? · How does leadership decide which deals to inspect in forecast calls?',
    'How quickly are new reps productive today? · Which signals tell you an account is ready to buy?',
]
SALES_OBJECTIONS = [
    'We just rolled out a sales engagement tool. (Position as complementary: it feeds better context into existing sequences.)',
    'Reps won\'t adopt another tool. (Show the zero-new-tab workflow inside {crm}.)',
    'Budget is locked until next half. (Offer a scoped pilot sized to one team.)',
    'Security review takes months. (Share SOC 2 report and tenant-isolation summary up front.)',
]
SALES_NOTES = [
    'Research: {company} grew headcount roughly 30% over the past year.',
    'Research: sales leadership is active on LinkedIn about pipeline hygiene.',
    'Research: currently uses {crm}; no account-intelligence layer in place.',
    'Research: recent reorg merged SDR and AE teams under one leader.',
]

SALES_REPLIES = {
    'positive': [
        'Timing is good — we\'re rebuilding our outbound process this half. Send over a few times.',
        'This is on our radar. Happy to take a call next week.',
        'Interesting. Let\'s find 30 minutes; I\'ll bring our sales ops lead.',
    ],
    'pricing': [
        'Can you send rough pricing for about {reps} seats before we meet?',
        'What does this cost for a team our size? Need a ballpark for planning.',
    ],
    'referral': [
        'Not my area — looping in {ref}, our {ref_title}.',
        '{ref} owns sales tooling here; copying them.',
    ],
    'later': [
        'Interested, but slammed until month-end. Ping me in two weeks.',
        'Not the right moment — we\'re mid-reorg. Check back after the quarter.',
    ],
}
SALES_TOUCH_EMAIL = [
    'Sequence step {n}: follow-up email to {first} with a short customer story.',
    'Sequence step {n}: shared the {industry} benchmark report with {first}.',
    'Sequence step {n}: bumped the thread with a two-line question about rep ramp.',
    'Sequence step {n}: sent {first} a teardown of their current outreach cadence.',
]
SALES_TOUCH_CALL = [
    'Call to {first}: no answer, left a 30-second voicemail referencing {signal_lower}.',
    'Call to {first}: reached the main line; assistant said to try back later this week.',
    'Call to {first}: connected for four minutes; asked to follow up by email.',
    'Call to {first}: no answer; will try again at a different time of day.',
]
SALES_MEETING_FINDINGS = [
    '{reps} reps, research takes about 25 minutes per account; pain confirmed.',
    'forecast calls run long because deal status lives in rep notes; strong interest from {first}.',
    'ramp time is the top concern; {first} wants to see the new-rep workflow.',
    'reps single-thread most deals; {first} asked for a multi-threading demo.',
]
SALES_DQ_EARLY = [
    'Disqualified: sales team is under five reps, below ICP.',
    'Disqualified: signed a two-year contract with a competitor last month.',
    'Disqualified: no outbound motion and no plans to build one.',
]
SALES_DQ_LATE = [
    'Disqualified after discovery: budget frozen until next fiscal year; moved to nurture.',
    'Closed: chose to extend their incumbent tool for another year.',
    'Disqualified after discovery: the project was deprioritized after a leadership change.',
]
SALES_DARK_AFTER_REPLY = [
    'No response after the initial reply and two follow-ups. Moved to cooldown.',
    'Went dark after the pricing discussion. Revisit next quarter.',
]
SALES_OPP_STEPS = [
    'technical validation with sales ops',
    'pilot scoping for one team',
    'security review and procurement',
    'executive sponsor alignment',
]

# The hero record visitors see first; kept stable for walkthroughs and tests.
SALES_HERO = {
    'company': 'Lumina HealthTech', 'contact': 'Elena Rostova', 'title': 'VP of Revenue Operations',
    'email': 'elena.rostova@luminahealth.example.com', 'phone': '(617) 555-0193',
    'website': 'https://luminahealth.example.com', 'industry': 'HealthTech', 'company_size': '250-500',
    'tech_stack': 'Salesforce · HubSpot · Gong', 'acv': 28500,
    'opportunity_brief': 'Rapidly scaling clinical analytics sales team; looking to unify cross-region pipeline visibility and standardize next-action discipline.',
    'pain_points': 'Reps spend close to half their prospecting time researching hospital systems by hand, and conversion drops sharply after the first meeting.',
    'desired_outcome': 'Automate pre-call account context, preserve deal history across rep turnover, and lift first-meeting conversion.',
    'icp_fit': 'High',
    'intent_signals': 'Hiring 6 enterprise AEs · Series B announced ($35M) · G2 research activity on sales engagement tools',
    'qualification_notes': 'Strong fit on team size and Salesforce footprint. Budget owner identified.',
    'source': 'Account Research', 'priority': 'High',
    'next_action': 'Map clinical tech stack & finalize executive outreach angle',
    'follow_up_status': 'In Research',
    'notes': 'Research hypothesis: rapid hospital-network expansion means new territories and new reps to ramp.',
    'fit_rationale': 'Ideal ICP match with high rep density and an existing Salesforce + Gong stack.',
    'opportunity_rationale': 'Elena joined recently and has announced an overhaul of sales productivity tooling.',
    'suggested_action': 'Reach out with the clinical sales-cycle benchmark study.',
    'suggested_angle': 'Show how standardized account briefs cut pre-call prep for clinical sales teams.',
    'discovery_questions': 'How do enterprise reps prepare account context before clinical discovery calls? · Where do deals stall after the first meeting?',
    'objections': 'Security review concerns about data privacy. (Confirm tenant isolation and SOC 2 alignment.)',
}

# ---------------------------------------------------------------------------
# B2B Services workspace: one independent RevOps & CRM consultant
# (Alex Rivera) selling fixed-fee projects and retainers to SMB/mid-market clients.
# ---------------------------------------------------------------------------

CONSULTANT = 'Alex Rivera'
CONSULTANT_CAPACITY_HOURS = 120  # billable hours per month for one person

B2B_CLIENTS = [  # (company, industry, employees)
    ('Harbor & Pine Dental Group', 'Healthcare Services', 140), ('Redwood Property Management', 'Real Estate', 85),
    ('Clearspring Water Systems', 'Manufacturing', 220), ('Fairway Equipment Rentals', 'Equipment Rental', 160),
    ('Bluebird Home Health', 'Healthcare Services', 310), ('Lakeside Veterinary Partners', 'Healthcare Services', 120),
    ('Northwind Analytics', 'B2B Software', 65), ('Prairie State Insurance Agency', 'Insurance', 45),
    ('Silverline HVAC', 'Home Services', 190), ('Tandem Marketing Co', 'Marketing Agency', 40),
    ('Ostrander Legal Group', 'Professional Services', 75), ('Brightside Learning', 'EdTech', 110),
    ('Cascade Craft Beverages', 'Consumer Goods', 130), ('Meridian Staffing Solutions', 'Staffing', 260),
    ('Pinecrest Senior Living', 'Healthcare Services', 400), ('Vantage Point Engineering', 'Professional Services', 95),
    ('Quarry Lane Builders', 'Construction', 180), ('Helm Street Software', 'B2B Software', 55),
    ('Atlas Fleet Maintenance', 'Transportation', 150), ('Juniper Wellness Clinics', 'Healthcare Services', 90),
    ('Orchard Valley Foods', 'Food Distribution', 240), ('Keel & Compass Travel', 'Travel', 60),
    ('Sablewood Furniture', 'Manufacturing', 170), ('Greenleaf Landscaping', 'Home Services', 120),
    ('Polaris Payroll Services', 'Financial Services', 70), ('Ridgeview Accounting', 'Professional Services', 50),
    ('Copperfield Security', 'Security Services', 210), ('Driftwood Hospitality Group', 'Hospitality', 350),
    ('Lanternfish Media', 'Marketing Agency', 35), ('Summit Ridge Solar', 'Energy', 140),
    ('Westbrook Logistics', 'Transportation', 280), ('Ivory Tower Tutoring', 'EdTech', 45),
    ('Fieldstone Insurance', 'Insurance', 160), ('Marlowe Biotech Supply', 'Life Sciences', 120),
]

B2B_TITLES = ['CEO', 'COO', 'VP of Sales', 'Head of Revenue Operations', 'Director of Sales',
              'Marketing Director', 'Founder & CEO', 'VP of Growth', 'Sales Operations Manager']

B2B_SOURCES = [('Client Referral', 26), ('Past Client', 14), ('LinkedIn Post', 14), ('Website Inquiry', 14),
               ('HubSpot Partner Directory', 10), ('Podcast Guest Appearance', 8), ('Newsletter', 8),
               ('Local Business Meetup', 6)]

# key: (label, value range, months, monthly hours range, tech, briefs, pains, outcomes)
B2B_ENGAGEMENTS = {
    'hubspot_impl': {
        'label': 'HubSpot CRM implementation', 'value': (18000, 34000), 'months': (2, 3), 'hours': (20, 35),
        'tech': 'HubSpot · Google Workspace · Zoom',
        'briefs': ['Moving off spreadsheets and a legacy contact manager onto HubSpot Sales Hub.',
                   'Rolling out HubSpot to a {size}-person team with marketing and sales on one system.'],
        'pains': ['Deals tracked in spreadsheets; no shared view of the pipeline or follow-ups.',
                  'Marketing leads disappear between form fill and first sales call.'],
        'outcomes': ['A configured HubSpot portal with pipelines, automation and reporting the team actually uses.',
                     'Lead routing and follow-up automation live within the quarter.'],
    },
    'sfdc_cleanup': {
        'label': 'Salesforce cleanup & data migration', 'value': (22000, 42000), 'months': (2, 4), 'hours': (25, 40),
        'tech': 'Salesforce · Outreach · Slack',
        'briefs': ['Years of Salesforce customization have made the org slow and the data unreliable.',
                   'Merging two Salesforce orgs after an acquisition.'],
        'pains': ['Duplicate accounts and abandoned fields make every report suspect.',
                  'Reps work around the CRM because required fields block them.'],
        'outcomes': ['A clean, deduplicated org with a documented data model.',
                     'One trusted Salesforce instance and a dashboard leadership believes.'],
    },
    'revops_audit': {
        'label': 'RevOps audit & roadmap', 'value': (12000, 19000), 'months': (1, 2), 'hours': (20, 30),
        'tech': 'HubSpot · Gong · Notion',
        'briefs': ['Leadership wants an outside assessment of the revenue process before hiring a RevOps lead.',
                   'Growth stalled for two quarters; the CEO wants a prioritized fix list.'],
        'pains': ['No one owns the funnel end to end; marketing and sales blame each other.',
                  'Lots of tools, little adoption, and no single source of truth.'],
        'outcomes': ['A prioritized 90-day roadmap with owners and quick wins.',
                     'A clear picture of where revenue leaks and what to fix first.'],
    },
    'sales_process': {
        'label': 'Sales process & stage design', 'value': (14000, 24000), 'months': (2, 2), 'hours': (20, 30),
        'tech': 'Pipedrive · Google Workspace · Calendly',
        'briefs': ['Founder-led sales is becoming a team; stages and exit criteria need definition.',
                   'Each rep runs deals differently; the forecast is a gut call.'],
        'pains': ['No exit criteria, so deals sit in "proposal" for months.',
                  'New reps have no playbook and ramp slowly.'],
        'outcomes': ['Documented stages, exit criteria and a rep playbook.',
                     'A forecast based on stage evidence, not optimism.'],
    },
    'forecast_dash': {
        'label': 'Pipeline & forecast dashboard build', 'value': (14000, 26000), 'months': (2, 2), 'hours': (20, 30),
        'tech': 'Salesforce · Looker Studio · Slack',
        'briefs': ['Board reporting takes days of spreadsheet work every month.',
                   'Leadership wants weekly pipeline visibility without asking reps.'],
        'pains': ['Monthly board prep takes the CFO two full days.',
                  'Forecast misses by 20% or more, quarter after quarter.'],
        'outcomes': ['Automated pipeline and forecast dashboards refreshed daily.',
                     'Board-ready metrics in minutes instead of days.'],
    },
    'fractional': {
        'label': 'Fractional RevOps retainer', 'value': (36000, 54000), 'months': (6, 6), 'hours': (24, 32),
        'tech': 'HubSpot · Salesforce · Zapier',
        'briefs': ['Needs ongoing RevOps leadership but is not ready for a full-time hire.',
                   'Previous RevOps manager left; systems are drifting without an owner.'],
        'pains': ['Ops requests pile up with no owner; reps build their own workarounds.',
                  'Every tool change breaks something nobody notices for weeks.'],
        'outcomes': ['A part-time RevOps owner for six months, plus a hiring plan for the full-time role.',
                     'Stable systems, a request queue and monthly reporting.'],
    },
    'marketing_auto': {
        'label': 'Marketing automation setup', 'value': (15000, 27000), 'months': (2, 3), 'hours': (20, 30),
        'tech': 'HubSpot Marketing Hub · WordPress · Canva',
        'briefs': ['Building nurture programs and lead scoring from scratch.',
                   'Email marketing runs from a newsletter tool with no CRM connection.'],
        'pains': ['Leads are never nurtured; sales only calls the hottest few.',
                  'Marketing cannot show which campaigns produce pipeline.'],
        'outcomes': ['Nurture sequences, lead scoring and campaign attribution in place.',
                     'Marketing-sourced pipeline reported monthly.'],
    },
    'comp_territory': {
        'label': 'Commission plan & territory design', 'value': (12000, 21000), 'months': (1, 2), 'hours': (15, 25),
        'tech': 'Salesforce · Excel · Slack',
        'briefs': ['Sales team doubled this year; territories and comp plans no longer make sense.',
                   'Reps are fighting over accounts and leadership wants a fair, simple plan.'],
        'pains': ['Comp disputes take hours of leadership time every month.',
                  'Territories are uneven, so top reps are capped and others starve.'],
        'outcomes': ['Balanced territories and a comp plan reps understand on one page.',
                     'Fewer disputes and a plan modeled against next year\'s targets.'],
    },
}

B2B_INTRO_FINDINGS = [
    'budget earmarked for this quarter; decision by {first} with CEO sign-off',
    'pain is real but timeline is loose; {first} wants a rough scope first',
    'previous consultant left the project half-done; wants a clear plan',
    'needs results before their next board meeting',
]
B2B_LOST_EARLY = [
    'Closed lost: scope too small for an engagement; sent a free checklist instead.',
    'Closed lost: decided to handle it in-house with a new hire.',
    'Closed lost: no budget this year; will revisit.',
]
B2B_LOST_LATE = [
    'Closed lost: chose a larger agency with a bundled offering.',
    'Closed lost: project postponed after a leadership change.',
    'Closed lost: budget reallocated to hiring.',
]
B2B_NEGOTIATION_ASKS = [
    'asked to phase the work across two quarters',
    'asked for a smaller first phase to prove value',
    'wants to add a training session for the sales team',
    'requested net-45 payment terms',
]

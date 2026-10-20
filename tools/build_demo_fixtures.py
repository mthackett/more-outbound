"""Generate rich, realistic synthetic demo fixtures and configuration files for More Outbound."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.domain.models import PipelineInstanceConfig
from pipeline.domain.records import PipelineRecord, validate_fields
from pipeline.adapters.secondary.memory_records import MemoryRecordStorage
from pipeline.domain.outreach_metrics import calculate_metrics, historical_cohorts

# Common Dates (relative to October 2026)
DATE_OVERDUE = "2026-10-16"
DATE_TODAY = "2026-10-19"
DATE_SOON = "2026-10-21"
DATE_LATER = "2026-10-24"

SALES_PROSPECTS_DATA = [
    # 1-4: Identified
    {
        "company": "Lumina HealthTech", "contact": "Elena Rostova", "title": "VP of Revenue Operations",
        "email": "elena.rostova@luminahealth.com", "website": "https://luminahealth.com",
        "industry": "HealthTech", "company_size": "250-500", "tech_stack": "Salesforce · HubSpot · Gong",
        "opportunity_brief": "Rapidly scaling clinical analytics sales team; looking to unify cross-region pipeline visibility and standardize next-action discipline.",
        "pain_points": "SDRs spend 45% of their working hours manually researching hospital systems; significant conversion drop-off after Stage 1.",
        "desired_outcome": "Automate rep account context prep, preserve deal history across rep turnover, and double SDR conversion rates.",
        "icp_fit": "High", "intent_signals": "Hiring 6 enterprise AEs · Series B announced ($35M) · G2 Crowd surge in CRM reviews",
        "qualification_notes": "Confirmed high fit against ICP employee size and Salesforce CRM presence. Budget authority in place.",
        "opportunity_owner": "Sarah Jenkins", "source": "Account Research", "priority": "High",
        "next_action": "Map clinical tech stack & finalize executive outreach angle",
        "next_action_date": DATE_SOON, "follow_up_status": "Pre-outreach",
        "notes": "Research hypothesis: Rapid hospital network expansion requires HIPAA-compliant workflow messaging.",
        "fit_rationale": "Perfect ICP match with high rep density and existing Salesforce infrastructure.",
        "opportunity_rationale": "Elena joined 60 days ago and announced an overhaul of sales productivity tools for Q4.",
        "suggested_action": "Reach out with executive benchmarking study on clinical sales cycle velocity.",
        "suggested_angle": "Showcase how standardized account briefs accelerate pre-call context prep for clinical sales targets.",
        "discovery_questions": "How do your enterprise reps currently prepare account context before clinical discovery calls?",
        "objections": "Security review concerns regarding data privacy (confirm strict tenant isolation and SOC 2 alignment)."
    },
    {
        "company": "Veloce Logistics", "contact": "Marcus Vance", "title": "Director of Sales Enablement",
        "email": "m.vance@velocelogistics.com", "website": "https://velocelogistics.com",
        "industry": "Supply Chain & Logistics", "company_size": "500-1000", "tech_stack": "Salesforce · Outreach · Snowflake",
        "opportunity_brief": "Freight brokerage expanding cold outbound into mid-market shippers across the Midwest.",
        "pain_points": "High broker turnover causing lost account intelligence and dropped follow-ups with major manufacturers.",
        "desired_outcome": "Preserve account intelligence systematically and decrease new broker ramp time by 30%.",
        "icp_fit": "High", "intent_signals": "Expanding freight broker team with 8 open listings in Chicago and Dallas",
        "qualification_notes": "High outbound transaction volume; strong management commitment to sales process.",
        "opportunity_owner": "Sarah Jenkins", "source": "LinkedIn Sales Nav", "priority": "High",
        "next_action": "Identify second champion in Regional Brokerage Management",
        "next_action_date": DATE_SOON, "follow_up_status": "In Research",
        "notes": "Freight brokers require rapid speed-to-lead and clear visual indicators for overdue actions.",
        "fit_rationale": "High volume outbound with clear operational friction in rep turnover.",
        "opportunity_rationale": "Expanding outbound team means immediate need for structured workflows.",
        "suggested_action": "Connect on LinkedIn with freight shipper intelligence angle.",
        "suggested_angle": "Showcase how rep ramp time dropped 35% in logistics sales teams.",
        "discovery_questions": "What happens to account notes when a mid-market rep leaves the team?",
        "objections": "We already use a sequencer (clarify how pipeline intelligence organizes account context before execution)."
    },
    {
        "company": "Beacon Robotics", "contact": "Priya Patel", "title": "Head of Commercial Strategy",
        "email": "p.patel@beaconrobotics.com", "website": "https://beaconrobotics.com",
        "industry": "Industrial Automation", "company_size": "100-250", "tech_stack": "HubSpot · Apollo · Notion",
        "opportunity_brief": "Warehouse robotics OEM transitioning from founder-led sales to dedicated outbound team.",
        "pain_points": "Engineers conducting discovery without standardized qualification criteria.",
        "desired_outcome": "Establish structured qualification frameworks and clear buyer stage gates.",
        "icp_fit": "Medium", "intent_signals": "Launched next-gen autonomous pallet jack at MODEX 2026",
        "qualification_notes": "Early sales motion maturity but healthy hardware+SaaS ACV margins.",
        "opportunity_owner": "Alex Rivera", "source": "Industry Conference", "priority": "Medium",
        "next_action": "Review conference presentation recording & verify commercial timeline",
        "next_action_date": DATE_LATER, "follow_up_status": "Pre-outreach",
        "notes": "Priya attended our booth session on manufacturing pipeline metrics.",
        "fit_rationale": "Growing contract sizes and desire to transition from ad-hoc sales to scalable outbound.",
        "opportunity_rationale": "Product launch creates urgency to generate pipeline for Q1 board targets.",
        "suggested_action": "Send personalized note referencing MODEX keynote topic.",
        "suggested_angle": "Bridge the gap between engineering specifications and C-level ROI value.",
        "discovery_questions": "How is your team currently prioritizing manufacturing plant accounts?",
        "objections": "Our sales cycle is 9 months (emphasize multi-touch intelligence preservation)."
    },
    {
        "company": "Syntropy Analytics", "contact": "David Sterling", "title": "VP of Customer Growth",
        "email": "dsterling@syntropyanalytics.com", "website": "https://syntropyanalytics.com",
        "industry": "Enterprise Software", "company_size": "250-500", "tech_stack": "Salesforce · Marketo · BigQuery",
        "opportunity_brief": "Data observability vendor aiming to identify cross-sell opportunities in Fortune 500 accounts.",
        "pain_points": "Account data siloed between customer success telemetry and sales CRM records.",
        "desired_outcome": "Unified account intelligence surfacing optimal expansion moments.",
        "icp_fit": "Medium", "intent_signals": "G2 Crowd High Performer badge · Acquired telemetry startup",
        "qualification_notes": "Enterprise customer base; high potential expansion ACV.",
        "opportunity_owner": "Alex Rivera", "source": "Partner Referral", "priority": "Medium",
        "next_action": "Map customer success leadership stakeholders",
        "next_action_date": DATE_LATER, "follow_up_status": "Research",
        "notes": "Partner noted that David is looking to revamp outbound playbooks.",
        "fit_rationale": "High ACV potential and sophisticated data infrastructure.",
        "opportunity_rationale": "Recent acquisition requires unified account strategy across both product lines.",
        "suggested_action": "Share cross-sell pipeline intelligence case study.",
        "suggested_angle": "Surfacing buying signals from product usage to trigger timely AE follow-ups.",
        "discovery_questions": "How quickly do AEs learn about sudden usage spikes in trial accounts?",
        "objections": "Internal BI team is building this (highlight 6-month delay vs turnkey solution)."
    },

    # 5-7: Qualified
    {
        "company": "Kestrel Cyber", "contact": "Amara Okafor", "title": "VP of Enterprise Sales",
        "email": "amara.okafor@kestrelcyber.com", "website": "https://kestrelcyber.com",
        "industry": "Cybersecurity", "company_size": "500-1000", "tech_stack": "Salesforce · Gong · ZoomInfo",
        "opportunity_brief": "Cloud security vendor with 20 SDRs struggling with message personalization at scale.",
        "pain_points": "Cold email reply rates dropped below 1.5% due to generic outreach copy.",
        "desired_outcome": "Boost reply rates to 4%+ with account-specific intent signals.",
        "icp_fit": "High", "intent_signals": "New CISO advisory board formed · Expansion into EMEA",
        "qualification_notes": "Budget confirmed for sales tooling upgrade in Q4 budget review.",
        "opportunity_owner": "Sarah Jenkins", "source": "Outbound Email", "priority": "High",
        "next_action": "Prepare customized security value thesis & draft sequence",
        "next_action_date": DATE_TODAY, "follow_up_status": "Qualified",
        "notes": "Amara confirmed during pre-qualification email exchange that personalization is her #1 priority.",
        "fit_rationale": "Exact ICP: B2B security SaaS, 20+ SDRs, established Salesforce setup.",
        "opportunity_rationale": "Urgent board pressure to increase outbound pipeline coverage to 3.5x.",
        "suggested_action": "Send teaser showing 3 specific security buying triggers for their top tier accounts.",
        "suggested_angle": "Show how contextual discovery prompts eliminate generic 'checking in' emails.",
        "discovery_questions": "What percentage of rep outreach is customized to specific breach risk signals?",
        "objections": "Our reps use ChatGPT (clarify that pipeline intelligence connects structured account data to workflow)."
    },
    {
        "company": "Crestline Financial", "contact": "Julian Weber", "title": "Managing Director, Advisory Sales",
        "email": "jweber@crestlinefin.com", "website": "https://crestlinefin.com",
        "industry": "Fintech & WealthTech", "company_size": "1000+", "tech_stack": "Microsoft Dynamics · Seismic · Bloomberg",
        "opportunity_brief": "Institutional advisory firm modernizing family office outreach workflows.",
        "pain_points": "Highly manual prospect tracking in spreadsheets; lack of next-action discipline across partners.",
        "desired_outcome": "Centralized deal progression tracking with strict follow-up alerts.",
        "icp_fit": "High", "intent_signals": "Announced $200M alternative assets fund closure",
        "qualification_notes": "Strict compliance environment; requires clear data residency and audit trails.",
        "opportunity_owner": "Sarah Jenkins", "source": "Executive Network", "priority": "High",
        "next_action": "Send security overview whitepaper and schedule technical review",
        "next_action_date": DATE_SOON, "follow_up_status": "Qualified",
        "notes": "Julian confirmed family office team needs structured next action tracking without complex CRM overhead.",
        "fit_rationale": "High contract value and urgent need for structured deal tracking.",
        "opportunity_rationale": "New fund launch demands systematic institutional LP outreach.",
        "suggested_action": "Follow up with compliance-friendly workflow overview.",
        "suggested_angle": "Highlight auditability and streamlined activity history.",
        "discovery_questions": "How do partners ensure critical investor follow-ups aren't dropped?",
        "objections": "Compliance restrictions on cloud tools (highlight offline sandbox capabilities)."
    },
    {
        "company": "Meridian Cloud", "contact": "Chloe Zhao", "title": "Director of GTM Operations",
        "email": "chloe.zhao@meridiancloud.com", "website": "https://meridiancloud.com",
        "industry": "Cloud Infrastructure", "company_size": "250-500", "tech_stack": "Salesforce · HubSpot · Mixmax",
        "opportunity_brief": "Multi-cloud optimization provider accelerating mid-market outbound pipeline.",
        "pain_points": "AEs and SDRs out of sync on target account qualification rules.",
        "desired_outcome": "Shared pipeline stage definitions and clear qualification gates.",
        "icp_fit": "High", "intent_signals": "Competitor pricing change driving cloud cost migration inquiries",
        "qualification_notes": "GTM leadership aligned on standardizing stage milestones.",
        "opportunity_owner": "Alex Rivera", "source": "Webinar Attendee", "priority": "Medium",
        "next_action": "Deliver pipeline stage criteria template for GTM review",
        "next_action_date": DATE_LATER, "follow_up_status": "Qualified",
        "notes": "Chloe attended webinar on 'Conversion Funnel Diagnostics'.",
        "fit_rationale": "Fast-growing GTM team with clear operational bottlenecks.",
        "opportunity_rationale": "Upcoming fiscal year kickoff makes November ideal for piloting new workflow.",
        "suggested_action": "Share interactive pipeline stage distribution model.",
        "suggested_angle": "Demonstrate conversion leak prevention across SDR-to-AE handoffs.",
        "discovery_questions": "What percentage of SDR-booked meetings get rejected by AEs during discovery?",
        "objections": "Busy with Q4 closing (offer a lightweight 14-day trial for 2 pilot reps)."
    },

    # 8-10: Ready for Outreach (Scenario 1: High-fit prospect ready for first outreach)
    {
        "company": "Octave Media", "contact": "Lucas Moreau", "title": "VP of Brand Partnerships",
        "email": "lmoreau@octavemedia.com", "website": "https://octavemedia.com",
        "industry": "AdTech & Digital Media", "company_size": "100-250", "tech_stack": "HubSpot · SalesLoft · Datanyze",
        "opportunity_brief": "High-growth creator media agency seeking enterprise brand sponsors.",
        "pain_points": "Outreach lacks brand-specific campaign context; low response from Fortune 500 CMOs.",
        "desired_outcome": "Equip partnership reps with company-specific cultural and advertising hooks.",
        "icp_fit": "High", "intent_signals": "Signed 5 top-tier podcast creators · Expanded NY sales office",
        "qualification_notes": "All initial qualification criteria verified. Ready for bespoke executive outreach.",
        "opportunity_owner": "Sarah Jenkins", "source": "Account Research", "priority": "High",
        "next_action": "Launch Step 1 personalized email with creator demographic brief",
        "next_action_date": DATE_TODAY, "follow_up_status": "Ready for Sequence",
        "notes": "High-fit prospect ready for first outreach. Outreach angle tailored to Q4 holiday ad budget cycle.",
        "fit_rationale": "High urgency before Q4 budget lock; strong product-market fit.",
        "opportunity_rationale": "Expanding NY sales office signals aggressive outreach goals.",
        "suggested_action": "Execute Step 1 cold email with tailored audience overlap metrics.",
        "suggested_angle": "Highlighting how personalized brand briefs cut outreach cycles by 40%.",
        "discovery_questions": "How do your reps tailor media kit data to specific brand goals?",
        "objections": "Brand budgets already committed for 2026 (position for Q1 2027 planning)."
    },
    {
        "company": "Highline Energy", "contact": "Karin Lindholm", "title": "Head of Commercial Sales",
        "email": "karin.lindholm@highlineenergy.com", "website": "https://highlineenergy.com",
        "industry": "CleanTech & Energy", "company_size": "500-1000", "tech_stack": "Salesforce · LinkedIn Sales Nav · Marketo",
        "opportunity_brief": "Commercial solar & battery storage provider targeting industrial facility managers.",
        "pain_points": "Long qualification cycles; reps fail to surface utility tariff signals early.",
        "desired_outcome": "Qualify energy efficiency opportunities faster with localized power pricing context.",
        "icp_fit": "High", "intent_signals": "Federal clean energy grant recipient · Hiring commercial developers",
        "qualification_notes": "Target account list finalized. High priority for Northeast manufacturing corridor.",
        "opportunity_owner": "Sarah Jenkins", "source": "CleanTech Expo", "priority": "High",
        "next_action": "Send personalized outreach referencing regional electricity rate hikes",
        "next_action_date": DATE_SOON, "follow_up_status": "Ready for Sequence",
        "notes": "Karin spoke on commercial decarbonization panel last month. Key focus: ROI payback speed.",
        "fit_rationale": "Large average deal size ($100k+ ACV) with complex multi-stakeholder approval.",
        "opportunity_rationale": "Regional tariff hikes create external trigger for facility managers to review proposals.",
        "suggested_action": "Send personalized email with tariff impact calculator.",
        "suggested_angle": "Showcase how account intelligence surfaces facility power constraints.",
        "discovery_questions": "What data points do your reps use to identify facilities with high demand charges?",
        "objections": "Municipal approvals take too long (focus on early pipeline velocity)."
    },
    {
        "company": "Polaris Supply", "contact": "Gabriel Santos", "title": "VP of Revenue",
        "email": "gsantos@polarissupply.com", "website": "https://polarissupply.com",
        "industry": "Logistics & Procurement", "company_size": "250-500", "tech_stack": "HubSpot · ZoomInfo · Slack",
        "opportunity_brief": "B2B wholesale distributor building outbound sales team from scratch.",
        "pain_points": "Relying on inbound word-of-mouth; no structured outbound cadence or playbooks.",
        "desired_outcome": "Deploy an end-to-end outbound prospecting engine with clear daily next actions.",
        "icp_fit": "High", "intent_signals": "New CEO mandate for 30% YoY revenue expansion",
        "qualification_notes": "Greenfield opportunity; high openness to workflow best practices.",
        "opportunity_owner": "Alex Rivera", "source": "CEO Network", "priority": "High",
        "next_action": "Send CEO peer benchmark letter & outbound maturity model",
        "next_action_date": DATE_SOON, "follow_up_status": "Ready for Sequence",
        "notes": "Gabriel joined from a tech-forward distributor; understands value of structured pipeline management.",
        "fit_rationale": "Greenfield outbound buildout represents ideal deployment timing.",
        "opportunity_rationale": "CEO mandate provides executive sponsorship and dedicated budget.",
        "suggested_action": "Send maturity benchmark showing typical 90-day outbound ramp.",
        "suggested_angle": "Focus on turnkey structure: who to contact, why, and what to say next.",
        "discovery_questions": "What tools are your new outbound hires currently using to organize their daily accounts?",
        "objections": "Want to hire the reps first (explain that systems should be ready before Day 1)."
    },

    # 11-20: Contacted (Scenario 2: Awaiting reply; Scenario 6: Requiring follow-up)
    {
        "company": "Aura Biosciences", "contact": "Dr. Aris Thorne", "title": "Chief Commercial Officer",
        "email": "athorne@aurabio.com", "website": "https://aurabio.com",
        "industry": "Biotech & Pharma", "company_size": "100-250", "tech_stack": "Veeva CRM · HubSpot",
        "opportunity_brief": "Pre-clinical genomics lab scaling commercial partnerships with research universities.",
        "pain_points": "Complex technical selling requirements; reps lack structured discovery question prompts.",
        "desired_outcome": "Equip sales scientists with structured discovery guides and objection handling cues.",
        "icp_fit": "High", "intent_signals": "Phase II trial milestone announced · Expanded lab facilities",
        "qualification_notes": "Specialized market; high ACV potential.",
        "opportunity_owner": "Sarah Jenkins", "source": "BioTech Forum", "priority": "High",
        "next_action": "Send follow-up #2 with genomics commercialization whitepaper",
        "next_action_date": DATE_OVERDUE, "follow_up_status": "Touch 2 Due (Overdue)",
        "notes": "Step 1 cold email sent Oct 12 referencing university partnership model. No response yet.",
        "fit_rationale": "High-value science sales with deep need for consultative discovery prompts.",
        "opportunity_rationale": "Commercial team expanding ahead of clinical trial data publication.",
        "suggested_action": "Send short follow-up pointing to Page 3 of the lab economics benchmark.",
        "suggested_angle": "Helping scientific AEs uncover hidden department grant deadlines.",
        "discovery_questions": "How do your account managers track university grant renewal cycles?",
        "objections": "Our sales reps are PhDs and don't like scripts (explain prompt cues vs rigid scripts)."
    },
    {
        "company": "Northstar Retail", "contact": "Siddharth Nair", "title": "VP of Omnichannel Systems",
        "email": "snair@northstarretail.com", "website": "https://northstarretail.com",
        "industry": "Retail & E-commerce", "company_size": "1000+", "tech_stack": "Salesforce · Shopify Plus · Segment",
        "opportunity_brief": "Regional department store chain modernizing B2B corporate gifting and wholesale division.",
        "pain_points": "Corporate gifting pipeline fragmented between retail POS and regional corporate reps.",
        "desired_outcome": "Consolidate corporate accounts and streamline seasonal quote turnaround.",
        "icp_fit": "Medium", "intent_signals": "Launching unified B2B corporate gifting portal for Q4",
        "qualification_notes": "Strong seasonal revenue spike; requires fast implementation.",
        "opportunity_owner": "Alex Rivera", "source": "Retail Tech Summit", "priority": "Medium",
        "next_action": "Deliver corporate holiday catalog workflow teardown",
        "next_action_date": DATE_OVERDUE, "follow_up_status": "Touch 2 Due (Overdue)",
        "notes": "Sent introductory note on Oct 13. Awaiting reply on procurement committee timeline.",
        "fit_rationale": "Opportunity to capture enterprise holiday spend before early November cutoff.",
        "opportunity_rationale": "Corporate portal launch makes this high priority for Siddharth's team.",
        "suggested_action": "Follow up with quick 2-minute video walkthrough of quotation acceleration.",
        "suggested_angle": "Cutting quote turnaround from 4 days to 4 hours during peak holiday weeks.",
        "discovery_questions": "What is the average turnaround time for custom enterprise gifting quotes?",
        "objections": "Too busy with holiday retail rush (emphasize minimal rep setup effort)."
    },
    {
        "company": "Kinetic Commerce", "contact": "Tasha Robinson", "title": "Head of Merchant Sales",
        "email": "trobinson@kineticcommerce.com", "website": "https://kineticcommerce.com",
        "industry": "Fintech & Payments", "company_size": "250-500", "tech_stack": "Salesforce · Gong · SalesLoft",
        "opportunity_brief": "Point-of-sale payment processor prospecting independent retail hospitality groups.",
        "pain_points": "High cold call resistance from restaurant owners; need multi-touch signal-driven outreach.",
        "desired_outcome": "Equip reps with local food & beverage permits data and seasonal expansion triggers.",
        "icp_fit": "High", "intent_signals": "Announced zero-fee processing promotion for new hospitality merchants",
        "qualification_notes": "15 inside SDRs dedicated to restaurant prospecting.",
        "opportunity_owner": "Sarah Jenkins", "source": "Outbound Campaign", "priority": "High",
        "next_action": "Send follow-up with hospitality permit intelligence workflow",
        "next_action_date": DATE_TODAY, "follow_up_status": "Touch 2 Due",
        "notes": "Touch 1 sent Oct 14. Opened twice according to email signals. Ready for value-add follow-up.",
        "fit_rationale": "High-velocity outbound team looking for incremental conversion bumps.",
        "opportunity_rationale": "Zero-fee promotion gives reps strong headline offer, but targeting needs precision.",
        "suggested_action": "Follow up referencing the promotional launch with target account filters.",
        "suggested_angle": "Targeting hospitality owners right after liquor license transfers.",
        "discovery_questions": "How do reps verify whether a new restaurant venue is open before dialing?",
        "objections": "Interchange rates are commoditized (highlight intelligence-led differentiation)."
    },
    {
        "company": "Zephyr Bio", "contact": "Matthias Bauer", "title": "Director of Commercial Operations",
        "email": "mbauer@zephyrbio.com", "website": "https://zephyrbio.com",
        "industry": "MedTech", "company_size": "100-250", "tech_stack": "HubSpot · ZoomInfo · Asana",
        "opportunity_brief": "Surgical optics manufacturer expanding hospital procurement outreach.",
        "pain_points": "Value analysis committees reject proposals due to insufficient clinical economic data.",
        "desired_outcome": "Standardize economic impact summaries for hospital purchasing committees.",
        "icp_fit": "Medium", "intent_signals": "FDA 510(k) clearance granted for flagship 3D endoscope",
        "qualification_notes": "Niche surgical device market; long buying cycles but high gross margins.",
        "opportunity_owner": "Alex Rivera", "source": "Industry Directory", "priority": "Medium",
        "next_action": "Send follow-up highlighting hospital value analysis committee playbook",
        "next_action_date": DATE_SOON, "follow_up_status": "Follow-up Scheduled",
        "notes": "Sent introductory package Oct 15. Matthias opened attachment.",
        "fit_rationale": "Strong fit for deal room and value brief features.",
        "opportunity_rationale": "510(k) clearance provides immediate green light for hospital commercialization.",
        "suggested_action": "Send value analysis committee briefing template.",
        "suggested_angle": "Helping clinical reps address hospital CFO scrutiny earlier in the cycle.",
        "discovery_questions": "At what stage does the hospital purchasing committee typically get involved?",
        "objections": "Hospital contracts are closed via GPO distributors (focus on clinical champion pull-through)."
    },
    {
        "company": "Granite Data", "contact": "Hannah Berg", "title": "VP of Global Outbound",
        "email": "hberg@granitedata.com", "website": "https://granitedata.com",
        "industry": "Data & Cloud Infrastructure", "company_size": "500-1000", "tech_stack": "Salesforce · Outreach · Snowflake",
        "opportunity_brief": "Database migration tooling firm targeting legacy on-premise Oracle installations.",
        "pain_points": "Reps struggle to identify which enterprise accounts are actively planning cloud migrations.",
        "desired_outcome": "Surface cloud modernization intent signals and orchestrate targeted multi-threaded outreach.",
        "icp_fit": "High", "intent_signals": "Partnered with AWS Database Migration Service · 4 new AE openings",
        "qualification_notes": "Well-funded; 30+ SDRs and AEs actively running outbound.",
        "opportunity_owner": "Sarah Jenkins", "source": "Cloud Summit", "priority": "High",
        "next_action": "Call follow-up after initial email touchpoint",
        "next_action_date": DATE_SOON, "follow_up_status": "Call Scheduled",
        "notes": "Initial email sent Oct 15 highlighting Oracle-to-Postgres migration triggers.",
        "fit_rationale": "Ideal scale for outbound intelligence and multi-threading workflows.",
        "opportunity_rationale": "AWS partnership requires Granite to generate 50 qualified co-sell leads this quarter.",
        "suggested_action": "Call Hannah's office phone with short executive value pitch.",
        "suggested_angle": "How to map IT architects and database admins across target Fortune 1000s.",
        "discovery_questions": "How do reps multi-thread into database teams beyond the VP of Infrastructure?",
        "objections": "We have an internal research team (highlight speed and real-time trigger updates)."
    },
    {
        "company": "Cobalt Security", "contact": "Devon Miller", "title": "Head of Sales Development",
        "email": "dmiller@cobaltsec.com", "website": "https://cobaltsec.com",
        "industry": "Cybersecurity", "company_size": "250-500", "tech_stack": "HubSpot · Apollo · Gong",
        "opportunity_brief": "Managed detection and response (MDR) provider expanding into regional banking sector.",
        "pain_points": "Community banks ignore generic cybersecurity pitches; require regulatory compliance angles.",
        "desired_outcome": "Tailor outreach angles to FDIC and GLBA cybersecurity exam requirements.",
        "icp_fit": "High", "intent_signals": "New regulatory audit deadlines announced by banking regulators",
        "qualification_notes": "Inside sales team focused purely on financial institutions.",
        "opportunity_owner": "Alex Rivera", "source": "Webinar Lead", "priority": "High",
        "next_action": "Send FDIC compliance discovery questions cheat sheet",
        "next_action_date": DATE_SOON, "follow_up_status": "In Sequence",
        "notes": "Devon registered for cybersecurity webinar. Initial email sent Oct 16.",
        "fit_rationale": "Vertical-specific outbound where customized discovery questions drive conversions.",
        "opportunity_rationale": "Upcoming audit deadlines create natural urgency for bank CISOs.",
        "suggested_action": "Send follow-up highlighting specific FDIC audit question prompts.",
        "suggested_angle": "Equipping reps to sound like compliance consultants rather than software vendors.",
        "discovery_questions": "How do your SDRs position MDR against in-house security teams?",
        "objections": "Bank IT leaders are hard to reach by phone (share multi-channel LinkedIn playbook)."
    },
    {
        "company": "Silverline Systems", "contact": "Craig Sterling", "title": "VP of Revenue Strategy",
        "email": "c.sterling@silverlinesys.com", "website": "https://silverlinesys.com",
        "industry": "Industrial Software", "company_size": "100-250", "tech_stack": "Salesforce · HubSpot",
        "opportunity_brief": "Field service management software provider targeting commercial HVAC contractors.",
        "pain_points": "Contractor owners operate in the field and rarely open standard corporate marketing emails.",
        "desired_outcome": "Design concise mobile-friendly outreach briefs and SMS follow-up prompts.",
        "icp_fit": "Medium", "intent_signals": "Integrating with major HVAC equipment telematics platforms",
        "qualification_notes": "Mid-market contractor focus; straightforward qualification model.",
        "opportunity_owner": "Alex Rivera", "source": "HVAC Trade Show", "priority": "Medium",
        "next_action": "Follow up with trade show demo attendees",
        "next_action_date": DATE_LATER, "follow_up_status": "Awaiting Response",
        "notes": "Spoke briefly with Craig at trade show. Sent summary email on Oct 16.",
        "fit_rationale": "High-velocity field sales where next actions must be executed quickly.",
        "opportunity_rationale": "Equipment telematics integration provides compelling new hook for commercial contractors.",
        "suggested_action": "Send mobile-optimized 3-point briefing.",
        "suggested_angle": "Short, bulleted value proposition: reducing unbilled technician overtime.",
        "discovery_questions": "How do reps contact contractor owners who are rarely in the office?",
        "objections": "Contractors are low-tech (reassure that workflows are dead simple)."
    },
    {
        "company": "Ironclad Logistics", "contact": "Rachel Kim", "title": "Director of National Accounts",
        "email": "rkim@ironcladlogistics.com", "website": "https://ironcladlogistics.com",
        "industry": "Transportation", "company_size": "500-1000", "tech_stack": "Salesforce · SalesLoft",
        "opportunity_brief": "Dedicated fleet carrier looking to win multi-year retail distribution contracts.",
        "pain_points": "RFPs arriving unannounced with short turnaround windows; reps lack account background.",
        "desired_outcome": "Build proactive account intelligence on enterprise shippers 6 months before RFP releases.",
        "icp_fit": "High", "intent_signals": "Acquired 150 refrigerated trailers to expand cold chain fleet",
        "qualification_notes": "High ACV multi-year logistics contracts.",
        "opportunity_owner": "Sarah Jenkins", "source": "Logistics Review", "priority": "High",
        "next_action": "Deliver pre-RFP enterprise shipper briefing document",
        "next_action_date": DATE_LATER, "follow_up_status": "In Sequence",
        "notes": "Step 1 outbound sent Oct 16. Rachel reviewed email and clicked on cold chain case study.",
        "fit_rationale": "Large enterprise deals where relationship context wins multi-million dollar contracts.",
        "opportunity_rationale": "Refrigerated trailer expansion requires immediate capacity utilization.",
        "suggested_action": "Follow up with cold chain shipper target list.",
        "suggested_angle": "Positioning carrier capacity ahead of seasonal produce harvest.",
        "discovery_questions": "How far in advance do your reps begin relationship building before RFP dates?",
        "objections": "Rates are dictated by shipper procurement portals (focus on contract lane commitments)."
    },
    {
        "company": "Horizon Defense", "contact": "Col. Frank Baxter (Ret.)", "title": "VP of Government Business",
        "email": "fbaxter@horizondefense.com", "website": "https://horizondefense.com",
        "industry": "Aerospace & Defense", "company_size": "250-500", "tech_stack": "Microsoft Dynamics · Deltek",
        "opportunity_brief": "Unmanned aerial surveillance firm targeting federal and state border protection agencies.",
        "pain_points": "Federal procurement cycles are 18+ months; staff rotations lose historical context.",
        "desired_outcome": "Durable stakeholder history tracking and compliance-ready record keeping.",
        "icp_fit": "Medium", "intent_signals": "Shortlisted for SBIR Phase III transition award",
        "qualification_notes": "Defense sector requires strict data boundaries; no public cloud telemetry leaks.",
        "opportunity_owner": "Sarah Jenkins", "source": "Defense Tech Day", "priority": "Medium",
        "next_action": "Send security isolation and air-gapped deployment architecture brief",
        "next_action_date": DATE_LATER, "follow_up_status": "Pending Tech Review",
        "notes": "Sent introductory note Oct 17. Frank requested confirmation of on-prem/memory-only demo isolation.",
        "fit_rationale": "Long, high-stakes deal tracking where account continuity is critical.",
        "opportunity_rationale": "SBIR Phase III transition requires commercialization roadmap for DOD sponsors.",
        "suggested_action": "Provide architectural documentation showing zero external tracking or public leaks.",
        "suggested_angle": "Durable stakeholder and procurement history retention across government rotations.",
        "discovery_questions": "How does your capture team preserve meeting notes across multi-year appropriations?",
        "objections": "Security clearance and ITAR compliance (clarify offline sandbox capabilities)."
    },
    {
        "company": "Vanguard Payments", "contact": "Simon Cross", "title": "Head of Enterprise Partnerships",
        "email": "scross@vanguardpayments.com", "website": "https://vanguardpayments.com",
        "industry": "Fintech", "company_size": "500-1000", "tech_stack": "Salesforce · Gong · HubSpot",
        "opportunity_brief": "Cross-border payment infrastructure provider expanding into Tier 2 marketplace platforms.",
        "pain_points": "Partnership reps struggle to qualify marketplace transaction volumes before discovery calls.",
        "desired_outcome": "Enrich accounts with public marketplace traffic and merchant volume estimates.",
        "icp_fit": "High", "intent_signals": "Secured European cross-border banking license",
        "qualification_notes": "Established fintech; aggressive expansion into cross-border e-commerce.",
        "opportunity_owner": "Alex Rivera", "source": "Fintech Weekly", "priority": "High",
        "next_action": "Follow up with cross-border marketplace volume teardown",
        "next_action_date": DATE_LATER, "follow_up_status": "In Sequence",
        "notes": "Outbound email sent Oct 17. Simon viewed shared benchmark deck.",
        "fit_rationale": "High ACV potential; complex multi-stakeholder commercial evaluation.",
        "opportunity_rationale": "New European banking license unlocks immediate addressable market for EU marketplaces.",
        "suggested_action": "Follow up with analysis of top 25 high-growth cross-border marketplaces.",
        "suggested_angle": "How to uncover high-volume marketplace platforms before competitors.",
        "discovery_questions": "How do reps evaluate whether a marketplace has sufficient cross-border volume to warrant an enterprise contract?",
        "objections": "Marketplaces build payments in-house (position as FX infrastructure partner)."
    },

    # 21-27: Replied (Scenarios 3, 4, 5)
    {
        "company": "Apex BioLabs", "contact": "Dr. Miriam Al-Mansoor", "title": "VP of Research Partnerships",
        "email": "m.almansoor@apexbio.com", "website": "https://apexbio.com",
        "industry": "Life Sciences", "company_size": "250-500", "tech_stack": "Veeva · HubSpot · Slack",
        "opportunity_brief": "Contract research organization (CRO) partnering with biotech drug discovery teams.",
        "pain_points": "High competition for oncology study contracts; proposals lack sponsor pipeline relevance.",
        "desired_outcome": "Empower business development directors with real-time clinical trial phase tracking.",
        "icp_fit": "High", "intent_signals": "Expanded bioanalytical testing laboratory in Boston",
        "qualification_notes": "Confirmed interest via reply. Miriam wants to see workflow demo for business development team.",
        "opportunity_owner": "Sarah Jenkins", "source": "BioPharma Digest", "priority": "High",
        "next_action": "Book 30-min discovery call and send CRO pipeline intelligence overview",
        "next_action_date": DATE_TODAY, "follow_up_status": "Replied - Positive",
        "notes": "Positive reply on Oct 18: 'We are revamping our BD outreach this month. What does your pipeline interface look like for science reps?'",
        "fit_rationale": "High-value contract research where account context makes or breaks deals.",
        "opportunity_rationale": "Active revamping of BD outreach creates immediate opening for demo.",
        "suggested_action": "Reply immediately offering two specific time slots this week.",
        "suggested_angle": "Demonstrating how reps see clinical trial milestones right in the account workspace.",
        "discovery_questions": "What criteria does your team use to qualify early-stage biotech sponsors?",
        "objections": "Scientists hate complicated software (showcase clean read-first workspace)."
    },
    {
        "company": "Solas Energy", "contact": "Brian O'Connor", "title": "Director of Distributed Generation",
        "email": "boconnor@solasenergy.com", "website": "https://solasenergy.com",
        "industry": "Renewable Energy", "company_size": "100-250", "tech_stack": "Salesforce · SolarGraf · Outreach",
        "opportunity_brief": "Commercial rooftop solar EPC prospecting corporate real estate portfolios.",
        "pain_points": "Reps waste time contacting building tenants who don't own the property roof rights.",
        "desired_outcome": "Distinguish property owners from facility tenants in account intelligence before outreach.",
        "icp_fit": "High", "intent_signals": "Secured $50M project financing facility for C&I rooftop projects",
        "qualification_notes": "Replied with high interest. Confirmed 12 reps would use the platform.",
        "opportunity_owner": "Sarah Jenkins", "source": "Solar Power Intl", "priority": "High",
        "next_action": "Schedule product demonstration with commercial sales managers",
        "next_action_date": DATE_TODAY, "follow_up_status": "Replied - Positive",
        "notes": "Replied Oct 18: 'The property owner versus tenant distinction is our biggest headache. Let's talk Thursday.'",
        "fit_rationale": "Exact match for structured account briefs with clear buying trigger tags.",
        "opportunity_rationale": "$50M financing facility needs to be deployed into funded solar assets rapidly.",
        "suggested_action": "Send calendar link and 1-page Rooftop Owner Intelligence brief.",
        "suggested_angle": "Filtering out unqualified tenant accounts before reps spend hours drafting proposals.",
        "discovery_questions": "How much time is lost each month working deals that fail title ownership checks?",
        "objections": "We need custom fields for roof square footage (show flexible JSON field schema)."
    },
    {
        "company": "Kinetix Robotics", "contact": "Sven Lindemann", "title": "VP of Commercial Automation",
        "email": "slindemann@kinetixrobotics.com", "website": "https://kinetixrobotics.com",
        "industry": "Manufacturing Automation", "company_size": "250-500", "tech_stack": "Microsoft Dynamics · HubSpot",
        "opportunity_brief": "Robotic welding cell manufacturer targeting automotive Tier 1 suppliers.",
        "pain_points": "Long, disjointed sales cycles; lack of visibility into plant manager decision processes.",
        "desired_outcome": "Track plant-level stakeholder champions and multi-site project milestones.",
        "icp_fit": "High", "intent_signals": "Tier 1 supplier reshoring announcements driving equipment upgrades",
        "qualification_notes": "Replied positively; requested overview deck and customer references.",
        "opportunity_owner": "Alex Rivera", "source": "Automotive News", "priority": "High",
        "next_action": "Send Tier 1 automotive supplier case study and schedule discovery",
        "next_action_date": DATE_SOON, "follow_up_status": "Replied - Positive",
        "notes": "Replied Oct 17: 'Looks promising. Can you share a reference in automotive manufacturing?'",
        "fit_rationale": "High deal value ($150k+ per welding cell) and complex multi-threaded account structure.",
        "opportunity_rationale": "Automotive reshoring trend driving immediate equipment replacement cycles.",
        "suggested_action": "Send manufacturing case study and invite to 20-minute screen-share.",
        "suggested_angle": "Multi-site plant intelligence and tracking champion changes during long cycles.",
        "discovery_questions": "How do your regional account managers track corporate vs plant-level approvals?",
        "objections": "Customer references required before demo (share sanitized industrial case study)."
    },
    {
        "company": "Triton Fleet", "contact": "Arthur Pendelton", "title": "VP of Commercial Fleet Sales",
        "email": "apendelton@tritonfleet.com", "website": "https://tritonfleet.com",
        "industry": "Automotive & Fleet", "company_size": "500-1000", "tech_stack": "Salesforce · Geotab · ZoomInfo",
        "opportunity_brief": "Commercial fleet telematics and dashcam vendor targeting municipal utilities.",
        "pain_points": "Reps miss municipal procurement budget cycles; pricing requests require formal breakdown.",
        "desired_outcome": "Track municipal budget approval timelines and provide standardized pricing calculators.",
        "icp_fit": "High", "intent_signals": "Municipal insurance mandates requiring dual-facing telematics dashcams",
        "qualification_notes": "Scenario 4 (Pricing Request): Arthur replied specifically requesting our licensing model and volume pricing tiers.",
        "opportunity_owner": "Sarah Jenkins", "source": "Fleet Safety Summit", "priority": "High",
        "next_action": "Provide pricing tier structure & schedule commercial scoping call",
        "next_action_date": DATE_TODAY, "follow_up_status": "Replied - Pricing Request",
        "notes": "Replied Oct 18: 'We are evaluating two other vendors. Can you send your per-seat pricing schedule and enterprise tiers?'",
        "fit_rationale": "Strong pricing request scenario; high volume potential across 40 sales reps.",
        "opportunity_rationale": "Active RFP evaluation means pricing transparency will keep us in the deal.",
        "suggested_action": "Send transparent pricing tier sheet and request 15-minute call to scope seat requirements.",
        "suggested_angle": "Demonstrating how ROI payback occurs within 60 days via rep productivity.",
        "discovery_questions": "How many active reps and managers would require workspace seats in Phase 1?",
        "objections": "Competitors offer per-company flat fees (highlight value of dedicated per-rep intelligence)."
    },
    {
        "company": "Vortex Dynamics", "contact": "Claire Beauchamp", "title": "Head of Strategic Accounts",
        "email": "cbeauchamp@vortexdynamics.com", "website": "https://vortexdynamics.com",
        "industry": "Aerospace & Engineering", "company_size": "250-500", "tech_stack": "Salesforce · Deltek · Teams",
        "opportunity_brief": "Turbine inspection drone manufacturer prospecting utility power plant operators.",
        "pain_points": "Scenario 5 (Budget Objection): Plant budgets committed for current fiscal year; interested but frozen.",
        "desired_outcome": "Build ROI business case for Q1 capital budget allocation.",
        "icp_fit": "High", "intent_signals": "Mandatory NERC inspection guidelines driving drone adoption",
        "qualification_notes": "Expressed high interest in product but stated 2026 software budget is officially locked.",
        "opportunity_owner": "Sarah Jenkins", "source": "PowerGen Expo", "priority": "Medium",
        "next_action": "Send Q1 budget justification package & ROI payback model",
        "next_action_date": DATE_SOON, "follow_up_status": "Replied - Budget Objection",
        "notes": "Replied Oct 17: 'We love the concept, but all 2026 budget is spent. We can only evaluate for January 2027.'",
        "fit_rationale": "Valuable account with clear buying need; requires budget enablement strategy.",
        "opportunity_rationale": "January budget unlock means planting the seed now guarantees inclusion in Q1 spend.",
        "suggested_action": "Acknowledge budget timing and offer a 'pilot in Q4, pay in Q1' structure.",
        "suggested_angle": "How other engineering firms justified early deployment using operational downtime savings.",
        "discovery_questions": "When does your executive committee begin reviewing Q1 capital budget proposals?",
        "objections": "Budget freeze until Jan 1 (offer deferred billing or early access trial)."
    },
    {
        "company": "Aegis Health Systems", "contact": "Dr. Leonard Vance", "title": "VP of Population Health",
        "email": "lvance@aegishealth.com", "website": "https://aegishealth.com",
        "industry": "Healthcare Services", "company_size": "1000+", "tech_stack": "Epic · Salesforce · Microsoft 365",
        "opportunity_brief": "Integrated health network expanding Medicare Advantage risk-sharing contracts.",
        "pain_points": "Payer contract team lacks clear pipeline tracking for regional employer group plans.",
        "desired_outcome": "Structured employer pipeline tracker with member enrollment forecasting.",
        "icp_fit": "High", "intent_signals": "CMS 4.5-star rating awarded · Expanding into two adjacent counties",
        "qualification_notes": "Replied Oct 18 asking for clinical stakeholder references.",
        "opportunity_owner": "Sarah Jenkins", "source": "Healthcare Exec Summit", "priority": "High",
        "next_action": "Coordinate reference call with Midwest health network peer",
        "next_action_date": DATE_SOON, "follow_up_status": "Replied - Follow-up",
        "notes": "Replied Oct 18: 'Sounds interesting. Have you worked with any other ACO networks in the Midwest?'",
        "fit_rationale": "High ACV healthcare enterprise contract.",
        "opportunity_rationale": "County expansion necessitates rapid employer enrollment pipeline buildout.",
        "suggested_action": "Provide sanitized case study of regional Medicare Advantage rollout.",
        "suggested_angle": "How account workspaces bridge clinical leadership and commercial sales teams.",
        "discovery_questions": "How are employer health benefits managers categorized during open enrollment outreach?",
        "objections": "Integration with Epic (clarify this is for employer sales, not clinical records)."
    },
    {
        "company": "Celerity Freight", "contact": "Jason Burke", "title": "VP of Enterprise Brokerage",
        "email": "jburke@celerityfreight.com", "website": "https://celerityfreight.com",
        "industry": "Freight & Logistics", "company_size": "500-1000", "tech_stack": "McLeod · Salesforce · ZoomInfo",
        "opportunity_brief": "Intermodal freight provider targeting Tier 1 automotive parts distributors.",
        "pain_points": "Shippers demanding dedicated lane contracts; spot market volatility hurting margins.",
        "desired_outcome": "Systematic target account prioritization for high-volume dedicated contract freight.",
        "icp_fit": "High", "intent_signals": "Opened new intermodal rail transfer hub in Kansas City",
        "qualification_notes": "Replied Oct 18 requesting a live demo for his 5 regional brokerage directors.",
        "opportunity_owner": "Sarah Jenkins", "source": "Intermodal World", "priority": "High",
        "next_action": "Set up dedicated team demo meeting for Thursday 2 PM",
        "next_action_date": DATE_TODAY, "follow_up_status": "Replied - Scheduling",
        "notes": "Replied Oct 18: 'I want my regional directors to see this. Can we do a team demo this week?'",
        "fit_rationale": "Immediate multi-seat expansion opportunity.",
        "opportunity_rationale": "Kansas City hub opening demands rapid customer lane commitments.",
        "suggested_action": "Confirm team calendar invitation and prepare dedicated lane intelligence walkthrough.",
        "suggested_angle": "Surfacing rail lane volume signals to win shippers away from long-haul trucking.",
        "discovery_questions": "What criteria decide whether a shipper account is routed to rail intermodal vs truckload?",
        "objections": "Brokers resist typing notes into CRM (show how next actions take 5 seconds to log)."
    },

    # 28-32: Meeting Booked (Scenario 7: Discovery meeting booked)
    {
        "company": "ZeoTech Materials", "contact": "Dr. Henrik Lindqvist", "title": "VP of Business Development",
        "email": "hlindqvist@zeotech.com", "website": "https://zeotech.com",
        "industry": "Specialty Chemicals", "company_size": "250-500", "tech_stack": "SAP · HubSpot · Teams",
        "opportunity_brief": "Advanced catalyst manufacturer prospecting semiconductor fabrication plants.",
        "pain_points": "Long technical evaluations; reps lose momentum between lab testing and commercial procurement.",
        "desired_outcome": "Maintain pipeline velocity across 12-month chemical qualification cycles.",
        "icp_fit": "High", "intent_signals": "CHIPS Act sub-grant finalist · Expanding Texas fab supply center",
        "qualification_notes": "Scenario 7: Discovery call confirmed for Oct 22, 10:00 AM EST via Zoom.",
        "opportunity_owner": "Sarah Jenkins", "source": "Semicon West", "priority": "High",
        "next_action": "Conduct discovery call: Fab supply cycle analysis & team workflow demo",
        "next_action_date": DATE_SOON, "follow_up_status": "Meeting Booked",
        "notes": "Discovery meeting scheduled. Henrik confirmed 3 technical BD directors will attend.",
        "fit_rationale": "Extremely high contract values ($250k+ annual chemical supply agreements).",
        "opportunity_rationale": "CHIPS Act fab construction timelines require early chemical supplier lock-in.",
        "suggested_action": "Review Henrik's recent technical paper on wafer cleaning chemistry before call.",
        "suggested_angle": "How structured pipeline intelligence preserves technical qualification data during extended 12-month evaluations.",
        "discovery_questions": "What milestone must be met for a fab customer to move from lab testing to pilot production?",
        "objections": "Security of confidential chemical formulations (highlight zero cloud storage)."
    },
    {
        "company": "Kestrel BioTherapeutics", "contact": "Camilla Vasquez", "title": "Director of Commercial Strategy",
        "email": "c.vasquez@kestrelbio.com", "website": "https://kestrelbio.com",
        "industry": "Biopharmaceuticals", "company_size": "100-250", "tech_stack": "Veeva · Salesforce · ZoomInfo",
        "opportunity_brief": "Rare disease biopharma preparing for commercial launch of orphan neurological therapy.",
        "pain_points": "Identifying specialized treatment centers and regional key opinion leaders (KOLs).",
        "desired_outcome": "Map hospital institutional access and track hospital committee formulary submissions.",
        "icp_fit": "High", "intent_signals": "FDA Priority Review designation granted · Commercial team buildout underway",
        "qualification_notes": "Discovery meeting booked for Oct 23, 2:00 PM EST.",
        "opportunity_owner": "Sarah Jenkins", "source": "Orphan Drug Summit", "priority": "High",
        "next_action": "Conduct discovery call: Rare disease commercial launch pipeline roadmap",
        "next_action_date": DATE_SOON, "follow_up_status": "Meeting Booked",
        "notes": "Meeting booked. Camilla expressed urgency around Q1 commercial launch planning.",
        "fit_rationale": "High-urgency launch timeline with specialized target account criteria.",
        "opportunity_rationale": "FDA Priority Review creates immutable commercial launch countdown.",
        "suggested_action": "Prepare hospital formulary tracking demo workflow.",
        "suggested_angle": "Preserving KOL engagement history and institutional committee stage progression.",
        "discovery_questions": "How do your account managers track formulary review dates across teaching hospitals?",
        "objections": "Compliance with healthcare Sunshine Act (explain software is workflow intelligence, not transfer of value)."
    },
    {
        "company": "Merit Financial", "contact": "Warren Hastings", "title": "Head of Institutional Sales",
        "email": "whastings@meritfinancial.com", "website": "https://meritfinancial.com",
        "industry": "Asset Management", "company_size": "500-1000", "tech_stack": "Salesforce · FactSet · Bloomberg",
        "opportunity_brief": "Fixed income asset manager targeting corporate pension fund consultants.",
        "pain_points": "Pension consultant relationships managed in fragmented personal Outlook notes.",
        "desired_outcome": "Centralized consultant mandate tracking and quarterly consultant due diligence updates.",
        "icp_fit": "High", "intent_signals": "Outperformed benchmark by 180 bps in private credit portfolio",
        "qualification_notes": "Discovery meeting confirmed for Oct 24, 11:30 AM EST.",
        "opportunity_owner": "Sarah Jenkins", "source": "Institutional Investor", "priority": "High",
        "next_action": "Execute institutional sales discovery session & consultant mapping",
        "next_action_date": DATE_LATER, "follow_up_status": "Meeting Booked",
        "notes": "Warren booked meeting via calendar link after seeing consultant relationship tracking mockup.",
        "fit_rationale": "High ACV institutional wealth management with major transparency gaps.",
        "opportunity_rationale": "Private credit outperformance makes this the best quarter to raise new institutional commitments.",
        "suggested_action": "Prepare consultant mandate stage progression view.",
        "suggested_angle": "Ensuring no consultant inquiry or RFP deadline slips through the cracks.",
        "discovery_questions": "How do partners ensure consultant due diligence updates happen on time every quarter?",
        "objections": "Partners are resistant to CRM data entry (demonstrate 10-second next-action updates)."
    },
    {
        "company": "Veloce Automation", "contact": "Gianna Rossi", "title": "VP of Robotics Sales",
        "email": "grossi@veloceauto.com", "website": "https://veloceauto.com",
        "industry": "Industrial Robotics", "company_size": "250-500", "tech_stack": "Salesforce · HubSpot · SAP",
        "opportunity_brief": "Autonomous mobile robot (AMR) manufacturer expanding into e-commerce fulfillment centers.",
        "pain_points": "Reps struggle to quantify warehouse labor cost savings during preliminary discovery.",
        "desired_outcome": "Incorporate warehouse labor wage benchmarks directly into account intelligence cards.",
        "icp_fit": "High", "intent_signals": "Won 'Robotics Innovation of the Year' · Expanded warehouse testing facility",
        "qualification_notes": "Discovery meeting confirmed for Oct 23, 3:30 PM EST.",
        "opportunity_owner": "Alex Rivera", "source": "Automate Expo", "priority": "High",
        "next_action": "Conduct AMR sales process discovery with Gianna and Lead Solutions Architect",
        "next_action_date": DATE_SOON, "follow_up_status": "Meeting Booked",
        "notes": "Gianna accepted calendar invite; requested Solutions Architect join for technical qualification.",
        "fit_rationale": "High ACV deals ($180k+) with high need for clear account opportunity briefs.",
        "opportunity_rationale": "E-commerce warehouse automation demand accelerating ahead of peak fulfillment season.",
        "suggested_action": "Prepare labor cost calculation module in account opportunity brief.",
        "suggested_angle": "Surfacing regional fulfillment wage rates to justify automation ROI in the very first touch.",
        "discovery_questions": "What warehouse metrics convince a VP of Supply Chain to sign off on an AMR pilot?",
        "objections": "Integration with existing warehouse management systems (highlight API compatibility)."
    },
    {
        "company": "Sentry Risk", "contact": "Malcolm Davies", "title": "Chief Commercial Officer",
        "email": "mdavies@sentryrisk.com", "website": "https://sentryrisk.com",
        "industry": "InsurTech", "company_size": "100-250", "tech_stack": "HubSpot · ZoomInfo · Slack",
        "opportunity_brief": "Commercial property risk modeling platform prospecting regional insurance carriers.",
        "pain_points": "Catastrophe risk modeling sales cycles stall in actuarial validation reviews.",
        "desired_outcome": "Equip reps with actuarial validation proofs and standardized carrier qualification criteria.",
        "icp_fit": "High", "intent_signals": "Severe convective storm losses driving insurers to seek updated risk models",
        "qualification_notes": "Meeting booked for Oct 22, 1:00 PM EST.",
        "opportunity_owner": "Sarah Jenkins", "source": "InsurTech Connect", "priority": "High",
        "next_action": "Conduct discovery call: Actuarial sales enablement & carrier buying gates",
        "next_action_date": DATE_SOON, "follow_up_status": "Meeting Booked",
        "notes": "Malcolm booked meeting after reviewing actuarial discovery question prompts.",
        "fit_rationale": "Complex technical sale where structured questions accelerate technical buy-in.",
        "opportunity_rationale": "Catastrophe loss spikes make carrier executives receptive to new predictive models.",
        "suggested_action": "Demonstrate actuarial discovery questionnaire and risk model comparison cards.",
        "suggested_angle": "Bridging commercial sales reps with chief actuarial officers.",
        "discovery_questions": "How do reps navigate the technical proof-of-concept phase with actuarial teams?",
        "objections": "Insurers take 18 months to adopt new models (showcase 30-day proof-of-concept workflow)."
    },

    # 33-36: Opportunity Created (Scenario 8: Qualified opportunity created after discovery)
    {
        "company": "Apex Cloud Systems", "contact": "Rachel Thorne", "title": "VP of Revenue Operations",
        "email": "rthorne@apexcloudsys.com", "website": "https://apexcloudsys.com",
        "industry": "Enterprise Software", "company_size": "500-1000", "tech_stack": "Salesforce · Gong · Outreach · Snowflake",
        "opportunity_brief": "Global SaaS vendor with 50 AEs; successfully completed discovery and technical validation.",
        "pain_points": "Pipeline conversion leaks between Stage 2 and Stage 4; lack of actionable next action discipline.",
        "desired_outcome": "Deploy standardized pipeline intelligence workspace across 50 enterprise AEs and 15 sales managers.",
        "icp_fit": "High", "intent_signals": "Active pilot evaluation underway with 5 champion reps",
        "qualification_notes": "Scenario 8: Discovery completed. Opportunity created with $60k ACV. Economic buyer approved.",
        "opportunity_owner": "Sarah Jenkins", "source": "Executive Referral", "priority": "High",
        "next_action": "Deliver formal commercial proposal & master service agreement for legal review",
        "next_action_date": DATE_SOON, "follow_up_status": "Proposal Review",
        "notes": "Discovery call completed with glowing feedback. Economic buyer (CRO) attended final 15 minutes and approved commercial rollout.",
        "fit_rationale": "Flagship enterprise deployment; validates multi-tier sales team scaling.",
        "opportunity_rationale": "CRO mandated implementation before annual sales kickoff in January.",
        "suggested_action": "Deliver MSA and schedule security walkthrough with IT procurement.",
        "suggested_angle": "Enterprise-grade governance, isolated data sandbox, and immediate rep time savings.",
        "discovery_questions": "What remaining vendor onboarding hurdles exist in your procurement team?",
        "objections": "Legal review duration (provide standard pre-approved agreement template)."
    },
    {
        "company": "Cobalt BioAnalytics", "contact": "Dr. Ethan Cole", "title": "Chief Business Officer",
        "email": "ecole@cobaltbio.com", "website": "https://cobaltbio.com",
        "industry": "Biotech & Genomics", "company_size": "250-500", "tech_stack": "Veeva · HubSpot · AWS",
        "opportunity_brief": "Next-gen sequencing platform provider; qualified opportunity created for pharmaceutical partnerships team.",
        "pain_points": "Sponsor engagement history lost across multiple business development directors.",
        "desired_outcome": "Standardize partner opportunity dossiers and unify account intelligence.",
        "icp_fit": "High", "intent_signals": "Signed 2 top-10 pharma partnerships; expanding BD team by 12 reps",
        "qualification_notes": "Scenario 8: Qualified opportunity ($61.5k ACV). Legal and security review underway.",
        "opportunity_owner": "Sarah Jenkins", "source": "BioPartnering Forum", "priority": "High",
        "next_action": "Finalize Statement of Work and schedule executive sponsor signature call",
        "next_action_date": DATE_SOON, "follow_up_status": "Contracting",
        "notes": "Security review completed with zero issues. Dr. Cole confirmed target start date of Nov 1.",
        "fit_rationale": "High contract value, high gross margin, multi-year expansion path.",
        "opportunity_rationale": "Expanding BD team requires unified workspace on Day 1 of onboarding.",
        "suggested_action": "Send final execution copy of SOW via DocuSign.",
        "suggested_angle": "Ensuring smooth onboarding for 12 incoming BD directors.",
        "discovery_questions": "Who is the primary administrator for your sales systems onboarding?",
        "objections": "Vendor onboarding timeline (coordinate directly with finance procurement contact)."
    },
    {
        "company": "Vanguard Logistics", "contact": "Travis Sterling", "title": "SVP of Commercial Logistics",
        "email": "tsterling@vanguardlog.com", "website": "https://vanguardlog.com",
        "industry": "Supply Chain", "company_size": "1000+", "tech_stack": "Salesforce · McLeod · ZoomInfo",
        "opportunity_brief": "National freight network deploying outbound workspace to 4 regional sales hubs.",
        "pain_points": "Regional brokers operating in silos; duplication of outreach to enterprise shippers.",
        "desired_outcome": "Universal account de-duplication and coordinated multi-hub next-action alerts.",
        "icp_fit": "High", "intent_signals": "Merged with regional carrier; consolidating commercial sales tools",
        "qualification_notes": "Scenario 8: Opportunity created ($63k ACV). Executive committee passed budget allocation.",
        "opportunity_owner": "Sarah Jenkins", "source": "Carrier Executive Council", "priority": "High",
        "next_action": "Conduct procurement pricing review & finalize multi-hub licensing agreement",
        "next_action_date": DATE_LATER, "follow_up_status": "Contracting",
        "notes": "Executive committee approved $63k annual contract. Travis confirmed agreement ready for signature next week.",
        "fit_rationale": "Major multi-hub deployment demonstrating enterprise operational value.",
        "opportunity_rationale": "Merger consolidation requires unified platform to prevent account territory clashes.",
        "suggested_action": "Send onboarding timeline covering all 4 regional hubs.",
        "suggested_angle": "Preventing territory conflicts between merged sales teams.",
        "discovery_questions": "How will regional territory managers be designated in the account hierarchy?",
        "objections": "Legacy broker habits (provide role-based champion training sessions)."
    },
    {
        "company": "Meridian Robotics", "contact": "Aria Montgomery", "title": "VP of Global Sales",
        "email": "amontgomery@meridianrobotics.com", "website": "https://meridianrobotics.com",
        "industry": "Robotics & Automation", "company_size": "500-1000", "tech_stack": "Salesforce · HubSpot · PowerBI",
        "opportunity_brief": "Collaborative robot manufacturer deploying opportunity workspace to EMEA and Americas sales forces.",
        "pain_points": "International distributors dropping leads; lack of pipeline conversion visibility.",
        "desired_outcome": "Real-time pipeline progression tracking and standardized distributor lead handoffs.",
        "icp_fit": "High", "intent_signals": "Opening direct sales subsidiary in Frankfurt and Chicago",
        "qualification_notes": "Scenario 8: Opportunity created ($64.5k ACV). Commercial terms agreed; awaiting final signature.",
        "opportunity_owner": "Alex Rivera", "source": "Robotics World", "priority": "High",
        "next_action": "Execute master subscription agreement and schedule kickoff call",
        "next_action_date": DATE_LATER, "follow_up_status": "Signature Pending",
        "notes": "Commercial terms finalized. Aria signed off; legal reviewing indemnification clause.",
        "fit_rationale": "Global scale, multi-currency compatibility, multi-region sales pipeline.",
        "opportunity_rationale": "Simultaneous opening of Frankfurt and Chicago offices requires immediate operational tooling.",
        "suggested_action": "Follow up with legal counsel on minor contract clause redline.",
        "suggested_angle": "Standardizing sales language and stage progression across European and American teams.",
        "discovery_questions": "What is the targeted kickoff date for the European sales cohort?",
        "objections": "Multi-region time zone training (offer asynchronous video walkthrough guides)."
    },

    # 37-38: Disqualified (Scenario 9: Disqualified with documented reason)
    {
        "company": "Kestrel Retail Media", "contact": "Derrick Vance", "title": "Director of Media Sales",
        "email": "dvance@kestrelrm.com", "website": "https://kestrelrm.com",
        "industry": "Retail & Advertising", "company_size": "50-100", "tech_stack": "Pipedrive · Mailchimp",
        "opportunity_brief": "Local retail signage agency looking for a cheap mass-email blast tool.",
        "pain_points": "Wanted to scrape local business emails and send 10,000 unverified cold blasts per day.",
        "desired_outcome": "Low-cost bulk email sender (incompatible with targeted account qualification standards).",
        "icp_fit": "Low", "intent_signals": "Downsized sales team from 12 to 3 reps",
        "qualification_notes": "Scenario 9 (Disqualified): Prospect is looking for bulk spam blast software. Refused account qualification and consultative outreach practices. Documented disqualification.",
        "opportunity_owner": "Alex Rivera", "source": "Web Form Lead", "priority": "Low",
        "next_action": "Archive record; no further outreach warranted",
        "next_action_date": DATE_OVERDUE, "follow_up_status": "Disqualified",
        "notes": "Disqualified on Oct 16. Derrick explicitly stated: 'We just want to blast 10,000 emails a day with no personalization.' Politely explained that our platform is designed for targeted B2B intelligence, not unverified mass spam.",
        "fit_rationale": "Unqualified: sub-scale team, negative sales culture, looking for spam execution.",
        "opportunity_rationale": "No revenue opportunity; clear violation of consultative B2B outreach standards.",
        "suggested_action": "Do not pursue. Mark as disqualified.",
        "suggested_angle": "N/A",
        "discovery_questions": "N/A",
        "objections": "Price resistance and unwillingness to qualify accounts."
    },
    {
        "company": "Zephyr Logistics", "contact": "Oliver King", "title": "VP of Operations",
        "email": "oking@zephyrlogistics.com", "website": "https://zephyrlogistics.com",
        "industry": "Freight Brokerage", "company_size": "250-500", "tech_stack": "Salesforce · ZoomInfo",
        "opportunity_brief": "Regional freight carrier acquired by multi-national conglomerate last month.",
        "pain_points": "Parent company mandated migration to global corporate ERP and locked all third-party software.",
        "desired_outcome": "Standardize on parent company's mandated enterprise platform.",
        "icp_fit": "Low", "intent_signals": "Acquired by Global Transport Corp; IT systems consolidated",
        "qualification_notes": "Scenario 9 (Disqualified): Oliver confirmed during discovery call that parent company strictly forbids any independent sales software contracts. Disqualified with documented reason.",
        "opportunity_owner": "Sarah Jenkins", "source": "Inbound Referral", "priority": "Low",
        "next_action": "Set nurture reminder for 2028 when parent contract is up for renewal",
        "next_action_date": "2027-10-01", "follow_up_status": "Disqualified - M&A",
        "notes": "Disqualified Oct 17. Oliver was very courteous: 'We would love to use you guys, but our acquisition by Global Transport requires us to use their corporate ERP. All local software spend is frozen for 3 years.'",
        "fit_rationale": "High initial fit negated by corporate acquisition lock-in.",
        "opportunity_rationale": "No commercial path available during 3-year post-merger IT lock.",
        "suggested_action": "Send gracious departure note and maintain relationship with Oliver for future moves.",
        "suggested_angle": "Keep in touch for when parent company ERP proves too cumbersome for regional brokers.",
        "discovery_questions": "N/A",
        "objections": "Corporate parent IT mandate."
    },

    # 39-40: No Response (Scenario 10: No response after multiple attempts)
    {
        "company": "Aura Industrial Solutions", "contact": "Bradley Cooper", "title": "Director of Procurement Sales",
        "email": "bcooper@auraindustrial.com", "website": "https://auraindustrial.com",
        "industry": "Industrial Supplies", "company_size": "100-250", "tech_stack": "NetSuite · Outlook",
        "opportunity_brief": "Pumps and valves distributor targeting regional water treatment facilities.",
        "pain_points": "Traditional catalog business struggling to generate outbound pipeline for new automated valve line.",
        "desired_outcome": "Equip catalog sales reps with water municipality project signals.",
        "icp_fit": "Medium", "intent_signals": "EPA clean water infrastructure funds allocated to regional plants",
        "qualification_notes": "Scenario 10 (No Response): Contacted across 4 personalized touches over 30 days. No response received.",
        "opportunity_owner": "Alex Rivera", "source": "Trade Directory", "priority": "Low",
        "next_action": "Queue for 90-day cold nurture re-engagement sequence",
        "next_action_date": "2027-01-15", "follow_up_status": "No Response - Cooldown",
        "notes": "Touch 1 (Sep 18), Touch 2 (Sep 25), Touch 3 (Oct 02), Touch 4 (Oct 10). Zero opens or replies. Moved to No Response stage. Scheduled for re-engagement in Q1 2027.",
        "fit_rationale": "Good initial industry fit, but lack of engagement indicates low current priority.",
        "opportunity_rationale": "Municipal infrastructure projects may take until 2027 to become active bids.",
        "suggested_action": "Pause active outbound. Re-evaluate in 90 days with fresh project data.",
        "suggested_angle": "Checking in when regional water authority bids are formally published.",
        "discovery_questions": "How do reps track EPA clean water grant allocations?",
        "objections": "Unresponsive."
    },
    {
        "company": "Crestline Heavy Equipment", "contact": "Douglas Fletcher", "title": "VP of Commercial Sales",
        "email": "dfletcher@crestlineequipment.com", "website": "https://crestlineequipment.com",
        "industry": "Heavy Machinery", "company_size": "250-500", "tech_stack": "Salesforce · CDK Global",
        "opportunity_brief": "Earthmoving equipment dealership prospecting commercial site preparation contractors.",
        "pain_points": "High dealer inventory carrying costs; need faster qualification of active subdivision developers.",
        "desired_outcome": "Surface land grading and site preparation permits to deploy equipment on rent-to-own.",
        "icp_fit": "Medium", "intent_signals": "Commercial site development surge in Sunbelt markets",
        "qualification_notes": "Scenario 10 (No Response): Reached out via email, phone, and LinkedIn. 4 attempts with zero response.",
        "opportunity_owner": "Alex Rivera", "source": "Construction Equipment Expo", "priority": "Low",
        "next_action": "Move to quarterly newsletter list; pause active outbound cadence",
        "next_action_date": "2027-01-15", "follow_up_status": "No Response - Cooldown",
        "notes": "Attempt 1 (Sep 20), Attempt 2 (Sep 28), Attempt 3 (Oct 05), Attempt 4 (Oct 12). No response. Moving to No Response stage with 90-day cooldown.",
        "fit_rationale": "Dealer business model has potential, but non-responsive executive means rep attention belongs elsewhere.",
        "opportunity_rationale": "Dealer inventory pressure may worsen by Q1, creating higher receptivity.",
        "suggested_action": "Maintain low-touch quarterly market report.",
        "suggested_angle": "Sunbelt site grading permit trends and dealer equipment financing benchmarks.",
        "discovery_questions": "How do sales reps identify which civil contractors just won new highway bids?",
        "objections": "Unresponsive."
    }
]

# Generate 40 records for demo_prospects.json strictly preserving stage IDs and ACVs
def build_sales_prospects():
    records = []
    # Base stages
    stages = (
        ['identified'] * 4 +
        ['qualified'] * 3 +
        ['ready'] * 3 +
        ['contacted'] * 10 +
        ['replied'] * 7 +
        ['meeting_booked'] * 5 +
        ['opportunity_created'] * 4 +
        ['disqualified'] * 2 +
        ['no_response'] * 2
    )
    
    for i in range(40):
        rec_id = f"demo-{i+1:03d}"
        stage_id = stages[i]
        acv = 12000 + i * 1500
        template = SALES_PROSPECTS_DATA[i]
        
        fields = {
            "company": template["company"],
            "contact": template["contact"],
            "title": template["title"],
            "email": template["email"],
            "website": template["website"],
            "industry": template["industry"],
            "company_size": template["company_size"],
            "tech_stack": template["tech_stack"],
            "acv": acv,
            "opportunity_brief": template["opportunity_brief"],
            "pain_points": template["pain_points"],
            "desired_outcome": template["desired_outcome"],
            "icp_fit": template["icp_fit"],
            "intent_signals": template["intent_signals"],
            "qualification_notes": template["qualification_notes"],
            "opportunity_owner": template["opportunity_owner"],
            "source": template["source"],
            "priority": template["priority"],
            "next_action": template["next_action"],
            "next_action_date": template["next_action_date"],
            "follow_up_status": template["follow_up_status"],
            "notes": template["notes"],
            "fit_rationale": template["fit_rationale"],
            "opportunity_rationale": template["opportunity_rationale"],
            "suggested_action": template["suggested_action"],
            "suggested_angle": template["suggested_angle"],
            "discovery_questions": template["discovery_questions"],
            "objections": template["objections"],
        }
        
        # Build coherent stage history
        created_at = f"2026-09-{15 + (i % 15):02d}T09:00:00+00:00"
        stage_history = [{"stage_id": "identified", "entered_at": created_at}]
        
        if stage_id in ('qualified', 'ready', 'contacted', 'replied', 'meeting_booked', 'opportunity_created', 'disqualified', 'no_response'):
            if stage_id != 'identified':
                stage_history.append({"stage_id": "qualified", "entered_at": f"2026-09-{18 + (i % 10):02d}T10:00:00+00:00"})
        if stage_id in ('ready', 'contacted', 'replied', 'meeting_booked', 'opportunity_created', 'disqualified', 'no_response'):
            if stage_id != 'qualified':
                stage_history.append({"stage_id": "ready", "entered_at": f"2026-09-{22 + (i % 8):02d}T11:00:00+00:00"})
        if stage_id in ('contacted', 'replied', 'meeting_booked', 'opportunity_created', 'disqualified', 'no_response'):
            stage_history.append({"stage_id": "contacted", "entered_at": f"2026-10-01T14:00:00+00:00"})
        if stage_id in ('replied', 'meeting_booked', 'opportunity_created') or rec_id == 'demo-038':
            stage_history.append({"stage_id": "replied", "entered_at": f"2026-10-08T15:30:00+00:00"})
        if stage_id in ('meeting_booked', 'opportunity_created') or rec_id == 'demo-038':
            stage_history.append({"stage_id": "meeting_booked", "entered_at": f"2026-10-14T11:00:00+00:00"})
        if stage_id == 'opportunity_created':
            stage_history.append({"stage_id": "opportunity_created", "entered_at": f"2026-10-18T16:00:00+00:00"})
        if stage_id == 'disqualified':
            stage_history.append({"stage_id": "disqualified", "entered_at": f"2026-10-16T17:00:00+00:00"})
        if stage_id == 'no_response':
            stage_history.append({"stage_id": "no_response", "entered_at": f"2026-10-15T18:00:00+00:00"})
            
        # Build coherent activities
        activities = []
        if stage_id in ('contacted', 'replied', 'meeting_booked', 'opportunity_created', 'disqualified', 'no_response'):
            activities.append({
                "id": f"act-{rec_id}-01",
                "kind": "contacted",
                "text": f"Step 1 personalized outreach sent to {template['contact']}: '{template['opportunity_brief'][:80]}...'",
                "occurred_at": "2026-10-01T14:00:00+00:00"
            })
        if stage_id in ('replied', 'meeting_booked', 'opportunity_created') or rec_id == 'demo-038':
            activities.append({
                "id": f"act-{rec_id}-02",
                "kind": "replied",
                "text": f"Prospect response received: '{template['notes'][:90]}...'",
                "occurred_at": "2026-10-08T15:30:00+00:00"
            })
        if stage_id in ('meeting_booked', 'opportunity_created') or rec_id == 'demo-038':
            activities.append({
                "id": f"act-{rec_id}-03",
                "kind": "meeting",
                "text": f"Discovery meeting confirmed with {template['contact']} ({template['title']}).",
                "occurred_at": "2026-10-14T11:00:00+00:00"
            })
        if stage_id == 'opportunity_created':
            activities.append({
                "id": f"act-{rec_id}-04",
                "kind": "opportunity",
                "text": f"Commercial opportunity qualified and approved by economic buyer (${acv:,.0f} ACV).",
                "occurred_at": "2026-10-18T16:00:00+00:00"
            })
        if stage_id in ('contacted', 'replied', 'ready'):
            activities.append({
                "id": f"act-{rec_id}-note",
                "kind": "note",
                "text": template["notes"],
                "occurred_at": "2026-10-16T12:00:00+00:00"
            })
            
        record = {
            "id": rec_id,
            "stage_id": stage_id,
            "created_at": created_at,
            "fields": fields,
            "stage_history": stage_history,
            "activities": activities
        }
        records.append(record)
        
    return records


# Generate 20 distinct records for B2B Services demo
def build_b2b_services_prospects():
    b2b_companies = [
        ("Acme Global Consulting", "Jonathan Vance", "Managing Director", "Management Consulting", 120000, "Enterprise digital transformation roadmap and change enablement."),
        ("Stratum Advisory Partners", "Beatrice Sterling", "Senior Partner", "Financial Advisory", 95000, "M&A post-merger integration framework for regional healthcare network."),
        ("Nexus Supply Chain Advisors", "Carlos Mendez", "VP of Client Services", "Logistics Consulting", 85000, "Warehouse automation feasibility and RFP vendor evaluation."),
        ("Veritas Regulatory Solutions", "Dr. Rachel Green", "Head of Compliance Advisory", "Healthcare & Pharma", 140000, "FDA regulatory submission readiness audit for commercial biotech client."),
        ("Helios Clean Energy Advisory", "Torsten Lind", "Director of Sustainable Infrastructure", "Clean Energy", 110000, "Commercial solar microgrid feasibility and ESG reporting program."),
        ("Pinnacle Cloud Architects", "Deepak Sharma", "Chief Architect", "IT Services", 130000, "Multi-cloud migration architecture and zero-trust security audit."),
        ("Vanguard Strategic Talent", "Claire Dupont", "Executive Search Partner", "Human Capital", 65000, "C-suite executive succession planning and leadership assessment."),
        ("Apex Forensic Accounting", "Franklin Pierce", "Lead Partner", "Accounting & Audit", 75000, "Internal controls review and compliance audit for Tier 1 defense subcontractor."),
        ("BlueShift Brand Strategy", "Simone Moreau", "Creative Director", "Marketing & Branding", 55000, "Corporate rebrand and market positioning for Series B fintech platform."),
        ("Crestline Industrial Engineering", "Harold Chen", "VP of Engineering Practice", "Industrial Automation", 160000, "Reshoring manufacturing plant layout and robotic automation design."),
        ("Sentry Cyber Defense Advisory", "Elena Rostova", "Principal Security Consultant", "Cybersecurity", 105000, "SOC2 Type II audit readiness and incident response tabletop exercise."),
        ("Meridian Operations Group", "Marcus Vance", "Managing Director", "Operations Consulting", 88000, "Lean Six Sigma supply chain waste reduction for medical device manufacturer."),
        ("Solas Environmental Planning", "Priya Patel", "Head of Environmental Practice", "Environmental Engineering", 72000, "Phase I environmental site assessment and municipal zoning approval."),
        ("Zephyr BioConsulting", "Dr. David Sterling", "Director of Regulatory Strategy", "Life Sciences", 125000, "Clinical trial protocol design and biostatistical analysis review."),
        ("Cobalt Tech Integration", "Amara Okafor", "VP of Enterprise Solutions", "Software Integration", 115000, "Salesforce CRM to SAP S/4HANA enterprise integration and master data sync."),
        ("Ironclad Risk Partners", "Julian Weber", "Managing Director", "Risk Management", 90000, "Enterprise risk management framework and supply chain continuity insurance."),
        ("Horizon Defense Consulting", "Frank Baxter", "Director of Federal Capture", "Government Contracting", 150000, "Federal capture strategy and SBIR Phase III transition compliance."),
        ("Veloce Fleet Advisory", "Chloe Zhao", "Head of Commercial Fleet Strategy", "Transportation", 68000, "Commercial fleet electrification feasibility and charging infrastructure."),
        ("Highline Retail Solutions", "Lucas Moreau", "Director of Omnichannel Practice", "Retail Strategy", 82000, "B2B wholesale portal scoping and headless e-commerce architecture."),
        ("Polaris Change Management", "Karin Lindholm", "Senior Change Consultant", "Organizational Change", 58000, "Enterprise ERP rollout change management and stakeholder communication.")
    ]
    
    stages = (
        ['inquiry'] * 3 +
        ['scoping'] * 3 +
        ['proposal_dev'] * 4 +
        ['proposal_sent'] * 4 +
        ['negotiation'] * 3 +
        ['contract_awarded'] * 2 +
        ['lost'] * 1
    )
    
    records = []
    for i, (company, contact, title, industry, val, brief) in enumerate(b2b_companies):
        rec_id = f"b2b-{i+1:03d}"
        stage_id = stages[i]
        
        fields = {
            "company": company,
            "contact": contact,
            "title": title,
            "email": f"{contact.lower().replace(' ', '.')}@{company.lower().replace(' ', '')}.com",
            "industry": industry,
            "acv": val,
            "opportunity_brief": brief,
            "pain_points": f"Client needs specialized expertise to navigate complex requirements within strict deadlines.",
            "desired_outcome": f"Comprehensive advisory report, implementation roadmap, and operational sign-off.",
            "tech_stack": "Microsoft 365 · Slack · Asana",
            "qualification_notes": "Commercial budget confirmed; stakeholder sponsor actively engaged.",
            "opportunity_owner": "Sarah Jenkins" if i % 2 == 0 else "Alex Rivera",
            "source": "Client Referral" if i % 3 == 0 else "Executive Inbound",
            "priority": "High" if val > 100000 else "Medium",
            "next_action": f"Review project deliverables with {contact}",
            "next_action_date": DATE_SOON if i % 2 == 0 else DATE_LATER,
            "notes": f"Initial scoping completed on Oct 10. Commercial engagement model agreed upon."
        }
        
        created_at = f"2026-09-20T10:00:00+00:00"
        stage_history = [{"stage_id": "inquiry", "entered_at": created_at}]
        if stage_id != 'inquiry':
            stage_history.append({"stage_id": "scoping", "entered_at": "2026-09-28T11:00:00+00:00"})
        if stage_id in ('proposal_dev', 'proposal_sent', 'negotiation', 'contract_awarded', 'lost'):
            stage_history.append({"stage_id": "proposal_dev", "entered_at": "2026-10-04T14:00:00+00:00"})
        if stage_id in ('proposal_sent', 'negotiation', 'contract_awarded', 'lost'):
            stage_history.append({"stage_id": "proposal_sent", "entered_at": "2026-10-10T15:00:00+00:00"})
        if stage_id in ('negotiation', 'contract_awarded'):
            stage_history.append({"stage_id": "negotiation", "entered_at": "2026-10-16T16:00:00+00:00"})
        if stage_id == 'contract_awarded':
            stage_history.append({"stage_id": "contract_awarded", "entered_at": "2026-10-18T17:00:00+00:00"})
        if stage_id == 'lost':
            stage_history.append({"stage_id": "lost", "entered_at": "2026-10-15T12:00:00+00:00"})
            
        activities = [
            {
                "id": f"act-{rec_id}-01",
                "kind": "contacted",
                "text": f"Initial requirements scoping interview conducted with {contact}.",
                "occurred_at": "2026-09-28T11:00:00+00:00"
            }
        ]
        if stage_id in ('proposal_sent', 'negotiation', 'contract_awarded'):
            activities.append({
                "id": f"act-{rec_id}-02",
                "kind": "replied",
                "text": f"Formal proposal deliverable submitted for committee evaluation (${val:,.0f}).",
                "occurred_at": "2026-10-10T15:00:00+00:00"
            })
        if stage_id in ('negotiation', 'contract_awarded'):
            activities.append({
                "id": f"act-{rec_id}-03",
                "kind": "meeting",
                "text": f"Commercial terms and SOW negotiation session with legal & procurement.",
                "occurred_at": "2026-10-16T16:00:00+00:00"
            })
        if stage_id == 'contract_awarded':
            activities.append({
                "id": f"act-{rec_id}-04",
                "kind": "opportunity",
                "text": f"Master Services Agreement executed and engagement staffing confirmed.",
                "occurred_at": "2026-10-18T17:00:00+00:00"
            })
            
        record = {
            "id": rec_id,
            "stage_id": stage_id,
            "created_at": created_at,
            "fields": fields,
            "stage_history": stage_history,
            "activities": activities
        }
        records.append(record)
        
    return records


def main():
    # Write config/demo.json and config/demo_sales_rep.json
    config_dir = ROOT / "config"
    fixtures_dir = ROOT / "pipeline/examples/fixtures"
    
    # Generate Sales Rep Dataset
    sales_records = build_sales_prospects()
    sales_file = fixtures_dir / "demo_prospects.json"
    sales_file.write_text(json.dumps(sales_records, indent=2), encoding="utf-8")
    print(f"Wrote {len(sales_records)} sales records to {sales_file}")
    
    # Generate B2B Services Dataset
    b2b_records = build_b2b_services_prospects()
    b2b_file = fixtures_dir / "demo_b2b_services.json"
    b2b_file.write_text(json.dumps(b2b_records, indent=2), encoding="utf-8")
    print(f"Wrote {len(b2b_records)} B2B services records to {b2b_file}")
    
    # Build B2B Services Config
    b2b_stages = [
        {"id": "inquiry", "name": "New Inquiry", "category": "open", "active": True, "terminal": False, "milestones": []},
        {"id": "scoping", "name": "Discovery & Scoping", "category": "open", "active": True, "terminal": False, "milestones": []},
        {"id": "proposal_dev", "name": "Proposal Preparation", "category": "active", "active": True, "terminal": False, "milestones": ["contacted"]},
        {"id": "proposal_sent", "name": "Proposal Delivered", "category": "active", "active": True, "terminal": False, "milestones": ["replied"]},
        {"id": "negotiation", "name": "Commercial Negotiation", "category": "active", "active": True, "terminal": False, "milestones": ["meeting"]},
        {"id": "contract_awarded", "name": "Contract Awarded", "category": "converted", "active": False, "terminal": True, "milestones": ["opportunity"]},
        {"id": "lost", "name": "Declined / Lost", "category": "closed", "active": False, "terminal": True, "milestones": []},
    ]
    
    b2b_fields = [
        {"key": "company", "label": "Client Organization", "type": "text", "required": True, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "contact", "label": "Primary Stakeholder", "type": "text", "required": True, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "title", "label": "Role / Title", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "email", "label": "Email", "type": "text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "industry", "label": "Client Sector", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "acv", "label": "Project Contract Value", "type": "currency", "required": False, "card": True, "table": True, "intake": True, "format": "currency"},
        {"key": "opportunity_brief", "label": "Engagement Brief", "type": "long_text", "required": False, "card": True, "table": False, "intake": True, "format": "text"},
        {"key": "pain_points", "label": "Client Gaps & Needs", "type": "long_text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "desired_outcome", "label": "Target Deliverables", "type": "long_text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "tech_stack", "label": "Client Tech Stack", "type": "text", "required": False, "card": True, "table": False, "intake": True, "format": "text"},
        {"key": "qualification_notes", "label": "Budget & Terms", "type": "long_text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "opportunity_owner", "label": "Engagement Lead", "type": "text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "source", "label": "Referral Source", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "priority", "label": "Deal Priority", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "next_action", "label": "Next Deliverable", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "next_action_date", "label": "Target Date", "type": "date", "required": False, "card": True, "table": True, "intake": True, "format": "date"},
        {"key": "notes", "label": "Engagement Notes", "type": "long_text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
    ]
    
    b2b_config = {
        "instance_config": {
            "schema_version": 1,
            "instance_id": "b2b-services-demo",
            "mode": "demo",
            "storage": "memory",
            "pipeline_type": "b2b_services",
            "display_name": "More Outbound",
            "page_title": "More Outbound — B2B Services Workspace",
            "page_subtitle": "Commercial qualification, client requirements, and opportunity management.",
            "page_icon": "💼",
            "stale_threshold_days": 14,
            "stages": b2b_stages,
            "initial_stage": "inquiry",
            "fields": b2b_fields,
            "navigation": [
                {"id": "pipeline", "label": "Pipeline"},
                {"id": "intake", "label": "New Opportunity"},
                {"id": "analytics", "label": "Analytics"},
                {"id": "intelligence", "label": "Intelligence"}
            ],
            "features": {
                "create_records": True,
                "edit_records": True,
                "activities": True,
                "intelligence": True,
                "reset_demo_data": False,
                "resume_matching": False,
                "screening_qa": False,
                "role_intelligence_docx": False
            },
            "integrations": {
                "google_workspace": False,
                "openai": False,
                "twilio": False,
                "gmail": False
            },
            "labels": {
                "record_singular": "Client Opportunity",
                "record_plural": "Client Opportunities",
                "stage": "Deal Stage",
                "create": "New Opportunity",
                "save": "Save Opportunity",
                "add_note": "Log Interaction",
                "reset": "Reset Demo Data",
                "intelligence": "Client Intelligence"
            },
            "metrics": [
                "meeting_booking_rate",
                "reply_rate",
                "reply_to_meeting_rate",
                "total",
                "active",
                "pipeline_value"
            ],
            "dashboard_modules": [
                "metrics",
                "funnel",
                "table"
            ],
            "seed": "b2b_services_prospects"
        }
    }
    
    # Write config/demo_b2b_services.json
    b2b_config_file = config_dir / "demo_b2b_services.json"
    b2b_config_file.write_text(json.dumps(b2b_config, indent=2), encoding="utf-8")
    print(f"Wrote B2B services config to {b2b_config_file}")
    
    sales_stages = [
        {"id": "identified", "name": "Identified", "category": "open", "active": True, "terminal": False, "milestones": []},
        {"id": "qualified", "name": "Qualified", "category": "open", "active": True, "terminal": False, "milestones": []},
        {"id": "ready", "name": "Ready for Outreach", "category": "open", "active": True, "terminal": False, "milestones": []},
        {"id": "contacted", "name": "Contacted", "category": "active", "active": True, "terminal": False, "milestones": ["contacted"]},
        {"id": "replied", "name": "Replied", "category": "active", "active": True, "terminal": False, "milestones": ["replied"]},
        {"id": "meeting_booked", "name": "Meeting Booked", "category": "active", "active": True, "terminal": False, "milestones": ["meeting"]},
        {"id": "opportunity_created", "name": "Opportunity Created", "category": "converted", "active": False, "terminal": True, "milestones": ["opportunity"]},
        {"id": "disqualified", "name": "Disqualified", "category": "closed", "active": False, "terminal": True, "milestones": []},
        {"id": "no_response", "name": "No Response", "category": "closed", "active": False, "terminal": True, "milestones": []}
    ]
    
    sales_fields = [
        {"key": "company", "label": "Account", "type": "text", "required": True, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "contact", "label": "Prospect Name", "type": "text", "required": True, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "title", "label": "Title", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "email", "label": "Email", "type": "text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "website", "label": "Website", "type": "text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "industry", "label": "Industry", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "company_size", "label": "Company Size", "type": "text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "tech_stack", "label": "Tech Stack", "type": "text", "required": False, "card": True, "table": False, "intake": True, "format": "text"},
        {"key": "acv", "label": "Estimated ACV", "type": "currency", "required": False, "card": True, "table": True, "intake": True, "format": "currency"},
        {"key": "opportunity_brief", "label": "Opportunity Brief", "type": "long_text", "required": False, "card": True, "table": False, "intake": True, "format": "text"},
        {"key": "pain_points", "label": "Pain Points & Needs", "type": "long_text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "desired_outcome", "label": "Desired Outcome", "type": "long_text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "icp_fit", "label": "ICP Fit", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "intent_signals", "label": "Intent & Buying Signals", "type": "long_text", "required": False, "card": True, "table": False, "intake": True, "format": "text"},
        {"key": "qualification_notes", "label": "Qualification Notes", "type": "long_text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "opportunity_owner", "label": "Opportunity Owner", "type": "text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "source", "label": "Lead Source", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "priority", "label": "Priority", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "next_action", "label": "Next Action", "type": "text", "required": False, "card": True, "table": True, "intake": True, "format": "text"},
        {"key": "next_action_date", "label": "Next Action Due", "type": "date", "required": False, "card": True, "table": True, "intake": True, "format": "date"},
        {"key": "follow_up_status", "label": "Follow-up Status", "type": "text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "notes", "label": "Account Notes", "type": "long_text", "required": False, "card": False, "table": False, "intake": True, "format": "text"},
        {"key": "fit_rationale", "label": "Fit Rationale", "type": "long_text", "required": False, "card": False, "table": False, "intake": False, "format": "text"},
        {"key": "opportunity_rationale", "label": "Opportunity Rationale", "type": "long_text", "required": False, "card": False, "table": False, "intake": False, "format": "text"},
        {"key": "suggested_action", "label": "Suggested Action", "type": "text", "required": False, "card": False, "table": False, "intake": False, "format": "text"},
        {"key": "suggested_angle", "label": "Suggested Outreach Angle", "type": "long_text", "required": False, "card": False, "table": False, "intake": False, "format": "text"},
        {"key": "discovery_questions", "label": "Discovery Questions", "type": "long_text", "required": False, "card": False, "table": False, "intake": False, "format": "text"},
        {"key": "objections", "label": "Potential Objections", "type": "long_text", "required": False, "card": False, "table": False, "intake": False, "format": "text"},
    ]
    
    sales_rep_config = {
        "instance_config": {
            "schema_version": 1,
            "instance_id": "sales-rep-demo",
            "mode": "demo",
            "storage": "memory",
            "pipeline_type": "sales_rep_outbound",
            "display_name": "More Outbound",
            "page_title": "More Outbound — Sales Prospecting & Pipeline Intelligence",
            "page_subtitle": "Know who to contact, why they're worth contacting, what to say, and what to do next.",
            "page_icon": "🎯",
            "stale_threshold_days": 7,
            "stages": sales_stages,
            "initial_stage": "identified",
            "fields": sales_fields,
            "navigation": [
                {"id": "pipeline", "label": "Pipeline"},
                {"id": "intake", "label": "Add Prospect"},
                {"id": "analytics", "label": "Analytics"},
                {"id": "intelligence", "label": "Intelligence"}
            ],
            "features": {
                "create_records": True,
                "edit_records": True,
                "activities": True,
                "intelligence": True,
                "reset_demo_data": False,
                "resume_matching": False,
                "screening_qa": False,
                "role_intelligence_docx": False
            },
            "integrations": {
                "google_workspace": False,
                "openai": False,
                "twilio": False,
                "gmail": False
            },
            "labels": {
                "record_singular": "Prospect",
                "record_plural": "Prospects",
                "stage": "Pipeline Stage",
                "create": "Add Prospect",
                "save": "Save Changes",
                "add_note": "Log Activity",
                "reset": "Reset Demo Data",
                "intelligence": "Prospect Intelligence"
            },
            "metrics": [
                "meeting_booking_rate",
                "reply_rate",
                "reply_to_meeting_rate",
                "total",
                "active",
                "pipeline_value"
            ],
            "dashboard_modules": [
                "metrics",
                "funnel",
                "table"
            ],
            "seed": "b2b_prospects"
        }
    }
    
    # Write config/demo_sales_rep.json and config/demo.json
    sales_config_file = config_dir / "demo_sales_rep.json"
    sales_config_file.write_text(json.dumps(sales_rep_config, indent=2), encoding="utf-8")
    print(f"Wrote sales rep config to {sales_config_file}")
    
    demo_file = config_dir / "demo.json"
    demo_file.write_text(json.dumps(sales_rep_config, indent=2), encoding="utf-8")
    print(f"Updated default demo config {demo_file}")
    
    # Validation check
    sales_cfg = PipelineInstanceConfig.model_validate(sales_rep_config["instance_config"])
    sales_store = MemoryRecordStorage(sales_cfg, sales_records)
    print("Sales store validated successfully with", len(sales_store.list_records()), "records")
    
    b2b_cfg = PipelineInstanceConfig.model_validate(b2b_config["instance_config"])
    b2b_store = MemoryRecordStorage(b2b_cfg, b2b_records)
    print("B2B store validated successfully with", len(b2b_store.list_records()), "records")
    
    # Check exact cohort metrics for test_outreach_demo compatibility
    c, cur = historical_cohorts(sales_records, sales_cfg)
    cohort_counts = {k: len(v) for k, v in c.items()}
    print("Sales cohorts:", cohort_counts)
    assert cohort_counts == {'total': 40, 'contacted': 30, 'replied': 17, 'meeting': 10, 'opportunity': 4}, f"Cohort mismatch: {cohort_counts}"
    
    metrics = calculate_metrics(sales_records, sales_cfg)
    print("Active prospects:", metrics['active']['value'])
    assert metrics['active']['value'] == 32
    print("Pipeline ACV:", metrics['pipeline_value']['value'])
    assert metrics['pipeline_value']['value'] == 1128000
    print("ALL VALIDATION CHECKS PASSED!")


if __name__ == "__main__":
    main()

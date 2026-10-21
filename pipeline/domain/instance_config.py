"""Finite, versioned instance capabilities; no executable configuration."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Milestone = Literal['contacted', 'replied', 'meeting', 'opportunity']
Metric = Literal['meeting_booking_rate', 'reply_rate', 'reply_to_meeting_rate', 'total', 'active', 'pipeline_value']
FIELD_TYPES = {
    # Core Identity & Account
    'company': 'text', 'contact': 'text', 'title': 'text', 'email': 'text',
    'phone': 'text', 'website': 'text', 'industry': 'text', 'company_size': 'text', 'tech_stack': 'text',
    # Opportunity Context
    'opportunity_brief': 'long_text', 'pain_points': 'long_text', 'desired_outcome': 'long_text',
    'icp_fit': 'text', 'intent_signals': 'long_text', 'acv': 'currency',
    'qualification_notes': 'long_text', 'opportunity_owner': 'text',
    # Pipeline, Attribution & Execution
    'source': 'text', 'priority': 'text', 'next_action': 'text',
    'next_action_date': 'date', 'follow_up_status': 'text', 'notes': 'long_text',
    'last_activity_date': 'date',
    # Structured Intelligence
    'fit_rationale': 'long_text', 'opportunity_rationale': 'long_text',
    'suggested_action': 'text', 'suggested_angle': 'long_text',
    'discovery_questions': 'long_text', 'objections': 'long_text',
}


class StrictConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')


class StageConfig(StrictConfig):
    id: str = Field(min_length=1, pattern=r'^[a-z][a-z0-9_]*$')
    name: str = Field(min_length=1)
    category: Literal['open', 'active', 'converted', 'closed'] = 'open'
    active: bool = True
    terminal: bool = False
    milestones: list[Milestone] = Field(default_factory=list)

    @model_validator(mode='after')
    def coherent(self):
        if self.terminal and self.active:
            raise ValueError('Terminal stages cannot be active')
        if len(self.milestones) != len(set(self.milestones)):
            raise ValueError('Duplicate stage milestones')
        return self


class FieldConfig(StrictConfig):
    key: str
    label: str = Field(min_length=1)
    type: Literal['text', 'long_text', 'currency', 'date'] = 'text'
    required: bool = False
    visible: bool = True
    editable: bool = True
    intake: bool = True
    card: bool = False
    table: bool = True
    format: Literal['text', 'currency', 'date'] = 'text'
    max_length: int = Field(default=2000, ge=1, le=10000)

    @model_validator(mode='after')
    def supported(self):
        if FIELD_TYPES.get(self.key) != self.type:
            raise ValueError('Unsupported field key/type combination')
        expected = self.type if self.type in ('currency', 'date') else 'text'
        if self.format != expected:
            raise ValueError('Field format must match its type')
        if self.required and not (self.visible and self.editable and self.intake):
            raise ValueError('Required fields must be available at intake')
        return self


class NavigationConfig(StrictConfig):
    id: Literal['pipeline', 'intake', 'analytics', 'intelligence']
    label: str = Field(min_length=1)


class FeatureConfig(StrictConfig):
    create_records: bool = True
    edit_records: bool = True
    activities: bool = True
    intelligence: bool = True
    reset_demo_data: bool = False
    resume_matching: bool = True
    screening_qa: bool = True
    role_intelligence_docx: bool = True


class IntegrationConfig(StrictConfig):
    google_workspace: bool = True
    openai: bool = True
    twilio: bool = False
    gmail: bool = False


class LabelsConfig(StrictConfig):
    record_singular: str = 'Opportunity'
    record_plural: str = 'Opportunities'
    stage: str = 'Stage'
    create: str = 'Add Opportunity'
    save: str = 'Save Changes'
    add_note: str = 'Add Note'
    reset: str = 'Reset Demo Data'
    intelligence: str = 'Intelligence'
    metric_labels: dict[str, str] = Field(default_factory=dict)


class InstanceCapabilities(StrictConfig):
    schema_version: Literal[1] = 1
    mode: Literal['private', 'demo'] = 'private'
    storage: Literal['google', 'memory'] = 'google'
    seed: Literal['empty', 'b2b_prospects', 'sales_rep_prospects', 'b2b_services_prospects'] = 'empty'
    stages: list[StageConfig] = Field(default_factory=list)
    initial_stage: str = ''
    fields: list[FieldConfig] = Field(default_factory=list)
    navigation: list[NavigationConfig] = Field(default_factory=list)
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    integrations: IntegrationConfig = Field(default_factory=IntegrationConfig)
    labels: LabelsConfig = Field(default_factory=LabelsConfig)
    metrics: list[Metric] = Field(default_factory=list)
    dashboard_modules: list[Literal['metrics', 'funnel', 'table']] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_instance(self):
        for values in ([s.id for s in self.stages], [s.name for s in self.stages],
                       [f.key for f in self.fields], [n.id for n in self.navigation],
                       [n.label for n in self.navigation], self.metrics, self.dashboard_modules):
            if len(values) != len(set(values)):
                raise ValueError('Duplicate configuration identifiers')
        if self.initial_stage and self.initial_stage not in {s.id for s in self.stages}:
            raise ValueError('Unknown initial stage')
        if self.mode == 'demo':
            if self.storage != 'memory' or any(self.integrations.model_dump().values()):
                raise ValueError('Demo requires memory storage and disabled integrations')
            if any((self.features.resume_matching, self.features.screening_qa, self.features.role_intelligence_docx)):
                raise ValueError('Private capabilities are unavailable in public demo')
            if not (self.stages and self.fields and self.navigation and self.initial_stage):
                raise ValueError('Demo stages, fields, navigation and initial stage are required')
            if not any(f.required for f in self.fields):
                raise ValueError('Demo needs a required identifying field')
            if 'pipeline' not in {n.id for n in self.navigation}:
                raise ValueError('Pipeline navigation is required')
            if any(n.id == 'intelligence' for n in self.navigation) and not self.features.intelligence:
                raise ValueError('Intelligence navigation requires its feature')
            if any(n.id == 'intake' for n in self.navigation) and not self.features.create_records:
                raise ValueError('Intake navigation requires record creation')
            if 'metrics' in self.dashboard_modules and not self.metrics:
                raise ValueError('Metrics dashboard requires metrics')
            if 'pipeline_value' in self.metrics and 'acv' not in {f.key for f in self.fields}:
                raise ValueError('Pipeline value requires the ACV field')
            if (getattr(self, 'logo_path', None) or getattr(self, 'favicon_path', None)):
                raise ValueError('Public branding cannot reference local private files')
        return self

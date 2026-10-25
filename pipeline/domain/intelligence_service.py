"""Account intelligence for actionable outreach."""
import json
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field


class IntelligenceItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1)
    title: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    context: str = ''
    pain_points: list[str] = Field(default_factory=list)
    outreach_angles: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)


class IntelligenceService:
    @staticmethod
    def load_intel(path):
        items = [IntelligenceItem.model_validate(item) for item in json.loads(Path(path).read_text(encoding='utf-8'))]
        if len({item.id for item in items}) != len(items):
            raise ValueError('Duplicate intelligence IDs')
        return items

    @staticmethod
    def get_cue_cards(items, query='', limit=6):
        tokens = set(query.lower().split())
        def score(item):
            searchable = [item.title, item.summary, item.context, *item.tags, *item.signals, *item.pain_points, *item.outreach_angles]
            words = set(' '.join(searchable).lower().split())
            return len(tokens & words)
        ranked = sorted(items, key=lambda item: (-score(item), item.id))
        return [i for i in ranked if not tokens or score(i)][:limit]

    @staticmethod
    def load_career_stories(path):
        from pipeline.domain.story_bank import StoryBankService
        return StoryBankService.load_stories(file_path=str(path))

    @staticmethod
    def career_cue_cards(*, file_path, **kwargs):
        from pipeline.domain.story_bank import StoryBankService
        return StoryBankService.suggest_story_cue_cards(file_path=str(file_path), **kwargs)

"""Per-session storage. No globals, caches, filesystem writes or providers."""
from copy import deepcopy
from job_pipeline.domain.records import PipelineRecord, StageEvent, Activity, validate_fields


class MemoryRecordStorage:
    def __init__(self, config, seed=()):
        self.config = config
        self._seed = [PipelineRecord.model_validate(deepcopy(row)) for row in seed]
        ids = [r.id for r in self._seed]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate seed IDs')
        for record in self._seed:
            self._stage(record.stage_id)
            validate_fields(config, record.fields)
            for event in record.stage_history:
                self._stage(event.stage_id)
        self.reset()

    def _stage(self, stage_id):
        if stage_id not in {s.id for s in self.config.stages}:
            raise ValueError('Unknown stage')

    def reset(self):
        self._records = {r.id: r.model_copy(deep=True) for r in self._seed}

    def list_records(self):
        return [r.model_copy(deep=True) for r in self._records.values()]

    def create(self, fields, stage_id=None):
        stage_id = stage_id or self.config.initial_stage
        self._stage(stage_id)
        record = PipelineRecord(stage_id=stage_id, fields=validate_fields(self.config, fields),
                                stage_history=[StageEvent(stage_id=stage_id)])
        self._records[record.id] = record
        return record.model_copy(deep=True)

    def update(self, record_id, fields, stage_id):
        self._stage(stage_id)
        record = self._records[record_id].model_copy(deep=True)
        editable = {f.key for f in self.config.fields if f.editable}
        if set(fields) - editable:
            raise ValueError('Field is not editable')
        clean = validate_fields(self.config, {**record.fields, **fields})
        if clean.get('notes') != record.fields.get('notes'):
            record.activities.append(Activity(kind='note', text=clean.get('notes') or 'Notes cleared'))
        record.fields = clean
        if record.stage_id != stage_id:
            record.stage_id = stage_id
            record.stage_history.append(StageEvent(stage_id=stage_id))
        self._records[record_id] = record

    def add_activity(self, record_id, kind, text):
        if not text.strip() or len(text) > 2000:
            raise ValueError('Activity text must contain 1–2000 characters')
        event = Activity(kind=kind, text=text.strip())
        self._records[record_id].activities.append(event)

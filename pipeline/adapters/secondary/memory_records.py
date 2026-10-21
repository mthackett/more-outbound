"""Per-session storage. No globals, caches, filesystem writes or providers."""
from copy import deepcopy
from pipeline.domain.records import PipelineRecord, StageEvent, Activity, ActionItem, timestamp, validate_fields
from pipeline.domain.demo_dates import session_reference, materialize_seed, is_relative


class MemoryRecordStorage:
    def __init__(self, config, seed=(), reference=None):
        self.config = config
        self.reference = reference or session_reference()
        date_fields = [f.key for f in config.fields if f.type == 'date']

        self._raw_seed = deepcopy(list(seed))
        has_relative = False
        for row in self._raw_seed:
            if isinstance(row, dict):
                if is_relative(row.get('created_at')):
                    has_relative = True
                    break
                for e in row.get('stage_history') or []:
                    if is_relative(e.get('entered_at')):
                        has_relative = True
                        break
                if has_relative:
                    break
                for a in row.get('actions') or []:
                    if is_relative(a.get('due_date')) or is_relative(a.get('completed_at')):
                        has_relative = True
                        break
                if has_relative:
                    break
                for v in (row.get('fields') or {}).values():
                    if is_relative(v):
                        has_relative = True
                        break
                if has_relative:
                    break

        self._has_relative = has_relative
        if has_relative:
            materialized = materialize_seed(self._raw_seed, self.reference, date_fields)
        else:
            materialized = self._raw_seed

        self._seed = [PipelineRecord.model_validate(deepcopy(row)) for row in materialized]
        ids = [r.id for r in self._seed]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate seed IDs')
        for record in self._seed:
            self._stage(record.stage_id)
            validate_fields(config, record.fields)
            for event in record.stage_history:
                self._stage(event.stage_id)
            if not record.actions and record.fields.get('next_action'):
                record.actions.append(ActionItem(
                    id=f"action-{record.id}-01",
                    record_id=record.id,
                    description=record.fields['next_action'],
                    due_date=record.fields.get('next_action_date'),
                    status='open',
                    created_at=record.created_at
                ))
        self.reset()

    def _stage(self, stage_id):
        if stage_id not in {s.id for s in self.config.stages}:
            raise ValueError('Unknown stage')

    def reset(self):
        if getattr(self, '_has_relative', False):
            date_fields = [f.key for f in self.config.fields if f.type == 'date']
            materialized = materialize_seed(self._raw_seed, self.reference, date_fields)
            records = [PipelineRecord.model_validate(r) for r in materialized]
            for r in records:
                if not r.actions and r.fields.get('next_action'):
                    r.actions.append(ActionItem(
                        id=f"action-{r.id}-01",
                        record_id=r.id,
                        description=r.fields['next_action'],
                        due_date=r.fields.get('next_action_date'),
                        status='open',
                        created_at=r.created_at
                    ))
            self._records = {r.id: r for r in records}
        else:
            self._records = {r.id: r.model_copy(deep=True) for r in self._seed}

    def list_records(self):
        return [r.model_copy(deep=True) for r in self._records.values()]

    def create(self, fields, stage_id=None):
        stage_id = stage_id or self.config.initial_stage
        self._stage(stage_id)
        clean = validate_fields(self.config, fields)
        record = PipelineRecord(stage_id=stage_id, fields=clean,
                                stage_history=[StageEvent(stage_id=stage_id)])
        if clean.get('next_action'):
            record.actions.append(ActionItem(
                record_id=record.id,
                description=clean['next_action'],
                due_date=clean.get('next_action_date'),
                status='open'
            ))
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
        
        if 'next_action' in fields or 'next_action_date' in fields:
            current = record.current_action
            new_desc = clean.get('next_action')
            new_due = clean.get('next_action_date')
            if new_desc:
                if current:
                    current.description = new_desc
                    current.due_date = new_due
                else:
                    record.actions.append(ActionItem(
                        record_id=record.id,
                        description=new_desc,
                        due_date=new_due,
                        status='open'
                    ))
            elif current and not new_desc:
                current.status = 'completed'
                current.completed_at = timestamp()

        record.fields = clean
        if record.stage_id != stage_id:
            record.stage_id = stage_id
            record.stage_history.append(StageEvent(stage_id=stage_id))
        self._records[record_id] = record

    def complete_action(self, record_id, note=None, new_next_action=None, new_next_action_date=None):
        record = self._records[record_id].model_copy(deep=True)
        action = record.current_action
        desc = action.description if action else (record.fields.get('next_action') or 'Scheduled action')
        if action:
            action.status = 'completed'
            action.completed_at = timestamp()
        else:
            record.actions.append(ActionItem(
                record_id=record.id,
                description=desc,
                due_date=record.fields.get('next_action_date'),
                status='completed',
                completed_at=timestamp()
            ))

        completion_msg = f"Completed action: {desc}"
        if note and str(note).strip():
            completion_msg += f" — {str(note).strip()}"
        record.activities.append(Activity(kind='follow_up', text=completion_msg))

        if new_next_action and str(new_next_action).strip():
            new_due_str = str(new_next_action_date)[:10] if new_next_action_date else None
            new_item = ActionItem(
                record_id=record.id,
                description=str(new_next_action).strip(),
                due_date=new_due_str,
                status='open'
            )
            record.actions.append(new_item)
            record.fields['next_action'] = new_item.description
            record.fields['next_action_date'] = new_due_str
            record.activities.append(Activity(kind='follow_up', text=f"Scheduled next action for {new_due_str or 'TBD'}: {new_item.description}"))
        else:
            record.fields['next_action'] = ''
            record.fields['next_action_date'] = None

        self._records[record_id] = record
        return record.model_copy(deep=True)

    def reschedule_action(self, record_id, new_due_date, reason=None):
        record = self._records[record_id].model_copy(deep=True)
        action = record.current_action
        if not action and record.fields.get('next_action'):
            action = ActionItem(
                record_id=record.id,
                description=record.fields['next_action'],
                due_date=record.fields.get('next_action_date'),
                status='open'
            )
            record.actions.append(action)
        if action:
            new_due_str = str(new_due_date)[:10] if new_due_date else None
            action.due_date = new_due_str
            record.fields['next_action_date'] = new_due_str
            msg = f"Rescheduled action to {new_due_str or 'TBD'}: {action.description}"
            if reason and str(reason).strip():
                msg += f" ({str(reason).strip()})"
            record.activities.append(Activity(kind='follow_up', text=msg))
        self._records[record_id] = record
        return record.model_copy(deep=True)

    def schedule_action(self, record_id, description, due_date):
        if not str(description).strip():
            raise ValueError('Action description is required')
        record = self._records[record_id].model_copy(deep=True)
        for a in record.actions:
            if a.status == 'open':
                a.status = 'canceled'
        new_due_str = str(due_date)[:10] if due_date else None
        new_item = ActionItem(
            record_id=record.id,
            description=str(description).strip(),
            due_date=new_due_str,
            status='open'
        )
        record.actions.append(new_item)
        record.fields['next_action'] = new_item.description
        record.fields['next_action_date'] = new_due_str
        record.activities.append(Activity(kind='follow_up', text=f"Scheduled next action for {new_due_str or 'TBD'}: {new_item.description}"))
        self._records[record_id] = record
        return record.model_copy(deep=True)

    def add_activity(self, record_id, kind, text, complete_action=False):
        if not text.strip() or len(text) > 2000:
            raise ValueError('Activity text must contain 1–2000 characters')
        event = Activity(kind=kind, text=text.strip())
        record = self._records[record_id].model_copy(deep=True)
        record.activities.append(event)
        if complete_action:
            action = record.current_action
            desc = action.description if action else (record.fields.get('next_action') or 'Scheduled action')
            if action:
                action.status = 'completed'
                action.completed_at = timestamp()
            else:
                record.actions.append(ActionItem(
                    record_id=record.id,
                    description=desc,
                    due_date=record.fields.get('next_action_date'),
                    status='completed',
                    completed_at=timestamp()
                ))
            record.activities.append(Activity(kind='follow_up', text=f"Completed action: {desc}"))
            record.fields['next_action'] = ''
            record.fields['next_action_date'] = None
        self._records[record_id] = record

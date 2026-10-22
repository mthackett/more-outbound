"""Read-only, strict public loader, separate from legacy preferences."""
import json
from pathlib import Path
from pydantic import ValidationError
from pipeline.domain.models import PipelineInstanceConfig

DEFAULT_DEMO_CONFIG = Path(__file__).resolve().parents[2] / 'config' / 'demo_sales_rep.json'


class InstanceConfigError(ValueError):
    pass


def load_demo_config(path=None):
    try:
        data = json.loads(Path(path or DEFAULT_DEMO_CONFIG).read_text(encoding='utf-8'))
        if not isinstance(data, dict) or set(data) != {'instance_config'}:
            raise ValueError('Expected an instance_config object')
        raw = data['instance_config']
        required = {'schema_version', 'instance_id', 'mode', 'storage', 'integrations',
                    'features', 'stages', 'initial_stage', 'fields', 'navigation'}
        if not isinstance(raw, dict) or not required <= raw.keys():
            raise ValueError('Missing explicit demo configuration')
        config = PipelineInstanceConfig.model_validate(raw)
        if config.mode != 'demo':
            raise ValueError('Public entry requires a demo configuration')
        return config
    except (OSError, UnicodeError, ValueError, ValidationError) as exc:
        # Never echo paths, JSON contents, or provider settings to the public page.
        raise InstanceConfigError('Demo configuration is missing or invalid. No integrations were started.') from exc

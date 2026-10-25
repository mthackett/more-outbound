"""Startup guards. Importing this module never loads settings or providers."""


def public_mode(environ):
    mode = environ.get('PIPELINE_MODE', '').strip().lower()
    demo = environ.get('DEMO_MODE', '').strip().lower()
    if mode not in ('', 'demo') or demo not in ('', 'true', 'false', '1', '0'):
        raise ValueError('Invalid instance mode')
    return True



def select_session(state, identity):
    """Discard adapter, data and widget state when the instance identity changes."""
    if state.get('_instance_identity') != identity:
        for key in list(state):
            del state[key]
        state['_instance_identity'] = identity


def offline_adapters(state):
    if '_offline_adapters' not in state:
        from pipeline.adapters.secondary.mock_adapter import (
            MockJobStorageAdapter, MockDocumentStorageAdapter,
            MockResumeRepositoryAdapter, MockLLMStrategyAdapter,
        )
        state['_offline_adapters'] = (
            MockJobStorageAdapter(), MockDocumentStorageAdapter(),
            MockResumeRepositoryAdapter(), MockLLMStrategyAdapter(), None, None,
        )
    return state['_offline_adapters']

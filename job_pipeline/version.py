"""Legacy leaf alias; shares the canonical module and all class/state identity."""
import importlib
import sys
sys.modules[__name__] = importlib.import_module("pipeline.version")

"""Read-only dashboard fallbacks; integrity/programming errors still propagate."""
from copy import deepcopy
from gspread.exceptions import APIError
from google.auth.exceptions import GoogleAuthError
from requests.exceptions import RequestException


def dashboard_records(storage, cached):
    if not storage.is_connected:
        return deepcopy(cached or []), True
    try:
        return storage.fetch_all_opportunities(), False
    except (OSError, APIError, GoogleAuthError, RequestException):
        return deepcopy(cached or []), True

from __future__ import annotations

import re

DEFAULT_CURRENCY = "RUB"

STATUS_ACTIVE = "действует"
STATUS_INACTIVE = "не действует"

CODE_PATTERN = re.compile(r"[A-Za-z0-9_]+")

SECONDS_PER_YEAR = 365.25 * 24 * 3600

ALL_RECORDS_PAGE_SIZE = 100_000

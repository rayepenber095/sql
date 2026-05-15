import re

from core.models import BaselineResponse, ScanResult


DB_ERROR_SIGNATURES = [
    "you have an error in your sql syntax",
    "warning: mysqli",
    "warning: mysql",
    "unclosed quotation mark after the character string",
    "quoted string not properly terminated",
    "pg_query(): query failed",
    "pg_exec(): query failed",
    "supplied argument is not a valid postgresql",
    "invalid input syntax for type",
    "unterminated string literal",
    "odbc sql server driver",
    "microsoft ole db provider for sql server",
    "microsoft jet database engine",
    "error converting data type",
    "sqlite_exception",
    "sqlite3::",
    "ora-00933",
    "ora-00907",
    "ora-01756",
    "ora-00936",
    "db2 sql error",
    "cli driver",
    "sqlstate",
    "syntax error at or near",
    "division by zero",
    "invalid column name",
    "invalid object name",
    "column does not exist",
]


def analyze_response(
    result: ScanResult,
    baseline: BaselineResponse,
) -> tuple[bool, str | None, str | None]:
    body_lower = result.response_body.lower()
    for sig in DB_ERROR_SIGNATURES:
        if sig in body_lower:
            return True, "Error-Based SQLi", "HIGH"

    if result.category == "union":
        if result.response_length > baseline.response_length * 1.3:
            return True, "Union-Based SQLi", "MEDIUM"

    if result.category == "blind_time":
        expected_seconds = extract_sleep_seconds(result.payload)
        if result.response_time_ms >= (expected_seconds * 1000 * 0.75):
            return True, "Time-Based Blind SQLi", "HIGH"

    if result.category == "auth_bypass":
        if result.status_code in (301, 302, 303, 307, 308):
            return True, "Auth Bypass SQLi", "HIGH"
        body_lower = result.response_body.lower()
        auth_success_keywords = [
            "welcome",
            "dashboard",
            "logout",
            "log out",
            "sign out",
            "my account",
            "profile",
            "admin panel",
        ]
        for kw in auth_success_keywords:
            if kw in body_lower:
                return True, "Auth Bypass SQLi", "MEDIUM"

    if result.status_code == 500 and baseline.status_code != 500:
        return True, "Possible Error-Based SQLi (HTTP 500)", "LOW"

    return False, None, None


def extract_sleep_seconds(payload: str) -> float:
    sleep_match = re.search(r"SLEEP\((\d+(?:\.\d+)?)\)", payload, re.I)
    if sleep_match:
        return float(sleep_match.group(1))

    delay_match = re.search(r"DELAY\s+'0:0:(\d+)'", payload, re.I)
    if delay_match:
        return float(delay_match.group(1))

    pg_sleep_match = re.search(r"pg_sleep\((\d+(?:\.\d+)?)\)", payload, re.I)
    if pg_sleep_match:
        return float(pg_sleep_match.group(1))

    return 5.0

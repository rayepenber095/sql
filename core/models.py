from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class FormField:
    name: str
    field_type: str
    value: str = ""


@dataclass
class FormVector:
    url: str
    method: str
    fields: List[FormField] = field(default_factory=list)
    source_page: str = ""


@dataclass
class ParamVector:
    url: str
    param_name: str
    param_value: str = ""
    method: str = "GET"


@dataclass
class CookieVector:
    name: str
    value: str
    url: str


@dataclass
class SiteMap:
    target_url: str
    pages: List[str] = field(default_factory=list)
    forms: List[FormVector] = field(default_factory=list)
    param_vectors: List[ParamVector] = field(default_factory=list)
    cookies: List[CookieVector] = field(default_factory=list)

    def all_vectors(self) -> list:
        vectors = []
        vectors.extend({"type": "form", "data": v} for v in self.forms)
        vectors.extend({"type": "param", "data": v} for v in self.param_vectors)
        vectors.extend({"type": "cookie", "data": v} for v in self.cookies)
        return vectors


@dataclass
class ScanResult:
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: int = 0
    vector_type: str = ""
    url: str = ""
    parameter: str = ""
    category: str = ""
    payload: str = ""
    status_code: int = 0
    response_time_ms: float = 0.0
    response_body: str = ""
    response_length: int = 0
    vulnerable: bool = False
    vuln_type: Optional[str] = None
    confidence: Optional[str] = None


@dataclass
class BaselineResponse:
    url: str
    status_code: int = 200
    response_length: int = 0
    response_time_ms: float = 0.0
    body_snippet: str = ""


@dataclass
class SessionRow:
    id: int
    target_url: str
    started_at: str
    ended_at: str = ""
    total_reqs: int = 0
    vulns_found: int = 0


@dataclass
class RateConfig:
    requests_per_second: float = 5.0
    max_threads: int = 10
    request_timeout_sec: int = 10
    max_total_requests: int = 0
    delay_between_ms: int = 0


CATEGORY_FILE_MAP: Dict[str, str] = {
    "union": "union_payloads.txt",
    "blind_boolean": "blind_boolean_payloads.txt",
    "blind_time": "blind_time_payloads.txt",
    "error_based": "error_based_payloads.txt",
    "stacked": "stacked_queries_payloads.txt",
    "oob": "out_of_band_payloads.txt",
    "auth_bypass": "auth_bypass_payloads.txt",
    "second_order": "second_order_payloads.txt",
    "waf_bypass": "waf_bypass_payloads.txt",
}

CATEGORY_DISPLAY_NAMES: Dict[str, str] = {
    "union": "Union-Based",
    "blind_boolean": "Boolean Blind",
    "blind_time": "Time-Based Blind",
    "error_based": "Error-Based",
    "stacked": "Stacked Queries",
    "oob": "Out-of-Band",
    "auth_bypass": "Auth Bypass",
    "second_order": "Second Order",
    "waf_bypass": "WAF Bypass",
}

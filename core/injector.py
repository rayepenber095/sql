from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import threading
import time

import requests
from PyQt6.QtCore import QThread, pyqtSignal

from core.analyzer import analyze_response
from core.history_manager import HistoryManager
from core.models import (
    CATEGORY_FILE_MAP,
    BaselineResponse,
    CookieVector,
    FormVector,
    ParamVector,
    RateConfig,
    ScanResult,
    SiteMap,
)
from core.rate_controller import RateLimiter


class InjectorWorker(QThread):
    scan_started = pyqtSignal(int)
    result_ready = pyqtSignal(object)
    progress_updated = pyqtSignal(int, int)
    scan_paused = pyqtSignal()
    scan_resumed = pyqtSignal()
    scan_complete = pyqtSignal(int, int)
    scan_error = pyqtSignal(str)

    def __init__(
        self,
        site_map: SiteMap,
        payloads: dict,
        rate_config: RateConfig,
        headers: dict,
        session_id: int,
        history: HistoryManager,
        wordlists_dir: str = "wordlists",
    ):
        super().__init__()
        self.site_map = site_map
        self.payloads = payloads
        self.rate_config = rate_config
        self.headers = headers
        self.session_id = session_id
        self.history = history
        self.wordlists_dir = wordlists_dir
        self._stop_flag = False
        self._limiter = RateLimiter(rate_config.requests_per_second)
        self._completed = 0
        self._vulns = 0
        self._lock = threading.Lock()

    def stop(self) -> None:
        self._stop_flag = True

    def pause(self) -> None:
        self._limiter.pause()
        self.scan_paused.emit()

    def resume(self) -> None:
        self._limiter.resume()
        self.scan_resumed.emit()

    def set_rps(self, rps: float) -> None:
        self._limiter.set_rps(rps)

    def run(self) -> None:
        try:
            jobs = []
            for form_vector in self.site_map.forms:
                for field in form_vector.fields:
                    if field.field_type in ("submit", "button", "image", "reset"):
                        continue
                    for category, payload_list in self.payloads.items():
                        for payload in payload_list:
                            jobs.append(("form", form_vector, field, category, payload))

            for param_vector in self.site_map.param_vectors:
                for category, payload_list in self.payloads.items():
                    for payload in payload_list:
                        jobs.append(("param", param_vector, None, category, payload))

            for cookie_vector in self.site_map.cookies:
                for category, payload_list in self.payloads.items():
                    for payload in payload_list:
                        jobs.append(("cookie", cookie_vector, None, category, payload))

            if self.rate_config.max_total_requests > 0:
                jobs = jobs[: self.rate_config.max_total_requests]

            self.scan_started.emit(len(jobs))
            total = len(jobs)

            baselines = {}
            unique_urls = set()
            for f in self.site_map.forms:
                unique_urls.add(f.url)
            for p in self.site_map.param_vectors:
                unique_urls.add(p.url)
            for c in self.site_map.cookies:
                unique_urls.add(c.url)

            for url in unique_urls:
                try:
                    r = requests.get(url, headers=self.headers, timeout=self.rate_config.request_timeout_sec)
                    baselines[url] = BaselineResponse(
                        url=url,
                        status_code=r.status_code,
                        response_length=len(r.text),
                        response_time_ms=r.elapsed.total_seconds() * 1000,
                        body_snippet=r.text[:500],
                    )
                except Exception:
                    baselines[url] = BaselineResponse(url=url)

            with ThreadPoolExecutor(max_workers=self.rate_config.max_threads) as pool:
                futures = {}
                for job in jobs:
                    if self._stop_flag:
                        break
                    f = pool.submit(self._send_job, job, baselines)
                    futures[f] = job

                for future in as_completed(futures):
                    if self._stop_flag:
                        break
                    result = future.result()
                    if result is None:
                        continue
                    with self._lock:
                        self._completed += 1
                        if result.vulnerable:
                            self._vulns += 1
                    self.history.save_result(result)
                    self.result_ready.emit(result)
                    self.progress_updated.emit(self._completed, total)

            self.history.close_session(self.session_id, self._completed, self._vulns)
            self.scan_complete.emit(self._completed, self._vulns)
        except Exception as e:
            self.scan_error.emit(str(e))

    def _send_job(self, job: tuple, baselines: dict) -> ScanResult | None:
        try:
            self._limiter.acquire()
            vector_type_job, vector_obj, field, category, payload = job

            if vector_type_job == "form":
                form_vec: FormVector = vector_obj
                data = {f.name: f.value for f in form_vec.fields}
                data[field.name] = payload
                url = form_vec.url
                start = datetime.now()
                if form_vec.method == "POST":
                    r = requests.post(
                        url,
                        data=data,
                        headers=self.headers,
                        timeout=self.rate_config.request_timeout_sec,
                        allow_redirects=True,
                    )
                else:
                    r = requests.get(
                        url,
                        params=data,
                        headers=self.headers,
                        timeout=self.rate_config.request_timeout_sec,
                        allow_redirects=True,
                    )
                param_name = field.name
                vector_type = "form"

            elif vector_type_job == "param":
                pv: ParamVector = vector_obj
                parsed = urlparse(pv.url)
                params = parse_qs(parsed.query)
                params[pv.param_name] = [payload]
                new_query = urlencode(params, doseq=True)
                injected_url = urlunparse(parsed._replace(query=new_query))
                start = datetime.now()
                r = requests.get(
                    injected_url,
                    headers=self.headers,
                    timeout=self.rate_config.request_timeout_sec,
                    allow_redirects=True,
                )
                url = injected_url
                param_name = pv.param_name
                vector_type = "param"

            else:
                cv: CookieVector = vector_obj
                cookie_headers = dict(self.headers)
                cookie_headers["Cookie"] = f"{cv.name}={payload}"
                start = datetime.now()
                r = requests.get(
                    cv.url,
                    headers=cookie_headers,
                    timeout=self.rate_config.request_timeout_sec,
                    allow_redirects=True,
                )
                url = cv.url
                param_name = cv.name
                vector_type = "cookie"

            if self.rate_config.delay_between_ms > 0:
                time.sleep(self.rate_config.delay_between_ms / 1000)

            elapsed_ms = (datetime.now() - start).total_seconds() * 1000
            result = ScanResult(
                session_id=self.session_id,
                vector_type=vector_type,
                url=url,
                parameter=param_name,
                category=category,
                payload=payload,
                status_code=r.status_code,
                response_time_ms=elapsed_ms,
                response_body=r.text[:5000],
                response_length=len(r.text),
            )

            baseline = baselines.get(vector_obj.url, BaselineResponse(url=vector_obj.url))
            is_vuln, vuln_type, confidence = analyze_response(result, baseline)
            result.vulnerable = is_vuln
            result.vuln_type = vuln_type
            result.confidence = confidence
            return result
        except Exception:
            return None


def load_payloads(selected_categories: list[str], wordlists_dir: str = "wordlists") -> dict:
    payloads: dict[str, list[str]] = {}
    base = Path(wordlists_dir)
    for category in selected_categories:
        filename = CATEGORY_FILE_MAP.get(category)
        if not filename:
            payloads[category] = []
            continue
        path = base / filename
        if not path.exists():
            payloads[category] = []
            continue
        lines = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                text = line.strip()
                if not text or text.startswith("#"):
                    continue
                lines.append(text)
        payloads[category] = lines
    return payloads

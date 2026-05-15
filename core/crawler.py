from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PyQt6.QtCore import QThread, pyqtSignal

from core.models import CookieVector, FormField, FormVector, ParamVector, SiteMap


class CrawlerWorker(QThread):
    page_found = pyqtSignal(str)
    vector_found = pyqtSignal(str, str)
    crawl_complete = pyqtSignal(object)
    crawl_error = pyqtSignal(str)
    progress = pyqtSignal(int, int)

    def __init__(self, target_url: str, max_depth: int = 3, headers: dict = None, max_pages: int = 200):
        super().__init__()
        self.target_url = target_url
        self.max_depth = max_depth
        self.headers = headers or {"User-Agent": "Mozilla/5.0"}
        self.max_pages = max_pages
        self._stop_flag = False

    def stop(self) -> None:
        self._stop_flag = True

    def run(self) -> None:
        try:
            site_map = SiteMap(target_url=self.target_url)
            visited = set()
            queue = [(self.target_url, 0)]
            base_domain = urlparse(self.target_url).netloc

            while queue and len(visited) < self.max_pages:
                if self._stop_flag:
                    break
                url, depth = queue.pop(0)
                if url in visited:
                    continue
                if depth > self.max_depth:
                    continue
                if urlparse(url).netloc != base_domain:
                    continue

                visited.add(url)
                self.progress.emit(len(visited), len(queue))

                try:
                    response = requests.get(url, headers=self.headers, timeout=10, allow_redirects=True)
                except requests.exceptions.RequestException:
                    continue

                if response.status_code not in (200, 301, 302):
                    continue

                site_map.pages.append(url)
                self.page_found.emit(url)

                soup = BeautifulSoup(response.text, "lxml")

                for form in soup.find_all("form"):
                    action = form.get("action", "")
                    action_url = urljoin(url, action) if action else url
                    method = (form.get("method", "get")).upper()
                    fields = []
                    for inp in form.find_all(["input", "textarea", "select"]):
                        name = inp.get("name")
                        if not name:
                            continue
                        fields.append(
                            FormField(
                                name=name,
                                field_type=inp.get("type", "text"),
                                value=inp.get("value", ""),
                            )
                        )
                    if fields:
                        fv = FormVector(url=action_url, method=method, fields=fields, source_page=url)
                        site_map.forms.append(fv)
                        self.vector_found.emit("form", f"{method} {action_url} [{', '.join(f.name for f in fields)}]")

                parsed = urlparse(url)
                if parsed.query:
                    query_values = parse_qs(parsed.query)
                    for param_name in query_values.keys():
                        pv = ParamVector(url=url, param_name=param_name, param_value=query_values[param_name][0])
                        site_map.param_vectors.append(pv)
                        self.vector_found.emit("param", f"GET {url} [{param_name}]")

                for a_tag in soup.find_all("a", href=True):
                    link = urljoin(url, a_tag["href"])
                    link_parsed = urlparse(link)
                    if link_parsed.netloc != base_domain:
                        continue
                    if link not in visited:
                        queue.append((link, depth + 1))
                    if link_parsed.query:
                        link_params = parse_qs(link_parsed.query)
                        for pname in link_params.keys():
                            pv = ParamVector(url=link, param_name=pname, param_value=link_params[pname][0])
                            existing = [(p.url, p.param_name) for p in site_map.param_vectors]
                            if (link, pname) not in existing:
                                site_map.param_vectors.append(pv)
                                self.vector_found.emit("param", f"GET {link} [{pname}]")

                for cookie_name, cookie_val in response.cookies.items():
                    cv = CookieVector(name=cookie_name, value=cookie_val, url=url)
                    existing_names = [c.name for c in site_map.cookies]
                    if cookie_name not in existing_names:
                        site_map.cookies.append(cv)
                        self.vector_found.emit("cookie", f"Cookie: {cookie_name} @ {url}")

            self.crawl_complete.emit(site_map)
        except Exception as e:
            self.crawl_error.emit(str(e))

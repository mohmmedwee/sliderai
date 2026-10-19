# Phase 15: US13, web research (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US13.

---

<a id="t213"></a>
### T213 · Web tool tests (write first)

**Depends on**: T069 · **Parallel**: yes · **Size**: S

**Read first**: contracts/agent-tools.md (`web_search`, `fetch_url`); `MA/tests/{test_web_search_retry,test_search_cap}.py`

**Files**: create `BT/unit/test_web_tools.py`

**Cases**:

1. `fetch_url("http://example.com")` → error (https only).
2. A host resolving to `127.0.0.1`, `10.x`, `172.16–31.x`, `192.168.x`, `169.254.x`, `::1`, or `fc00::/7` → blocked. Mock `getaddrinfo`, and also test **DNS rebinding**: resolve once and connect to that IP.
3. A body over 2 MB → cut off with a note. Non-HTML or non-text → error.
4. HTML → readable text (the port of MA `_TextExtractor`), with scripts and styles removed.
5. With web search off for the thread, neither tool is in `build_tools`.
6. Port the MA retry and cap tests for search.
7. The prompt rule: the eval check (T088 suite `web`) verifies that the cited URLs appear in `notes`. Add 5 cases.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t214"></a>
### T214 · `web_search`

**Depends on**: T213 · **Parallel**: no · **Size**: S

**Read first**: `MAS/clients/search.py` (`SearchBackend`, `DuckDuckGoBackend`); `MAS/services/tools/web_search.py`

**Files**: create `BE/agent/web/search.py` and `BE/agent/tools/web.py`

**Steps**:

1. Port `SearchBackend` and `DuckDuckGoBackend` (ddgs). Add `TavilyBackend` and `BraveBackend` behind `settings.web.search_provider`.
2. The tool returns up to `maxResults` items `{title, url, snippet}` as a numbered list.
3. Limits: 30 calls per turn and 300 per hour per workspace (T036). Over the limit → an "Error: rate_limited" string.


**Acceptance**:
- [ ] The ported MA search tests pass
- [ ] The rate limit returns an error string, not an exception

**Verify**: `uv run pytest tests/unit/test_web_tools.py -q -k search`

---

<a id="t215"></a>
### T215 · `fetch_url` (hardened)

**Depends on**: T213 · **Parallel**: no · **Size**: M

**Read first**: `MAS/clients/search.py` (`PageFetcher`, `_TextExtractor`); `MAS/services/tools/fetch_url.py`

**Files**: modify `BE/agent/web/fetch.py` and `BE/agent/tools/web.py`

**Steps**:

1. Resolve the host with `getaddrinfo`, reject private, loopback, link-local, multicast, and reserved addresses (`ipaddress` module), then connect **to the resolved IP** with the `Host` header and SNI set (an httpx transport with a custom `local_address` won't do this, so use `httpx.AsyncHTTPTransport` with a resolver hook, or `aiohttp`'s resolver).
2. At most 3 redirects, each re-checked.
3. Stream with a 2 MB cap and a 10 s timeout. Allowed content types are `text/html`, `text/plain`, and `application/xhtml+xml`.
4. Extract the text with the ported `_TextExtractor`, clip to 12k characters, and wrap as `<web_content url="…">…</web_content>`.

**Acceptance**:
- [ ] T213 cases 1–4 pass

---

<a id="t216"></a>
### T216 · Web toggle and result blocks

**Depends on**: T214, T215, T085 · **Parallel**: yes · **Size**: S

**Read first**: ux.md §5.2 (`⚙` popover); `MAF/components/chat/{WebSearchResults,FetchUrlResult}.tsx`

**Files**: port `FE/components/chat/{WebSearchResults,FetchUrlResult}.tsx` and modify the Composer `⚙` popover

**Steps**:

1. A "Search the web" switch per thread, stored in `threads.web_search` (data-model.md), set with `PATCH /v1/threads/{id} {webSearch}`. The send request includes `webSearch`. Turn the `web_search` feature flag on.
2. Tool blocks for `web_search` and `fetch_url` render with the ported components (result list with favicons and hosts).
3. The session prompts (`session_web_search_on`/`off`) are already wired in `system_prompt.py`.

**Acceptance**:
- [ ] The toggle persists per thread
- [ ] With it off, no web tools appear in the trace (T213 case 5)
- [ ] The result blocks render in both languages

**Verify**: `pnpm test:e2e -- create` (add a web case with a fake script)

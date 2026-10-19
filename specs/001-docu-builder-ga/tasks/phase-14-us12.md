# Phase 14: US12, connectors over MCP (task cards)

Before any card, read [IMPLEMENTER.md](../IMPLEMENTER.md). **Story test**: quickstart.md › US12.

**Background**: `MAS/services/mcp/` is a mature MCP client with OAuth, sealed secrets, result shrinking, progressive tool groups, and repeat guards, but its state lives in process memory. This phase keeps its logic and moves the state to Postgres and Redis. The tool execution uses `langchain-mcp-adapters`.

---

<a id="t205"></a>
### T205 · MCP test fixture server

**Depends on**: T001 · **Parallel**: yes · **Size**: S

**Files**: create `evals/fixtures/mcp_wiki/server.py` and `evals/fixtures/mcp_wiki/README.md`

**Steps**:

1. A FastMCP server (`mcp` package) over streamable HTTP on port 8765. It has two groups:
   - `reports`: `get_report(name) -> markdown` (returns a fixed "Q3 report" with numbers) and `list_reports()`
   - `pages`: `create_page(title, body)`, a **write** tool marked in its description and annotations `destructiveHint=true`
2. An optional bearer token check (`TOKEN=secret`).
3. A `make mcp-fixture` command or a compose profile `mcp` to run it.


**Acceptance**:
- [ ] `curl` against the fixture lists both tool groups
- [ ] The bearer check rejects a wrong token

**Verify**: `uv run python evals/fixtures/mcp_wiki/server.py &` (then run the T206 tests)

---

<a id="t206"></a>
### T206 · Connector tests (write first)

**Depends on**: T205 · **Parallel**: yes · **Size**: M

**Read first**: `MA/tests/{test_mcp_oauth,test_mcp_secrets,test_mcp_shrink,test_mcp_progressive,test_mcp_loaded_cache,test_mcp_names}.py`

**Files**: create `BT/integration/test_connectors.py`, and port the MA unit tests to `BT/unit/test_mcp_*.py`

**Cases**:

1. Port the MA unit tests (secrets seal and unseal, shrink, names, progressive groups) for the T208 modules.
2. Add a bearer connector to the fixture → status `connected`, with the groups `reports` and `pages`.
3. Headers are stored sealed (the raw DB value doesn't contain "secret").
4. In a turn: `list_mcp_tools` → `use_mcp_tools(server, ["reports"])` → `mcp_wiki_get_report` works. In the **next turn** (a different worker process; simulate it by clearing the in-process caches), the loaded group is still available from Redis.
5. `mcp_wiki_create_page` → `tool_approval` (`mcp_write`).
6. The same failing MCP call 3 times → refused (the T067 guard).
7. A result over the shrink limit is shrunk (MA behavior).
8. OAuth: mock the authorization server (respx). Start → redirect URL with PKCE → callback stores sealed tokens → status `connected`.


**Acceptance**:
- [ ] Every case listed above is its own test function (`test_<short_name>`)
- [ ] The tests run and **fail for the expected reason** (missing module or not implemented) until the implementation task lands
- [ ] No production code is added in this task

---

<a id="t207"></a>
### T207 · Connectors model

**Depends on**: T024 · **Parallel**: no · **Size**: S

**Read first**: data-model.md › connectors; `MAS/db/models.py` (`McpServer`)

**Files**: create `BE/db/models/connectors.py` and `backend/alembic/versions/0009_connectors.py`

**Steps**: per data-model.md, plus RLS. A unique `(workspace_id, name)`.


**Acceptance**:
- [ ] The migration upgrades and downgrades cleanly
- [ ] `(workspace_id, name)` is unique
- [ ] The RLS block is in the migration

**Verify**: `uv run alembic upgrade head`

---

<a id="t208"></a>
### T208 · Port the MCP internals

**Depends on**: T206, T207, T127 (seal) · **Parallel**: no · **Size**: L

**Read first**: every file in `MAS/services/mcp/`; in particular `oauth_flow.py`, `oauth.py`, `secrets.py`, `shrink.py`, `guards.py`, `groups.py`, `progressive.py`, `names.py`, `loaded_cache.py`, `results.py`

**Files**: create `BE/mcp/{oauth_flow,secrets,shrink,guards,groups,progressive,names,results,loaded_cache,registry}.py`

**Steps**:

1. Port `names`, `shrink`, `results`, `guards`, `groups`, and `progressive` **unchanged in logic**. Rename imports. Drop the Work and Cleverso specifics (`work_asks.py`, `shared_config.py` Cleverso entries, `uploads.py` if it's Cleverso-only; check and note it).
2. `secrets.py` uses the T127 `seal` and `unseal` (keep MA's function names).
3. `oauth_flow.py`/`oauth.py`: port them. Persist the pending OAuth state in Redis (10 min) instead of memory, and store tokens sealed in `connectors.oauth_tokens_sealed`. Token refresh happens before calls, when expired.
4. `loaded_cache.py`: replace the process dict with Redis: `SADD mcp:loaded:{thread_id}:{server} <group>`, with a TTL of 7 days. Keep the same function names (`mark_loaded`, `loaded_groups`, `clear`).
5. `registry.py`: replace MA's in-memory registry with a DB-backed one: `list_connectors(ws)`, `get(ws, name)`, `set_status(...)`. Cache the tool lists per connector in `connectors.groups` (jsonb), refreshed on reconnect.

**Acceptance**:
- [ ] The ported MA unit tests pass (T206 case 1)

---

<a id="t209"></a>
### T209 · MCP client on langchain-mcp-adapters

**Depends on**: T208 · **Parallel**: no · **Size**: M

**Read first**: the `langchain-mcp-adapters` README (`MultiServerMCPClient`, `load_mcp_tools`, session usage); `MAS/services/mcp/http_session.py`, `connect.py`

**Files**: create `BE/mcp/client.py`

**Interface**:

```python
async def connector_tools(ws_id: UUID, *, server: str, groups: list[str]) -> list[BaseTool]
async def probe(connector: Connector) -> ProbeResult       # connect, list tools, map to groups (groups.py)
```

**Steps**:

1. Build the `MultiServerMCPClient({name: {"url": url, "transport": "streamable_http", "headers": unsealed_headers}})` per call. It is cheap; don't hold long-lived sessions across Celery tasks. Within one turn, reuse it by caching on the turn runtime object.
2. Map MCP tools to groups with the ported `groups.py`. Rename tools to `mcp_<server>_<tool>` with the ported `names.py`.
3. Wrap each tool so that its result passes through `shrink.py` and its errors become `"Error: …"` strings (MA `results.py`).
4. Mark write tools: an MCP annotation `destructiveHint`/`readOnlyHint`, or the MA heuristic (`_CONNECTOR_READ` regex in `tool_round.py`: names matching `get|list|search` are reads). Expose `is_write_tool(name)` (T071 uses it).


**Acceptance**:
- [ ] `probe` against the fixture returns the groups `reports` and `pages`
- [ ] Tool names are `mcp_wiki_get_report` …
- [ ] A large result is shrunk
- [ ] `is_write_tool('mcp_wiki_create_page')` is True

**Verify**: `uv run pytest tests/integration/test_connectors.py -q -k client`

---

<a id="t210"></a>
### T210 · Connector tools in the agent

**Depends on**: T209, T072 · **Parallel**: no · **Size**: M

**Read first**: contracts/agent-tools.md › Connector tools; `MAS/services/tools/mcp_bridge.py`; `MAS/services/mcp/progressive.py`

**Files**: create `BE/agent/tools/mcp.py` and modify `BE/agent/tools/__init__.py` and `BE/agent/approvals.py`

**Steps**:

1. `list_mcp_tools(server?)` returns the groups with their descriptions for the allowed connectors (filtered by `profile.allows_mcp_server` and `connectors.allowed_profiles`).
2. `use_mcp_tools(server, groups)` marks the groups loaded (Redis) and returns "Loaded N tools: …". The **next model call** includes them, because `build_tools` is called again in `prepare` each round when the loaded set changed. Add `state["mcp_loaded"]` as the version stamp.
3. `build_tools` adds the specs for the loaded groups (from `connector_tools`), and runners that call the wrapped tools.
4. Connector instructions: if a server provides `instructions` (MCP initialize result), pass them into `system_prompt.py` (MA `mcp.instructions_for`).
5. Approvals: `policy_for` uses `is_write_tool`.
6. Both `list_mcp_tools` and `use_mcp_tools` are **uncharged** (the MA `schema_only_tools`).

**Acceptance**:
- [ ] T206 cases 4–7 pass

---

<a id="t211"></a>
### T211 · Connector routes

**Depends on**: T208, T209 · **Parallel**: no · **Size**: M

**Read first**: contracts/rest-api.md › Connectors; `MAS/api/routes/mcp.py`

**Files**: create `BE/api/routers/connectors.py`

**Steps**:

1. Port the MA route behavior onto workspace scope: create (probe, then status), list, delete, reconnect, OAuth start, OAuth callback.
2. Admin only for writes. Members can list.
3. `GET` never returns secrets, only `{hasToken: bool}`.
4. Validate the URL scheme: https, or http to localhost only in dev.

**Acceptance**:
- [ ] T206 cases 2, 3, and 8 pass

---

<a id="t212"></a>
### T212 · Connectors page

**Depends on**: T211 · **Parallel**: yes · **Size**: M

**Read first**: ux.md §5.9; `MAF/pages/ConnectorsPage.tsx`, `MAF/components/{McpServerDialog,McpConnectorDetails}.tsx`, `MAF/lib/{mcpOAuth,mcpCatalog,connectorResults}.ts`

**Files**: create `FE/pages/Connectors.tsx` and port the components and libs (remove Cleverso catalog entries)

**Steps**: port and restyle to the ux §5.9 card layout. Non-admins see the list read-only. The OAuth popup flow comes from the ported `mcpOAuth.ts`. Details show the groups and tools (names and descriptions).

**Acceptance**:
- [ ] Adding the fixture server through the UI works, and its status shows Connected

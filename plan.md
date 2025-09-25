## Feature 1: Extract textual summary of architectural & design facts about code

- Objectives:
  - Parse repository at provided root path.
  - Build an internal model of modules, packages, classes, functions, imports, and dependencies.
  - Produce concise textual summaries (per package, per module, global overview).
- Execution Steps:
  1. Create Python package `analyzer/` with modules: `fs_scan.py`, `ast_parse.py`, `model.py`, `summarize.py`.
  2. Implement repository scanning to enumerate files, detect languages (focus Python first; design for pluggability).
  3. Implement AST parsing using `ast` to extract classes, functions, method signatures, decorators, imports.
  4. Build graph structures: module dependency graph, class-to-module mapping, function call references (static import-level only at this stage).
  5. Implement summarization rules that generate deterministic text (no LLMs) for facts; add optional LLM enhancer via API adapter.
  6. Expose API endpoint `POST /analyze` to run analysis and return JSON facts and human-readable summaries.
  7. Add unit tests for parsing edge cases and model integrity.
- Deliverables:
  - `analyzer` package with parsers and summarizer.
  - JSON schema for facts.
  - REST endpoint returning summaries.

## Feature 2: Build diagram visualizing packages, classes, & files

- Objectives:
  - Interactive diagram showing relationships between packages, modules, classes.
  - Support zoom/pan, highlight on hover, click to focus.
- Execution Steps:
  1. Create `web/` with Python web app using `FastAPI` and templating via `Jinja2` serving a single-page app.
  2. Serve static assets `web/static/` with D3.js and minimal CSS.
  3. Define `/facts` API returning normalized graph JSON for visualization.
  4. Implement D3 force-directed or hierarchical layout (toggleable) in `web/static/app.js`.
  5. Encode nodes (package/module/class) with shapes/colors; edges for dependencies.
  6. Add search box to locate nodes; fit-to-selection and breadcrumbs.
  7. Add export to SVG/PNG and persist layout positions per repo hash.
- Deliverables:
  - SPA served by Python backend with D3-based diagram.
  - API delivering graph data from Feature 1.

## Feature 3: Drill-down to view code overlayed on diagram

- Objectives:
  - Click node to open overlay with source code snippet and metadata.
  - Syntax highlighting and open-in-editor link (VS Code protocol where available).
- Execution Steps:
  1. Add `/source` API: `GET /source?path=...&symbol=...` returning code snippet, language, and ranges.
  2. Store file text cache during analysis for fast retrieval.
  3. Use `highlight.js` on frontend; show symbol definition and surrounding context.
  4. Wire D3 node click to fetch and display overlay with tabs: Summary | Code | References.
  5. Implement server-side symbol lookup from AST indices.
- Deliverables:
  - Overlay UI with code and facts, connected to diagram nodes.

## Feature 4: Control flow between methods, starting from a specific method

- Objectives:
  - Visualize static call graph starting from a given function/method.
  - Overlay call paths on the main diagram with step-wise expansion.
- Execution Steps:
  1. Extend AST analysis to build intra-module call relations (conservative static approximations).
  2. Add `/callgraph` API: `GET /callgraph?symbol=...` returning reachable call graph with depths/edges.
  3. Frontend: add mode toggle “Control Flow”; highlight edges and nodes along selected paths.
  4. Support step expansion, max depth, and filters (external libs on/off).
  5. Add diff view between two entry symbols to compare flows.
- Deliverables:
  - Call graph overlay with interactive exploration controls.

## Feature 5: Code clone detection and highlighting

- Objectives:
  - Detect duplicated code regions and near-miss clones.
  - Visualize clones on diagram and within code overlays.
- Execution Steps:
  1. Integrate a Python clone detection approach: token-based w/ winnowing (Rabin-Karp) or reuse `jscpd` via CLI with JSON output; prefer pure Python for portability.
  2. Implement `clones.py` producing clone classes with file paths and line ranges.
  3. Add `/clones` API: list clone groups and severity (size, dispersion, duplication percent).
  4. Frontend: highlight nodes with duplication badges; overlay shows clone groups and navigate between occurrences.
  5. Add suppression mechanism and baseline file.
- Deliverables:
  - Clone detection results integrated into UI and APIs.

## Feature 6: Code smell detection and quality assessment

- Objectives:
  - Detect common smells (long function, large class, god module, high coupling, cyclic deps, dead code heuristics).
  - Provide issue list with locations, severity, and rationale.
- Execution Steps:
  1. Implement `smells.py` with metrics: LOC, cyclomatic complexity (via `ast`), parameter count, fan-in/out, instability, cycles.
  2. Compute package-level metrics (afferent/efferent coupling, abstractness, instability) and identify outliers.
  3. Add `/issues` API returning smell findings with remediation suggestions.
  4. Frontend: Issues panel with filters; badges on nodes and inline markers in code overlay.
  5. Export SARIF for integration with CI.
- Deliverables:
  - Smell detectors, metrics, and API endpoints with UI.

## Feature 7: Propose high-level refactorings

- Objectives:
  - Help developers define refactoring intents; generate LLM-ready prompts with context.
  - Track rationale, impacted symbols, and expected outcomes.
- Execution Steps:
  1. Implement `refactor_planner.py` to aggregate smells, clones, and dependencies into candidate refactorings (extract module, extract class/method, rename, break cycles, move function).
  2. UI form to select issues and propose refactoring goals; compute affected artifacts.
  3. Generate deterministic plan plus optional LLM prompt including code excerpts and constraints.
  4. Add `/refactor/prompt` API returning structured prompt and metadata.
  5. Persist proposals and allow export to Markdown.
- Deliverables:
  - Refactoring planner and prompt generator exposed via API and UI.

## Feature 8: MCP interface for Cursor integration

- Objectives:
  - Implement an MCP server exposing analysis and refactoring actions as tools.
  - Support “halt-and-interact” flow: Cursor invokes tool, developer uses UI, then a final prompt is emitted.
- Execution Steps:
  1. Add `mcp/` module exposing MCP server using Python reference implementation; define tools: `analyze_repo`, `open_ui`, `get_refactor_prompt`, `get_issues`, `get_clones`.
  2. Implement session storage keyed by repo path and analysis hash.
  3. Define tool schemas consistent with backend APIs.
  4. Provide setup docs and example Cursor `mcpServers` config.
  5. Add end-to-end test: launch MCP server, analyze sample repo, open UI, generate prompt.
- Deliverables:
  - MCP server that Cursor can call, coordinating user-in-the-loop interactions.

## Cross-cutting Concerns and Infrastructure

- Tech Stack:
  - Python 3.11+, FastAPI, Uvicorn, Jinja2, D3.js, highlight.js.
- Packaging & CLI:
  - CLI `archviz` with commands: `analyze`, `serve`, `export`.
- Data Model & Storage:
  - In-memory cache with optional SQLite for session persistence.
- Testing & CI:
  - Pytest, mypy, Ruff; GitHub Actions workflow.
- Performance:
  - Incremental analysis, caching, worker pool for AST parsing.
- Security:
  - Path sanitization, static file safety, CORS controls for MCP.
- Deliverables:
  - Working plan with modular milestones and APIs for each feature.

# ARCHITECTURE: car-ecu-dev-agent (Developer documentation)

This document explains the architecture, data flow, key modules, extension points, and the GUI API for developers who will maintain or extend the PoC.

1. High-level architecture

- vda_agent (engine/vda_agent): orchestration engine providing the control loop and stage semantics (Orchestrator, BaseStageAgent, QualityGate, traceability tools). The engine is included unchanged; adapter injects domain-specific behavior.
- Adapter layer (adapter/): the glue between domain assets (driver-hal templates and agent-spec markdown) and the engine. Responsibilities:
  - Convert domain descriptors into DomainProfile (adapter/domain_profile.py, adapter/agent_spec_loader.py)
  - Provide Stage Agent implementations that drive each V-model stage using tools (adapter/domain_stage_agent.py)
  - Provide tools for codegen and gates (adapter/tlf_codegen_tool.py, adapter/tlf_consistency_gate.py)
  - Provide a generic pipeline for domains lacking templates (adapter/generic_pipeline.py)
  - Provide a forward-traceability gate to ensure every requirement is validated by tests (adapter/forward_trace.py)
  - Select pipeline for a domain (adapter/pipeline_factory.py)

- Domains (domains/): per-domain profiles and pipelines. Example: domains/tlf35584/profile.py and pipeline.py implement registers, API, states, and the seven-stage produce/assembly logic.

- GUI (gui/): a tiny single-page app backed by a stdlib http.server (gui/server.py) and an importable api module (gui/api.py). The GUI calls the engine via the adapter's run APIs to start domain runs and query results/logs.

- driver-hal-develop (external asset): holds Jinja templates, default_params.json, and consistency_checker logic. This repository references driver-hal assets read-only via DRIVER_HAL_ROOT.

2. Control and data flow

- The orchestrator triggers a StageAgent for each V-model stage. StageAgent uses configured tools to produce artifacts and to run gates.
- For TLF35584 (rich pipeline): the codegen tool (tlf_codegen_tool.py) renders Jinja templates from driver-hal to produce 7 ZCU_TLF35584_* artifacts. The tlf_consistency_gate runs G01–G13 checks on rendered outputs.
- If a gate fails, the engine's QualityGate mechanism returns a rejection; the orchestrator may invoke a REPLAN (self-heal) path implemented by the stage agent.
- Traceability: the engine's traceability tool ensures source coverage (every artifact links upstream). The adapter's forward_trace gate verifies forward coverage (every requirement has at least one downstream test). The forward_trace gate runs at orchestration level to complement engine checks.

3. Key modules & notable functions/classes

- adapter/domain_profile.py
  - DomainProfile: container for domain metadata (registers, templates, API, states, ASIL range). Used as the injection point into the engine.

- adapter/agent_spec_loader.py
  - Parses agents/*.md frontmatter + sections (skills, tools, rules, knowledges, human_checks) into DomainProfile instances.
  - Filters placeholder/test artifacts and derives ASIL from asil_range.

- adapter/domain_stage_agent.py
  - DomainStageAgent (generic): drives a stage by calling configured tools and wiring results to traceability and the engine's artifact store.

- adapter/tlf_codegen_tool.py
  - render_template(profile, template_name, context) -> artifact files
  - supports --inject-defect behavior for tests

- adapter/tlf_consistency_gate.py
  - run_consistency_checks(artifacts) -> list of gate results (G01..G13)
  - Contains narrow exemptions for known G06 misreports (see README notes)

- adapter/generic_pipeline.py
  - Produces MISRA-clean stubs for domains without real templates and wires MISRA-based gates & compilers.

- adapter/forward_trace.py
  - validate_forward_coverage(traceability_matrix, tests_summary) -> pass/fail
  - Called at orchestration level after test stages complete, rejects pipeline if any requirement lacks a verifying test.

- domains/tlf35584/pipeline.py
  - produce(): implements the seven-stage produce/assembly sequence for tlf35584 and writes pipeline artifacts to out/tlf35584/

- gui/api.py
  - Exposes functions used by server and tests: list_domains(), run_domain(domain, options), get_run_status(run_id), get_traceability(run_id), get_logs(run_id)

- gui/server.py
  - Simple HTTP server routing /api/domains, /api/run, /api/matrix and serving the SPA index.html

4. File locations to inspect for changes
- To change codegen behavior: adapter/tlf_codegen_tool.py
- To change gate logic: adapter/tlf_consistency_gate.py and adapter/forward_trace.py
- To add a domain: add domains/<your_domain>/profile.py + pipeline.py
- To teach agent to discover new skill assets: update adapter/agent_spec_loader.py

5. Extending the system
- Adding a domain
  1. Create domains/<new>/profile.py — provide registers, templates mapping, API, and default params
  2. Create domains/<new>/pipeline.py — implement produce() and stage wiring or use pipeline_factory to assign generic_pipeline
  3. If custom templates exist, ensure DRIVER_HAL_ROOT points to the driver-hal templates and agent_spec_loader can find them

- Replacing stubs with real tools
  - Replace calls in adapter/generic_pipeline.py to call production tools (e.g., QAC, AURIX-GCC, Tessy). Provide a thin wrapper tool class implementing the engine Tool interface.

6. GUI API (HTTP endpoints)
- GET /api/domains
  - returns JSON list of discovered domains and their status
- POST /api/run
  - body: { "domain": "tlf35584", "options": { "inject_defect": false }}
  - returns: { "run_id": "..." }
- GET /api/run/{run_id}/status
  - returns run progress, stage statuses, gate results
- GET /api/run/{run_id}/traceability
  - returns traceability_matrix.csv contents or JSON representation
- GET /api/run/{run_id}/logs
  - returns logs produced during the run

7. Testing & CI suggestions
- Smoke tests already available under tests/ (test_poc_p0_p3, test_poc_p4_p6, test_m2, test_m3). Add a GitHub Actions workflow that:
  - installs Jinja2
  - sets DRIVER_HAL_ROOT to a minimal test fixture (checked-in small template set or a mocked path)
  - runs the smoke tests and reports results

8. Environment variables
- DRIVER_HAL_ROOT — path to driver-hal-develop assets (read-only). If unset, adapter falls back to an example path; for CI set to a fixture path.

9. Troubleshooting notes (from PoC)
- G06 may misreport for memory-segment macros like TLF35584_*_SEC_*; adapter includes narrow exemptions. Prefer upstream fix to the G06 regex.
- Ensure default_params.json vs template hex/decimal consistency; adapter currently trusts templates as the truth for codegen and treats checker JSON as authoritative only when consistent.

10. Next development tasks (short list)
- Add a GitHub Action to run smoke tests on push/PR
- Add CI fixture for DRIVER_HAL_ROOT to avoid requiring private assets
- Add more detailed API docs (OpenAPI) for gui/api.py
- Replace MISRA stubs with an LLM-based codegen option behind a feature flag (llm.mode=anthropic)

Appendix: useful entry points to inspect
- adapter/agent_spec_loader.py
- adapter/tlf_codegen_tool.py
- adapter/tlf_consistency_gate.py
- adapter/forward_trace.py
- domains/tlf35584/pipeline.py
- engine/vda_agent/factory.py
- gui/api.py

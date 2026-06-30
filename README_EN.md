# car-ecu-dev-agent — Overview (English)

A PoC agent project for in-vehicle ECU/domain embedded development. It connects driver-hal-develop's declarative domain assets (Jinja2 codegen templates + consistency checker) to the vda_agent orchestration engine and demonstrates an end-to-end flow: render → quality gates (G01–G13) → traceability → self-heal (REPLAN) across a seven-stage V-model. It also includes a zero-dependency web GUI for visualization and control.

Key goals
- Treat domain templates as the single source of truth for codegen and run them through engine gates.
- Reuse driver-hal's consistency checker as QualityGate for codegen outputs.
- Add a forward-traceability gate to ensure each requirement is validated by at least one test.
- Provide a lightweight GUI for inspection and running domain/process matrices.

Stack
- Languages: Python (primary), C (generated artifacts), HTML/Jinja for templates and frontend
- Runtime: Python standard library + vda_agent orchestrator
- Notable dependency: Jinja2

Quickstart
```bash
git clone https://github.com/jiaruoruo/car-ecu-dev-agent.git
cd car-ecu-dev-agent/car-ecu-dev-agent
pip install -r requirements.txt
# optional: set DRIVER_HAL_ROOT to your driver-hal-develop path
python gui/server.py  # open http://127.0.0.1:8765
```

Common runs
- Full seven-stage PoC (P4–P6):
  - python run_poc_pipeline.py
  - python run_poc_pipeline.py --inject-defect  # show gate rejection + REPLAN
- Codegen + gates (P0–P3):
  - python run_codegen_gate.py
  - python run_codegen_gate.py --inject-defect
- Domain × process matrix:
  - python run_matrix.py
  - python run_matrix.py --all

Repository layout (summary)
```
car-ecu-dev-agent/
├── engine/vda_agent/        # orchestrator engine (copied, unchanged)
├── domains/tlf35584/        # domain profile and pipeline (profile.py, pipeline.py)
├── adapter/                 # adapter layer (profile, loaders, codegen tools, gates)
├── gui/                     # zero-dependency GUI (api.py, server.py, index.html)
├── out/<domain>/            # generated artifacts and pipeline outputs
├── run_*.py                 # example runs
└── tests/                   # smoke / e2e tests
```

Notes
- vda_agent is used unchanged; domain logic is injected via the adapter layer.
- driver-hal assets are referenced read-only via DRIVER_HAL_ROOT; adapter does not copy or fork them.
- The PoC's only runtime dependency is Jinja2; engine code relies on Python stdlib.

If you'd like I can add CI that runs smoke tests and/or a GitHub Action that checks the codegen+gate pipeline on push.
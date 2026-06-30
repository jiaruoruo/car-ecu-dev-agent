# car-ecu-dev-agent — Quick summary

Short, actionable summary for developers who want to run or extend the PoC.

- Purpose: connect driver-hal Jinja templates + consistency checker to vda_agent and run a 7-stage V-model with gates and traceability.
- Important dirs:
  - adapter/  — glue code: codegen tool, gates, pipeline factory, agent spec loader
  - domains/tlf35584/ — domain-specific profile and pipeline
  - engine/vda_agent/ — orchestration engine (unchanged)
  - gui/ — local web UI (python http.server)
- Quick steps:
  1. pip install -r requirements.txt
  2. python run_codegen_gate.py  # check codegen + G01-G13
  3. python run_poc_pipeline.py  # full 7-stage PoC
  4. python gui/server.py  # open UI

Env:
- DRIVER_HAL_ROOT: path to driver-hal-develop (read-only). If not set, adapter uses an example/default path.

Extending:
- Add a new domain under domains/ with profile.py and pipeline.py
- Or add templates/skills in driver-hal and let agent_spec_loader.py map them to DomainProfile

Contact: file issues or PRs under this repository.

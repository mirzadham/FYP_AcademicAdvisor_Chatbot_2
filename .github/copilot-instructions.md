This repository is a Rasa assistant project (NLU + Core) with optional custom actions.

**Quick Architecture**
- **Assistant Type**: Rasa (NLU + Core). Core pieces live in the project root (`domain.yml`, `config.yml`, `endpoints.yml`) and training material in the `data/` folder (`data/nlu.yml`, `data/stories.yml`).
- **Custom Actions**: Python actions are placed under `actions/` (module package). Implement actions by subclassing `rasa_sdk.Action` in `actions/actions.py` and export them via the package `actions` (the folder is a package because of `__init__.py`).
- **Models**: Trained model artifacts are stored in `models/`. Use `rasa train` to produce models there.

**Key Files to Inspect**
- `domain.yml`: Intents, responses (`utter_*`), and `session_config`. Example: `utter_greet` is used by stories and tests.
- `config.yml`: Rasa pipeline and policies (currently commented defaults). Note `assistant_id` should be replaced with your deployment-specific name.
- `endpoints.yml`: Configure `action_endpoint`, tracker store, and model server here. By default entries are commented.
- `data/`: Training data — `data/nlu.yml` and `data/stories.yml` define user examples and dialogue flows.
- `actions/`: Custom action implementations. Keep actions small and pure where possible; they run in a separate action server process.
- `tests/test_stories.yml`: Story-based tests used by `rasa test`.

**Developer Workflows & Commands**
- Train models: `rasa train` (outputs to `models/`).
- Run the action server (in a separate terminal): `rasa run actions --port 5055` (ensure `endpoints.yml` has `action_endpoint` set to `http://localhost:5055/webhook` if testing with a running Rasa server).
- Run the assistant locally: `rasa shell` or `rasa run --enable-api` to expose the HTTP API.
- Run story tests: `rasa test` (this will pick up files in `tests/`); to test specific stories: `rasa test core --stories tests/test_stories.yml`.
- Evaluate NLU: `rasa test nlu` after training.

**Project-specific Conventions**
- Responses use the `utter_` prefix in `domain.yml` (e.g., `utter_greet`). Stories and tests call those response names via `action: utter_greet`.
- Custom actions live in `actions/`. If adding actions, ensure they are importable by the action server (package name `actions`).
- `config.yml` includes `assistant_id: placeholder_default` — replace for deployments to avoid collisions.
- The repository uses YAML story tests under `tests/` rather than pytest-based unit tests for conversation testing.

**Integration Points & External Dependencies**
- Action server: external process, communicates with Rasa Core via `endpoints.yml` `action_endpoint` (default webhook `http://localhost:5055/webhook`).
- Tracker stores, event brokers, and model servers are configured in `endpoints.yml` when used (Redis, Mongo, external model storage). Currently these are commented out.
- Typical external libs: `rasa`, `rasa-sdk` (ensure matching versions between the assistant and action server).

**Common Pitfalls & Tips**
- If `rasa run` can't find your actions, start `rasa run actions` in a separate terminal and set the `action_endpoint` in `endpoints.yml`.
- If training looks unchanged, confirm `data/` files and `domain.yml` contain the examples referenced by stories and tests.
- Keep `utter_*` message names stable — tests/stories reference them directly.

If anything here is unclear or you'd like the instructions expanded (for CI, exact test commands for specific Rasa versions, or examples of a minimal custom action), tell me which part to expand and I will iterate.

# File Manifest

| File / Directory | Responsibility |
| --- | --- |
| `run.py` | CLI Entrypoint wrapper. Delegates to `engine.cli`. |
| `.env` | Secret management (Neo4j, OpenRouter, Model toggles, `KB_REPOS`). |
| `docker-compose.yml` | Manages the Neo4j instance with proper plugin config and local volumes. |
| `requirements.txt` | Python dependency list. |
| **`engine/`** | **Core Python Package** |
| `engine/config.py` | Environment loader. Parses `KB_REPOS` as JSON/CSV list. |
| `engine/logger.py` | Professional Audit Logging system (writes to `logs/audit.log`). |
| `engine/parser.py` | Brain of Robot Framework data extraction (Static + Runtime). |
| `engine/helpers.py` | Pure data transformation functions. |
| `engine/cli.py` | Refactored for modular loading (`load_repo_to_graph` and `clear_db`). |
| `engine/server.py` | FastAPI server. Implements `lifespan` sync and streaming analysis. |
| **`ui/`** | **Frontend Assets** |
| `ui/index.html` | Glassmorphism UI with unified Agent Operations Log console. |
| `ui/app.js` | Frontend logic. Handles chunk-buffered streaming for AI and KB Refresh. |
| `ui/style.css` | Design system with shimmering pulse animations for AI "Thinking" states. |
| **`logs/`** | Contains persistent `audit.log`. |
| **`temp_data/`** | Safe landing zone for incoming `output.xml` file processing. |
| **`temp_repos/`** | Storage for automated Git clones (ignored by git). |

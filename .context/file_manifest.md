# File Manifest

| File / Directory | Responsibility |
| --- | --- |
| `run.py` | CLI Entrypoint wrapper. Delegates to `engine.cli`. |
| `.env` | Secret management (Neo4j Auth, OpenRouter Key, Model toggles). |
| `docker-compose.yml` | Manages the Neo4j instance with named volumes and proper plugin config. |
| `requirements.txt` | Python dependency list (LangChain, FastAPI, Robot, etc.). |
| **`engine/`** | **Core Python Package** |
| `engine/config.py` | Centralized environment loader via `python-dotenv`. |
| `engine/logger.py` | Professional Audit Logging system (writes to `logs/audit.log`). |
| `engine/parser.py` | The "brain" of Robot Framework data extraction (Static + Runtime). |
| `engine/helpers.py` | Pure data transformation functions (objects to LangChain Documents). |
| `engine/cli.py` | Permanent Knowledge Base creation logic and Neo4j schema bootstrapping. |
| `engine/server.py` | FastAPI server with specialized streaming event analysis endpoints. |
| **`ui/`** | **Frontend Assets** |
| `ui/index.html` | Glassmorphism-themed UI with streaming log console. |
| `ui/app.js` | Frontend logic for file uploads, EventSource streaming, and `marked.js` rendering. |
| `ui/style.css` | Sophisticated design system using CSS variables and modern layout techniques. |
| **`logs/`** | Contains persistent `audit.log` for debugging and production tracking. |
| **`temp_data/`** | Multi-user safe landing zone for incoming `output.xml` file processing. |

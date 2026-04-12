# Robot Test Analyzer

A simple tool to help you understand why your Robot Framework tests failed. It looks at your test code and your results to give you a clear explanation of the root cause.

## 1. Setup

### Prerequisites
- **Docker**: For the database.
- **Python 3.10+**: To run the logic.

### Installation
1. Start the database:
   ```bash
   docker-compose up -d
   ```
2. Install Python requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (copy from `.env.example`) and add your OpenRouter API key.

## 2. Usage

### Step 1: Teach the tool about your tests
Run this once or whenever you change your `.robot` files. It builds a map of your keywords and test cases.
```bash
python run.py --init-kb <path_to_your_test_folder>
```

### Step 2: Start the Web UI
```bash
uvicorn engine.server:app --reload
```
Open your browser to: `http://localhost:8000`

### Step 3: Analyze
1. Upload your `output.xml` file.
2. Wait for the engine to cross-check your code and logs.
3. Read the analysis report.

---

## Technical Info
- **Database**: Neo4j (stores your test structure).
- **Logs**: Check `logs/audit.log` if something isn't working.
- **Config**: Tweak `LLM_DEBUG=true` in `.env` to switch between "Mock" mode and "Real AI" mode.

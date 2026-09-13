# Internship Saathi (इंटर्नशिप साथी)

A lightweight, accessible internship recommendation prototype inspired by the problem statement of the **PM Internship Scheme**.

> [!IMPORTANT]
> **Demonstration prototype. Sample internships only. Not an official government portal.**  
> This application is built for local demonstration and algorithmic evaluation. It uses 120 synthetic sample listings and does not claim official eligibility verification, live government data, real applications, or official portal integration.

---

## Highlights

- **Zero External API Keys & 100% Free**: Operates completely offline on your local machine using SQLite, scikit-learn (TF-IDF), FastAPI, and React.
- **Privacy-First**: No user profiles or personal tracking data are stored on the server or in databases. No names, phone numbers, or Aadhaar numbers are collected.
- **Bilingual Interface**: Full bundled support for English and Hindi (हिन्दी) with instant switching and persistent language selection.
- **Accessible & Beginner-Friendly**: Designed for first-time seekers with high contrast, large touch targets (48px+), minimal animation, and special support for candidates with no prior experience or computer skills.
- **Explainable Matching**: Deterministic hybrid scoring (Skills 40%, Sector 30%, Location 20%, TF-IDF 10%) with dynamic weight renormalization and truthful reason codes.

---

## Architecture at a Glance

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, React Router, react-i18next, Vite PWA plugin, Vitest + React Testing Library.
- **Backend**: Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.0 (synchronous session pattern with SQLite foreign keys), Alembic migrations, scikit-learn, pytest, httpx.
- **Database**: SQLite stored at `backend/data/app.db`.

---

## How the Application Works Behind the Scenes

This project is not a static form. It is a full local recommendation stack with a React UI and a Python scoring engine.

The user journey starts in the frontend wizard, implemented in the React page at `frontend/src/pages/WizardPage.tsx`. The wizard has four steps:
1. Education
2. Skills
3. Sectors
4. Location and work mode

At the end of the wizard, the frontend sends a JSON payload shaped like the `CandidateProfile` schema from `backend/app/schemas/recommendation.py` to the FastAPI endpoint `POST /api/v1/recommendations`. The payload contains:
- `education`
- `skills`
- `sectors`
- `state`
- `district`
- `preferred_work_mode`
- `is_work_mode_mandatory`
- `is_location_mandatory`
- `willing_to_relocate`
- `resume_text` (optional)

On the backend, the route in `backend/app/api/routes/recommendations.py` validates that the education string is not empty and that it can be mapped to a supported education category. If the request passes the route guard, it hands the validated `CandidateProfile` object to the recommender engine in `backend/app/services/recommender.py`.

The recommender engine is a deterministic hybrid scorer. It works in four stages:

1. **Eligibility filtering**
   - It reads all active, non-expired internships from SQLite.
   - It checks if the internship accepts the candidate’s education category.
   - It applies the hard mandatory constraints such as work mode and location if the user selected them.
   - Only matching internships enter the scoring pool.

2. **Candidate and listing normalization**
   - Education, skills, sector codes, and location strings are normalized into canonical keys using the helper functions in `backend/app/services/normalization.py`.
   - This prevents mismatches like `python`, `Python`, `PYTHON`, or `Python 3` from being treated as separate entries.

3. **Weighted scoring**
   - Skills are scored using an IDF-based overlap calculation inspired by information retrieval. Rare skills receive more signal. The scoring function returns a skill component score and a list of explanation `ReasonCode` objects.
   - Sector alignment is scored as a binary 1.0 / 0.0 component when the user selected a sector.
   - Location compatibility is scored with explicit district, state, relocation, and work-mode rules. Remote opportunities receive a friendly score when the selected mode is remote, hybrid, or any.
   - Text relevance is computed using a TF-IDF vectorizer on internship text plus an embedding similarity fallback when the embedding service is available.

4. **Weighted recombination**
   - The base weights are:
     - skill = `0.40`
     - sector = `0.30`
     - location = `0.20`
     - text = `0.10`
   - If a candidate leaves out a component, such as no skill evidence or no selected sector, the available weights are renormalized so the remaining meaningful components still add up to the full score.
   - The score is clipped into the range `0.0` to `1.0`, bucketed into `strong`, `good`, `moderate`, or `exploratory`, and sorted deterministically by score descending, then earliest deadline, then stable internship ID.

The result returned to the frontend is a `RecommendationResponse` object containing:
- `results`: top recommended internships
- `total_eligible`
- `has_limited_profile`
- `profile_summary_en` and `profile_summary_hi`
- a `disclaimer`

Every result card includes `component_scores`, `effective_weights`, `missing_skills`, and `reasons`. These reasons are created as structured `ReasonCode` objects and later rendered in English or Hindi by the UI layer.

Example behind-the-scenes signal:
- If a candidate selected a sector that a listing belongs to, the engine records a sector reason such as `SECTOR_INTEREST`.
- If the location is the same as the home district, the engine records `SAME_DISTRICT`.
- If the listing is beginner-friendly, the engine may append `NO_PRIOR_SKILLS_REQUIRED`.

This design is what makes the tool both explainable and transparent rather than a pure black-box ranking system.

---

## Prerequisites

Before running the application, make sure you have:
- **Python 3.12** (verify with `python --version` or `py -3.12 --version`)
- **Node.js 18+** and **npm** (verify with `node --version` and `npm --version`)

---

## Quick Start (Automated Scripts)

### On Windows (PowerShell)
```powershell
# 1. Run automated setup (creates virtual environment, installs dependencies, migrates DB, seeds 120 internships)
.\scripts\setup.ps1

# 2. Start Backend Server (Terminal 1)
.\scripts\run-backend.ps1

# 3. Start Frontend Dev Server (Terminal 2)
.\scripts\run-frontend.ps1
```

### On macOS / Linux (Bash)
```bash
# 1. Run automated setup
chmod +x scripts/*.sh
./scripts/setup.sh

# 2. Start Backend Server (Terminal 1)
./scripts/run-backend.sh

# 3. Start Frontend Dev Server (Terminal 2)
./scripts/run-frontend.sh
```

---

## Manual Step-by-Step Setup

If you prefer running commands manually:

### 1. Backend Setup
From the repository root:
```bash
cd backend

# Create isolated virtual environment (using Python 3.12)
py -3.12 -m venv .venv        # On Windows
# or: python3 -m venv .venv  # On macOS/Linux

# Install dependencies using the isolated interpreter directly:
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# Run database migrations
.\.venv\Scripts\python.exe -m alembic upgrade head

# Seed reproducible taxonomy and 120 sample internships
.\.venv\Scripts\python.exe seed.py
```

### 2. Frontend Setup
From the repository root:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

---

## Local URLs

Once running, access the application at:
- **Frontend Web App**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Backend Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Docs**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running Automated Tests & Verification

Run the unified verification suite which executes backend tests, integration checks, frontend unit tests, and production build checks in one step:

### Windows PowerShell
```powershell
powershell -ExecutionPolicy Bypass -File scripts\check.ps1
```

### macOS / Linux
```bash
./scripts/check.sh
```

### Individual Test Commands
- **Backend Tests (20 tests)**:
  ```powershell
  cd backend
  .\.venv\Scripts\python.exe -m pytest -v
  ```
- **End-to-End Integration Smoke Test**:
  ```powershell
  .\backend\.venv\Scripts\python.exe scripts\smoke_test.py
  ```
- **Frontend Tests (Vitest)**:
  ```bash
  cd frontend
  npm run test
  ```
- **Frontend Production Build Check**:
  ```bash
  cd frontend
  npm run build
  ```

---

## Virtual Environment Isolation & Shell Activation

This project maintains strict environment isolation in `backend/.venv`:
- **Direct Interpreter (Recommended)**:
  - Windows: `backend\.venv\Scripts\python.exe`
  - macOS/Linux: `backend/.venv/bin/python`
- **Shell Activation (Optional)**:
  - PowerShell: `.\backend\.venv\Scripts\Activate.ps1`
  - Windows Command Prompt (CMD): `backend\.venv\Scripts\activate.bat`
  - macOS/Linux: `source backend/.venv/bin/activate`

> [!NOTE]
> If PowerShell blocks `.ps1` script activation due to execution policies, do **not** alter your machine-wide security policy. Instead, simply invoke the Python binary directly via `backend\.venv\Scripts\python.exe` or open a Windows CMD prompt.

---

## Troubleshooting Guide

### 1. Port 8000 or 5173 Conflict
If another program is already using port 8000 or 5173:
- For the backend: edit `PORT=8000` in `backend/.env` (e.g. change to 8001), and update the Vite dev proxy target in `frontend/vite.config.ts`.
- For the frontend: Vite will automatically suggest port 5174 if 5173 is occupied.

### 2. Backend Connection Error in Frontend
- Verify that Uvicorn is running in your backend terminal (`http://127.0.0.1:8000/api/v1/health` should return `{"status":"healthy"}`).
- The Vite development server automatically proxies `/api/v1` requests to `http://127.0.0.1:8000`. If you run the frontend on a custom URL or standalone host, set `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1` in `frontend/.env`.

### 3. Seed Idempotency & Deadline Refresh
- Re-running `seed.py` is safe and idempotent; it will update existing records without creating duplicate rows.
- If you wish to refresh synthetic deadlines relative to today for demo testing, run:
  ```powershell
  .\.venv\Scripts\python.exe seed.py --refresh-deadlines
  ```

---

## What Would Be Needed Before Real Public Deployment

To transition this demonstration prototype into a production service:
1. **Official Integration**: Secure, authenticated integrations with authorized government single-sign-on (SSO) and official scheme verification APIs.
2. **Database Scaling**: Migrate from SQLite to an enterprise managed database such as PostgreSQL with read replicas and row-level security.
3. **Identity & Access Management**: Role-based access control (RBAC) with Aadhaar e-KYC or mobile OTP conforming to national data privacy standards.
4. **Security & Auditing**: End-to-end encryption at rest and in transit, comprehensive audit logging, rate limiting, and DDoS protection via a secure reverse proxy / CDN.
5. **Human-in-the-Loop Supervision**: Verification workflows for partner employers offering internships to prevent fraud and wage exploitation.

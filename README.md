# CareerAI — All 13 Modules

AI Resume Screening + AI Interview Coach. Upload a resume → get it parsed →
score it against a job description → see your skill gaps → get AI-rewritten
wording → practice with an adaptive mock interview (text, voice, or video) →
get scored on technical accuracy, communication, and delivery → see it all
in one performance report with a radar chart, PDF export, and progress
history over time.

## Read this first: what "complete" means here

All 13 modules are built — every endpoint in the spec exists, with real
logic behind it, not stubs. But **not everything is verified the same way**,
and pretending otherwise would be dishonest. Three different categories:

1. **Fully tested (119 automated tests + a live-HTTP smoke test).** Modules
   1-5, all data-storage/retrieval/ownership logic in 6-8 and 12-13, and
   every AI-backed *orchestration* path (prompt building → provider call →
   response validation → error handling → persistence) via a fake LLM
   provider that stands in for Gemini/Ollama.
2. **Real code, verified logic, but the live external call is untested.**
   The actual quality of LLM-generated text (Modules 6, 7, 8's questions,
   11), Whisper transcription (Module 9), and MediaPipe landmark detection
   (Module 10) can't be exercised here — no LLM API key, and Whisper/
   MediaPipe's model downloads are blocked by this sandbox's network/disk
   constraints (verified, not assumed — see "Environment constraints" below).
   What *is* tested: the analysis math each of these feeds into (filler-word
   detection, speaking-pace scoring, eye-contact/smile/posture scoring from
   landmark coordinates) is pure-function tested against synthetic data,
   completely independent of whether the live model call works.
3. **Untestable without your own setup, by nature.** Voice/video capture
   needs an actual browser with a microphone/camera — there's no browser in
   this build environment at all.

If you configure a real `GEMINI_API_KEY` and download the MediaPipe model
files (see SETUP.md), categories 2 and 3 become fully live. Nothing here
needs code changes to go from "built" to "verified" — just credentials and
a browser.

## Module status

| # | Module | Status |
|---|---|---|
| 1 | Authentication (JWT, RBAC, password reset) | ✅ Fully tested |
| 2 | Resume Upload (PDF/DOCX, validation, extraction) | ✅ Fully tested |
| 3 | Resume Parser (skills, education, experience, links) | ✅ Fully tested |
| 4 | ATS Analysis (score, skill match, suggestions) | ✅ Fully tested |
| 5 | Skill Gap Analysis (priority, difficulty, resources) | ✅ Fully tested |
| 6 | Resume Improvement (LLM rewriting) | ⚠️ Orchestration tested; output quality needs your API key |
| 7 | Interview Question Generator | ⚠️ Orchestration tested; output quality needs your API key |
| 8 | AI Interview (text/voice/video, adaptive) | ⚠️ Text flow fully tested; voice/video need Whisper+MediaPipe+browser |
| 9 | Speech Analysis (speed, pauses, fillers, confidence) | ⚠️ Analysis logic fully tested; transcription needs Whisper |
| 10 | Video Analysis (eye contact, smile, pose, posture) | ⚠️ Analysis logic fully tested; detection needs MediaPipe models |
| 11 | AI Evaluation (technical/completeness/communication/grammar) | ✅ Same code as Module 8's evaluator — see there |
| 12 | Performance Report (radar chart, PDF export, progress) | ✅ Fully tested |
| 13 | Candidate Dashboard (history, achievements, practice count) | ✅ Fully tested |

**119 backend tests, 37 API endpoints, 14/14 live-HTTP smoke checks, clean
frontend build & lint.**

## Environment constraints (verified, not assumed)

Three real constraints shaped this build — each one checked directly rather
than guessed at:

- **No LLM API key available.** Gemini/Ollama calls in Modules 6-8/11 are
  fully coded and orchestration-tested via a fake provider, but never called
  live. Give your own `GEMINI_API_KEY` in `.env` to make them real.
- **Whisper (Module 9) can't install here.** `openai-whisper` depends on
  `torch`, whose default PyPI wheel pulls ~3GB of CUDA libraries even for
  CPU-only inference — this sandbox doesn't have that much disk to spare on
  libraries it wouldn't use anyway, and can't reach
  `download.pytorch.org`'s CPU-only index to get a smaller build. Confirmed
  by attempting the install twice (running out of disk both times), not
  assumed from a network-allowlist read. Install `openai-whisper` yourself
  in an environment with more headroom — the code in
  `app/services/speech/transcription.py` doesn't need to change.
- **MediaPipe's model file (Module 10) is on a blocked domain.**
  `storage.googleapis.com` isn't reachable from this sandbox. An unofficial
  third-party GitHub mirror of the file exists and *would* be reachable —
  deliberately not used: it's an unverified binary with no official checksum
  to validate against, not something to depend on for either testing or a
  production deployment. Download the official files yourself — see
  SETUP.md.

## Tech stack actually installed (verified against the registries)

**Backend:** FastAPI 0.141.1 · Motor 3.7.1 · Pydantic 2.13.4 · PyJWT · bcrypt
· slowapi · PyMuPDF · python-docx · spaCy 3.8.14 + `en_core_web_sm` ·
scikit-learn 1.8.0 (TF-IDF) · reportlab (PDF export) · OpenCV + MediaPipe
(pre-available in this environment) · Python 3.12

**Not installed here, real integration code written for:** `openai-whisper`
(Module 9 — see constraints above)

**Frontend:** React 19.2.8 · Vite 8.2.0 · Tailwind CSS 4.3.3 · React Router
7.18.2 · Axios · React Hook Form · Framer Motion · Recharts (radar chart,
lazy-loaded) · Lucide

**LLM provider (Gemini vs Ollama):** For a hosted SaaS, **Gemini** is the
better default — real free tier, no GPU to provision, better structured-JSON
quality out of the box. **Ollama** if you want zero per-request cost and full
data privacy and are fine self-hosting the compute. Both sit behind one
`LLMProvider` interface (`app/ai/providers/`) — switching is a `LLM_PROVIDER`
env var, not a code change.

## Project structure

```
careerai/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # 13 route modules, one per feature area
│   │   ├── api/deps.py      # get_current_user, require_roles(), get_llm_provider_dep
│   │   ├── services/
│   │   │   ├── parsing/     # text_extraction, resume_parser, context_builder
│   │   │   ├── ats/         # jd_requirements, ats_scorer
│   │   │   ├── interview/   # question_generator, adaptive_question_service, evaluator
│   │   │   ├── speech/      # speech_analyzer (tested), transcription (Whisper, untested)
│   │   │   ├── video/       # video_analyzer (tested), frame_processor (MediaPipe, untested)
│   │   │   ├── report/      # resume_score, pdf_export
│   │   │   └── *.py         # one orchestration service per module
│   │   ├── models/, schemas/, utils/, middleware/, database/
│   │   ├── ai/               # providers/ (Gemini, Ollama, factory), skills_taxonomy,
│   │   │                     # skill_metadata, prompts.py (every LLM prompt, centralized)
│   │   ├── config/settings.py
│   │   └── main.py
│   ├── scripts/smoke_test_live.py
│   ├── tests/                # 119 tests + fake_llm_provider.py + PDF/DOCX fixtures
│   └── requirements.txt / requirements-dev.txt
├── frontend/
│   └── src/
│       ├── components/common/, components/layout/
│       ├── pages/
│       │   ├── auth/         # Login, Register, ForgotPassword, ResetPassword
│       │   ├── resume/       # ResumeList, UploadResume, ResumeDetail, ResumeImprovement
│       │   ├── ats/          # CompareJobDescription, ATSResults
│       │   ├── interview/    # StartInterview, InterviewSession (real MediaRecorder capture)
│       │   ├── report/       # PerformanceReport (radar chart, lazy-loaded)
│       │   └── Dashboard.jsx # Module 13, real aggregated data
│       ├── context/, services/, hooks/, utils/, types/
├── SETUP.md               # MongoDB, secret key, Gemini key, Whisper/MediaPipe setup
└── docker-compose.yml
```

## Quick start

```bash
# Backend
cd backend
python -m venv venv &&  venv/Scripts/activate
pip install -r requirements-dev.txt
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

cp .env.example .env   # see SETUP.md for MongoDB URI, SECRET_KEY, and (optional) GEMINI_API_KEY
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
cp .env.example .env
npm install
npm run dev
```
API docs: http://localhost:8000/api/docs · App: http://localhost:5173

**→ [SETUP.md](./SETUP.md)** has the full walkthrough: MongoDB connection
options, generating a secret key, getting a Gemini API key, and the
Whisper/MediaPipe setup steps for Modules 9-10.

## Database collections

`users` · `resumes` · `resume_analysis` · `job_descriptions` · `ats_results`
· `interview_questions` · `interviews` · `interview_answers`

Full schema details for each are in the code (`app/models/`) — every field
is typed and documented there via Pydantic models, which is the actual
source of truth and won't drift out of sync with a separate written copy the
way a hand-maintained schema doc in this file would.

## API reference

All responses use `{ success, message, data }` on success or
`{ success: false, error: { code, message } }` on failure. Full interactive
docs (Swagger) at `/api/docs` once the backend is running — 37 endpoints
across auth, users, resume, resume analysis, job descriptions, ATS, skill
gap, resume improvement, interview questions, interviews (+ audio/video
answer submission), reports, and dashboard.

Key flows:
```
POST /api/resume/upload          → resume_id
POST /api/resume/{id}/parse      → structured skills/education/experience
POST /api/job                    → job_description_id
POST /api/ats/compare            → score + missing skills + suggestions
GET  /api/skill-gap/{r}/{jd}     → learning plan for the gap
POST /api/resume/{id}/improve    → rewritten summary/experience/projects
POST /api/interview/start        → interview_id + first question
POST /api/interview/{id}/answer(/audio|/video) → evaluated + next question
GET  /api/report                 → the full dashboard (radar chart data)
GET  /api/report/export-pdf      → downloadable PDF
GET  /api/dashboard              → recent activity + achievements
```

## Security notes

- **Passwords:** SHA-256 pre-hash then bcrypt(12 rounds) — avoids bcrypt's
  72-byte silent-truncation bug.
- **JWT:** algorithm pinned on decode; access + refresh tokens with a
  token-version claim so logout/password-change revokes every outstanding
  refresh token without a server-side session store.
- **Refresh token:** httpOnly, `SameSite=Lax` cookie — never touched by JS.
- **Rate limiting:** `200/min` baseline on every route, `5/min` (`3/min` for
  register) on the routes that touch bcrypt or account enumeration.
- **File upload:** validated on extension + actual byte size + magic-byte
  content sniffing, stored under a random UUID filename.
- **Ownership enforcement:** every resource-scoped endpoint (resume, JD,
  ATS result, interview) checks `user_id` server-side before returning
  anything — tested explicitly for each resource type, not assumed to
  follow from authentication alone.
- **Role injection:** registration hard-codes `role=candidate`; no client
  path to self-promote.

## Known limitations (read before trusting outputs blindly)

- **Resume parser (Module 3):** heuristic (regex + spaCy), not
  state-of-the-art. Bare institution acronyms ("MIT" alone) aren't reliably
  detected; university-name keywords (University/College/Institute) are.
  Highly creative multi-column layouts parse worse than conventional ones.
- **ATS scoring (Module 4):** keyword/TF-IDF based, not embeddings —
  deliberately: real ATS software is keyword-matching, not semantic, so
  this is arguably more representative than an embedding score would be.
  `missing_keywords` doesn't know "container orchestration" ≈ "Kubernetes".
- **Certification matching:** strict exact-name-or-alias — "AWS certified
  solutions architect" style loose JD phrasing may miss registered
  taxonomy entries; add aliases as you hit them in `skills_taxonomy.py`.
- **Modules 6, 7, 11 (LLM-generated content):** quality is only as good as
  the model you configure. The "never invent experience" rule is a prompt-
  level instruction, not something code can 100% enforce — spot-check
  rewritten content against the original before trusting it fully.
- **Module 9's pronunciation score** is an ASR-confidence proxy, not real
  phonetic analysis — low confidence can mean unclear speech, or just
  background noise or a quiet mic.
- **Module 10's posture/head-pose scores** are simplified landmark-geometry
  heuristics, not a full 3D pose solve (no camera calibration available) —
  good for "facing away" vs "facing forward," not precise rotation angles.

## Testing

```bash
cd backend
python3 -m pytest -v                # 119 tests, ~50s
python3 scripts/smoke_test_live.py  # real HTTP: cookies, CORS, headers
```

The fake LLM provider (`tests/fake_llm_provider.py`) is what makes Modules
6-8/11 genuinely testable without a real API key — it's schema-aware, so
one shared fake correctly serves services that expect different response
shapes even when their calls interleave (the interview loop calls both the
question generator and the evaluator through one injected provider).

## What building this surfaced — real bugs, not hypotheticals

Worth naming since it's the actual evidence "tested" means something here:
a section-splitting bug that fragmented single resume entries into three
weak ones; an entry-boundary bug in experience parsing where dates opened
the wrong entry instead of closing the right one; `missing_keywords`
returning bigram noise like "aws docker" that slipped past an exact-term
filter; lucide-react quietly dropping brand icons in a version bump; a
service silently requiring an LLM API key for pure-read operations that
never call the LLM at all; and a genuinely subtle multi-turn testing problem
(one shared fake provider serving two different response shapes across
interleaved calls) that needed a schema-aware fake rather than a simple
ordered list. All caught by actually running things, not by inspection.

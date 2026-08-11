# Setup Guide: MongoDB Connection + Secret Key

Two things the backend refuses to start without: a MongoDB connection string
and a `SECRET_KEY`. This doc covers both, plus how to verify each is actually
working before you blame your code for a connection error.

## 1. MongoDB

You need a MongoDB instance somewhere reachable, and its connection string in
`backend/.env` as `MONGODB_URI`. Pick whichever of these three fits you —
they're listed easiest-to-set-up first.

### Option A — Docker (recommended, works identically on Mac/Windows/Linux)

If you have Docker installed, this is the least error-prone path:

```bash
docker run -d --name careerai-mongo -p 27017:27017 -v careerai_mongo_data:/data/db mongo:7
```

Your `.env` connection string:
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=careerai
```

Check it's actually running:
```bash
docker ps                      # should show careerai-mongo as "Up"
docker logs careerai-mongo     # should show "Waiting for connections"
```

To stop/start later: `docker stop careerai-mongo` / `docker start careerai-mongo`.

This is also exactly what `docker-compose.yml` in the project root does
automatically if you use `docker compose up` instead — you don't need to run
the command above if you're using Compose.

### Option B — MongoDB Atlas (free cloud-hosted, no local install)

Good if you don't want anything running on your own machine, or you're
deploying and need a real hosted database anyway.

1. Go to https://www.mongodb.com/cloud/atlas/register and create a free account.
2. Create a free **M0** cluster (no credit card required for the free tier).
3. **Database Access** (left sidebar) → Add a database user → note the username/password.
4. **Network Access** (left sidebar) → Add IP Address → for local development,
   "Allow Access from Anywhere" (`0.0.0.0/0`) is simplest; for production, restrict
   this to your server's actual IP.
5. **Database** → Connect → Drivers → copy the connection string. It looks like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. Replace `<username>`/`<password>` with your actual credentials, and put it in `.env`:
   ```
   MONGODB_URI=mongodb+srv://myuser:mypassword@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DB_NAME=careerai
   ```
   If your password contains special characters (`@`, `:`, `/`, etc.), URL-encode
   them or the connection string will fail to parse — e.g. `p@ss` → `p%40ss`.

### Option C — Native local install

**macOS** (via Homebrew):
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

**Ubuntu/Debian** — MongoDB isn't in the default apt repos (licensing), so add
their official repo first: follow
https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/,
then:
```bash
sudo systemctl start mongod
sudo systemctl enable mongod   # start on boot
```

**Windows**: download the installer from
https://www.mongodb.com/try/download/community and run it — it installs as a
Windows service that starts automatically.

Connection string is the same for all three:
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=careerai
```

### Verifying the connection actually works

Don't just trust that it "should" work — check:

```bash
# If you have the mongosh shell installed:
mongosh "mongodb://localhost:27017" --eval "db.runCommand({ping: 1})"
# Expect: { ok: 1 }
```

Or start the backend and watch the logs:
```bash
cd backend
uvicorn app.main:app --reload
```
You should see `Connected to MongoDB database 'careerai'` in the startup log.
If instead you see a `ServerSelectionTimeoutError` after ~30 seconds, the URI
is unreachable — double check the connection string, that the service is
actually running (`docker ps` / `brew services list` / `systemctl status mongod`),
and for Atlas, that your IP is allow-listed under Network Access.

## 2. Secret key

`SECRET_KEY` signs every JWT this app issues. It has no default — the app
raises a validation error on startup if it's missing, which is intentional:
a guessable or empty signing key means anyone can forge an access token.

**Generate a real one:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
or, if you don't have Python handy:
```bash
openssl rand -hex 32
```
Either gives you a 64-character random hex string. Paste it into `backend/.env`:
```
SECRET_KEY=<the string you just generated>
```

**Rules that actually matter:**
- Generate a **different** key per environment (dev, staging, production).
  Never reuse your local dev key in production.
- Never commit it. `.env` is already in `.gitignore` — keep it that way.
  Only `.env.example` (with a placeholder, not a real key) belongs in git.
- If a real key ever leaks (committed by accident, logged, etc.), rotate it
  immediately — every access and refresh token in circulation becomes
  worthless the moment you do, since all of them are signed with the old key
  (which is exactly the point: this instantly logs out every session).

## Quick check that both are wired up correctly

```bash
cd backend
cp .env.example .env
# edit .env: paste your MONGODB_URI and SECRET_KEY
uvicorn app.main:app --reload
```
Then in another terminal:
```bash
curl http://localhost:8000/api/health
# {"status":"ok","service":"CareerAI"}
```
If that returns successfully, both MongoDB and the secret key are correctly
configured — you're ready to run the frontend against it.

## 3. Gemini API key (Modules 6, 7, 8, 11)

Only needed once you want real AI-generated content (resume rewrites,
interview questions, answer evaluation) instead of just the parsing/ATS/
skill-gap modules, which work with zero external API key.

1. Go to https://aistudio.google.com/apikey and sign in with a Google account.
2. Click **Create API key** — the free tier is generous enough for development.
3. Add it to `backend/.env`:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=<your key>
   ```
4. Restart the backend. `POST /api/resume/{id}/improve` (or any Module
   6/7/8/11 endpoint) will now call the real model.

**Prefer Ollama instead?** Install it locally (https://ollama.com), pull a
model (`ollama pull llama3.1`), then set:
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```
No API key needed — it's talking to your own machine.

## 4. Whisper (Module 9 — voice interview transcription)

```bash
pip install openai-whisper
```
This pulls in `torch` — expect a sizeable download (1-3GB depending on
whether a GPU build gets selected). If you're on a disk-constrained
environment and only need CPU inference, install the CPU-only PyTorch build
first, then openai-whisper on top:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install openai-whisper
```
No code changes needed — `app/services/speech/transcription.py` already
expects the package to exist and loads the `base` model on first use.

## 5. MediaPipe models (Module 10 — video interview analysis)

Download the two official model files Google publishes:
```bash
mkdir -p backend/models
curl -o backend/models/face_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
curl -o backend/models/pose_landmarker_lite.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
```
(URLs per MediaPipe's official docs as of this writing — check
https://ai.google.dev/edge/mediapipe/solutions/vision if these paths have
moved.) The paths above match the defaults in `.env.example`
(`FACE_LANDMARKER_MODEL_PATH`, `POSE_LANDMARKER_MODEL_PATH`); override those
if you save the files elsewhere.

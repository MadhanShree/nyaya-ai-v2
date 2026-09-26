# NyayaAI

NyayaAI is a document-grounded legal information assistant. It extracts text from PDF, DOCX, and TXT files, splits the document into clause-like units, retrieves relevant clauses with TF-IDF, and uses a Groq-hosted model to answer questions from the retrieved context.

> **Important:** NyayaAI provides information, not legal advice. Always read the cited clause and consult a qualified legal professional when legal advice is needed.

## What this version improves

- Modular service architecture with typed models and small responsibilities.
- Bounded uploads, PDF pages, extracted text, context, questions, risks, retrieval, and in-memory documents.
- TF-IDF index built once per uploaded document instead of per question.
- Document-grounded prompting that treats document text as untrusted data.
- Model-output citation validation for analysis results.
- Security headers, same-origin frontend, process-local API rate limiting, and no persistent document storage.
- PDF signature and DOCX container validation before extraction.
- Accessible labels, skip navigation, visible focus states, status announcements, responsive layout, and reduced-motion support.
- Frontend uses DOM text APIs rather than injecting model output as HTML.
- Automated API, security, retrieval, document, and LLM-sanitization tests.
- Non-root Docker image and Vercel ASGI entry point.

## Local setup

Python 3.12+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Put your own Groq key in `.env`. Never commit `.env`.

Run locally:

```powershell
uvicorn index:app --reload
```

Open `http://127.0.0.1:8000`.

## Verification

Run these before every Git push:

```powershell
python -m ruff check .
pytest -q
```

Optional coverage:

```powershell
python -m pip install -r requirements-coverage.txt
pytest --cov=nyayaai --cov-report=term-missing
```

## GitHub

Create a new empty GitHub repository, then from this folder:

```powershell
git init
git branch -M main
git add .
git commit -m "feat: launch NyayaAI 2.1"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

## Vercel

Import the GitHub repository into Vercel. The repository includes `api/index.py` and `vercel.json` for the FastAPI entry point.

Set this environment variable in Vercel:

- `GROQ_API_KEY` — required

Optional configuration variables are documented in `.env.example`.

## Security notes

- Secrets are loaded from environment variables and excluded by `.gitignore`.
- Uploaded documents are held only in process memory and are removed when the service restarts or exceeds its bounded document cache.
- The rate limiter is process-local; multi-instance deployments should add a shared rate-limiting layer.
- AI output is treated as untrusted output and is never inserted into the frontend as HTML.
- Scanned PDFs require OCR before upload.

## Known limitations

- OCR is not built in.
- In-memory document storage is intentionally temporary and is not a legal records system.
- Retrieval is lexical TF-IDF rather than semantic vector search.
- Model answers can still be incorrect or incomplete. Citations are intended to help users inspect the source clauses, not to establish legal correctness.

# MedSight AI Local Development

## Backend

1. Create `.env` from `.env.example`.
2. Generate strong secrets:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Use different values for `SECRET_KEY` and `JWT_SECRET_KEY`.

3. Install and run:

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`; Swagger is at `http://localhost:8000/docs`.

## Frontend

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then run:

```bash
cd frontend
npm install
npm run dev
```

The app is available at `http://localhost:3000`.

## Storage

Local uploads are copied to `data/uploads` and temp processing files live in `backend/temp`.
Use `STORAGE_BACKEND=r2` only after adding the Cloudflare R2 values in `.env`.

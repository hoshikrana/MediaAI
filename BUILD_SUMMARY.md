# Build Summary

## Completed Non-Model Readiness

- Backend accepts comma-separated `ALLOWED_ORIGINS` and `TRUSTED_HOSTS`.
- Upload submissions now record a real SHA-256 hash.
- Analysis sessions now receive an expiry timestamp.
- Analysis tasks now store `symptoms_text`, matching the queue worker.
- Uploads are copied to durable local storage by default, with optional Cloudflare R2 support.
- API-key auth can work when no bearer token is present.
- Frontend Google login now falls back to `http://localhost:8000` when `NEXT_PUBLIC_API_URL` is unset.
- The global analysis queue is instantiated and connected to the analysis pipeline.
- Analysis results are serialized in JSON mode before DB storage.
- Result lookup accepts either a task id or a session id.
- Vision, NLP, fusion, report, and chat paths now have deterministic fallbacks when pretrained/custom models are unavailable.
- Session deletion and PDF download are wired from the frontend to real backend endpoints.
- Login no longer records every attempt as a failed attempt before password verification.
- Login responses are JSON-safe and persist last login metadata.
- User profile update endpoints and pages are implemented.
- API key create/list/revoke endpoints and pages are implemented, with usage metadata tracked on API-key auth.
- Background scheduler now starts with the app and cleans temp files, expired token blacklist entries, and expired analysis sessions.
- Local development and deployment docs are filled in.

## Still Excluded

Custom model training and model quality tuning remain untouched. Pretrained loaders can still be used when their dependencies and model files are available; otherwise the app uses demo-safe fallbacks.

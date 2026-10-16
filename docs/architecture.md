# Architecture

## Component model

```text
APScheduler service
      │ daily trigger
      ▼
Site configuration ──▶ Playwright collector ──▶ PNG evidence storage
                              │                        │
                              ├──▶ EasyOCR ──fallback──┤ Tesseract
                              │                        │
                              ▼                        ▼
                      Rule/visual analyzer ──▶ PostgreSQL history
                                                      │
                                                      ▼
                         Streamlit dashboard ◀── Repository/query layer
                              │
                              └──▶ CSV and Excel exports
```

The dashboard and scheduler are separate processes. Streamlit reruns on widget interaction, so placing a scheduler inside the dashboard could create duplicate jobs. The scheduler owns browser automation; the dashboard is read-mostly.

## Modules

| Module | Responsibility |
|---|---|
| `config.py` | Environment and YAML configuration |
| `collector.py` | Browser navigation, carousel discovery, screenshots, de-duplication, and persistence |
| `ocr.py` | Lazy EasyOCR loading with independent Tesseract fallback |
| `analyzer.py` | Money/date parsing, multi-label classification, colours, flags, and descriptions |
| `models.py` | SQLAlchemy database model |
| `repository.py` | Dashboard query and filtering boundary |
| `dashboard.py` | Streamlit presentation and Plotly charts |
| `scheduler.py` | One daily, timezone-aware, coalesced job |
| `exporter.py` | Filter-aware CSV and formatted Excel exports |

## Capture lifecycle

1. The scheduler starts one job per configured daily trigger.
2. A `capture_runs` row is written with `running` status before browser activity.
3. The site adapter opens a 1920×1080 Chromium page and tries ordered carousel selectors.
4. Every unique visible slide is captured. Exact SHA-256 prevents duplicates within the same run; dHash provides a stable visual identity.
5. OCR extracts text. If the preferred engine fails, the second engine runs automatically.
6. Deterministic rules extract fields and allow multiple promotion categories.
7. The capture and its child values are inserted. Existing history is never overwritten.
8. The run is marked `success` or `failed`, including its error message and completion time.

## Change and activity semantics

- `content_hash` identifies byte-identical image captures.
- `perceptual_hash` supports future similarity thresholds for visually near-identical banners.
- `unique_identifier` combines the site and perceptual hash.
- `is_new` is true when an exact content hash has not previously appeared for that website.
- `is_active` is retained for lifecycle analysis. Version 1 creates records as active; a production retention job can mark a promotion inactive after it is absent for an administrator-defined number of successful runs.

## Scaling path

- Replace the local image volume with S3, Azure Blob Storage, or another object store while retaining the URI in `image_path`.
- Split each website into its own worker queue when collection volume grows.
- Add a read replica or materialized analytics views for long histories.
- Add an `InsightProvider` interface alongside deterministic insights for a future LLM. Do not place provider SDK calls in collectors or database models.
- Use Alembic migrations for subsequent schema changes; `schema.sql` and `create_all` establish Version 1 only.

## Security and privacy

- Keep secrets in environment variables or a secret manager; do not commit `.env`.
- Put the dashboard behind SSO or an authenticated reverse proxy for production use.
- Give the dashboard a read-only database account if operational settings are administered elsewhere.
- Limit outbound network access to configured domains.
- Apply a retention policy to logs; banner images are business records and should follow company retention rules.


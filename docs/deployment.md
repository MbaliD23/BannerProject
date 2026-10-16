# Deployment guide

## Docker Compose reference deployment

The supplied Compose file runs three services: PostgreSQL, the Streamlit dashboard, and a dedicated scheduler. Database and image volumes persist across container replacement.

1. Copy `.env.example` to `.env`.
2. Change the PostgreSQL credentials in both `.env` and `docker-compose.yml`, or inject them with your deployment platform.
3. Set `SCHEDULE_TIME` and `SCHEDULE_TIMEZONE`.
4. Run `docker compose up --build -d`.
5. Check health with `docker compose ps` and `docker compose logs --tail=100 scheduler`.
6. Open port 8501 only through TLS and an authenticated reverse proxy.

Back up the `postgres_data` and `banner_images` volumes together so database paths and evidence files remain consistent.

## VM or bare-metal deployment

Install Python, PostgreSQL, Chromium dependencies, and optional Tesseract. Create a virtual environment, install `requirements.txt`, run `playwright install --with-deps chromium`, initialize the database, and use a service manager for both processes.

Example service commands:

```text
streamlit run /opt/banner-analytics/app.py --server.address=127.0.0.1 --server.port=8501
banner-analytics scheduler
```

Configure automatic restart, a working directory of `/opt/banner-analytics`, environment-file loading, and separate non-root service users.

## Kubernetes or cloud containers

- Deploy dashboard and scheduler as separate workloads from the same image.
- Use managed PostgreSQL and managed object storage.
- Mount no shared filesystem if `image_path` is changed to object storage URIs.
- Give the scheduler one replica unless distributed locking is added.
- Add readiness checks for the dashboard and database connectivity alerts for both workloads.
- Use a NetworkPolicy or equivalent egress allow-list for the target sites.

## Scheduler alternatives

The application uses APScheduler by default. If the platform provides CronJobs, stop the scheduler service and run this once per day instead:

```text
banner-analytics collect
```

Use `0 6 * * *` only as an illustration for 06:00 in the cron host's configured timezone. Platform cron and APScheduler must not both be active.

## Monitoring

- Alert on `capture_runs.status = 'failed'` or a successful run with zero banners.
- Alert if no successful run exists for more than 26 hours.
- Track disk/object-store growth and database table size.
- Review OCR error frequency and selector failure messages after site releases.
- Test database restoration and evidence-volume restoration together.

## Production checklist

- Change every example credential.
- Enable HTTPS and SSO/reverse-proxy authentication.
- Confirm site automation governance and rate limits.
- Configure backups and retention.
- Run `pytest` and an approved live collection in staging.
- Verify OCR accuracy manually against both reference sites.
- Confirm the scheduler timezone and daylight-saving expectations.


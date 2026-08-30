# Local operations runbook

## Environment variables

Copy the relevant `.env.example` file; never put secrets in Git. Values are intentionally blank for all potential commercial providers.

- `MENGO_DATABASE_URL`: local SQLite URL, default `sqlite:///./mengo.db`
- `MENGO_CORS_ORIGINS`: comma-separated local origins; do not use `*`
- `MENGO_DEMO_MODE`: enables the local-only demo header identity and deletion route
- `MENGO_AI_PROVIDER_MODE`: must remain `mock`; `live` fails closed
- `MENGO_POSTHOG_API_KEY`, `MENGO_POSTHOG_HOST`: reserved placeholders; no PostHog adapter is active
- `EXPO_PUBLIC_API_URL`, `NEXT_PUBLIC_API_URL`: client API endpoints

## Checks and diagnostics

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/v1/admin/analytics -Headers @{ 'X-Demo-User' = 'demo-learner' }
```

If a mobile physical device cannot reach the API, verify the host LAN address, Windows firewall, and URL in `apps/mobile/.env`. Do not expose this development API publicly.

## Logging and data handling

The API logs route/method/status and allowlisted event names only. It must not log raw audio, full transcripts, provider keys, payment data, or sensitive profile information. SQLite files, `.env`, Node dependencies, Python environments, and build output are ignored by Git.

## Local reset

Stop the API and delete `apps/api/mengo.db` (or Docker's `mengo_sqlite` volume) to reset local data. This removes only local demo data.

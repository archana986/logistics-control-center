# Validation and Integration Tests

This suite validates Databricks deployment resources and end-to-end application behavior.

## Environment Variables

- `DATABRICKS_CLI_PROFILE` (default: `DEFAULT`)
- `DATABRICKS_SQL_WAREHOUSE_ID` (optional override)
- `DATABRICKS_CATALOG` (optional override)
- `DATABRICKS_SCHEMA` (optional override)
- `DATABRICKS_KA_ENDPOINT` (required for KA deploy/integration checks)
- `APP_BASE_URL` for backend API tests (default: `http://localhost:8001/api`)
- `APP_UI_BASE_URL` for Playwright UI tests (default resolves from `APP_BASE_URL` or `http://localhost:8000`)

## Run

```bash
pytest tests/deploy -m deploy
pytest tests/integration -m integration
npm run test:e2e
python scripts/validate_deployment.py
```

# Changelog

All notable changes to the Logistics Control Center will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.1.0] - 2026-04-16

### Changed

#### Two-Phase Deployment (App Split)
- Moved app resource and permissions job from `databricks.yml` to `resources/app.yml`
- First deploy now creates only infrastructure (pipeline + jobs), without the app
- App is included via `include: - resources/app.yml` after the setup job provides agent IDs
- **Fixes first-time deploy failure** where Terraform errored on empty `genie_space_id`

#### `valueFrom` for Auto-Injected Config
- `app.yaml` now uses `valueFrom` for warehouse ID, Genie Space ID, and KA endpoint
- These values are auto-injected from the app resource definition — no manual entry in `app.yaml`
- Only `catalog` and `schema` need to be set in `app.yaml` (non-resource values)

#### Foundation Model Update
- Updated default model from `databricks-meta-llama-3-1-70b-instruct` to `databricks-llama-4-maverick`
- Documented how to change the model endpoint in `app.yaml` and README

#### Resource Tagging
- Added `project: logistics-control-center` and `managed_by: dab` tags to all jobs and pipeline
- Enables tag-based resource discovery for cleanup and monitoring

### Added
- `cleanup.sh` — full teardown script (DAB destroy, Genie Space, KA endpoint, schema)
  - Falls back to tag-based cleanup if bundle state is broken
  - Verification step confirms all resources are removed

### Fixed
- `stream_events_to_volume.ipynb` — fixed `orderBy("updated_at DESC")` (column didn't exist; changed to `desc("currentETA")`)

#### Documentation
- Rewrote SETUP.md with 7-step CLI-based deployment flow (includes streaming refresh step)
- Updated README.md deploy table and project structure
- All docs use generic placeholders (no workspace-specific values)

---

## [1.0.0] - 2026-04-03

### Initial Release

First production-ready release of the Logistics Control Center - an AI-powered logistics incident response application built on Databricks.

### Features

#### Real-Time Analytics Dashboard
- Live shipment tracking with interactive map visualization
- Network health monitoring with KPI cards
- Incident timeline with severity indicators
- Lane performance metrics and drill-down views

#### AI-Powered Incident Response
- **Genie Space Integration** - Natural language queries for logistics metrics
  - "What lanes have the highest delay rates?"
  - "Show me incidents from the last 24 hours"
  - "Which distribution centers are over capacity?"
- **Knowledge Assistant** - Document Q&A for SOPs and procedures
  - Query logistics policies and guidelines
  - Get procedure recommendations during incidents
  - Access historical incident resolutions

#### Intelligent Rerouting
- Automatic reroute suggestions when incidents occur
- Capacity-aware lane recommendations
- Cost and delay impact analysis
- One-click reroute approval workflow

#### Customer Communications
- AI-generated customer update drafts
- Foundation Model integration (Llama 4 Maverick)
- Customizable communication templates
- Delivery status notifications

### Technical Architecture

#### Data Pipeline (Spark Declarative Pipelines)
- **Bronze Layer** - Raw event ingestion from UC Volumes
- **Silver Layer** - Cleaned, validated logistics records
- **Gold Layer** - Aggregated metrics and KPIs
- **Serving Tables** - Optimized for app queries
- **Metric Views** - Genie Space compatible views

#### Application Stack
- **Frontend** - React 18 + TypeScript + Vite + Tailwind CSS
- **Backend** - Python FastAPI with async handlers
- **Runtime** - Gunicorn + Uvicorn (ASGI)
- **Deployment** - Databricks Asset Bundles

#### Databricks Services
- Unity Catalog for data governance
- SQL Warehouse for query execution
- Genie Space for natural language analytics
- Model Serving for Knowledge Assistant
- Foundation Models for text generation

### Deployment

#### Simplified 5-Step Deployment
No YAML commenting/uncommenting required. Just fill in values and deploy:

1. **Configure** - Update `databricks.yml` with workspace values
2. **Deploy** - `databricks bundle deploy -t dev`
3. **Setup** - `databricks bundle run logistics_setup -t dev`
4. **Add IDs** - Update with genie_space_id and ka_endpoint from job output
5. **Finish** - `databricks bundle deploy && databricks bundle run logistics_app_permissions`

#### Jobs Included
- `logistics-control-center-setup` - One-time initialization (creates data, agents)
- `logistics-control-center-streaming-refresh` - Scheduled updates (5 min)
- `logistics-control-center-app-permissions` - UC access grants for app

### Configuration

#### Parameterized Deployment
- All customer-specific values in `targets.dev.variables` section
- Same values mirrored in `app.yaml` environment variables
- No need to edit YAML structure - just fill in values
- Supports multiple deployment targets (dev, prod)

#### Serverless Compatible
- All notebooks run on serverless compute
- Pipeline uses serverless Spark
- No cluster management required

---

## Development Notes

### What's Included

| Component | Description |
|-----------|-------------|
| `databricks/notebooks/` | Setup and job notebooks (Jupyter format) |
| `databricks/pipelines/` | Bronze/Silver/Gold SQL definitions |
| `backend/` | FastAPI Python backend |
| `src/` | React TypeScript frontend |
| `public/` | Static assets and mock data |

### What's Excluded from Git

| Folder | Purpose |
|--------|---------|
| `.local/` | Local testing parameters (gitignored) |
| `_archive/` | Development artifacts (gitignored) |
| `node_modules/` | NPM dependencies (rebuilt) |
| `dist/` | Build output (rebuilt) |

---

## Roadmap

### Planned Features
- [ ] Multi-agent supervisor for complex queries
- [ ] Real-time streaming with continuous pipeline
- [ ] Mobile-responsive UI improvements
- [ ] Additional carrier integrations
- [ ] Custom alert thresholds and notifications

### Known Limitations
- Synthetic data only (no real carrier APIs)
- Single-tenant deployment model
- English language support only

---

## Credits

Built with:
- [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html)
- [Spark Declarative Pipelines](https://docs.databricks.com/en/delta-live-tables/index.html)
- [Genie Spaces](https://docs.databricks.com/en/genie/index.html)
- [Databricks Apps](https://docs.databricks.com/en/apps/index.html)
- [React](https://react.dev/) + [Vite](https://vitejs.dev/) + [Tailwind CSS](https://tailwindcss.com/)
- [FastAPI](https://fastapi.tiangolo.com/)

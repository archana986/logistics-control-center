# Logistics Control Center

AI-powered logistics incident response application built on Databricks. Features real-time streaming analytics, natural language queries via Genie Space, and intelligent document Q&A with Knowledge Assistant.

![Architecture Diagram](architecture-diagram.png)

## Features

| Feature | Description |
|---------|-------------|
| **Real-time Dashboard** | Monitor shipments, incidents, and network health with live updates |
| **AI-Powered Rerouting** | Automatic reroute suggestions when incidents occur |
| **Natural Language Analytics** | Ask questions about your data using Genie Space |
| **Document Q&A** | Query logistics SOPs and procedures via Knowledge Assistant |
| **Customer Communications** | AI-generated customer updates using Foundation Models |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Logistics Control Center                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────┐ │
│  │   React UI   │────▶│  FastAPI     │────▶│  Databricks Services         │ │
│  │   (Vite)     │     │  Backend     │     │  ├─ SQL Warehouse            │ │
│  └──────────────┘     └──────────────┘     │  ├─ Genie Space              │ │
│                                             │  ├─ Knowledge Assistant      │ │
│                                             │  └─ Foundation Models        │ │
│                                             └──────────────────────────────┘ │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                          Data Pipeline (SDP)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────────┐   │
│  │  Bronze  │────▶│  Silver  │────▶│   Gold   │────▶│  Serving Tables  │   │
│  │  (Raw)   │     │ (Clean)  │     │ (Agg)    │     │  + Metric Views  │   │
│  └──────────┘     └──────────┘     └──────────┘     └──────────────────┘   │
│       ▲                                                                      │
│       │                                                                      │
│  ┌────┴─────┐                                                               │
│  │ UC Volume │  ◀── Raw JSON events (shipments, incidents, sensors)        │
│  └──────────┘                                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- Databricks CLI installed and authenticated
- SQL Warehouse (Serverless recommended)
- A catalog where you have `CREATE SCHEMA` permission

### Deployment (5 Commands)

```bash
# 1. Edit databricks.yml with your workspace values (profile, warehouse_id, catalog)

# 2. Deploy infrastructure
databricks bundle deploy -t dev

# 3. Run setup job (creates data + agents)
databricks bundle run logistics_setup -t dev
# Note the GENIE_SPACE_ID and KA_ENDPOINT from output

# 4. Add agent IDs to databricks.yml and app.yaml, then redeploy
databricks bundle deploy -t dev

# 5. Grant permissions and you're done!
databricks bundle run logistics_app_permissions -t dev
```

**No YAML commenting/uncommenting required.** 

- [SETUP.md](SETUP.md) - Step-by-step deployment guide
- [CONFIG.md](CONFIG.md) - Detailed explanation of all configuration files

## Project Structure

```
logistics-control-center/
├── README.md                 # This file
├── SETUP.md                  # Detailed setup instructions
├── databricks.yml            # Databricks Asset Bundle config
├── app.yaml                  # Databricks App config
│
├── backend/                  # FastAPI Python backend
│   ├── main.py               # App entry point
│   └── api.py                # API routes
│
├── src/                      # React TypeScript frontend
│   ├── App.tsx               # Main app component
│   ├── components/           # UI components
│   ├── pages/                # Page views
│   └── lib/                  # Utilities
│
├── databricks/               # Databricks resources
│   ├── notebooks/            # Setup and job notebooks
│   │   ├── setup_tables.sql
│   │   ├── generate_synthetic_data.ipynb
│   │   ├── create_genie_space.ipynb
│   │   ├── create_knowledge_assistant.ipynb
│   │   └── ...
│   └── pipelines/            # SDP SQL definitions
│       ├── 01_bronze.sql
│       ├── 02_silver.sql
│       └── 03_gold.sql
│
├── public/                   # Static assets
├── requirements.txt          # Python dependencies
├── package.json              # Node.js dependencies
└── *.config files            # Build configuration
```

## Configuration Files

### Databricks Configuration

| File | Purpose | Customer Edits? |
|------|---------|-----------------|
| `databricks.yml` | Asset Bundle definition - pipelines, jobs, app, variables | **Yes** - update `targets.dev` section |
| `app.yaml` | App runtime config - environment variables for the running app | **Yes** - update env values |

### Frontend Build Configuration

| File | Purpose | Customer Edits? |
|------|---------|-----------------|
| `package.json` | Node.js dependencies and build scripts | No |
| `vite.config.ts` | Vite bundler - handles React builds, path aliases | No |
| `tailwind.config.ts` | Tailwind CSS theme, colors, animations | No |
| `postcss.config.js` | PostCSS plugins for CSS processing | No |
| `tsconfig.json` | TypeScript project references (points to app/node configs) | No |
| `tsconfig.app.json` | TypeScript settings for React source code | No |
| `tsconfig.node.json` | TypeScript settings for Vite config | No |

### What Each Config Does

**`package.json`** - Node.js project manifest
- Defines dependencies (React, Vite, Tailwind, deck.gl for maps)
- Build scripts: `npm run dev` (local), `npm run build` (production)
- No customer changes needed

**`tsconfig.json`** - TypeScript root config
- References `tsconfig.app.json` for source code
- References `tsconfig.node.json` for build tools
- Enables project references for faster builds

**`tsconfig.app.json`** - Frontend TypeScript settings
- Target: ES2022 for modern JavaScript
- Path alias: `@/*` maps to `./src/*` for cleaner imports
- Strict mode enabled for type safety

**`tsconfig.node.json`** - Build tooling TypeScript settings
- Used only for `vite.config.ts`
- Node.js types for build-time scripts

> **Note:** JSON files don't support comments. See [CONFIG.md](CONFIG.md) for detailed explanations of each file.

## What Gets Deployed

| Resource | Name | Description |
|----------|------|-------------|
| **Pipeline** | `logistics-control-center-streaming` | Bronze/Silver/Gold data processing |
| **Job** | `logistics-control-center-setup` | One-time setup (data, agents) |
| **Job** | `logistics-control-center-streaming-refresh` | Scheduled data updates (5 min) |
| **Job** | `logistics-control-center-app-permissions` | Grant app UC access |
| **App** | `logistics-incident-response` | React + FastAPI application |
| **Genie Space** | `Logistics Control Center Metrics` | Natural language analytics |
| **Knowledge Assistant** | `ka-*-endpoint` | Document Q&A |

## Customization

### Using Your Own Data

1. Replace the synthetic data generation in `generate_synthetic_data.ipynb`
2. Update the Bronze layer schema in `01_bronze.sql` to match your data
3. Adjust Silver/Gold transformations for your business logic
4. Update Genie Space instructions in `create_genie_space.ipynb`

### Adding New Metrics

1. Add new views in `create_helper_metric_views.sql`
2. Update the Genie Space with new tables
3. Add corresponding API endpoints in `backend/api.py`
4. Create frontend components in `src/components/`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Catalog not found` | Ensure you have access to the catalog specified in `databricks.yml` |
| `Warehouse not found` | Verify warehouse ID and that you have CAN_USE permission |
| `App won't start` | Check logs at `https://<app-url>/logz` |
| `Genie Space errors` | Ensure metric views were created successfully |

## License

TBD

## Contributing

TBD

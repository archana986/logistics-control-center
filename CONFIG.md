# Configuration Reference

This document explains all configuration files in the Logistics Control Center.

---

## Files You Need to Edit

### `databricks.yml` — Single Source of Truth

**Purpose:** Defines all Databricks resources (pipeline, jobs), variables, and deployment targets.

**What to change:** Only the `targets.dev` section:

```yaml
targets:
  dev:
    workspace:
      profile: your-cli-profile            # Your Databricks CLI profile name
    variables:
      warehouse_id: "your-warehouse-id"    # SQL Warehouse ID
      catalog: "your-catalog"              # Unity Catalog name
      schema: "logistics_control_center"
      genie_space_id: "your-genie-id"      # Add in Step 5 (from setup job)
      ka_endpoint: "your-ka-endpoint"      # Add in Step 5 (from setup job)
```

**In Step 5, also add the include line near the top of the file:**

```yaml
include:
  - resources/app.yml
```

**Where to find values:**
| Value | Location |
|-------|----------|
| `profile` | Run `databricks auth profiles` in terminal |
| `warehouse_id` | Databricks UI → SQL Warehouses → Copy ID |
| `catalog` | Databricks UI → Data Explorer → Your catalog |
| `genie_space_id` | Output of `logistics_setup` job (Step 4) |
| `ka_endpoint` | Output of `logistics_setup` job (Step 4) |

### `app.yaml` — App Runtime Configuration

**Purpose:** Configures how the app runs (startup command, environment variables).

**What to change:** Only `DATABRICKS_CATALOG` (and optionally `DATABRICKS_SCHEMA`):

```yaml
env:
  - name: DATABRICKS_CATALOG
    value: "your-catalog"                   # ← Same as databricks.yml
  - name: DATABRICKS_SCHEMA
    value: "logistics_control_center"
```

**Values you do NOT edit in `app.yaml`:**
- `DATABRICKS_SQL_WAREHOUSE_ID` — auto-injected via `valueFrom: app-sql-warehouse`
- `DATABRICKS_GENIE_SPACE_ID` — auto-injected via `valueFrom: app-genie-space`
- `DATABRICKS_KA_ENDPOINT` — auto-injected via `valueFrom: app-ka-endpoint`

These `valueFrom` references pull the actual IDs from the app resource definition in `resources/app.yml`, which in turn reads from `databricks.yml` variables. This means each value is entered **once** in `databricks.yml`.

**Startup command (don't change):**
```yaml
command: pip install && npm install && npm run build && gunicorn ...
```

## Files You Don't Need to Edit

### `resources/app.yml` — App Resource Definition

**Purpose:** Defines the Databricks App and its permissions job. Included by `databricks.yml` after the setup job creates agent IDs.

**Why it's separate:** The app requires a Genie Space ID and KA endpoint that don't exist until the setup job creates them. By keeping the app in a separate include file, the first deploy succeeds without those IDs. You add the include in Step 5 after the values are available.

**No edits needed:** This file uses `${var.*}` references to read values from `databricks.yml`.

### `package.json` - Node.js Project

**Purpose:** Defines JavaScript/TypeScript dependencies and build scripts.

**Key sections:**
| Section | Purpose |
|---------|---------|
| `name` | Project identifier |
| `scripts.dev` | Starts local development server (Vite) |
| `scripts.build` | Creates production build |
| `dependencies` | Runtime packages (React, deck.gl, etc.) |
| `devDependencies` | Build-time packages (ESLint, Playwright) |

**Key dependencies explained:**
- `react`, `react-dom` - UI framework
- `vite` - Fast build tool and dev server
- `tailwindcss` - Utility-first CSS framework
- `deck.gl`, `maplibre-gl` - Map visualization
- `zustand` - State management
- `recharts` - Chart components

---

### `tsconfig.json` - TypeScript Root

**Purpose:** Project-level TypeScript configuration using references.

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },  // React source code
    { "path": "./tsconfig.node.json" }  // Build tools (vite.config.ts)
  ]
}
```

This enables faster incremental builds by separating app code from tooling.

---

### `tsconfig.app.json` - Frontend TypeScript

**Purpose:** TypeScript settings for React application code in `src/`.

**Key settings:**
| Setting | Value | Purpose |
|---------|-------|---------|
| `target` | ES2022 | Modern JavaScript output |
| `jsx` | react-jsx | Enable JSX transformation |
| `strict` | true | Enable all strict type checks |
| `paths.@/*` | ./src/* | Import alias (e.g., `@/components/Button`) |
| `noEmit` | true | Vite handles output, not tsc |

---

### `tsconfig.node.json` - Build Tools TypeScript

**Purpose:** TypeScript settings for Node.js build scripts like `vite.config.ts`.

**Key settings:**
| Setting | Value | Purpose |
|---------|-------|---------|
| `target` | ES2023 | Latest Node.js features |
| `types` | ["node"] | Node.js type definitions |
| `include` | vite.config.ts | Only compile build config |

---

### `vite.config.ts` - Vite Build Tool

**Purpose:** Configures the Vite bundler for development and production builds.

**What it does:**
- Enables React Fast Refresh (instant updates in dev)
- Sets up `@/` path alias for cleaner imports
- Handles production bundling and optimization

---

### `tailwind.config.ts` - Tailwind CSS

**Purpose:** Customizes Tailwind CSS theme and utilities.

**What it configures:**
- Color palette using CSS variables (supports dark mode)
- Custom border radius values
- Animation keyframes (accordion, slide-in)
- Content paths for class detection

---

### `postcss.config.js` - CSS Processing

**Purpose:** Runs CSS through PostCSS plugins.

**Plugins:**
- `tailwindcss` - Processes Tailwind classes into CSS
- `autoprefixer` - Adds vendor prefixes for browser compatibility

---

## Mock Data Files (`public/mock/`)

These JSON files provide sample data for local development:

| File | Contents |
|------|----------|
| `centers.json` | Distribution center locations and capacity |
| `incidents.json` | Sample incident records |
| `lanes.json` | Shipping lane definitions |
| `shipments.json` | Sample shipment tracking data |
| `reroute_solutions.json` | Pre-computed rerouting options |

**Note:** In production, the app queries live data from Unity Catalog via the backend API.

---

## Summary

| File | Edit? | Purpose |
|------|-------|---------|
| `databricks.yml` | **Yes** | Databricks resources and variables |
| `app.yaml` | **Yes** | App environment variables |
| `package.json` | No | Node.js dependencies |
| `tsconfig*.json` | No | TypeScript settings |
| `vite.config.ts` | No | Build configuration |
| `tailwind.config.ts` | No | CSS theme |
| `postcss.config.js` | No | CSS processing |

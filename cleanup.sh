#!/usr/bin/env bash
# =============================================================================
# Cleanup Script - Logistics Control Center
# =============================================================================
# Removes all resources created by the deploy + setup workflow.
# Run from the repo root: ./cleanup.sh
#
# Requires: Databricks CLI authenticated to the target workspace.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  LOGISTICS CONTROL CENTER - FULL CLEANUP                     ║${NC}"
echo -e "${RED}║                                                               ║${NC}"
echo -e "${RED}║  This will PERMANENTLY delete:                                ║${NC}"
echo -e "${RED}║    • All DAB resources (pipeline, jobs, app)                  ║${NC}"
echo -e "${RED}║    • Unity Catalog schema + all tables                        ║${NC}"
echo -e "${RED}║    • Genie Space                                              ║${NC}"
echo -e "${RED}║    • Knowledge Assistant serving endpoint                     ║${NC}"
echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Read config from databricks.yml — extract quoted values from targets.dev.variables
extract_var() {
    grep "^      $1:" databricks.yml | head -1 | sed 's/.*: *"\([^"]*\)".*/\1/'
}

CATALOG=$(extract_var catalog)
SCHEMA=$(extract_var schema)
WAREHOUSE_ID=$(extract_var warehouse_id)
GENIE_SPACE_ID=$(extract_var genie_space_id)
KA_ENDPOINT=$(extract_var ka_endpoint)

echo -e "  Catalog:          ${YELLOW}${CATALOG:-<not set>}${NC}"
echo -e "  Schema:           ${YELLOW}${SCHEMA:-<not set>}${NC}"
echo -e "  Warehouse ID:     ${YELLOW}${WAREHOUSE_ID:-<not set>}${NC}"
echo -e "  Genie Space ID:   ${YELLOW}${GENIE_SPACE_ID:-<not set>}${NC}"
echo -e "  KA Endpoint:      ${YELLOW}${KA_ENDPOINT:-<not set>}${NC}"
echo ""

read -p "Are you sure you want to delete everything? (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""

# ── 1. Destroy DAB resources (pipeline, jobs, app) ──────────────────────────
echo -e "${YELLOW}[1/4] Destroying DAB resources...${NC}"
if databricks bundle destroy -t dev --auto-approve 2>&1; then
    echo -e "${GREEN}  ✓ DAB resources destroyed${NC}"
else
    echo -e "${RED}  ✗ DAB destroy failed (may already be cleaned up)${NC}"
fi

# ── 2. Delete Genie Space ───────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/4] Deleting Genie Space...${NC}"
if [[ -n "$GENIE_SPACE_ID" && "$GENIE_SPACE_ID" != "<"* ]]; then
    if databricks api delete "/api/2.0/genie/spaces/${GENIE_SPACE_ID}" 2>&1; then
        echo -e "${GREEN}  ✓ Genie Space deleted (${GENIE_SPACE_ID})${NC}"
    else
        echo -e "${RED}  ✗ Failed to delete Genie Space (may already be deleted)${NC}"
    fi
else
    echo -e "${YELLOW}  ⊘ No Genie Space ID configured, skipping${NC}"
fi

# ── 3. Delete Knowledge Assistant serving endpoint ──────────────────────────
echo ""
echo -e "${YELLOW}[3/4] Deleting Knowledge Assistant endpoint...${NC}"
if [[ -n "$KA_ENDPOINT" && "$KA_ENDPOINT" != "<"* ]]; then
    if databricks serving-endpoints delete "$KA_ENDPOINT" 2>&1; then
        echo -e "${GREEN}  ✓ KA endpoint deleted (${KA_ENDPOINT})${NC}"
    else
        echo -e "${RED}  ✗ Failed to delete KA endpoint (may already be deleted)${NC}"
    fi
else
    echo -e "${YELLOW}  ⊘ No KA endpoint configured, skipping${NC}"
fi

# ── 4. Drop Unity Catalog schema ───────────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/4] Dropping Unity Catalog schema...${NC}"
if [[ -n "$CATALOG" && "$CATALOG" != "<"* && -n "$SCHEMA" && "$SCHEMA" != "<"* ]]; then
    if databricks api post /api/2.1/unity-catalog/schemas/delete \
        --json "{\"full_name\": \"${CATALOG}.${SCHEMA}\", \"force\": true}" 2>/dev/null; then
        echo -e "${GREEN}  ✓ Schema ${CATALOG}.${SCHEMA} dropped${NC}"
    elif databricks schemas delete "${CATALOG}.${SCHEMA}" --force 2>&1; then
        echo -e "${GREEN}  ✓ Schema ${CATALOG}.${SCHEMA} dropped${NC}"
    else
        echo -e "${RED}  ✗ Failed to drop schema (drop manually: DROP SCHEMA IF EXISTS ${CATALOG}.${SCHEMA} CASCADE)${NC}"
    fi
else
    echo -e "${YELLOW}  ⊘ Catalog/schema not configured, skipping${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Cleanup complete.${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

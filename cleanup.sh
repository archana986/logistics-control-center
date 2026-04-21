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

PROJECT_TAG="logistics-control-center"

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

# Read config from databricks.yml
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
echo -e "  Project Tag:      ${YELLOW}${PROJECT_TAG}${NC}"
echo ""

read -p "Are you sure you want to delete everything? (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""

# ── 1. Try bundle destroy first ─────────────────────────────────────────────
echo -e "${YELLOW}[1/5] Destroying DAB resources (bundle destroy)...${NC}"
if databricks bundle destroy -t dev --auto-approve 2>&1; then
    echo -e "${GREEN}  ✓ DAB resources destroyed via bundle${NC}"
else
    echo -e "${YELLOW}  ⚠ Bundle destroy failed — falling back to tag-based cleanup${NC}"

    # Find and delete jobs by tag
    echo -e "${YELLOW}      Searching for jobs tagged project=${PROJECT_TAG}...${NC}"
    JOB_IDS=$(databricks jobs list --output json 2>/dev/null \
        | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        j = json.loads(line)
        tags = j.get('settings',{}).get('tags',{})
        if tags.get('project') == '${PROJECT_TAG}':
            print(j['job_id'])
    except: pass
" 2>/dev/null || true)

    if [[ -n "$JOB_IDS" ]]; then
        for jid in $JOB_IDS; do
            if databricks jobs delete "$jid" 2>&1; then
                echo -e "${GREEN}      ✓ Deleted job $jid${NC}"
            fi
        done
    else
        echo -e "${YELLOW}      No tagged jobs found${NC}"
    fi

    # Find and delete pipelines by name
    echo -e "${YELLOW}      Searching for pipelines matching logistics-control-center...${NC}"
    PIPE_IDS=$(databricks pipelines list-pipelines --output json 2>/dev/null \
        | python3 -c "
import sys, json
data = json.loads(sys.stdin.read())
items = data if isinstance(data, list) else data.get('statuses', [])
for p in items:
    if 'logistics-control-center' in p.get('name','').lower():
        print(p['pipeline_id'])
" 2>/dev/null || true)

    if [[ -n "$PIPE_IDS" ]]; then
        for pid in $PIPE_IDS; do
            if databricks pipelines delete "$pid" 2>&1; then
                echo -e "${GREEN}      ✓ Deleted pipeline $pid${NC}"
            fi
        done
    else
        echo -e "${YELLOW}      No matching pipelines found${NC}"
    fi

    # Delete app by name
    echo -e "${YELLOW}      Checking for app logistics-incident-response...${NC}"
    if databricks apps delete logistics-incident-response 2>/dev/null; then
        echo -e "${GREEN}      ✓ Deleted app${NC}"
    else
        echo -e "${YELLOW}      App not found or already deleted${NC}"
    fi

    # Clean up bundle state
    echo -e "${YELLOW}      Removing bundle state from workspace...${NC}"
    databricks workspace delete "/Workspace/Users/$(databricks auth describe 2>/dev/null | grep 'User:' | awk '{print $2}' || echo 'unknown')/.bundle/logistics-control-center" --recursive 2>/dev/null \
        && echo -e "${GREEN}      ✓ Bundle state removed${NC}" \
        || echo -e "${YELLOW}      Bundle state not found${NC}"
fi

# ── 2. Delete Genie Space ───────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/5] Deleting Genie Space...${NC}"
if [[ -n "$GENIE_SPACE_ID" && "$GENIE_SPACE_ID" != "<"* && "$GENIE_SPACE_ID" != "" ]]; then
    if databricks api delete "/api/2.0/genie/spaces/${GENIE_SPACE_ID}" 2>/dev/null; then
        echo -e "${GREEN}  ✓ Genie Space deleted (${GENIE_SPACE_ID})${NC}"
    else
        echo -e "${YELLOW}  ⚠ Genie Space must be deleted from the UI:${NC}"
        echo -e "${YELLOW}    Workspace → Genie → Logistics Control Center Metrics → ⋮ → Delete${NC}"
    fi
else
    echo -e "${YELLOW}  ⊘ No Genie Space ID configured, skipping${NC}"
fi

# ── 3. Delete Knowledge Assistant serving endpoint ──────────────────────────
echo ""
echo -e "${YELLOW}[3/5] Deleting Knowledge Assistant endpoint...${NC}"
if [[ -n "$KA_ENDPOINT" && "$KA_ENDPOINT" != "<"* && "$KA_ENDPOINT" != "" ]]; then
    if databricks serving-endpoints delete "$KA_ENDPOINT" 2>/dev/null; then
        echo -e "${GREEN}  ✓ KA endpoint deleted (${KA_ENDPOINT})${NC}"
    else
        echo -e "${YELLOW}  ⚠ KA endpoint must be deleted from the UI:${NC}"
        echo -e "${YELLOW}    Workspace → Serving → ${KA_ENDPOINT} → Delete${NC}"
        echo -e "${YELLOW}    (The Knowledge Assistant tile must be deleted first)${NC}"
    fi
else
    echo -e "${YELLOW}  ⊘ No KA endpoint configured, skipping${NC}"
fi

# ── 4. Drop Unity Catalog schema ───────────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/5] Dropping Unity Catalog schema...${NC}"
if [[ -n "$CATALOG" && "$CATALOG" != "<"* && -n "$SCHEMA" && "$SCHEMA" != "<"* ]]; then
    if databricks schemas delete "${CATALOG}.${SCHEMA}" --force 2>&1; then
        echo -e "${GREEN}  ✓ Schema ${CATALOG}.${SCHEMA} dropped${NC}"
    else
        echo -e "${RED}  ✗ Failed to drop schema (drop manually: DROP SCHEMA IF EXISTS ${CATALOG}.${SCHEMA} CASCADE)${NC}"
    fi
else
    echo -e "${YELLOW}  ⊘ Catalog/schema not configured, skipping${NC}"
fi

# ── 5. Verify cleanup ──────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/5] Verifying cleanup (waiting 5s for deletions to propagate)...${NC}"
sleep 5
REMAINING=0

JOBS_LEFT=$(databricks jobs list 2>/dev/null | grep -c "logistics-control-center" || true)
if [[ "$JOBS_LEFT" -gt 0 ]]; then
    echo -e "${RED}  ✗ $JOBS_LEFT logistics job(s) still exist${NC}"
    databricks jobs list 2>/dev/null | grep "logistics-control-center" || true
    REMAINING=$((REMAINING + JOBS_LEFT))
else
    echo -e "${GREEN}  ✓ No logistics jobs remain${NC}"
fi

PIPES_LEFT=$(databricks pipelines list-pipelines 2>/dev/null | grep -c "logistics-control-center" || true)
if [[ "$PIPES_LEFT" -gt 0 ]]; then
    echo -e "${RED}  ✗ $PIPES_LEFT logistics pipeline(s) still exist${NC}"
    REMAINING=$((REMAINING + PIPES_LEFT))
else
    echo -e "${GREEN}  ✓ No logistics pipelines remain${NC}"
fi

APPS_LEFT=$(databricks apps list 2>/dev/null | grep -c "logistics-incident-response" || true)
if [[ "$APPS_LEFT" -gt 0 ]]; then
    echo -e "${RED}  ✗ Logistics app still exists${NC}"
    REMAINING=$((REMAINING + APPS_LEFT))
else
    echo -e "${GREEN}  ✓ No logistics app remains${NC}"
fi

echo ""
if [[ "$REMAINING" -eq 0 ]]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Cleanup complete. All resources removed.${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
else
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  Cleanup finished with $REMAINING resource(s) remaining.${NC}"
    echo -e "${RED}  Check the output above and delete manually if needed.${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
fi
echo ""

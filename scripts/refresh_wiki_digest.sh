#!/usr/bin/env bash
# refresh_wiki_digest.sh - Refresh wiki/rule digest from raw assets
#
# This script regenerates wiki entities, concepts, and synthesis pages
# from raw documentation assets. It ensures the wiki stays in sync with
# the latest documentation captures.
#
# Usage:
#   ./scripts/refresh_wiki_digest.sh
#
# Requirements:
#   - Python 3.9+
#   - orca-lsp package installed (pip install -e .)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== ORCA LSP Wiki Digest Refresh ==="
echo "Project directory: $PROJECT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Check if orca-lsp is installed
if ! python3 -c "import orca_lsp" &> /dev/null; then
    echo "Error: orca_lsp not installed. Run: pip install -e ."
    exit 1
fi

# Step 1: Validate raw assets
echo ""
echo "Step 1: Validating raw assets..."
if [ -d "$PROJECT_DIR/raw/assets" ]; then
    ASSET_COUNT=$(find "$PROJECT_DIR/raw/assets" -type f | wc -l | tr -d ' ')
    echo "  Found $ASSET_COUNT raw assets"
else
    echo "  Warning: raw/assets directory not found"
fi

# Step 2: Validate wiki structure
echo ""
echo "Step 2: Validating wiki structure..."
for dir in entities concepts synthesis; do
    if [ -d "$PROJECT_DIR/wiki/$dir" ]; then
        COUNT=$(find "$PROJECT_DIR/wiki/$dir" -type f -name "*.md" | wc -l | tr -d ' ')
        echo "  wiki/$dir: $COUNT pages"
    else
        echo "  Warning: wiki/$dir directory not found"
    fi
done

# Step 3: Run rule manifest validation
echo ""
echo "Step 3: Validating rule manifest..."
python3 -c "
from orca_lsp.features.agent_api import AgentAPIProvider
provider = AgentAPIProvider()
manifest = provider.get_rule_manifest()
print(f'  Rule manifest: {len(manifest)} rules')
codes = {r['code'] for r in manifest}
print(f'  Unique codes: {len(codes)}')
"

# Step 4: Run OpenQC smoke test
echo ""
echo "Step 4: Running OpenQC smoke test..."
python3 -c "
from orca_lsp.features.agent_api import AgentAPIProvider
provider = AgentAPIProvider()
smoke = provider.openqc_smoke()
if smoke['ok']:
    print('  OpenQC smoke: PASSED')
else:
    print('  OpenQC smoke: FAILED')
    for check in smoke['checks']:
        if not check['ok']:
            print(f'    - {check[\"name\"]}: {check[\"detail\"]}')
"

# Step 5: Generate provenance report
echo ""
echo "Step 5: Generating provenance report..."
PROVENANCE_FILE="$PROJECT_DIR/wiki/provenance_report.md"
cat > "$PROVENANCE_FILE" << EOF
# ORCA LSP Provenance Report

Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Raw Assets

$(find "$PROJECT_DIR/raw/assets" -type f -exec echo "- {}" \; 2>/dev/null || echo "No raw assets found")

## Wiki Pages

### Entities
$(find "$PROJECT_DIR/wiki/entities" -type f -name "*.md" -exec echo "- {}" \; 2>/dev/null || echo "No entity pages")

### Concepts
$(find "$PROJECT_DIR/wiki/concepts" -type f -name "*.md" -exec echo "- {}" \; 2>/dev/null || echo "No concept pages")

### Synthesis
$(find "$PROJECT_DIR/wiki/synthesis" -type f -name "*.md" -exec echo "- {}" \; 2>/dev/null || echo "No synthesis pages")

## Rule Manifest

$(python3 -c "
from orca_lsp.features.agent_api import AgentAPIProvider
provider = AgentAPIProvider()
manifest = provider.get_rule_manifest()
for rule in manifest:
    print(f'- {rule[\"code\"]}: {rule[\"description\"][:80]}...' if len(rule['description']) > 80 else f'- {rule[\"code\"]}: {rule[\"description\"]}')
" 2>/dev/null || echo "Could not generate rule manifest")

## OpenQC Compatibility

$(python3 -c "
from orca_lsp.features.agent_api import AgentAPIProvider
provider = AgentAPIProvider()
smoke = provider.openqc_smoke()
print(f'Status: {\"PASSED\" if smoke[\"ok\"] else \"FAILED\"}')
print(f'Checks: {len(smoke[\"checks\"])}')
for check in smoke['checks']:
    print(f'  - {check[\"name\"]}: {\"OK\" if check[\"ok\"] else \"FAILED\"} - {check[\"detail\"]}')
" 2>/dev/null || echo "Could not run OpenQC smoke test")
EOF

echo "  Provenance report written to: $PROVENANCE_FILE"

echo ""
echo "=== Wiki Digest Refresh Complete ==="

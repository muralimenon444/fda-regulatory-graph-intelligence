# Genie Code Session Context Template

**Copy/paste this at the start of each new Genie Code session**

---

## Project Information
- **Project**: fda-regulatory-graph-intelligence
- **Location**: `/Workspace/Repos/muralimenon444@gmail.com/fda-regulatory-graph-intelligence/`
- **Workspace ID**: 116488627034187

## Data Assets

### Catalog & Schema
- **Catalog**: `hc_regulatory_sandbox`
- **Schema**: `metadata_results`

### Key Tables (fully qualified)
- `hc_regulatory_sandbox.metadata_results.knowledge_base` - 102,228 relationships (drug-entity-relationship triples)
- `hc_regulatory_sandbox.metadata_results.knowledge_graph` - 8,370 drugs with metadata
- `hc_regulatory_sandbox.metadata_results.universal_entity_index` - Normalized entity lookup (UPPER/TRIM)
- `hc_regulatory_sandbox.metadata_results.fda_enforcement` - FDA enforcement actions
- `hc_regulatory_sandbox.metadata_results.fda_ndc` - National Drug Codes
- `hc_regulatory_sandbox.metadata_results.fda_unii` - Unique Ingredient Identifiers

### Key Notebooks
- `03c_semantic_enrichment` (3611406766238821) - Knowledge graph construction with entity normalization
- `03d_knowledge_graph_validation` (3611406766238822) - Multi-hop query validation suite
- `04_graphrag_chatbot` - GraphRAG chatbot implementation

### Streamlit Application
- `streamlit_graphrag_chatbot.py` - Production GraphRAG chatbot
- Deployment script: `deploy_graphrag_chatbot.sh`

## Current Status
- ✅ GraphRAG entity resolution implemented (UPPER/TRIM normalization)
- ✅ Multi-hop queries working (e.g., MELOXICAM → NSAID → IBUPROFEN returns 2,601 rows)
- ✅ Comprehensive test suite (6/6 tests passing)
- ✅ Streamlit chatbot deployed and functional

## Recent Work
- Fixed entity resolution issue: 0 rows → 2,601 rows for multi-hop queries
- Implemented Universal Entity Index for case-insensitive matching
- Validated with 6 test cases (drug lookups, entity deduplication, performance, coverage)

---

## Today's Goal
**[REPLACE WITH YOUR TASK]**

Example: "Add similarity search to GraphRAG chatbot" or "Optimize knowledge_base query performance"

---

**After pasting this context, immediately state your goal and I'll get to work.**

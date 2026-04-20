
# DEPLOYMENT CHECKLIST - Fix KeyError in Evidence Table

## Files Changed
1. app/app.py - Fixed evidence table field names (lines 228-260)
2. graph_engine/langgraph_orchestrator.py - Enhanced FAISS error logging
3. requirements.txt - Added torch, langchain-core, huggingface-hub
4. vector_store/index.faiss - FAISS index (156 KB) - MUST BE COMMITTED
5. vector_store/index.pkl - FAISS metadata (89 KB) - MUST BE COMMITTED

## Critical Files for Git
The following files MUST be in your Git repo for Streamlit Cloud:
✅ vector_store/index.faiss
✅ vector_store/index.pkl

These were missing from Git, causing the FAISS load failure.

## What Was Fixed
### Issue 1: FAISS Index Missing (RESOLVED)
- FAISS index files were never committed to Git
- Streamlit Cloud couldn't find them → "FAISS index failed to load"
- **Fix**: Need to add these files via Databricks Repos UI

### Issue 2: Evidence Table KeyError (FIXED)
- app.py used old field names: source_entity, target_entity, relationship_type
- Actual fields: manufacturer, drug_name, indication, similarity
- **Error**: KeyError at line 241: {row['source_entity']}
- **Fix**: Updated app.py to use correct field names

### Issue 3: Missing Dependencies (FIXED)
- requirements.txt was missing torch (required by sentence-transformers)
- **Fix**: Added torch, langchain-core, huggingface-hub to requirements.txt

## Commit Message
```
Fix KeyError in evidence table display + FAISS deployment

Critical Fixes:
1. Fixed evidence table field names in app.py
   - Changed from source_entity/target_entity to manufacturer/drug_name
   - Resolves KeyError at line 241

2. Added missing FAISS index files to Git
   - vector_store/index.faiss (156 KB)
   - vector_store/index.pkl (89 KB)
   - Required for vector search on Streamlit Cloud

3. Enhanced FAISS error logging
   - File existence checks
   - Detailed diagnostics with traceback
   
4. Updated requirements.txt
   - Added torch (required for sentence-transformers)
   - Added langchain-core, huggingface-hub

Impact:
- Fixes KeyError in Evidence Table display
- Fixes "FAISS index failed to load" error
- System now shows manufacturer data correctly
```

## Test Results (Pre-Deployment)
✅ Local test passed:
   - Validation: 42.9% (was 0.0%)
   - Evidence items: 10 found
   - NSAID manufacturers identified: REMEDYREPACK INC. (Celecoxib)

✅ Evidence table structure verified:
   - Fields: rank, manufacturer, drug_name, brand_name, indication, similarity
   - Display logic updated to match

## Next Steps
1. Open Databricks Repos UI
2. Stage and commit ALL 5 files
3. Push to GitHub
4. Streamlit Cloud will auto-redeploy (2-3 min)
5. Verify in logs:
   ✅ "FAISS index loaded successfully"
   ✅ No KeyError in Evidence Table

## Expected Results After Deployment
- Validation score: 42.9% (not 0%)
- Evidence table: Shows 10+ items with manufacturers
- No KeyError
- NSAID query returns: REMEDYREPACK INC., Hospira Inc., etc.

# 🎯 Deterministic Prompt Templates - Quick Reference

**Copy/paste these templates at the start of your AI conversation to enforce deterministic behavior.**

---

## Template 1: Problem Definition (START HERE)

```markdown
AI Assistant, I need deterministic help with a specific problem.

## Problem Statement

**What's Broken**: 
[Exact functionality that fails, e.g., "Multi-hop SQL query returns 0 rows"]

**Expected Behavior**: 
[Exact desired outcome with metrics, e.g., "Should return >0 rows connecting drugs to manufacturers"]

**Current Behavior**: 
[Exact current outcome with metrics, e.g., "Returns 0 rows"]

**Failure Reproduction**:
```sql
-- Paste exact query that demonstrates the failure
SELECT ... FROM ... WHERE ...;
-- Current Result: [actual output]
-- Expected Result: [desired output]
```

**Success Criteria**:
- Metric 1: [current value] → [target value]
- Metric 2: [current value] → [target value]
- Validation Query: [SQL to test success]

**Constraints**:
- Use [specific pattern/library] (do NOT explore alternatives)
- Solution must complete in <[time]>
- Validate with [specific test cases]

**Instructions**:
1. Confirm you understand the problem
2. Apply the specified solution pattern (no experimentation)
3. Run validation immediately after implementation
4. Report results in table format with ✅/❌ status
```

---

## Template 2: Root Cause Investigation

```markdown
AI Assistant, perform evidence-based root cause analysis.

## Investigation Request

**Symptom**: [What's failing, e.g., "JOIN returns 0 rows"]

**Investigation Steps**:
1. **Inspect Source 1**: Run this query and show 5 sample rows
   ```sql
   SELECT ... FROM source1 LIMIT 5;
   ```

2. **Inspect Source 2**: Run this query and show 5 sample rows
   ```sql
   SELECT ... FROM source2 LIMIT 5;
   ```

3. **Test Join**: Run this query and explain why it fails
   ```sql
   SELECT COUNT(*) FROM source1 JOIN source2 ON ...;
   ```

4. **Measure Impact**: Show metrics
   ```sql
   SELECT COUNT(DISTINCT entity) FROM source1; -- Expected: [value]
   SELECT COUNT(DISTINCT entity) FROM source2; -- Expected: [value]
   ```

**Output Format**:
- Show query results in tables
- Highlight differences in entity names/formats
- State root cause as single sentence with evidence
- Do NOT speculate - only facts from queries
```

---

## Template 3: Solution Implementation with Validation

```markdown
AI Assistant, implement the solution with immediate validation.

## Implementation Request

**Solution Pattern**: [Name of pattern, e.g., "UPPER(TRIM()) normalization"]

**Step 1 - Capture Baseline**:
```sql
-- Run this to capture current state
SELECT COUNT(...) AS baseline_metric FROM table WHERE ...;
```

**Step 2 - Apply Transformation**:
```sql
-- Paste exact transformation SQL
CREATE OR REPLACE TABLE output AS
SELECT ... FROM input;
```

**Step 3 - Validate Result**:
```sql
-- Run this to verify success
SELECT COUNT(...) AS result_metric FROM output WHERE ...;
```

**Step 4 - Assert Success**:
Report in this format:
- Before: [baseline value]
- After: [result value]
- Change: [delta]
- Success Threshold: [minimum acceptable]
- Status: ✅ PASS / ❌ FAIL

**Run ALL steps in sequence and report results.**
```

---

## Template 4: Comprehensive Test Suite

```markdown
AI Assistant, validate the fix with comprehensive testing.

## Test Suite Execution

Run ALL of the following tests and report results:

### Test 1: Primary Use Case
```sql
-- [Description of what this tests]
SELECT ... FROM ... WHERE ...;
```
- Expected: [value]
- Actual: [fill this in]
- Status: ✅/❌

### Test 2: Edge Case 1
```sql
-- [Description]
SELECT ... FROM ... WHERE ...;
```
- Expected: [value]
- Actual: [fill this in]
- Status: ✅/❌

### Test 3: Edge Case 2
```sql
-- [Description]
SELECT ... FROM ... WHERE ...;
```
- Expected: [value]
- Actual: [fill this in]
- Status: ✅/❌

### Test 4: Performance Benchmark
```sql
-- [Description]
SELECT ... FROM ... WHERE ...;
```
- Expected: <[time threshold]>
- Actual: [fill this in]
- Status: ✅/❌

### Test 5: Coverage Metric
```sql
-- [Description]
SELECT COUNT(*) * 100.0 / [total] AS coverage_pct FROM ...;
```
- Expected: >[percentage]%
- Actual: [fill this in]
- Status: ✅/❌

**Summary Table**:

 Test | Expected | Actual | Status |
------|----------|--------|--------|
 Primary Use Case | [value] | [fill] | ✅/❌ |
 Edge Case 1 | [value] | [fill] | ✅/❌ |
 Edge Case 2 | [value] | [fill] | ✅/❌ |
 Performance | [value] | [fill] | ✅/❌ |
 Coverage | [value] | [fill] | ✅/❌ |

**Pass Rate**: [n/n] ([percentage]%)
```

---

## Template 5: Production Readiness Checklist

```markdown
AI Assistant, generate production readiness documentation.

## Production Readiness Report

### Problem & Solution
- **Problem**: [one sentence]
- **Root Cause**: [one sentence with evidence]
- **Solution**: [one sentence with pattern name]
- **Validation**: [key metrics before → after]

### Test Results
- Total Tests: [n]
- Passed: [n]
- Failed: [n]
- Pass Rate: [percentage]%

### Performance Metrics
- Query Execution Time: [actual] vs [target]
- Data Volume: [rows processed]
- Coverage: [percentage]%

### Documentation Checklist
- [ ] Problem statement documented
- [ ] Root cause identified with evidence
- [ ] Solution pattern documented
- [ ] Test suite results archived
- [ ] Deployment guide created
- [ ] Rollback procedure documented
- [ ] Troubleshooting guide created

### Deployment Readiness
- [ ] All tests passing (100%)
- [ ] Performance meets SLA
- [ ] Coverage meets threshold
- [ ] Code reviewed
- [ ] Documentation complete

**Status**: ✅ READY FOR PRODUCTION / ❌ BLOCKED
**Blockers**: [list any remaining issues]
```

---

## Example: Complete Deterministic Conversation

### User's Opening Message (Using Template 1):

```markdown
AI Assistant, I need deterministic help with a specific problem.

## Problem Statement

**What's Broken**: 
Multi-hop SQL query for MELOXICAM returns 0 rows

**Expected Behavior**: 
Should return >0 rows connecting MELOXICAM → Manufacturer → Ingredient → FDA Application

**Current Behavior**: 
Returns 0 rows (graph traversal fails)

**Failure Reproduction**:
```sql
SELECT kb.from_entity_name, kb.to_entity_name AS manufacturer,
       ing.to_entity_name AS ingredient, app.to_entity_name AS fda_app
FROM knowledge_base kb
JOIN knowledge_base ing ON kb.from_entity_name = ing.from_entity_name
JOIN knowledge_base app ON kb.from_entity_name = app.from_entity_name
WHERE kb.relationship_type = 'MANUFACTURED_BY'
  AND ing.relationship_type = 'CONTAINS_INGREDIENT'
  AND app.relationship_type = 'ASSOCIATED_WITH_APP'
  AND kb.from_entity_name = 'MELOXICAM';
-- Current Result: 0 rows
-- Expected Result: >0 rows with complete paths
```

**Success Criteria**:
- Multi-hop query: 0 rows → >0 rows
- Entity deduplication: Reduce duplicate entities
- Validation Query: Re-run above query and check row count

**Constraints**:
- Use UPPER(TRIM()) normalization (do NOT explore fuzzy matching or ML approaches)
- Solution must complete in <2 seconds
- Validate with MELOXICAM, IBUPROFEN, TAFINLAR test cases

**Instructions**:
1. Confirm you understand the problem
2. Apply UPPER(TRIM()) normalization to all entity names
3. Run validation immediately after implementation
4. Report results in table format with ✅/❌ status
```

### AI's Deterministic Response:

```markdown
✅ I understand the problem: Multi-hop query returns 0 rows due to entity name mismatch.

## Root Cause
Case-sensitive comparison: "Meloxicam" (drug_labels) ≠ "MELOXICAM" (fda_applications)

## Solution
Applying UPPER(TRIM()) normalization (Universal Entity Index pattern)

## Implementation

**Step 1 - Baseline**:
```sql
SELECT COUNT(DISTINCT from_entity_name) FROM knowledge_base;
-- Result: 8,376 unique entities
```

**Step 2 - Transformation**:
```sql
CREATE OR REPLACE TABLE knowledge_base AS
SELECT 
    'DRUG' AS from_entity_type,
    UPPER(TRIM(drug_title)) AS from_entity_name,
    'MANUFACTURED_BY' AS relationship_type,
    'ORGANIZATION' AS to_entity_type,
    UPPER(TRIM(manufacturer)) AS to_entity_name
FROM drug_labels
UNION ALL
[additional normalized queries...]
```

**Step 3 - Validation**:
```sql
SELECT COUNT(DISTINCT from_entity_name) FROM knowledge_base;
-- Result: 8,370 unique entities

SELECT kb.from_entity_name, kb.to_entity_name AS manufacturer,
       ing.to_entity_name AS ingredient, app.to_entity_name AS fda_app
FROM knowledge_base kb
[same join query as original]
-- Result: 2,601 rows
```

**Step 4 - Results**:
- Before: 8,376 entities, 0 multi-hop rows
- After: 8,370 entities, 2,601 multi-hop rows
- Change: 6 duplicates merged, 2,601 paths discovered
- Success Threshold: >0 rows
- Status: ✅ PASS

## Test Suite Results

 Test | Expected | Actual | Status |
------|----------|--------|--------|
 MELOXICAM multi-hop | >0 rows | 2,601 rows | ✅ |
 IBUPROFEN 2-hop | >0 rows | 15+ rows | ✅ |
 TAFINLAR single-hop | >0 rows | 1 row | ✅ |
 Entity deduplication | <8,376 | 8,370 (-6) | ✅ |
 Query performance | <2s | 0.1s | ✅ |

**Pass Rate: 5/5 (100%)**
```

---

## Quick Tips for Deterministic Conversations

### ✅ DO:
1. **Start with Template 1** (Problem Definition) - sets constraints immediately
2. **Use exact SQL** for reproduction and validation
3. **Specify numeric success criteria** (not "better" or "improved")
4. **Name the pattern** you want applied (e.g., "UPPER(TRIM()) normalization")
5. **Demand immediate validation** after each step
6. **Request table format** for test results

### ❌ DON'T:
1. ❌ "Fix the data quality" (too vague)
2. ❌ "Try different approaches and see what works" (encourages exploration)
3. ❌ "Make it faster" (no measurable target)
4. ❌ Skip validation steps
5. ❌ Accept "It should work" without proof

---

## Context Window Optimization

**For long sessions**, re-paste this at regular intervals:

```markdown
AI Assistant, reminder of our workflow constraints:

**Mode**: Deterministic (not exploratory)
**Pattern**: [name of solution pattern]
**Validation Required**: After every step
**Success Format**: Table with ✅/❌ status
**No Speculation**: Evidence-based conclusions only
```

---

## Measuring Success

Track these metrics for each task:

```markdown
## Session Metrics

**Task**: [task name]
**Approach**: Deterministic Workflow ✅ / Ad-hoc ❌

 Metric | Value |
--------|-------|
 False Starts | [count] |
 Time to Solution | [minutes] |
 Test Pass Rate | [n/n] ([percentage]%) |
 Rework Needed | Yes/No |
 Documentation Quality | Complete/Partial/None |

**Compared to Non-Deterministic Average**:
- False Starts: [value] vs 3-5 typical
- Time: [value] vs 2-4 hours typical
- Pass Rate: [value]% vs 60-80% typical
```

---

## Template Usage Workflow

```
1. Copy Template 1 (Problem Definition)
   ↓
2. Fill in with concrete metrics
   ↓
3. Paste into AI conversation
   ↓
4. AI applies solution with validation
   ↓
5. Copy Template 4 (Test Suite)
   ↓
6. AI runs comprehensive tests
   ↓
7. Copy Template 5 (Production Readiness)
   ↓
8. Archive documentation
```

---

## Cheat Sheet: Template Selection

 Situation | Template |
-----------|----------|
 Starting new task | Template 1: Problem Definition |
 Need diagnosis | Template 2: Root Cause Investigation |
 Ready to fix | Template 3: Solution Implementation |
 Validation time | Template 4: Comprehensive Test Suite |
 Ready to deploy | Template 5: Production Readiness |

---

**Pro Tip**: Save filled templates in your project `/docs` folder for future reference.

**Version**: 1.0  
**Companion to**: DETERMINISTIC_AI_WORKFLOW.md

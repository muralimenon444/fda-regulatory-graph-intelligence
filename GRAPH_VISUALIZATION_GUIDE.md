# Graph Visualization Guide for Healthcare Regulatory Intelligence

## Databricks-Native Options Comparison

| Feature | PyVis ⭐ Recommended | Plotly | NetworkX + Matplotlib | Neo4j (External) |
|---------|---------------------|--------|----------------------|------------------|
| **Databricks Native** | ✅ Pure Python | ✅ Pre-installed | ✅ Pre-installed | ❌ Requires external service |
| **Interactivity** | ⭐⭐⭐⭐⭐ Drag, zoom, physics | ⭐⭐⭐⭐ Click, zoom | ⭐ Static images | ⭐⭐⭐⭐⭐ Full graph DB queries |
| **Streamlit Support** | ✅ Excellent (components.html) | ✅ Native (st.plotly_chart) | ✅ (st.pyplot) | ❌ Requires external viz |
| **Setup Complexity** | ⭐ Simple (pip install pyvis) | ⭐ None (already installed) | ⭐ None | ⭐⭐⭐⭐⭐ Complex infrastructure |
| **Performance (100+ nodes)** | ⭐⭐⭐⭐ Fast, client-side physics | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Fast static | ⭐⭐⭐⭐⭐ Excellent with indexing |
| **Learning Curve** | ⭐⭐ Easy | ⭐⭐⭐ Moderate | ⭐⭐ Easy | ⭐⭐⭐⭐⭐ Steep (Cypher, administration) |
| **Styling/Colors** | ⭐⭐⭐⭐ Per-node colors, sizes | ⭐⭐⭐⭐⭐ Highly customizable | ⭐⭐⭐ Basic | ⭐⭐⭐⭐ Good with Bloom |
| **Use Case Fit** | ✅ Perfect for this app | ✅ Good alternative | ❌ Too basic | ❌ Overkill for viz only |

## Why PyVis is Recommended

### ✅ Pros
* **100% Databricks-native**: No external services needed
* **Interactive out-of-the-box**: Users can drag nodes, zoom, explore relationships
* **Physics-based layout**: Graph automatically arranges itself beautifully
* **Easy integration**: Works seamlessly with Streamlit via `components.html`
* **Low overhead**: Just add 2 libraries (pyvis, networkx)
* **Works with your data**: Directly consumes your evidence_table structure

### ❌ When NOT to Use PyVis
* Need server-side graph queries (use Neo4j)
* Need real-time graph updates (use Neo4j + websockets)
* Graph > 1000 nodes (consider subgraphs or Neo4j)
* Need graph algorithms (shortest path, PageRank) at query time (use Neo4j)

## Why NOT Neo4j for "Visualization Only"

You mentioned staying within Databricks stack - **Neo4j is external infrastructure**:

### ❌ Cons for Visualization-Only Use Case
1. **Infrastructure complexity**
   * Requires separate Neo4j server (Databricks → Neo4j → Streamlit)
   * Need to manage Neo4j instance (cloud or self-hosted)
   * Data synchronization: FAISS → Neo4j copy

2. **Cost**
   * Neo4j Bloom (visualization tool) requires Enterprise license
   * Neo4j Aura (cloud) pricing starts at $65/month
   * Adds operational overhead

3. **Overkill**
   * Neo4j is a full graph database for complex queries
   * You already have FAISS for search
   * For 100-200 nodes, client-side rendering is sufficient

4. **Not Databricks-native**
   * Breaks your "stay in Databricks" requirement
   * Adds external dependency

### ✅ When Neo4j DOES Make Sense
* You need graph algorithms (shortest path, community detection, etc.)
* Complex multi-hop queries ("find all drugs by manufacturers who also make NSAIDs")
* Real-time graph updates from multiple sources
* Graph size > 10,000 nodes
* **You want to replace FAISS, not just visualize**

## Implementation Guide

### Option 1: PyVis (Recommended) ⭐

**Installation:**
```bash
pip install pyvis networkx
```

**Code:** (See GRAPH_VISUALIZATION_CODE.py in this repo)

**Integration Point:**
* Add after evidence table display in `app/app.py`
* Function: `display_knowledge_graph(evidence_table)`

**What Users See:**
* Interactive graph below evidence table
* Blue nodes: Manufacturers
* Green nodes: Drugs  
* Orange nodes: Ingredients
* Drag nodes, zoom, click for details

**Estimated Dev Time:** 30 minutes

---

### Option 2: Plotly Network Graph

**Installation:**
```bash
# Already installed in Databricks
```

**Pros:**
* No new dependencies
* Highly customizable
* Good for static reports

**Cons:**
* More code to build graph layout
* Less interactive than PyVis
* Manual positioning required

**Use When:** You need publication-quality static visualizations

---

### Option 3: NetworkX + Matplotlib

**Installation:**
```bash
# Already installed in Databricks
```

**Pros:**
* Simplest code
* Good for exploratory analysis in notebooks

**Cons:**
* Static images only
* Basic styling
* Not interactive

**Use When:** Quick prototyping in Databricks notebooks (not for Streamlit)

---

## Architecture Decision

### Current Architecture (Working)
```
User Query → Streamlit App → LangGraph Orchestrator → FAISS Vector Search
                                                    → LLM Reasoning (Databricks)
                                                    → Evidence Table
```

### Recommended: Add PyVis Visualization
```
User Query → Streamlit App → LangGraph Orchestrator → FAISS Vector Search
                                                    → LLM Reasoning (Databricks)
                                                    → Evidence Table
                                                    → PyVis Graph (NEW) ✅
```

### NOT Recommended: Add Neo4j for Viz Only
```
User Query → Streamlit App → LangGraph Orchestrator → FAISS Vector Search
                                                    → LLM Reasoning (Databricks)
                                                    → Evidence Table
                                                    → Export to Neo4j (❌ complexity)
                                                    → Neo4j Bloom (❌ licensing)
```

## Next Steps

1. **Immediate:** Add PyVis to your app (see GRAPH_VISUALIZATION_CODE.py)
2. **Short-term:** Evaluate if graph queries are needed (then consider Neo4j)
3. **Long-term:** If you add 1000+ drugs, consider:
   * Neo4j as primary graph store
   * FAISS for vector search + Neo4j for relationships
   * Unified graph database architecture

## Files in This Repo

* `GRAPH_VISUALIZATION_CODE.py` - Complete PyVis implementation
* `GRAPH_VISUALIZATION_GUIDE.md` - This file
* `examples/pyvis_example.html` - Sample interactive graph
* `examples/plotly_example.html` - Sample Plotly graph

## Support

Both PyVis and NetworkX have excellent documentation:
* PyVis: https://pyvis.readthedocs.io/
* NetworkX: https://networkx.org/documentation/
* Streamlit Components: https://docs.streamlit.io/library/components

---

**TL;DR:** Use PyVis. It's Databricks-native, interactive, and perfect for your use case. Neo4j is overkill for visualization-only needs.

import sys
import os

# Force the repository root into the Python path
# This ensures 'graph_engine' is discoverable regardless of where the script is launched
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(current_dir, ".."))

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Diagnostic log - This will show up in Streamlit 'Manage App' logs
print(f"DEBUG: System Path initialized with Root: {repo_root}")
print(f"DEBUG: Contents of Root: {os.listdir(repo_root)}")

# Configure FAISS index path for Streamlit deployment
faiss_index_path = os.path.join(repo_root, "vector_store")
print(f"DEBUG: FAISS index path configured: {faiss_index_path}")

"""
Streamlit Research Interface for Healthcare Regulatory Intelligence
Healthcare Regulatory Intelligence with side-by-side Evidence + Analysis
"""

import streamlit as st
import pandas as pd
import sys
import os

# Add graph_engine to path
# sys.path.append('/Workspace/Repos/muralimenon444@gmail.com/fda-regulatory-graph-intelligence')

from graph_engine.langgraph_orchestrator import get_orchestrator


@st.cache_resource(show_spinner=False)
def get_cached_orchestrator(faiss_index_path: str):
    """
    Cached orchestrator initialization for Streamlit.
    
    The orchestrator is expensive to initialize (loads embedding model + FAISS index).
    Cache it with st.cache_resource to avoid reloading on every query.
    
    Args:
        faiss_index_path: Path to FAISS index directory
    
    Returns:
        Initialized HealthcareGraphRAG orchestrator
    """
    print(f"🔄 Initializing orchestrator (this happens once per deployment)...")
    print(f"   FAISS path: {faiss_index_path}")
    
    orchestrator = get_orchestrator(faiss_index_path=faiss_index_path)
    
    # Verify the vector store loaded successfully
    if orchestrator.vector_store is None:
        st.error("⚠️ FAISS index failed to load! Check Streamlit logs for details.")
        print("❌ CRITICAL: FAISS vector store is None - searches will return no results")
    else:
        print("✅ Orchestrator initialized successfully with FAISS index")
    
    return orchestrator


# Page Configuration
st.set_page_config(
    page_title="Healthcare Regulatory Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional layout
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #1f2937;
    }
    .evidence-card {
        background: #f9fafb;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin-bottom: 0.5rem;
    }
    .relationship {
        font-family: 'Courier New', monospace;
        background: #e0e7ff;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.9rem;
    }
    .validation-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.875rem;
    }
    .validation-high { background: #d1fae5; color: #065f46; }
    .validation-medium { background: #fef3c7; color: #92400e; }
    .validation-low { background: #fee2e2; color: #991b1b; }
</style>
""", unsafe_allow_html=True)


def normalize_input(text: str) -> str:
    """Normalize user input with UPPER(TRIM())"""
    return text.upper().strip()


def get_validation_badge(score: float) -> str:
    """Generate HTML badge for validation score"""
    if score >= 0.7:
        badge_class = "validation-high"
        label = "HIGH CONFIDENCE"
    elif score >= 0.4:
        badge_class = "validation-medium"
        label = "MEDIUM CONFIDENCE"
    else:
        badge_class = "validation-low"
        label = "LOW CONFIDENCE"
    
    return f'<span class="validation-badge {badge_class}">{label} ({score:.1%})</span>'




# ============================================================================
# Graph Visualization Functions
# ============================================================================

import streamlit.components.v1 as components
from pyvis.network import Network
import networkx as nx


def build_knowledge_graph(evidence_table):
    """
    Build force-directed network: Manufacturers → Drugs → Active Ingredients
    
    Args:
        evidence_table: List of dicts with manufacturer, drug_name, ingredients
    
    Returns:
        PyVis Network object, node count, edge count
    """
    import networkx as nx
    from pyvis.network import Network
    import re
    
    # Use undirected graph for natural clustering
    G = nx.Graph()
    
    print(f"\n{'='*60}")
    print(f"BUILDING NETWORK GRAPH from {len(evidence_table)} items")
    print(f"{'='*60}")
    
    # Track nodes by type
    manufacturers_added = set()
    drugs_added = set()
    ingredients_added = set()
    edge_count = 0
    
    for idx, item in enumerate(evidence_table[:10], 1):
        manufacturer = item.get("manufacturer", "Unknown")
        drug_name_meta = item.get("drug_name", "Unknown")
        brand_name = item.get("brand_name", "")
        active_ingredient = item.get("active_ingredient", "N/A")
        ingredients_str = item.get("ingredients", "")
        
        if manufacturer == "Unknown":
            continue
        
        # SMART DRUG NAME EXTRACTION
        # If drug_name == manufacturer (repackager case), use active_ingredient or brand_name
        if drug_name_meta == manufacturer or drug_name_meta == "Unknown":
            if active_ingredient and active_ingredient != "N/A":
                drug_identifier = active_ingredient.split('|')[0].strip()  # First active ingredient
            elif brand_name and brand_name != manufacturer:
                # Extract drug name from brand_name like "MANUFACTURER (DrugName)"
                match = re.search(r'\(([^)]+)\)', brand_name)
                if match:
                    drug_identifier = match.group(1)
                else:
                    drug_identifier = f"{manufacturer}_product_{idx}"
            else:
                drug_identifier = f"{manufacturer}_product_{idx}"
        else:
            drug_identifier = drug_name_meta
        
        print(f"\n{idx}. {manufacturer} → {drug_identifier}")
        
        # Add MANUFACTURER node (LARGE BLUE CIRCLE)
        if manufacturer not in manufacturers_added:
            G.add_node(
                manufacturer,
                label=manufacturer[:30],
                title=f"Manufacturer: {manufacturer}",
                color="#3b82f6",  # bright blue
                size=50,
                shape="dot",
                borderWidth=3,
                font={'size': 16, 'color': 'white', 'bold': True}
            )
            manufacturers_added.add(manufacturer)
            print(f"   + Manufacturer (blue): {manufacturer}")
        
        # Add DRUG node (MEDIUM GREEN CIRCLE)
        if drug_identifier not in drugs_added:
            G.add_node(
                drug_identifier,
                label=drug_identifier[:30],
                title=f"Drug: {drug_identifier}",
                color="#10b981",  # bright green
                size=35,
                shape="dot",
                borderWidth=2,
                font={'size': 14, 'color': 'white'}
            )
            drugs_added.add(drug_identifier)
            print(f"   + Drug (green): {drug_identifier}")
        
        # Add EDGE: Manufacturer ↔ Drug (THICK WHITE LINE)
        if not G.has_edge(manufacturer, drug_identifier):
            G.add_edge(
                manufacturer,
                drug_identifier,
                title="manufactures",
                color={'color': '#FFFFFF', 'highlight': '#FFFF00'},
                width=5,
                value=5
            )
            edge_count += 1
            print(f"   ✓ Edge: {manufacturer} ↔ {drug_identifier}")
        
        # Add ACTIVE INGREDIENT as orange node (better than full ingredients list)
        if active_ingredient and active_ingredient != "N/A":
            # Split if multiple active ingredients
            active_ing_list = [ing.strip() for ing in active_ingredient.split('|') if ing.strip()]
            
            for ing in active_ing_list[:2]:  # Up to 2 active ingredients per drug
                if len(ing) > 3 and ing.upper() != drug_identifier.upper():
                    if ing not in ingredients_added:
                        G.add_node(
                            ing,
                            label=ing[:20],
                            title=f"Active Ingredient: {ing}",
                            color="#f59e0b",  # bright orange
                            size=25,
                            shape="dot",
                            borderWidth=1,
                            font={'size': 12, 'color': 'white'}
                        )
                        ingredients_added.add(ing)
                        print(f"     + Ingredient (orange): {ing}")
                    
                    # Add EDGE: Drug ↔ Ingredient
                    if not G.has_edge(drug_identifier, ing):
                        G.add_edge(
                            drug_identifier,
                            ing,
                            title="contains",
                            color={'color': '#999999', 'highlight': '#FFFF00'},
                            width=3,
                            value=3
                        )
                        edge_count += 1
                        print(f"     ✓ Edge: {drug_identifier} ↔ {ing}")
    
    print(f"\n{'='*60}")
    print(f"NETWORK SUMMARY:")
    print(f"  🔵 Manufacturers: {len(manufacturers_added)}")
    print(f"  🟢 Drugs: {len(drugs_added)}")
    print(f"  🟠 Active Ingredients: {len(ingredients_added)}")
    print(f"  Total nodes: {len(G.nodes())}")
    print(f"  Total edges: {edge_count}")
    print(f"{'='*60}\n")
    
    if len(G.nodes()) == 0:
        print("⚠️  No nodes created")
        return None, 0, 0
    
    # Create PyVis with PHYSICS-BASED layout
    net = Network(
        height="500px",
        width="100%",
        bgcolor="#1e1e1e",
        font_color="white",
        notebook=False
    )
    
    net.from_nx(G)
    
    # Force-directed layout config
    net.set_options("""
    {
      "nodes": {
        "font": {"size": 14, "color": "white"},
        "scaling": {"min": 10, "max": 50}
      },
      "edges": {
        "color": {"inherit": false},
        "smooth": {"enabled": true, "type": "continuous"},
        "scaling": {"min": 1, "max": 5}
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -80000,
          "centralGravity": 0.3,
          "springLength": 200,
          "springConstant": 0.04,
          "damping": 0.5
        },
        "stabilization": {"enabled": true, "iterations": 200}
      },
      "interaction": {
        "hover": true,
        "zoomView": true,
        "dragView": true,
        "navigationButtons": true
      }
    }
    """)
    
    return net, len(G.nodes()), len(G.edges())
    return net, len(G.nodes()), len(G.edges())


def display_knowledge_graph(evidence_table):
    """
    Display interactive knowledge graph in Streamlit
    
    Args:
        evidence_table: List of evidence items from orchestrator
    """
    if not evidence_table or len(evidence_table) == 0:
        st.info("No graph data available. Run a search to see relationships.")
        return
    
    st.markdown("*Hierarchical view: Manufacturers ➜ Drugs ➜ Ingredients*")
    
    try:
        # Build graph
        result = build_knowledge_graph(evidence_table)
        
        if result is None or result[0] is None:
            st.warning("Unable to build graph. Check Streamlit logs for details.")
            print("⚠️  build_knowledge_graph returned None")
            return
        
        net, node_count, edge_count = result
        
        if node_count == 0:
            st.warning("No graph relationships found in evidence.")
            return
        
        # Display stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Nodes", node_count)
        col2.metric("Edges", edge_count)
        col3.metric("Evidence", len(evidence_table))
        
        # Generate and display HTML
        graph_html = net.generate_html()
        components.html(graph_html, height=550, scrolling=False)
        
        # Legend
        st.markdown("""
        <div style="padding: 10px; background: #f9fafb; border-radius: 5px; margin-top: 10px;">
            <strong>Legend:</strong> 
            <span style="color: #3b82f6;">●</span> Manufacturers  
            <span style="color: #10b981;">●</span> Drugs  
            <span style="color: #f59e0b;">●</span> Ingredients
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error generating graph: {str(e)}")
        print(f"Graph generation error: {e}")
        import traceback
        traceback.print_exc()



def main():
    # Header
    st.markdown('<div class="main-header">🏥 Healthcare Regulatory Intelligence</div>', unsafe_allow_html=True)
    st.markdown("*Powered by Knowledge Graphs, Vector Search, and Agentic AI*")
    
    # Sidebar
    with st.sidebar:
        st.header("About")
        st.markdown("""
        **GraphRAG System Features:**
        - 🔍 Hybrid Search (Vector + Graph)
        - 🧠 LLM Reasoning (Llama 3.3 70B)
        - ✅ Hallucination Detection
        - 📊 Evidence-Based Citations
        
        **Data Sources:**
        - FDA Drugs@FDA Database
        - DailyMed SPL Labels
        - National Drug Codes (NDC)
        - UNII Substance Registry
        """)
        
        st.divider()
        
        st.header("Example Queries")
        example_queries = [
            "What are the indications for MELOXICAM?",
            "Find drugs similar to IBUPROFEN",
            "List manufacturers of NSAID drugs",
            "What drugs treat rheumatoid arthritis?"
        ]
        
        for query in example_queries:
            if st.button(query, key=f"example_{query}"):
                st.session_state["query_input"] = query
    
    # Main Query Input
    query = st.text_input(
        "Enter your research question:",
        placeholder="e.g., What are the clinical indications for MELOXICAM?",
        key="query_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_button:
        st.session_state["results"] = None
        st.rerun()
    
    # Execute Search
    if search_button and query:
        with st.spinner("🤖 Searching knowledge graph and generating analysis..."):
            try:
                # Normalize input before passing to orchestrator
                normalized_query = normalize_input(query)
                
                # Diagnostic logs for debugging
                MODEL_ENDPOINT = os.getenv("MODEL_NAME", "databricks-meta-llama-3-3-70b-instruct")
                print(f"DEBUG: Active LLM Endpoint: {MODEL_ENDPOINT}")
                print(f"DEBUG: Loading FAISS from: {faiss_index_path}")
                
                # Initialize orchestrator and execute query
                orchestrator = get_cached_orchestrator(faiss_index_path)
                results = orchestrator.query(normalized_query)
                
                st.session_state["results"] = results
                st.session_state["original_query"] = query
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    # Display Results (Side-by-Side Layout)
    if "results" in st.session_state and st.session_state["results"]:
        results = st.session_state["results"]
        
        st.divider()
        st.subheader(f"Results for: *{st.session_state.get('original_query', '')}*")
        
        # Validation Badge
        validation_score = results.get("validation_score", 0.0)
        st.markdown(get_validation_badge(validation_score), unsafe_allow_html=True)
        
        # Two-column layout: Analysis (Left) | Evidence (Right)
        col_analysis, col_evidence = st.columns([1, 1])
        
        with col_analysis:
            st.markdown("### 📝 AI Analysis")
            st.markdown(results["final_answer"])
        
        with col_evidence:
            # Knowledge Graph at the top
            st.markdown("### 🕸️ Knowledge Graph")
            
            evidence_table = results.get("evidence_table", [])
            
            if evidence_table and len(evidence_table) > 0:
                display_knowledge_graph(evidence_table)
            else:
                st.info("No graph data available.")
            
            # Evidence Table below graph
            st.divider()
            st.markdown("### 📊 Evidence Table")
            
            evidence_table = results.get("evidence_table", [])
            
            if evidence_table:
                # Convert to DataFrame for display
                df = pd.DataFrame(evidence_table)
                
                # Format as cards for better readability
                st.markdown(f"**{len(evidence_table)} Knowledge Graph Relationships**")
                
                for i, row in enumerate(evidence_table[:15], 1):  # Show top 15
                    # Get fields with safe defaults
                    manufacturer = row.get('manufacturer', 'Unknown')
                    drug_name = row.get('drug_name', '')
                    indication = row.get('indication', 'N/A')
                    similarity = row.get('similarity', '0.000')
                    
                    # Format display
                    display_text = manufacturer
                    if drug_name and drug_name != manufacturer:
                        display_text += f" ({drug_name})"
                    
                    st.markdown(f"""
                    <div class="evidence-card">
                        <strong>#{i}</strong><br>
                        <strong>{display_text}</strong><br>
                        <small>{indication[:100]}...</small><br>
                        <small>Similarity: {similarity}</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Download option
                st.download_button(
                    label="📥 Download Full Evidence (CSV)",
                    data=df.to_csv(index=False),
                    file_name="evidence_table.csv",
                    mime="text/csv"
                )
            
            
            else:
                st.info("No evidence found in knowledge graph.")
    
    # Footer
    st.divider()
    st.caption("Healthcare Regulatory Intelligence System | Medallion Architecture | GraphRAG + LangGraph")


if __name__ == "__main__":
    main()

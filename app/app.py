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
    Build interactive knowledge graph from evidence_table
    
    Args:
        evidence_table: List of dicts with manufacturer, drug_name, ingredients
    
    Returns:
        PyVis Network object, node count, edge count
    """
    import networkx as nx
    from pyvis.network import Network
    
    G = nx.Graph()
    
    # Track unique entities to avoid duplicates
    manufacturers = set()
    drugs = set()
    ingredients_set = set()
    
    print(f"DEBUG: Building graph from {len(evidence_table)} evidence items")
    
    for idx, item in enumerate(evidence_table):
        manufacturer = item.get("manufacturer", "Unknown")
        drug_name = item.get("drug_name", "Unknown")
        
        # Get ingredients from the evidence table
        # The orchestrator includes 'ingredients' field (pipe-separated)
        ingredient_str = item.get("ingredients", "")
        
        print(f"DEBUG: Item {idx+1}: {manufacturer} -> {drug_name}")
        
        # Skip if missing critical data
        if manufacturer == "Unknown":
            continue
        
        # Add manufacturer node (blue)
        if manufacturer not in manufacturers:
            G.add_node(
                manufacturer, 
                title=f"Manufacturer: {manufacturer}",
                color="#3b82f6",  # bright blue
                size=35,
                group="manufacturer",
                borderWidth=3,
                borderColor="white"
            )
            manufacturers.add(manufacturer)
        
        # Add drug node (green) - even if drug_name == manufacturer
        drug_node_name = drug_name if drug_name != "Unknown" else manufacturer
        if drug_node_name not in drugs:
            G.add_node(
                drug_node_name,
                title=f"Drug: {drug_node_name}",
                color="#10b981",  # bright green
                size=30,
                group="drug",
                borderWidth=2,
                borderColor="white"
            )
            drugs.add(drug_node_name)
        
        # Add edge: manufacturer → drug (BRIGHT WHITE)
        if not G.has_edge(manufacturer, drug_node_name):
            G.add_edge(manufacturer, drug_node_name, 
                      title="manufactures",
                      color="#ffffff",  # white edges
                      width=3)
            print(f"  Added edge: {manufacturer} -> {drug_node_name}")
        
        # Add ingredient nodes (orange)
        if ingredient_str:
            ingredients_list = ingredient_str.split("|")
            print(f"  Ingredients: {len(ingredients_list)} found")
            
            for ingredient in ingredients_list[:2]:  # Limit to 2 ingredients per drug
                ingredient = ingredient.strip()
                if ingredient and len(ingredient) > 3:
                    if ingredient not in ingredients_set:
                        G.add_node(
                            ingredient,
                            title=f"Ingredient: {ingredient}",
                            color="#f59e0b",  # bright orange
                            size=25,
                            group="ingredient",
                            borderWidth=2,
                            borderColor="white"
                        )
                        ingredients_set.add(ingredient)
                    
                    if not G.has_edge(drug_node_name, ingredient):
                        G.add_edge(drug_node_name, ingredient, 
                                  title="contains",
                                  color="#cccccc",  # light gray
                                  width=2)
                        print(f"    Added edge: {drug_node_name} -> {ingredient}")
    
    print(f"DEBUG: Graph built - Nodes: {len(G.nodes())}, Edges: {len(G.edges())}")
    print(f"  Manufacturers: {len(manufacturers)}")
    print(f"  Drugs: {len(drugs)}")
    print(f"  Ingredients: {len(ingredients_set)}")
    
    # Create PyVis network with better visibility
    net = Network(
        height="500px",
        width="100%",
        bgcolor="#1e1e1e",
        font_color="white",
        notebook=False
    )
    
    # Import NetworkX graph
    net.from_nx(G)
    
    # Configure physics for clustered layout
    net.set_options("""
    {
      "nodes": {
        "font": {"size": 12, "color": "white", "face": "arial"},
        "borderWidth": 2
      },
      "edges": {
        "color": {"inherit": false},
        "smooth": {
          "enabled": true,
          "type": "continuous"
        },
        "width": 2
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -40000,
          "centralGravity": 0.4,
          "springLength": 120,
          "springConstant": 0.05,
          "damping": 0.5
        },
        "minVelocity": 0.75,
        "stabilization": {
          "enabled": true,
          "iterations": 100
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
    """)
    
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
    
    st.markdown("*Drag nodes • Zoom with wheel • Click for details*")
    
    try:
        # Build graph
        net, node_count, edge_count = build_knowledge_graph(evidence_table)
        
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

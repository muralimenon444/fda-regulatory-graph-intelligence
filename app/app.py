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
                
                # Initialize orchestrator and execute query
                orchestrator = get_orchestrator()
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
            st.markdown("### 📊 Evidence Table")
            
            evidence_table = results.get("evidence_table", [])
            
            if evidence_table:
                # Convert to DataFrame for display
                df = pd.DataFrame(evidence_table)
                
                # Format as cards for better readability
                st.markdown(f"**{len(evidence_table)} Knowledge Graph Relationships**")
                
                for i, row in enumerate(evidence_table[:15], 1):  # Show top 15
                    st.markdown(f"""
                    <div class="evidence-card">
                        <strong>#{i}</strong><br>
                        <span class="relationship">
                            {row['source_entity']} 
                            <strong>--[{row['relationship_type']}]--></strong> 
                            {row['target_entity']}
                        </span><br>
                        <small>Confidence: {row['confidence_score']:.2f}</small>
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

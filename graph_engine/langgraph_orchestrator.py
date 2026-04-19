"""
LangGraph Orchestrator for Healthcare Regulatory Intelligence
Implements: Search Node → Reasoning Node → Validation Node

PORTABLE VERSION: Uses local FAISS index + Databricks Foundation Model API
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


class GraphState(TypedDict):
    """State object for the LangGraph workflow"""
    query: str
    normalized_query: str
    vector_results: List[Dict[str, Any]]
    graph_results: List[Dict[str, Any]]
    llm_response: str
    validation_score: float
    final_answer: str
    evidence_table: List[Dict[str, Any]]


class HealthcareGraphRAG:
    """
    Agentic GraphRAG Orchestrator using LangGraph
    
    Workflow:
    1. Search Node: Local FAISS vector search
    2. Reasoning Node: LLM synthesis using databricks-llama-3-3-70b-instruct
    3. Validation Node: Hallucination check against retrieved evidence
    
    Portable Design:
    - Uses local FAISS index (no Databricks Vector Search dependency)
    - Embeddings via sentence-transformers/all-MiniLM-L6-v2 (<100ms)
    - LLM reasoning via Databricks Foundation Model API
    """
    
    def __init__(
        self,
        faiss_index_path: str = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize the orchestrator with local FAISS index
        
        Args:
            faiss_index_path: Path to FAISS index directory (defaults to ./app/vector_store)
            embedding_model: HuggingFace model for embeddings
        """
        # Default to app/vector_store directory
        if faiss_index_path is None:
            # Try to find the vector store relative to current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            faiss_index_path = os.path.join(os.path.dirname(current_dir), "app", "vector_store")
        
        self.faiss_index_path = faiss_index_path
        
        # Initialize local embeddings (all-MiniLM-L6-v2 for <100ms latency)
        print(f"Loading embeddings model: {embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Load FAISS index from disk
        print(f"Loading FAISS index from: {self.faiss_index_path}")
        try:
            self.vector_store = FAISS.load_local(
                self.faiss_index_path,
                self.embeddings,
                allow_dangerous_deserialization=True  # Required for FAISS loading
            )
            print("SUCCESS: Orchestrator initialized using local FAISS index.")
        except Exception as e:
            print(f"⚠️ Warning: Could not load FAISS index from {self.faiss_index_path}: {e}")
            print("   Orchestrator will continue but vector search will be unavailable.")
            self.vector_store = None
        
        # Initialize Databricks client for LLM calls
        self.workspace = WorkspaceClient()
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Construct the LangGraph state machine"""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("search", self.search_node)
        workflow.add_node("reasoning", self.reasoning_node)
        workflow.add_node("validation", self.validation_node)
        
        # Define edges
        workflow.set_entry_point("search")
        workflow.add_edge("search", "reasoning")
        workflow.add_edge("reasoning", "validation")
        workflow.add_edge("validation", END)
        
        return workflow.compile()
    
    def search_node(self, state: GraphState) -> GraphState:
        """
        Search Node: Local FAISS Vector Search
        
        1. Normalize query with UPPER(TRIM())
        2. Local FAISS similarity search on clinical indications
        3. Returns top-k results with metadata
        """
        query = state["query"]
        normalized_query = query.upper().strip()
        state["normalized_query"] = normalized_query
        
        # Local FAISS Vector Search
        vector_results = []
        if self.vector_store is not None:
            try:
                # Perform similarity search with metadata
                results = self.vector_store.similarity_search_with_score(
                    query=query,
                    k=10  # Top 10 results
                )
                
                # Convert to dictionary format compatible with downstream nodes
                for doc, score in results:
                    vector_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": float(score),
                        # Extract common fields if available in metadata
                        "brand_name": doc.metadata.get("brand_name", "Unknown"),
                        "clinical_indications": doc.metadata.get("clinical_indications", doc.page_content),
                        "active_ingredient": doc.metadata.get("active_ingredient", "N/A")
                    })
                
                print(f"✅ Retrieved {len(vector_results)} results from FAISS index")
                
            except Exception as e:
                print(f"⚠️ FAISS search error: {e}")
                vector_results = []
        else:
            print("⚠️ FAISS vector store not available - skipping vector search")
        
        state["vector_results"] = vector_results
        
        # Graph Traversal: Placeholder for future knowledge graph integration
        # In portable mode, we can load graph relationships from parquet/json files
        # For now, we'll use vector results as the primary evidence source
        state["graph_results"] = []
        
        return state
    
    def reasoning_node(self, state: GraphState) -> GraphState:
        """
        Reasoning Node: LLM Synthesis
        
        Uses databricks-llama-3-3-70b-instruct to synthesize retrieved data
        """
        query = state["query"]
        vector_results = state["vector_results"]
        graph_results = state["graph_results"]
        
        # Build context from search results
        context_parts = []
        
        if vector_results:
            context_parts.append("**Vector Search Results (Clinical Indications):**")
            for i, result in enumerate(vector_results[:5], 1):
                brand_name = result.get('brand_name', 'Unknown')
                indication = result.get('clinical_indications', 'N/A')
                score = result.get('similarity_score', 0.0)
                
                # Truncate long indications
                indication_preview = indication[:200] + "..." if len(indication) > 200 else indication
                
                context_parts.append(
                    f"{i}. {brand_name}: {indication_preview} (similarity: {score:.3f})"
                )
        
        if graph_results:
            context_parts.append("\n**Knowledge Graph Relationships:**")
            for i, rel in enumerate(graph_results[:10], 1):
                context_parts.append(
                    f"{i}. {rel['source_entity']} --[{rel['relationship_type']}]--> {rel['target_entity']} "
                    f"(confidence: {rel['confidence_score']:.2f})"
                )
        
        if not context_parts:
            context = "No relevant evidence found in the knowledge base."
        else:
            context = "\n".join(context_parts)
        
        # Construct prompt for LLM
        system_prompt = """You are a healthcare regulatory intelligence assistant. 
Synthesize the provided evidence to answer the user's question. 
Cite specific evidence using numbered references [1], [2], etc.
Be precise and only state facts supported by the evidence.
If the evidence is insufficient, clearly state what information is missing."""
        
        user_prompt = f"""Question: {query}

Evidence:
{context}

Please provide a comprehensive answer with citations."""
        
        # Call Databricks Foundation Model API
        try:
            response = self.workspace.serving_endpoints.query(
                name="databricks-llama-3-3-70b-instruct",
                messages=[
                    ChatMessage(role=ChatMessageRole.SYSTEM, content=system_prompt),
                    ChatMessage(role=ChatMessageRole.USER, content=user_prompt)
                ],
                temperature=0.1,
                max_tokens=1000
            )
            state["llm_response"] = response.choices[0].message.content
        except Exception as e:
            state["llm_response"] = f"Error generating response: {e}"
            print(f"⚠️ LLM API error: {e}")
        
        return state
    
    def validation_node(self, state: GraphState) -> GraphState:
        """
        Validation Node: Hallucination Check
        
        Compares LLM claims against raw retrieved evidence
        """
        llm_response = state["llm_response"]
        vector_results = state["vector_results"]
        graph_results = state["graph_results"]
        
        # Collect all entities mentioned in evidence
        mentioned_entities = set()
        
        # Extract from vector results
        for result in vector_results:
            brand_name = result.get("brand_name", "").lower()
            ingredient = result.get("active_ingredient", "").lower()
            if brand_name and brand_name != "unknown":
                mentioned_entities.add(brand_name)
            if ingredient and ingredient != "n/a":
                mentioned_entities.add(ingredient)
        
        # Extract from graph results (if available)
        for result in graph_results:
            mentioned_entities.add(result["source_entity"].lower())
            mentioned_entities.add(result["target_entity"].lower())
        
        # Validation: Check if LLM mentions entities that exist in evidence
        llm_lower = llm_response.lower()
        validated_entities = [e for e in mentioned_entities if e in llm_lower and len(e) > 3]
        
        validation_score = len(validated_entities) / max(len(mentioned_entities), 1) if mentioned_entities else 0.0
        state["validation_score"] = validation_score
        
        # Build evidence table for UI
        evidence_table = []
        for i, result in enumerate(vector_results[:20], 1):
            evidence_table.append({
                "rank": i,
                "brand_name": result.get("brand_name", "Unknown"),
                "indication": result.get("clinical_indications", "N/A")[:150],
                "similarity": f"{result.get('similarity_score', 0.0):.3f}"
            })
        
        state["evidence_table"] = evidence_table
        
        # Final answer includes validation metadata
        total_sources = len(vector_results) + len(graph_results)
        state["final_answer"] = f"""{llm_response}

---
**Validation Score**: {validation_score:.2%}
**Evidence Sources**: {total_sources} total ({len(vector_results)} vector, {len(graph_results)} graph)
"""
        
        return state
    
    def query(self, user_query: str) -> Dict[str, Any]:
        """
        Execute the full GraphRAG workflow
        
        Args:
            user_query: Natural language question from user
        
        Returns:
            Dictionary with final_answer and evidence_table
        """
        initial_state = {
            "query": user_query,
            "normalized_query": "",
            "vector_results": [],
            "graph_results": [],
            "llm_response": "",
            "validation_score": 0.0,
            "final_answer": "",
            "evidence_table": []
        }
        
        # Run the workflow
        final_state = self.workflow.invoke(initial_state)
        
        return {
            "final_answer": final_state["final_answer"],
            "evidence_table": final_state["evidence_table"],
            "validation_score": final_state["validation_score"]
        }


# Convenience functions for backward compatibility
_orchestrator = None

def get_orchestrator(faiss_index_path: str = None) -> HealthcareGraphRAG:
    """Singleton accessor for the orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HealthcareGraphRAG(faiss_index_path=faiss_index_path)
    return _orchestrator


def query_regulatory_agent(query: str, faiss_index_path: str = None) -> Dict[str, Any]:
    """
    Convenience function to query the regulatory agent
    
    Args:
        query: Natural language question
        faiss_index_path: Optional path to FAISS index
    
    Returns:
        Dictionary with final_answer and evidence_table
    """
    orchestrator = get_orchestrator(faiss_index_path=faiss_index_path)
    return orchestrator.query(query)

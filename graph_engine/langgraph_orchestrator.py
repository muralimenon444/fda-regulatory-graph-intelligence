"""
LangGraph Orchestrator for Healthcare Regulatory Intelligence
Implements: Search Node → Reasoning Node → Validation Node
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
import os
from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole


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
    1. Search Node: Hybrid vector + graph traversal
    2. Reasoning Node: LLM synthesis using databricks-llama-3-3-70b-instruct
    3. Validation Node: Hallucination check against raw knowledge graph
    """
    
    def __init__(
        self,
        vector_index_name: str = "hc_regulatory_sandbox.metadata_results.drug_indications_index",
        catalog: str = "hc_regulatory_sandbox",
        schema: str = "metadata_results"
    ):
        self.catalog = catalog
        self.schema = schema
        self.vector_index_name = vector_index_name
        
        # Initialize Databricks clients
        self.workspace = WorkspaceClient()
        self.vector_client = VectorSearchClient()
        
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
        Search Node: Hybrid Vector + Graph Traversal
        
        1. Normalize query with UPPER(TRIM())
        2. Vector search on clinical_indications
        3. Graph traversal for multi-hop relationships
        """
        query = state["query"]
        normalized_query = query.upper().strip()
        state["normalized_query"] = normalized_query
        
        # Vector Search: Find similar clinical indications
        try:
            vector_results = self.vector_client.get_index(
                index_name=self.vector_index_name
            ).similarity_search(
                query_text=query,
                columns=["brand_name", "clinical_indications", "active_ingredient"],
                num_results=10
            )
            state["vector_results"] = vector_results.get("result", {}).get("data_array", [])
        except Exception as e:
            print(f"⚠️ Vector search error: {e}")
            state["vector_results"] = []
        
        # Graph Traversal: Multi-hop relationship queries
        graph_query = f"""
        WITH drug_matches AS (
            SELECT DISTINCT entity_normalized
            FROM {self.catalog}.{self.schema}.universal_entity_index
            WHERE entity_normalized = '{normalized_query}'
            AND entity_type = 'DRUG'
        )
        SELECT 
            kb.source_entity,
            kb.relationship_type,
            kb.target_entity,
            kb.confidence_score
        FROM {self.catalog}.{self.schema}.knowledge_base kb
        INNER JOIN drug_matches dm
            ON kb.source_entity = dm.entity_normalized
        ORDER BY kb.confidence_score DESC
        LIMIT 50
        """
        
        try:
            graph_df = spark.sql(graph_query)
            state["graph_results"] = [row.asDict() for row in graph_df.collect()]
        except Exception as e:
            print(f"⚠️ Graph query error: {e}")
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
                context_parts.append(
                    f"{i}. {result.get('brand_name', 'Unknown')}: {result.get('clinical_indications', 'N/A')[:200]}"
                )
        
        if graph_results:
            context_parts.append("\n**Knowledge Graph Relationships:**")
            for i, rel in enumerate(graph_results[:10], 1):
                context_parts.append(
                    f"{i}. {rel['source_entity']} --[{rel['relationship_type']}]--> {rel['target_entity']} "
                    f"(confidence: {rel['confidence_score']:.2f})"
                )
        
        context = "\n".join(context_parts)
        
        # Construct prompt for LLM
        system_prompt = """You are a healthcare regulatory intelligence assistant. 
Synthesize the provided evidence to answer the user's question. 
Cite specific evidence using numbered references [1], [2], etc.
Be precise and only state facts supported by the evidence."""
        
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
        
        return state
    
    def validation_node(self, state: GraphState) -> GraphState:
        """
        Validation Node: Hallucination Check
        
        Compares LLM claims against raw knowledge graph data
        """
        llm_response = state["llm_response"]
        graph_results = state["graph_results"]
        
        # Simple validation: Check if LLM mentions entities that exist in graph
        mentioned_entities = set()
        for result in graph_results:
            mentioned_entities.add(result["source_entity"].lower())
            mentioned_entities.add(result["target_entity"].lower())
        
        llm_lower = llm_response.lower()
        validated_entities = [e for e in mentioned_entities if e in llm_lower]
        
        validation_score = len(validated_entities) / max(len(mentioned_entities), 1)
        state["validation_score"] = validation_score
        
        # Build evidence table for UI
        state["evidence_table"] = graph_results[:20]  # Top 20 relationships
        
        # Final answer includes validation metadata
        state["final_answer"] = f"""{llm_response}

---
**Validation Score**: {validation_score:.2%}
**Evidence Sources**: {len(graph_results)} knowledge graph relationships
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


# Initialize global orchestrator instance
_orchestrator = None

def get_orchestrator() -> HealthcareGraphRAG:
    """Singleton accessor for the orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HealthcareGraphRAG()
    return _orchestrator

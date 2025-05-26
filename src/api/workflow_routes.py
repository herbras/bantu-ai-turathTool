from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import json
import time
from datetime import datetime

from agno.storage.workflow.sqlite import SqliteWorkflowStorage
from ..workflows import TurathResearchWorkflow, TurathPublicationWorkflow


router = APIRouter(prefix="/workflows", tags=["Workflows"])


# Pydantic Models
class ResearchWorkflowRequest(BaseModel):
    research_query: str = Field(
        ..., description="Main research query in Arabic or English"
    )
    research_type: str = Field(
        default="comprehensive", description="Type: quick, comprehensive, academic"
    )
    output_format: str = Field(
        default="article", description="Format: article, summary, academic_paper"
    )
    include_scientific: bool = Field(
        default=True, description="Include ArXiv/PubMed scientific literature"
    )
    include_web_sources: bool = Field(
        default=True, description="Include Tavily web search"
    )
    max_sources: int = Field(default=10, description="Maximum sources to gather")
    use_cache: bool = Field(default=True, description="Use caching for performance")
    session_id: Optional[str] = Field(
        default=None, description="Custom session ID for workflow state"
    )


class PublicationWorkflowRequest(BaseModel):
    publication_topic: str = Field(..., description="Academic publication topic")
    publication_type: str = Field(
        default="academic_paper",
        description="Type: academic_paper, book_chapter, monograph",
    )
    target_audience: str = Field(
        default="academic", description="Audience: academic, general, specialized"
    )
    citation_style: str = Field(
        default="chicago", description="Style: chicago, apa, mla, islamic_traditional"
    )
    peer_review_rounds: int = Field(
        default=2, description="Number of peer review simulation rounds"
    )
    word_count_target: Optional[int] = Field(
        default=None, description="Target word count"
    )
    use_cache: bool = Field(default=True, description="Use caching for performance")
    session_id: Optional[str] = Field(
        default=None, description="Custom session ID for workflow state"
    )


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str  # running, completed, failed
    progress: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    session_id: str


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowStatusResponse]
    total: int


# Global workflow tracking
active_workflows: Dict[str, Dict[str, Any]] = {}


# Workflow catalog - available workflow types
WORKFLOW_CATALOG = [
    {
        "workflow_id": "turath-research-workflow",
        "name": "TurathResearchWorkflow",
        "description": "Comprehensive Islamic research workflow that orchestrates multiple AI agents to research, analyze, and synthesize Islamic knowledge from diverse sources. This workflow combines traditional Islamic texts, contemporary scholarly works, and scientific literature to provide well-researched, fact-checked content. The system excels at creating balanced perspectives that honor classical scholarship while addressing modern contexts.",
    },
    {
        "workflow_id": "turath-publication-workflow",
        "name": "TurathPublicationWorkflow",
        "description": "An intelligent academic publication system that produces scholarly papers, books, and research articles with proper Islamic academic methodology. This workflow orchestrates multiple AI agents to conduct literature reviews, develop research methodologies, analyze sources, and create publication-ready content with peer review simulation. The system excels at combining traditional Islamic scholarship with modern academic standards.",
    },
]


def generate_workflow_id() -> str:
    """Generate unique workflow ID"""
    return f"workflow_{int(time.time() * 1000)}"


def create_workflow_storage(
    session_id: str, workflow_type: str
) -> SqliteWorkflowStorage:
    """Create workflow storage with proper configuration"""
    return SqliteWorkflowStorage(
        table_name=f"turath_{workflow_type}_workflows", db_file="workflows.db"
    )


@router.get("/", response_model=List[Dict[str, str]])
async def list_available_workflows():
    """List all available workflow types (Agno-style catalog)"""
    return WORKFLOW_CATALOG


@router.get("/instances", response_model=WorkflowListResponse)
async def list_workflow_instances():
    """List all active and recent workflow instances"""
    workflows = []
    for workflow_id, info in active_workflows.items():
        workflows.append(
            WorkflowStatusResponse(
                workflow_id=workflow_id,
                status=info["status"],
                progress=info.get("progress"),
                started_at=info["started_at"],
                completed_at=info.get("completed_at"),
                session_id=info["session_id"],
            )
        )

    return WorkflowListResponse(workflows=workflows, total=len(workflows))


@router.get("/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get status of specific workflow"""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    info = active_workflows[workflow_id]
    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        status=info["status"],
        progress=info.get("progress"),
        started_at=info["started_at"],
        completed_at=info.get("completed_at"),
        session_id=info["session_id"],
    )


@router.post("/research/run")
async def run_research_workflow(request: ResearchWorkflowRequest):
    """Execute research workflow and return complete result"""
    workflow_id = generate_workflow_id()
    session_id = request.session_id or f"research-{workflow_id}"

    # Track workflow
    active_workflows[workflow_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "session_id": session_id,
        "type": "research",
    }

    try:
        # Initialize workflow
        workflow = TurathResearchWorkflow(
            session_id=session_id,
            storage=create_workflow_storage(session_id, "research"),
        )

        # Run workflow
        response_iterator = workflow.run(
            research_query=request.research_query,
            research_type=request.research_type,
            output_format=request.output_format,
            use_cache=request.use_cache,
            include_scientific=request.include_scientific,
            include_web_sources=request.include_web_sources,
            max_sources=request.max_sources,
        )

        # Collect all responses
        final_content = ""
        progress_updates = []

        for response in response_iterator:
            if response.event.value == "workflow_progress":
                progress_updates.append(response.content)
                active_workflows[workflow_id]["progress"] = response.content
            elif response.event.value == "workflow_completed":
                final_content = response.content

        # Mark as completed
        active_workflows[workflow_id].update(
            {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "result": final_content,
            }
        )

        return {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "status": "completed",
            "result": final_content,
            "progress_log": progress_updates,
        }

    except Exception as e:
        active_workflows[workflow_id].update(
            {
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error": str(e),
            }
        )
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")


@router.post("/research/stream")
async def stream_research_workflow(request: ResearchWorkflowRequest):
    """Execute research workflow with streaming response"""
    workflow_id = generate_workflow_id()
    session_id = request.session_id or f"research-stream-{workflow_id}"

    async def generate_stream():
        """Generate streaming response"""
        try:
            # Track workflow
            active_workflows[workflow_id] = {
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "session_id": session_id,
                "type": "research_stream",
            }

            # Initialize workflow
            workflow = TurathResearchWorkflow(
                session_id=session_id,
                storage=create_workflow_storage(session_id, "research"),
            )

            # Stream responses
            response_iterator = workflow.run(
                research_query=request.research_query,
                research_type=request.research_type,
                output_format=request.output_format,
                use_cache=request.use_cache,
                include_scientific=request.include_scientific,
                include_web_sources=request.include_web_sources,
                max_sources=request.max_sources,
            )

            for response in response_iterator:
                # Format as SSE
                data = {
                    "workflow_id": workflow_id,
                    "event": response.event.value,
                    "content": response.content,
                    "timestamp": datetime.now().isoformat(),
                }

                yield f"data: {json.dumps(data)}\n\n"

                # Update tracking
                if response.event.value == "workflow_progress":
                    active_workflows[workflow_id]["progress"] = response.content
                elif response.event.value == "workflow_completed":
                    active_workflows[workflow_id].update(
                        {
                            "status": "completed",
                            "completed_at": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            error_data = {
                "workflow_id": workflow_id,
                "event": "workflow_failed",
                "content": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }
            yield f"data: {json.dumps(error_data)}\n\n"

            active_workflows[workflow_id].update(
                {
                    "status": "failed",
                    "completed_at": datetime.now().isoformat(),
                    "error": str(e),
                }
            )

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/publication/run")
async def run_publication_workflow(request: PublicationWorkflowRequest):
    """Execute publication workflow and return complete result"""
    workflow_id = generate_workflow_id()
    session_id = request.session_id or f"publication-{workflow_id}"

    # Track workflow
    active_workflows[workflow_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "session_id": session_id,
        "type": "publication",
    }

    try:
        # Initialize workflow
        workflow = TurathPublicationWorkflow(
            session_id=session_id,
            storage=create_workflow_storage(session_id, "publication"),
        )

        # Run workflow
        response_iterator = workflow.run(
            publication_topic=request.publication_topic,
            publication_type=request.publication_type,
            target_audience=request.target_audience,
            citation_style=request.citation_style,
            peer_review_rounds=request.peer_review_rounds,
            use_cache=request.use_cache,
            word_count_target=request.word_count_target,
        )

        # Collect all responses
        final_content = ""
        progress_updates = []

        for response in response_iterator:
            if response.event.value == "workflow_progress":
                progress_updates.append(response.content)
                active_workflows[workflow_id]["progress"] = response.content
            elif response.event.value == "workflow_completed":
                final_content = response.content

        # Mark as completed
        active_workflows[workflow_id].update(
            {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "result": final_content,
            }
        )

        return {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "status": "completed",
            "result": final_content,
            "progress_log": progress_updates,
        }

    except Exception as e:
        active_workflows[workflow_id].update(
            {
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error": str(e),
            }
        )
        raise HTTPException(
            status_code=500, detail=f"Publication workflow failed: {str(e)}"
        )


@router.post("/publication/stream")
async def stream_publication_workflow(request: PublicationWorkflowRequest):
    """Execute publication workflow with streaming response"""
    workflow_id = generate_workflow_id()
    session_id = request.session_id or f"publication-stream-{workflow_id}"

    async def generate_stream():
        """Generate streaming response"""
        try:
            # Track workflow
            active_workflows[workflow_id] = {
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "session_id": session_id,
                "type": "publication_stream",
            }

            # Initialize workflow
            workflow = TurathPublicationWorkflow(
                session_id=session_id,
                storage=create_workflow_storage(session_id, "publication"),
            )

            # Stream responses
            response_iterator = workflow.run(
                publication_topic=request.publication_topic,
                publication_type=request.publication_type,
                target_audience=request.target_audience,
                citation_style=request.citation_style,
                peer_review_rounds=request.peer_review_rounds,
                use_cache=request.use_cache,
                word_count_target=request.word_count_target,
            )

            for response in response_iterator:
                # Format as SSE
                data = {
                    "workflow_id": workflow_id,
                    "event": response.event.value,
                    "content": response.content,
                    "timestamp": datetime.now().isoformat(),
                }

                yield f"data: {json.dumps(data)}\n\n"

                # Update tracking
                if response.event.value == "workflow_progress":
                    active_workflows[workflow_id]["progress"] = response.content
                elif response.event.value == "workflow_completed":
                    active_workflows[workflow_id].update(
                        {
                            "status": "completed",
                            "completed_at": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            error_data = {
                "workflow_id": workflow_id,
                "event": "workflow_failed",
                "content": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }
            yield f"data: {json.dumps(error_data)}\n\n"

            active_workflows[workflow_id].update(
                {
                    "status": "failed",
                    "completed_at": datetime.now().isoformat(),
                    "error": str(e),
                }
            )

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """Cancel or remove workflow"""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow_info = active_workflows[workflow_id]

    if workflow_info["status"] == "running":
        # In production, you'd implement actual cancellation logic
        workflow_info.update(
            {"status": "cancelled", "completed_at": datetime.now().isoformat()}
        )

    # Remove from tracking
    del active_workflows[workflow_id]

    return {"message": f"Workflow {workflow_id} removed", "status": "success"}


@router.post("/research/quick")
async def quick_research(query: str):
    """Quick research endpoint for simple queries"""
    request = ResearchWorkflowRequest(
        research_query=query,
        research_type="quick",
        output_format="summary",
        include_scientific=False,
        max_sources=5,
    )
    return await run_research_workflow(request)


@router.get("/templates")
async def get_workflow_templates():
    """Get pre-configured workflow templates"""
    return {
        "research_templates": {
            "fatwa_quick": {
                "research_type": "quick",
                "output_format": "summary",
                "include_scientific": False,
                "max_sources": 5,
                "description": "Quick fatwa-style research",
            },
            "academic_comprehensive": {
                "research_type": "comprehensive",
                "output_format": "article",
                "include_scientific": True,
                "include_web_sources": True,
                "max_sources": 15,
                "description": "Comprehensive academic research",
            },
            "modern_issues": {
                "research_type": "academic",
                "output_format": "article",
                "include_scientific": True,
                "include_web_sources": True,
                "max_sources": 12,
                "description": "Modern Islamic issues with scientific context",
            },
        },
        "publication_templates": {
            "academic_paper": {
                "publication_type": "academic_paper",
                "citation_style": "chicago",
                "peer_review_rounds": 2,
                "word_count_target": 8000,
                "description": "Standard academic paper",
            },
            "book_chapter": {
                "publication_type": "book_chapter",
                "citation_style": "apa",
                "peer_review_rounds": 1,
                "word_count_target": 5000,
                "description": "Book chapter format",
            },
            "research_brief": {
                "publication_type": "academic_paper",
                "citation_style": "islamic_traditional",
                "peer_review_rounds": 1,
                "word_count_target": 3000,
                "description": "Short research brief",
            },
        },
    }


@router.get("/health")
async def workflow_health_check():
    """Health check for workflow service"""
    return {
        "status": "healthy",
        "service": "workflow_service",
        "active_workflows": len(active_workflows),
        "workflow_types": ["research", "publication"],
        "features": [
            "multi_source_search",
            "fact_checking",
            "streaming_responses",
            "session_persistence",
            "caching",
        ],
    }


@router.post("/{catalog_workflow_id}/run")
async def run_workflow_by_catalog_id(
    catalog_workflow_id: str, request_data: Dict[str, Any]
):
    """Run workflow by catalog workflow_id (Agno-style execution)"""

    # Validate catalog workflow ID
    valid_workflows = {wf["workflow_id"]: wf for wf in WORKFLOW_CATALOG}
    if catalog_workflow_id not in valid_workflows:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{catalog_workflow_id}' not found. Available: {list(valid_workflows.keys())}",
        )

    workflow_info = valid_workflows[catalog_workflow_id]

    try:
        if catalog_workflow_id == "turath-research-workflow":
            # Convert generic request to ResearchWorkflowRequest
            research_request = ResearchWorkflowRequest(
                research_query=request_data.get(
                    "research_query", request_data.get("query", "")
                ),
                research_type=request_data.get("research_type", "comprehensive"),
                output_format=request_data.get("output_format", "article"),
                include_scientific=request_data.get("include_scientific", True),
                include_web_sources=request_data.get("include_web_sources", True),
                max_sources=request_data.get("max_sources", 10),
                use_cache=request_data.get("use_cache", True),
                session_id=request_data.get("session_id"),
            )
            return await run_research_workflow(research_request)

        elif catalog_workflow_id == "turath-publication-workflow":
            # Convert generic request to PublicationWorkflowRequest
            publication_request = PublicationWorkflowRequest(
                publication_topic=request_data.get(
                    "publication_topic", request_data.get("topic", "")
                ),
                publication_type=request_data.get("publication_type", "academic_paper"),
                target_audience=request_data.get("target_audience", "academic"),
                citation_style=request_data.get("citation_style", "chicago"),
                peer_review_rounds=request_data.get("peer_review_rounds", 2),
                word_count_target=request_data.get("word_count_target"),
                use_cache=request_data.get("use_cache", True),
                session_id=request_data.get("session_id"),
            )
            return await run_publication_workflow(publication_request)

        else:
            raise HTTPException(
                status_code=501,
                detail=f"Workflow '{catalog_workflow_id}' not implemented",
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute workflow '{catalog_workflow_id}': {str(e)}",
        )


@router.post("/{catalog_workflow_id}/stream")
async def stream_workflow_by_catalog_id(
    catalog_workflow_id: str, request_data: Dict[str, Any]
):
    """Stream workflow execution by catalog workflow_id"""

    # Validate catalog workflow ID
    valid_workflows = {wf["workflow_id"]: wf for wf in WORKFLOW_CATALOG}
    if catalog_workflow_id not in valid_workflows:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{catalog_workflow_id}' not found. Available: {list(valid_workflows.keys())}",
        )

    try:
        if catalog_workflow_id == "turath-research-workflow":
            # Convert generic request to ResearchWorkflowRequest
            research_request = ResearchWorkflowRequest(
                research_query=request_data.get(
                    "research_query", request_data.get("query", "")
                ),
                research_type=request_data.get("research_type", "comprehensive"),
                output_format=request_data.get("output_format", "article"),
                include_scientific=request_data.get("include_scientific", True),
                include_web_sources=request_data.get("include_web_sources", True),
                max_sources=request_data.get("max_sources", 10),
                use_cache=request_data.get("use_cache", True),
                session_id=request_data.get("session_id"),
            )
            return await stream_research_workflow(research_request)

        elif catalog_workflow_id == "turath-publication-workflow":
            # Convert generic request to PublicationWorkflowRequest
            publication_request = PublicationWorkflowRequest(
                publication_topic=request_data.get(
                    "publication_topic", request_data.get("topic", "")
                ),
                publication_type=request_data.get("publication_type", "academic_paper"),
                target_audience=request_data.get("target_audience", "academic"),
                citation_style=request_data.get("citation_style", "chicago"),
                peer_review_rounds=request_data.get("peer_review_rounds", 2),
                word_count_target=request_data.get("word_count_target"),
                use_cache=request_data.get("use_cache", True),
                session_id=request_data.get("session_id"),
            )
            return await stream_publication_workflow(publication_request)

        else:
            raise HTTPException(
                status_code=501,
                detail=f"Streaming for workflow '{catalog_workflow_id}' not implemented",
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stream workflow '{catalog_workflow_id}': {str(e)}",
        )


# Legacy endpoints (for backward compatibility)
@router.get("/list", response_model=WorkflowListResponse)
async def list_workflows_legacy():
    """Legacy endpoint - use /instances instead"""
    return await list_workflow_instances()

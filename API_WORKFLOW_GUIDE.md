# 🚀 Turath AI Workflow API Guide

Complete REST API documentation for Turath AI Workflow orchestration system.

## 🌟 Overview

The Workflow API provides powerful orchestration capabilities for Islamic research and academic publication:

- **🔍 Research Workflows** - Multi-source Islamic research with fact-checking
- **📖 Publication Workflows** - Academic paper writing with peer review simulation  
- **🌊 Streaming Support** - Real-time progress updates via Server-Sent Events
- **💾 Smart Caching** - Session-based state management for performance
- **⚡ Parallel Processing** - Concurrent workflow execution

## 📋 Base URL

```
http://localhost:8000/workflows
```

## 🔧 Quick Start

### 1. Start the API Server
```bash
# Install dependencies
pip install agno fastapi uvicorn

# Run the server
uvicorn src.api.app:app --reload --port 8000
```

### 2. Test Workflow Health
```bash
curl http://localhost:8000/workflows/health
```

### 3. Quick Research
```bash
curl -X POST "http://localhost:8000/workflows/research/quick" \
  -H "Content-Type: application/json" \
  -d '{"query": "حكم زكاة الذهب"}'
```

## 📚 Research Workflow Endpoints

### POST `/research/run`
Execute complete research workflow and return final result.

**Request Body:**
```json
{
  "research_query": "حكم زكاة الذهب المُدَّخر للزينة",
  "research_type": "comprehensive",
  "output_format": "article", 
  "include_scientific": true,
  "include_web_sources": true,
  "max_sources": 10,
  "use_cache": true,
  "session_id": "research-session-1"
}
```

**Response:**
```json
{
  "workflow_id": "workflow_1703123456789",
  "session_id": "research-session-1",
  "status": "completed",
  "result": "# حكم زكاة الذهب المُدَّخر للزينة\n\n## المقدمة\n...",
  "progress_log": [
    "📋 Stage 1: Research Planning...",
    "🔍 Stage 2: Information Gathering...",
    "✅ Stage 3: Fact Checking...",
    "✍️ Stage 4: Content Writing...",
    "📝 Stage 5: Editorial Review..."
  ]
}
```

### POST `/research/stream`
Execute research workflow with streaming progress updates.

**Request:** Same as `/research/run`

**Response:** Server-Sent Events stream
```
data: {"workflow_id": "workflow_123", "event": "workflow_progress", "content": "📋 Stage 1: Research Planning...", "timestamp": "2024-01-01T12:00:00"}

data: {"workflow_id": "workflow_123", "event": "workflow_completed", "content": "# Final Result...", "timestamp": "2024-01-01T12:05:00"}
```

### POST `/research/quick?query={query}`
Quick research endpoint for simple fatwa-style queries.

**Example:**
```bash
curl -X POST "http://localhost:8000/workflows/research/quick?query=أحكام%20صلاة%20المسافر"
```

## 📖 Publication Workflow Endpoints

### POST `/publication/run`
Execute academic publication workflow with peer review simulation.

**Request Body:**
```json
{
  "publication_topic": "تطبيق مقاصد الشريعة في النوازل المعاصرة",
  "publication_type": "academic_paper",
  "target_audience": "academic",
  "citation_style": "chicago",
  "peer_review_rounds": 2,
  "word_count_target": 8000,
  "use_cache": true,
  "session_id": "publication-session-1"
}
```

**Response:**
```json
{
  "workflow_id": "workflow_1703123456790",
  "session_id": "publication-session-1", 
  "status": "completed",
  "result": "# تطبيق مقاصد الشريعة في النوازل المعاصرة\n\n## Abstract\n...\n\n## Publication Metadata\n...",
  "progress_log": [
    "📚 Stage 1: Literature Review...",
    "🔬 Stage 2: Research Methodology...",
    "📋 Stage 3: Source Analysis...",
    "✍️ Stage 4: Academic Writing...",
    "👥 Stage 5.1: Peer Review Round 1...",
    "👥 Stage 5.2: Peer Review Round 2...",
    "📝 Stage 6: Final Editing..."
  ]
}
```

### POST `/publication/stream`
Execute publication workflow with streaming updates.

**Request:** Same as `/publication/run`
**Response:** Server-Sent Events stream (similar to research stream)

## ⚙️ Management Endpoints

### GET `/`
List all active and recent workflows.

**Response:**
```json
{
  "workflows": [
    {
      "workflow_id": "workflow_1703123456789",
      "status": "completed",
      "progress": null,
      "started_at": "2024-01-01T12:00:00",
      "completed_at": "2024-01-01T12:05:00",
      "session_id": "research-session-1"
    }
  ],
  "total": 1
}
```

### GET `/{workflow_id}`
Get status of specific workflow.

**Response:**
```json
{
  "workflow_id": "workflow_1703123456789",
  "status": "running",
  "progress": "📋 Stage 3: Fact Checking...",
  "started_at": "2024-01-01T12:00:00",
  "completed_at": null,
  "session_id": "research-session-1"
}
```

### DELETE `/{workflow_id}`
Cancel or remove workflow.

**Response:**
```json
{
  "message": "Workflow workflow_1703123456789 removed",
  "status": "success"
}
```

### GET `/templates`
Get pre-configured workflow templates.

**Response:**
```json
{
  "research_templates": {
    "fatwa_quick": {
      "research_type": "quick",
      "output_format": "summary",
      "include_scientific": false,
      "max_sources": 5,
      "description": "Quick fatwa-style research"
    },
    "academic_comprehensive": {
      "research_type": "comprehensive", 
      "output_format": "article",
      "include_scientific": true,
      "include_web_sources": true,
      "max_sources": 15,
      "description": "Comprehensive academic research"
    }
  },
  "publication_templates": {
    "academic_paper": {
      "publication_type": "academic_paper",
      "citation_style": "chicago",
      "peer_review_rounds": 2,
      "word_count_target": 8000,
      "description": "Standard academic paper"
    }
  }
}
```

### GET `/health`
Workflow service health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "workflow_service",
  "active_workflows": 3,
  "workflow_types": ["research", "publication"],
  "features": [
    "multi_source_search",
    "fact_checking", 
    "streaming_responses",
    "session_persistence",
    "caching"
  ]
}
```

## 🛠️ Configuration Options

### Research Workflow Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `research_query` | string | **required** | Main research query (Arabic/English) |
| `research_type` | string | `"comprehensive"` | `quick`, `comprehensive`, `academic` |
| `output_format` | string | `"article"` | `article`, `summary`, `academic_paper` |
| `include_scientific` | boolean | `true` | Include ArXiv/PubMed scientific literature |
| `include_web_sources` | boolean | `true` | Include Tavily web search results |
| `max_sources` | integer | `10` | Maximum sources to gather (1-20) |
| `use_cache` | boolean | `true` | Enable session-based caching |
| `session_id` | string | `null` | Custom session ID for state management |

### Publication Workflow Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `publication_topic` | string | **required** | Academic publication topic |
| `publication_type` | string | `"academic_paper"` | `academic_paper`, `book_chapter`, `monograph` |
| `target_audience` | string | `"academic"` | `academic`, `general`, `specialized` |
| `citation_style` | string | `"chicago"` | `chicago`, `apa`, `mla`, `islamic_traditional` |
| `peer_review_rounds` | integer | `2` | Number of peer review simulation rounds (1-5) |
| `word_count_target` | integer | `null` | Target word count (optional) |
| `use_cache` | boolean | `true` | Enable session-based caching |
| `session_id` | string | `null` | Custom session ID for state management |

## 📊 Usage Examples

### Python with `httpx`
```python
import httpx
import asyncio

async def research_example():
    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "research_query": "حكم التجارة الإلكترونية",
            "research_type": "comprehensive",
            "include_scientific": True,
            "include_web_sources": True
        }
        
        response = await client.post(
            "http://localhost:8000/workflows/research/run",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Research completed: {result['workflow_id']}")
            print(result['result'])

asyncio.run(research_example())
```

### JavaScript with `fetch`
```javascript
async function runResearchWorkflow() {
    const payload = {
        research_query: "الذكاء الاصطناعي في الإسلام",
        research_type: "academic",
        output_format: "article",
        include_scientific: true
    };
    
    const response = await fetch('http://localhost:8000/workflows/research/run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    console.log('Research Result:', result);
}
```

### Streaming with JavaScript
```javascript
async function streamingResearch() {
    const payload = {
        research_query: "مقاصد الشريعة",
        research_type: "comprehensive"
    };
    
    const response = await fetch('http://localhost:8000/workflows/research/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                
                if (data.event === 'workflow_progress') {
                    console.log('Progress:', data.content);
                } else if (data.event === 'workflow_completed') {
                    console.log('Completed!', data.content);
                    return;
                }
            }
        }
    }
}
```

### cURL Examples
```bash
# Quick research
curl -X POST "http://localhost:8000/workflows/research/quick" \
  -H "Content-Type: application/json" \
  -d '{"query": "أحكام الصيام"}'

# Comprehensive research  
curl -X POST "http://localhost:8000/workflows/research/run" \
  -H "Content-Type: application/json" \
  -d '{
    "research_query": "الذكاء الاصطناعي في التعليم الإسلامي",
    "research_type": "comprehensive",
    "include_scientific": true,
    "max_sources": 15
  }'

# Publication workflow
curl -X POST "http://localhost:8000/workflows/publication/run" \
  -H "Content-Type: application/json" \
  -d '{
    "publication_topic": "AI Ethics in Islamic Perspective", 
    "publication_type": "academic_paper",
    "citation_style": "chicago",
    "peer_review_rounds": 2
  }'

# Check workflow status
curl "http://localhost:8000/workflows/workflow_1703123456789"

# List all workflows
curl "http://localhost:8000/workflows/"
```

## ⚡ Performance & Caching

### Caching Strategy
- **Session-based caching** persists across requests with same `session_id`
- **Intermediate result caching** for research stages
- **Complete workflow caching** for identical queries

### Performance Tips
```python
# Use consistent session_ids for related research
session_id = "ai-research-project-2024"

# Enable caching for repeated queries
use_cache = True

# Adjust source limits for faster processing
max_sources = 5  # Quick research
max_sources = 15 # Comprehensive research

# Use appropriate research types
research_type = "quick"        # ~30-60 seconds
research_type = "comprehensive" # ~2-5 minutes  
research_type = "academic"     # ~5-10 minutes
```

### Parallel Execution
```python
import asyncio
import httpx

async def parallel_research():
    topics = [
        "حكم التجارة الإلكترونية",
        "ضوابط الاستثمار في العملات الرقمية", 
        "فقه النوازل في الطب الحديث"
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        tasks = []
        for topic in topics:
            payload = {"research_query": topic, "research_type": "quick"}
            task = client.post("http://localhost:8000/workflows/research/run", json=payload)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        for topic, response in zip(topics, responses):
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {topic}: {result['workflow_id']}")
```

## 🛡️ Error Handling

### Common HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Workflow not found
- `422` - Validation Error (missing required fields)
- `500` - Internal Server Error (workflow execution failed)

### Error Response Format
```json
{
  "detail": "Workflow failed: Error message describing the issue"
}
```

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "research_query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Best Practices
```python
import httpx

async def robust_workflow_call():
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8000/workflows/research/run",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 422:
                print("Validation error:", response.json()["detail"])
            else:
                print(f"Error {response.status_code}: {response.text}")
                
    except httpx.TimeoutException:
        print("Request timed out - try reducing max_sources or use quick research_type")
    except httpx.RequestError as e:
        print(f"Request failed: {e}")
```

## 🔗 Integration Examples

### Frontend Integration
```javascript
// React component example
import React, { useState } from 'react';

function ResearchComponent() {
    const [query, setQuery] = useState('');
    const [result, setResult] = useState('');
    const [loading, setLoading] = useState(false);
    
    const runResearch = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/workflows/research/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    research_query: query,
                    research_type: 'quick'
                })
            });
            
            const data = await response.json();
            setResult(data.result);
        } catch (error) {
            console.error('Research failed:', error);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div>
            <input 
                value={query} 
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter research query..."
            />
            <button onClick={runResearch} disabled={loading}>
                {loading ? 'Researching...' : 'Start Research'}
            </button>
            {result && <div dangerouslySetInnerHTML={{__html: result}} />}
        </div>
    );
}
```

### Backend Integration
```python
# FastAPI endpoint that uses workflows
from fastapi import FastAPI
import httpx

app = FastAPI()

@app.post("/api/research")
async def research_endpoint(query: str, type: str = "quick"):
    async with httpx.AsyncClient() as client:
        workflow_payload = {
            "research_query": query,
            "research_type": type,
            "include_scientific": type != "quick"
        }
        
        response = await client.post(
            "http://localhost:8000/workflows/research/run",
            json=workflow_payload
        )
        
        return response.json()
```

## 📈 Monitoring & Analytics

### Workflow Tracking
```python
# Track workflow performance
import time

start_time = time.time()
response = await client.post("/workflows/research/run", json=payload)
end_time = time.time()

print(f"Workflow completed in {end_time - start_time:.2f} seconds")

if response.status_code == 200:
    result = response.json()
    print(f"Sources used: {len(result.get('progress_log', []))}")
    print(f"Result length: {len(result['result'])} characters")
```

### Health Monitoring
```python
async def monitor_workflow_health():
    async with httpx.AsyncClient() as client:
        health = await client.get("http://localhost:8000/workflows/health")
        
        if health.status_code == 200:
            data = health.json()
            print(f"Service status: {data['status']}")
            print(f"Active workflows: {data['active_workflows']}")
        else:
            print("Workflow service unhealthy!")
```

---

## 🎯 Summary

The Turath AI Workflow API provides:

- **🔍 Research Workflows** - Multi-source Islamic research automation
- **📖 Publication Workflows** - Academic paper generation with peer review
- **🌊 Streaming Support** - Real-time progress monitoring
- **💾 Smart Caching** - Performance optimization through session management
- **⚡ Parallel Processing** - Concurrent workflow execution
- **🛡️ Robust Error Handling** - Comprehensive validation and error management

**Perfect for building production Islamic research applications with enterprise-grade reliability!** 🚀📚🕌

**Explore the complete API documentation at:** `/docs` (Swagger UI) 
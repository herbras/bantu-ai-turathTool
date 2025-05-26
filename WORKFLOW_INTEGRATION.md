# Turath AI Workflow Integration

Sistem Turath AI sekarang mendukung **Agno Workflows** - orchestration platform yang powerful untuk koordinasi multi-agent research dengan state management dan caching.

## 🔄 Migration dari Agents ke Workflows

### Before: Single Agent Approach
```python
# Old way - single agent
query_agent = TurathQueryAgent()
response = query_agent.run("حكم التجارة الإلكترونية")
```

### After: Workflow Orchestration
```python
# New way - comprehensive workflow
workflow = TurathResearchWorkflow(session_id="research-ecommerce")
response = workflow.run(
    research_query="حكم التجارة الإلكترونية",
    research_type="comprehensive",
    include_scientific=True,
    include_web_sources=True
)
```

## 📊 Available Workflows

### 1. TurathResearchWorkflow
**Purpose:** Comprehensive Islamic research dengan multi-source integration

**Capabilities:**
- ✅ Multi-source search (Internal DB + Web + Scientific)
- ✅ Progressive research stages dengan caching
- ✅ Fact-checking dan cross-validation
- ✅ Collaborative writing dengan teams
- ✅ Session state management

**Stages:**
1. **Research Planning** - Query enhancement & strategy
2. **Information Gathering** - Parallel multi-source search
3. **Fact Checking** - Cross-validation & reliability scoring
4. **Content Writing** - Structured content generation
5. **Editorial Review** - Team-based finalization

### 2. TurathPublicationWorkflow
**Purpose:** Academic publication dengan peer review simulation

**Capabilities:**
- ✅ Literature review & methodology development
- ✅ Comprehensive source analysis & categorization
- ✅ Academic writing dengan proper citations
- ✅ Multi-round peer review simulation
- ✅ Publication-ready formatting

**Stages:**
1. **Literature Review** - Comprehensive source gathering
2. **Research Methodology** - Framework development
3. **Source Analysis** - Primary/secondary classification
4. **Academic Writing** - Draft dengan citations
5. **Peer Review** - Simulation & revision cycles
6. **Final Formatting** - Publication-ready output

## 🚀 Key Advantages

### 1. **State Management & Caching**
```python
# Automatic caching of intermediate results
workflow = TurathResearchWorkflow(
    session_id="research-session-1",
    storage=SqliteWorkflowStorage(db_file="workflows.db")
)

# First run - full processing
response1 = workflow.run("query", use_cache=True)

# Second run - instant cache retrieval  
response2 = workflow.run("query", use_cache=True)  # ⚡ Instant!
```

### 2. **Progressive Research**
```python
# Monitor real-time progress
for response in workflow.run("research_query"):
    if response.event == RunEvent.workflow_progress:
        print(f"Stage: {response.content}")
    elif response.event == RunEvent.workflow_completed:
        print("Research completed!")
```

### 3. **Parallel Processing**
```python
# Multiple searches simultaneously
gathered_sources = yield from self._gather_information_parallel(
    ["query1", "query2", "query3"],
    include_scientific=True,
    include_web_sources=True
)
```

### 4. **Flexible Configuration**
```python
# Quick research untuk fatwa
workflow.run(
    research_query="حكم زكاة الذهب",
    research_type="quick",
    output_format="summary",
    include_scientific=False
)

# Comprehensive academic research
workflow.run(
    research_query="AI dalam perbankan syariah",
    research_type="comprehensive",
    output_format="article", 
    include_scientific=True,
    include_web_sources=True
)
```

## 🔧 Setup & Configuration

### 1. Install Agno
```bash
pip install agno openai
```

### 2. Basic Workflow Setup
```python
from agno.storage.workflow.sqlite import SqliteWorkflowStorage
from src.workflows import TurathResearchWorkflow

# Initialize dengan persistent storage
workflow = TurathResearchWorkflow(
    session_id="my-research-session",
    storage=SqliteWorkflowStorage(
        table_name="turath_workflows",
        db_file="workflows.db"
    )
)
```

### 3. Environment Variables
```bash
# Required for full functionality
export OPENAI_API_KEY="your-openai-key"
export TAVILY_API_KEY="your-tavily-key"  # Optional for web search
```

## 📚 Usage Examples

### Quick Fatwa Research
```python
workflow = TurathResearchWorkflow(session_id="fatwa-research")

response = workflow.run(
    research_query="حكم صلاة الجمعة للمسافر",
    research_type="quick",
    output_format="summary",
    max_sources=5
)
```

### Comprehensive Academic Research
```python
workflow = TurathResearchWorkflow(session_id="academic-research")

response = workflow.run(
    research_query="تطبيق الذكاء الاصطناعي في الفقه الإسلامي",
    research_type="comprehensive",
    output_format="article",
    include_scientific=True,
    include_web_sources=True,
    max_sources=15
)
```

### Academic Paper Writing
```python
workflow = TurathPublicationWorkflow(session_id="paper-writing")

response = workflow.run(
    publication_topic="مقاصد الشريعة في النوازل المعاصرة",
    publication_type="academic_paper",
    citation_style="chicago",
    peer_review_rounds=2,
    word_count_target=8000
)
```

### Parallel Research
```python
async def parallel_research():
    topics = [
        "حكم التجارة الإلكترونية",
        "ضوابط الاستثمار في العملات الرقمية",
        "فقه النوازل في الطب الحديث"
    ]
    
    workflows = [
        TurathResearchWorkflow(session_id=f"research-{i}")
        for i in range(len(topics))
    ]
    
    results = await asyncio.gather(*[
        workflow.run(topic, research_type="quick")
        for workflow, topic in zip(workflows, topics)
    ])
    
    return results
```

## 🔍 Integration dengan Existing Components

### Agent Integration
```python
class TurathResearchWorkflow(Workflow):
    # Menggunakan agents yang sudah ada
    query_agent: TurathQueryAgent = TurathQueryAgent()
    fact_checker: FactCheckerAgent = FactCheckerAgent()
    writer: TurathWriterAgent = TurathWriterAgent()
    
    # Teams collaboration
    research_team: TurathResearchTeam = TurathResearchTeam()
    editor_team: TurathEditorTeam = TurathEditorTeam()
```

### Multi-Source Search Integration
```python
# Internal database + Web + Scientific literature
def _gather_information_parallel(self, queries, include_scientific, include_web):
    for query in queries:
        # Internal DB via MCP
        db_response = self.query_agent.run(query)
        
        # Web search via Tavily  
        if include_web:
            web_response = self.query_agent.run(f"web_search: {query}")
        
        # Scientific literature via ArXiv/PubMed
        if include_scientific:
            sci_response = self.query_agent.run(f"scientific_search: {query}")
```

## 📊 Performance Benefits

### Caching Results
- **First run:** ~15-30 seconds (full processing)
- **Cached run:** ~1-2 seconds (instant retrieval)
- **Partial cache:** ~5-10 seconds (partial processing)

### Parallel Processing
- **Sequential:** 5 queries × 6 seconds = 30 seconds
- **Parallel:** 5 queries in ~8 seconds total

### State Management
- **Session persistence:** Resume interrupted research
- **Incremental updates:** Add sources without re-processing
- **Cross-session sharing:** Reuse research across sessions

## 🔄 Migration Strategy

### Phase 1: Dual Mode (Current)
```python
# Keep existing agents working
query_agent = TurathQueryAgent()
response = query_agent.run("query")

# Add workflows for complex research
workflow = TurathResearchWorkflow()
comprehensive_response = workflow.run("query", research_type="comprehensive")
```

### Phase 2: Workflow-First (Recommended)
```python
# Use workflows as primary interface
workflow = TurathResearchWorkflow()

# Quick queries (replaces simple agent calls)
quick_response = workflow.run("query", research_type="quick")

# Complex research (enhanced capability)
comprehensive_response = workflow.run("query", research_type="comprehensive")
```

### Phase 3: Full Integration
```python
# Unified interface for all research types
research_service = TurathResearchService()

# Automatically chooses appropriate workflow
response = research_service.research(
    query="query",
    complexity="auto",  # auto-detects complexity
    output_format="auto"  # auto-detects required format
)
```

## 🧪 Testing & Examples

### Run Examples
```bash
# Run specific example
python examples/workflow_examples.py 1  # Quick research

# Run all examples
python examples/workflow_examples.py
```

### Available Examples
1. **Quick Research** - Fatwa-style quick answers
2. **Comprehensive Research** - Multi-source academic research
3. **Academic Publication** - Paper writing dengan peer review
4. **Book Chapter** - Long-form content creation
5. **Parallel Workflows** - Multiple research streams
6. **Caching Demo** - Performance optimization
7. **Custom Configuration** - Advanced setup
8. **Progress Monitoring** - Real-time workflow tracking

## 📈 Roadmap

### Immediate (Current)
- ✅ Core workflow implementation
- ✅ Multi-source integration
- ✅ State management & caching
- ✅ Comprehensive examples

### Short Term (Next Month)
- 🔄 Advanced parallel processing
- 🔄 Enhanced semantic search
- 🔄 Custom citation styles
- 🔄 Export to multiple formats

### Long Term (Next Quarter)  
- 📋 Visual workflow designer
- 📋 Advanced analytics & metrics
- 📋 Collaborative research features
- 📋 Integration with publishing platforms

## 💡 Best Practices

### 1. Session ID Naming
```python
# Good - descriptive and unique
session_id = "research-ai-banking-2024-01"

# Bad - generic
session_id = "session1"
```

### 2. Caching Strategy
```python
# Enable caching for repeated research
workflow.run(query, use_cache=True)

# Disable for real-time updates
workflow.run(query, use_cache=False)
```

### 3. Resource Management
```python
# Use appropriate research types
research_type = "quick"        # For simple queries
research_type = "comprehensive" # For complex research  
research_type = "academic"     # For scholarly work
```

### 4. Error Handling
```python
try:
    response = workflow.run(query)
    for result in response:
        process_result(result)
except Exception as e:
    logger.error(f"Workflow error: {e}")
    # Fallback to simple agent
    fallback_response = query_agent.run(query)
```

## 🆘 Troubleshooting

### Common Issues

**1. Workflow not starting**
```bash
# Check dependencies
pip install agno openai tavily-python

# Verify environment variables
echo $OPENAI_API_KEY
echo $TAVILY_API_KEY
```

**2. Cache not working**
```python
# Ensure storage is properly configured
storage = SqliteWorkflowStorage(
    table_name="workflows",
    db_file="workflows.db"  # Check file permissions
)
```

**3. Agents not responding**
```python
# Check agent initialization
query_agent = TurathQueryAgent()
test_response = query_agent.run("test query")
print(test_response)
```

**4. Memory issues with large workflows**
```python
# Use smaller batch sizes
workflow.run(query, max_sources=5)  # Instead of 15

# Clear session state periodically
workflow.session_state.clear()
```

---

**🎯 Workflows memberikan level of control, flexibility, dan reliability yang tidak mungkin dicapai dengan single agents. Perfect untuk production Islamic research applications!**

**📖 Source:** [Agno Workflows Documentation](https://docs.agno.com/workflows/introduction) 
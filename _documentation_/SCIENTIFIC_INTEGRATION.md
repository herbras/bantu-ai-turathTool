# Scientific Literature Integration

The Turath AI system now supports **scientific literature search** with Islamic perspective for medical and technology topics.

## Features

### Multi-Domain Search Capabilities
1. **Islamic Texts** - Internal MCP database
2. **General Web Search** - Tavily API  
3. **Scientific Literature** - ArXiv + PubMed with Islamic context

### Smart Query Detection
The agent automatically detects query types and routes to appropriate tools:

```python
# Medical queries -> PubMed + Islamic bioethics
"organ transplantation Islamic ethics" -> Medical

# Technology queries -> ArXiv + Islamic ethics  
"artificial intelligence Islamic perspective" -> Technology

# Combined queries -> Both sources
"AI in medical diagnosis Islamic bioethics" -> Both
```

## Setup

### 1. Install Dependencies
```bash
# Required for ArXiv search
uv add arxiv pypdf

# Or with pip
pip install arxiv pypdf
```

### 2. Optional: Enable All Features
```bash
# For complete functionality
export TAVILY_API_KEY="your-tavily-key"
```

### 3. Test Installation
```bash
uv run python test_scientific_tools.py
```

## Available Tools

### Scientific Search Functions

1. **`search_arxiv_with_islamic_context`**
   - Technology, AI, computer science, physics, mathematics
   - Adds Islamic ethics perspective on scientific research
   - Enhanced with ethics and philosophy keywords

2. **`search_pubmed_with_islamic_context`**
   - Medical research, healthcare, bioethics
   - Includes Islamic bioethics framework
   - Considers halal/haram, maslaha, and scholarly guidance

3. **`search_scientific_literature`**
   - Auto-detects query type (medical/technology/both)
   - Comprehensive search across relevant databases
   - Integrated Islamic perspective notes

## Islamic Context Integration

### For Medical Topics
- **Islamic Bioethics Principles**: Sanctity of life, prohibition of harm
- **Scholarly Consultation**: Recommendation for complex issues
- **Necessity Principle**: Emergency medical situations
- **Halal/Haram Considerations**: Substances and procedures

### For Technology Topics  
- **Knowledge as Trust**: Humans as stewards of technology
- **Ethical Responsibility**: Benefit vs harm analysis
- **Tawhid Perspective**: All knowledge points to Creator
- **Social Impact**: Community benefit considerations

## Query Examples

### Medical Queries
```
"What does Islam say about organ transplantation?"
"Islamic perspective on genetic engineering"
"Bioethics of stem cell research in Islamic jurisprudence"
```

### Technology Queries
```
"Islamic ethics on artificial intelligence"
"Machine learning algorithms for Quran analysis"
"Automation and employment in Islamic economics"
```

### Combined Queries
```
"AI in medical diagnosis from Islamic bioethics perspective"
"Technology ethics in healthcare according to Islamic principles"
```

## Response Structure

### Multi-Source Results
```markdown
## Islamic Database Results
[Traditional Islamic texts and rulings]

## Scientific Literature  
### Islamic Bioethics Perspective
[Relevant Islamic principles and guidance]

### ArXiv/PubMed Results
[Scientific papers with Islamic context notes]

## Additional Web References
[Contemporary scholarly opinions and discussions]
```

## Configuration

### Agent Factory Settings
```python
# Enable/disable scientific search
enable_scientific_search: bool = True

# Email for PubMed (recommended)
email = "research@your-domain.com"

# Max results per source
max_results = 5
```

### Auto-Detection Keywords

**Medical Keywords:**
- medical, health, disease, treatment, therapy
- bioethics, pharmaceutical, genetics, surgery
- healthcare, hospital, diagnosis, medication

**Technology Keywords:**  
- technology, ai, artificial intelligence, computer
- machine learning, physics, mathematics, engineering
- robotics, automation, digital, software

## Benefits

1. **Comprehensive Coverage**: Traditional Islamic texts + modern scientific research
2. **Islamic Perspective**: Every scientific result includes relevant Islamic context
3. **Scholarly Guidance**: Recommendations for consulting Islamic scholars
4. **Ethical Framework**: Islamic principles applied to modern challenges
5. **Quality Sources**: Peer-reviewed papers with Islamic perspective
6. **Auto-Detection**: Smart routing to appropriate knowledge sources

## Dependencies

```txt
# Core scientific tools
arxiv>=2.1.0
pypdf>=3.0.0

# Optional for enhanced web search  
tavily-python>=0.3.0
```

## Testing

### Query Type Detection Test
```bash
# Test automatic query categorization
uv run python test_scientific_tools.py
```

### Full Integration Test
```bash
# Test all tools together
uv run python test_combined_search.py
```

## Integration Status

- ✅ **ArXiv Integration** - Scientific papers with Islamic ethics context
- ✅ **PubMed Integration** - Medical research with Islamic bioethics  
- ✅ **Auto Query Detection** - Smart routing based on content
- ✅ **Islamic Context** - Relevant perspectives for all scientific topics
- ✅ **Multi-Source Results** - Combined traditional and modern sources
- ✅ **Agent Integration** - Seamless incorporation in TurathQueryAgent

**Ready for comprehensive Islamic scholarly research with modern scientific literature! 📚🔬🕌** 
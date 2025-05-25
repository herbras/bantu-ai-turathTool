# Tavily Web Search Integration

Sistem ini sekarang mendukung pencarian web menggunakan Tavily API sebagai pelengkap database Islamic texts internal.

## Setup

### 1. Install Dependencies
```bash
uv add tavily-python
# atau
pip install tavily-python
```

### 2. Get Tavily API Key
1. Daftar di [Tavily.com](https://tavily.com)
2. Dapatkan API key gratis
3. Set environment variable:

```bash
export TAVILY_API_KEY="your-tavily-api-key"
```

### 3. Test Installation
```bash
uv run python test_combined_search.py
```

## Features

### Dual Search Capability
- **Internal Database**: MCP tools untuk database Islamic texts (Turath)
- **Web Search**: Tavily tools untuk referensi web tambahan

### Enhanced Islamic Search
- Automatically enhances queries dengan kata kunci Islamic
- **Granular Source Detection**: 9 categories dengan 30+ Islamic websites
- **Dorar.net Specialization**: Detects specific encyclopedias (Tafsir, Hadith, Fiqh, dll.)
- Structured output dengan clear separation antara internal dan web results

### Tool Functions Available
1. **search_islamic_content_web**: General Islamic web search
2. **search_islamic_references_web**: Contextual search dengan summarization

## Usage Examples

### Query
```
"Cari buku tentang kaidah fiqh Syafi'i dan rujukan web tentang topik ini"
```

### Expected Response Structure
```
## Internal Database Results
1. Judul: [dari MCP database]
   Sumber: [reference_info dari database]

## Additional Web References  
1. [Academic Paper] Title from web
   Source Type: Academic Paper
   Content: [excerpt]
```

## Configuration

Di `src/config/settings.py`:
```python
self.tavily_api_key: str = os.getenv("TAVILY_API_KEY", None)
```

Jika TAVILY_API_KEY tidak di-set, sistem akan berjalan dengan MCP tools saja (graceful degradation).

## Enhanced Source Detection

### Supported Categories:
1. **Fatwa/Q&A Sites** - IslamQA, Binbaz, MUI, RumahFiqih, dll.
2. **Hadith Collections** - Sunnah.com, Bukhari, Muslim collections
3. **Dorar.net Encyclopedias**:
   - Tafsir Encyclopedia (`/tafseer`)
   - Hadith Encyclopedia (`/hadith`) 
   - Aqidah Encyclopedia (`/aqeeda`)
   - Fiqh Encyclopedia (`/feqhia`)
   - Usul Fiqh Encyclopedia (`/osolfeqh`)
   - Qawaid Fiqhiyya Encyclopedia (`/qfiqhia`)
   - Weak & Fabricated Hadiths (`/fake-hadith`)
   - And 8 more specialized sections
4. **Quranic Resources** - Quran.com, Corpus, Tanzil
5. **Islamic Digital Libraries** - Shamela, Waqfeya, IslamHouse
6. **Islamic Multimedia** - Yufid, IslamWay, Audio/Video platforms
7. **Islamic Portals** - Rumaysho, Muslim.or.id, Alukah, dll.
8. **Academic Papers** - Academia.edu, JSTOR, DOI sources
9. **General Web Sources** - Other websites

### Test Coverage
```bash
# Run source detection tests
uv run python test_source_detection.py
```

## Benefits

1. **Comprehensive Coverage**: Combine database internal + web references
2. **Quality Sources**: Identifies Islamic websites, academic papers, fatwa sites
3. **Modern References**: Akses contemporary scholarly opinions
4. **Cross-Validation**: Compare traditional texts dengan modern interpretations
5. **Granular Classification**: 30+ Islamic websites properly categorized 
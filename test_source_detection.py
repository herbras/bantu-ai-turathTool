import os
from src.tools.tavily_service import TurathTavilyTools

def test_source_detection():
    """Test the enhanced source type detection"""
    print("Testing Enhanced Source Type Detection...")
    
    # Create TavilyTools instance (without API key for testing)
    os.environ["TAVILY_API_KEY"] = "dummy-key-for-testing"
    tavily_tools = TurathTavilyTools()
    
    # Test URLs with expected categories
    test_cases = [
        # Fatwa/Q&A Sites
        ("https://islamqa.info/en/answers/123", "Fatwa/Q&A Site"),
        ("https://binbaz.org.sa/fatawa/123", "Fatwa/Q&A Site"),
        ("https://mui.or.id/fatwa/123", "Fatwa/Q&A Site"),
        ("https://rumahfiqih.com/tanya-jawab/123", "Fatwa/Q&A Site"),
        
        # Hadith Collections
        ("https://sunnah.com/bukhari/1", "Hadith Collection"),
        ("https://hadithcollection.com/sahih-muslim", "Hadith Collection"),
        
        # Dorar.net - Granular Detection
        ("https://dorar.net/tafseer/quran/1", "Tafsir Encyclopedia"),
        ("https://dorar.net/hadith/sharh/123", "Hadith Encyclopedia"),
        ("https://dorar.net/aqeeda/topics/123", "Aqidah Encyclopedia"),
        ("https://dorar.net/feqhia/issues/456", "Fiqh Encyclopedia"),
        ("https://dorar.net/osolfeqh/rules/789", "Usul Fiqh Encyclopedia"),
        ("https://dorar.net/qfiqhia/maxims/111", "Qawaid Fiqhiyya Encyclopedia"),
        ("https://dorar.net/fake-hadith/weak/222", "Weak & Fabricated Hadiths"),
        ("https://dorar.net/random-page", "Dorar – Other Section"),
        
        # Quranic Resources
        ("https://quran.com/2/255", "Quranic Resource"),
        ("https://corpus.quran.com/wordbyword.jsp", "Quranic Resource"),
        
        # Islamic Digital Libraries
        ("https://shamela.ws/book/12345", "Islamic Digital Library"),
        ("https://waqfeya.net/book.php?bid=1234", "Islamic Digital Library"),
        ("https://islamhouse.com/books/arabic/123", "Islamic Digital Library"),
        
        # Islamic Multimedia
        ("https://yufid.com/video/123", "Islamic Multimedia"),
        ("https://islamway.net/audio/123", "Islamic Multimedia"),
        ("https://ar.islamway.net/lesson/12345", "Islamic Multimedia"),
        
        # Islamic Portals
        ("https://rumaysho.com/article/123", "Islamic Portal"),
        ("https://muslim.or.id/akidah/123", "Islamic Portal"),
        ("https://mawdoo3.com/topic/123", "Islamic Portal"),
        ("https://alukah.net/sharia/456", "Islamic Portal"),
        
        # Academic Papers
        ("https://academia.edu/123456/islamic-studies", "Academic Paper"),
        ("https://jstor.org/stable/123456", "Academic Paper"),
        
        # General Web Sources
        ("https://example.com/islamic-content", "General Web Source"),
        ("https://randomsite.org/islam", "General Web Source"),
    ]
    
    print(f"\nTesting {len(test_cases)} URL classifications...\n")
    
    passed = 0
    failed = 0
    
    for url, expected in test_cases:
        actual = tavily_tools._identify_source_type(url)
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        
        if actual == expected:
            passed += 1
        else:
            failed += 1
            
        print(f"{status} {url}")
        print(f"    Expected: {expected}")
        print(f"    Actual:   {actual}")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Source detection working perfectly.")
    else:
        print(f"⚠️ {failed} tests failed. Check implementation.")

if __name__ == "__main__":
    test_source_detection() 
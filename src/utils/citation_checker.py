import re
from typing import List, Dict, Any

class CitationChecker:
    """
    Validates that claims made in the text have accurate citations from the provided excerpts.
    This is a simpler programmatic fallback to catching hallucinated citations.
    """
    
    @staticmethod
    def extract_citations(text: str) -> List[str]:
        """
        Extracts citations from text in the format [DocTitle, Section]
        """
        # Matches patterns like [General Return Policy, Section 1.2] or [Policy Name]
        pattern = r'\\[([^\\]]+)\\]'
        return re.findall(pattern, text)
        
    @staticmethod
    def verify_citations(text: str, retrieved_excerpts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verifies that the citations mentioned in the text actually exist in the retrieved excerpts.
        Returns a result dict with pass/fail and details.
        """
        citations_in_text = CitationChecker.extract_citations(text)
        
        if not citations_in_text:
            return {
                "passed": False,
                "reason": "No citations found in the text. All claims must be cited.",
                "missing_citations": []
            }
            
        valid_sources = []
        for excerpt in retrieved_excerpts:
            doc_title = excerpt.get("doc_title", "")
            section = excerpt.get("section", "")
            valid_sources.append(doc_title.lower())
            if section:
                valid_sources.append(f"{doc_title.lower()}, {section.lower()}")
                
        invalid_citations = []
        for cite in citations_in_text:
            cite_lower = cite.lower()
            # Loose matching: check if the citation text matches any valid source document or section
            is_valid = any(cite_lower in v or v in cite_lower for v in valid_sources)
            if not is_valid:
                invalid_citations.append(cite)
                
        if invalid_citations:
            return {
                "passed": False,
                "reason": f"Found unsupported citations that do not match retrieved excerpts: {invalid_citations}",
                "missing_citations": invalid_citations
            }
            
        return {
            "passed": True,
            "reason": "All citations appear to map to retrieved excerpts.",
            "missing_citations": []
        }

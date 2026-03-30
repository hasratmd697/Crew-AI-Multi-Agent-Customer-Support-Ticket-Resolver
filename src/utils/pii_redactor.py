import re

class PIIRedactor:
    """
    A simple PII redactor to ensure sensitive customer data does not leak into 
    logs or external AI models if not necessary.
    """
    
    # Basic regex patterns for sensitive data
    PATTERNS = {
        "CREDIT_CARD": r"\\b(?:\\d[ -]*?){13,16}\\b",
        "SSN": r"\\b\\d{3}-\\d{2}-\\d{4}\\b",
        "EMAIL": r"\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,7}\\b",
        "PHONE": r"\\b(?:\\+\\d{1,2}\\s)?\\(?\\d{3}\\)?[\\s.-]?\\d{3}[\\s.-]?\\d{4}\\b"
    }

    @classmethod
    def redact(cls, text: str) -> str:
        """
        Redacts PII from the given text.
        """
        if not text:
            return text
            
        redacted_text = text
        for pii_type, pattern in cls.PATTERNS.items():
            redacted_text = re.sub(pattern, f"[REDACTED_{pii_type}]", redacted_text)
            
        return redacted_text
        
    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """
        Checks if the text contains any PII.
        """
        if not text:
            return False
            
        for pattern in cls.PATTERNS.values():
            if re.search(pattern, text):
                return True
        return False

if __name__ == "__main__":
    test_text = "Customer email is john.doe@example.com and phone is 555-123-4567. Card: 4111 1111 1111 1111"
    print("Original:", test_text)
    print("Redacted:", PIIRedactor.redact(test_text))

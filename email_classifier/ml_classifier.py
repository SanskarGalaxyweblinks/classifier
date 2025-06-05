"""
Lightweight ML Classifier - Hybrid Approach
Works with Rule Engine and Pattern Matcher
Removed General (Thank You) and simplified for performance
"""

import logging
import torch
from transformers import pipeline
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)

# Simple Configuration
CONFIDENCE_THRESHOLDS = {
    'high': 0.80,
    'medium': 0.65,
    'low': 0.50
}

MAX_TEXT_LENGTH = 256  # Reduced for performance
MIN_TEXT_LENGTH = 10

class MLClassifier:
    """
    Lightweight ML Classifier for hybrid email classification.
    Simple, fast, and works with rule engine.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_model()
        self._initialize_categories()
        self.logger.info("✅ Lightweight ML Classifier initialized")

    def _initialize_model(self) -> None:
        """Initialize lightweight model."""
        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            self.logger.info("✅ BART model loaded")
        except Exception as e:
            self.logger.warning(f"BART model failed: {e}")
            self.classifier = None

    def _initialize_categories(self) -> None:
        """Initialize simplified categories for ML classification."""
        self.main_categories = {
            "Manual Review": "Complex business disputes, legal matters, closure notifications, and invoice documentation requiring human review",
            "No Reply": "System notifications, ticket updates, processing errors, and sales offers requiring no response", 
            "Invoices Request": "Requests for invoice copies or documentation",
            "Payments Claim": "Claims about payments made with or without supporting proof",
            "Auto Reply": "Automatic responses, out-of-office messages, surveys, and contact redirections"
        }

        # Simple subcategory mapping
        self.subcategory_defaults = {
            "Manual Review": "Complex Queries",
            "No Reply": "System Alerts", 
            "Invoices Request": "Request (No Info)",
            "Payments Claim": "Claims Paid (No Info)",
            "Auto Reply": "No Info/Autoreply"
        }

    def classify_email(self, text: str) -> Dict[str, Any]:
        """
        Simple ML classification for hybrid approach.
        
        Args:
            text: Email content to classify
            
        Returns:
            Basic classification result
        """
        if not text or len(text.strip()) < MIN_TEXT_LENGTH:
            return self._create_result("Manual Review", "Complex Queries", 0.3, "Empty content")

        cleaned_text = self._preprocess_text(text)
        
        # ML Classification
        main_category, confidence = self._classify_main_category(cleaned_text)
        subcategory = self._get_default_subcategory(main_category)
        
        return self._create_result(
            category=main_category,
            subcategory=subcategory,
            confidence=confidence,
            reason=f"ML: {main_category}"
        )

    def _classify_main_category(self, text: str) -> tuple[str, float]:
        """Simple main category classification."""
        
        # Quick keyword check first
        keyword_category = self._quick_keyword_check(text)
        if keyword_category:
            return keyword_category, CONFIDENCE_THRESHOLDS['medium']
        
        # Use BART if available
        if self.classifier:
            try:
                result = self.classifier(
                    text[:MAX_TEXT_LENGTH], 
                    list(self.main_categories.values()),
                    multi_label=False
                )
                
                if result['scores'][0] > 0.6:
                    best_description = result['labels'][0]
                    for category, description in self.main_categories.items():
                        if description == best_description:
                            return category, min(result['scores'][0], 0.85)
            except Exception as e:
                self.logger.debug(f"BART failed: {e}")
        
        # Fallback
        return self._fallback_classification(text)

    def _quick_keyword_check(self, text: str) -> Optional[str]:
        """Quick keyword-based classification."""
        text_lower = text.lower()
        
        # Strong dispute indicators
        if any(word in text_lower for word in [
            'dispute', 'owe nothing', 'scam', 'fdcpa', 'cease and desist'
        ]):
            return "Manual Review"
        
        # Payment proof indicators
        if any(phrase in text_lower for phrase in [
            'proof of payment', 'payment confirmation', 'check number', 'transaction id'
        ]):
            return "Payments Claim"
        
        # Invoice request indicators
        if any(phrase in text_lower for phrase in [
            'send me the invoice', 'need invoice copy', 'provide invoice'
        ]):
            return "Invoices Request"
        
        # Auto-reply indicators
        if any(phrase in text_lower for phrase in [
            'out of office', 'automatic reply', 'survey', 'feedback'
        ]):
            return "Auto Reply"
        
        # System/processing indicators
        if any(phrase in text_lower for phrase in [
            'ticket created', 'case opened', 'processing error', 'system notification'
        ]):
            return "No Reply"
        
        return None

    def _fallback_classification(self, text: str) -> tuple[str, float]:
        """Simple fallback based on basic business terms."""
        text_lower = text.lower()
        
        # Business terms count
        business_terms = ['payment', 'invoice', 'dispute', 'collection', 'debt']
        business_count = sum(1 for term in business_terms if term in text_lower)
        
        if business_count >= 2:
            return "Manual Review", CONFIDENCE_THRESHOLDS['low']
        elif 'payment' in text_lower:
            return "Payments Claim", CONFIDENCE_THRESHOLDS['low']
        elif 'invoice' in text_lower:
            return "Invoices Request", CONFIDENCE_THRESHOLDS['low']
        else:
            return "Manual Review", 0.4

    def _get_default_subcategory(self, main_category: str) -> str:
        """Get default subcategory for main category."""
        return self.subcategory_defaults.get(main_category, "Complex Queries")

    def _preprocess_text(self, text: str) -> str:
        """Simple text preprocessing."""
        if not isinstance(text, str):
            return ""
        
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\w\s@.-]', ' ', text)
        
        # Limit length
        words = text.split()
        if len(words) > MAX_TEXT_LENGTH:
            text = ' '.join(words[:MAX_TEXT_LENGTH])
        
        return text.lower()

    def _create_result(self, category: str, subcategory: str, confidence: float, reason: str) -> Dict[str, Any]:
        """Create simple classification result."""
        return {
            'category': category,
            'subcategory': subcategory,
            'confidence': round(confidence, 3),
            'method_used': 'ml_classification',
            'reason': reason
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get basic model information."""
        return {
            'model_available': self.classifier is not None,
            'main_categories': len(self.main_categories),
            'confidence_thresholds': CONFIDENCE_THRESHOLDS,
            'max_text_length': MAX_TEXT_LENGTH
        }
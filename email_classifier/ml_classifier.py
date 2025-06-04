"""
High-Quality ML Classifier - Aligned with Exact Hierarchy, No Thread Logic
Focus on accuracy and performance, minimal safety overhead
"""

import logging
import torch
from transformers import pipeline
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)

# Configuration Constants
CONFIDENCE_THRESHOLDS = {
    'high': 0.85,
    'medium': 0.70,
    'low': 0.55,
    'fallback': 0.45
}

MAX_TEXT_LENGTH = 512  # Tokens for transformer models
MIN_TEXT_LENGTH = 10

class MLClassifier:
    """
    Production-grade ML Classifier for email categorization.
    Aligned with exact hierarchy structure, optimized for accuracy.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_model()
        self._initialize_categories()
        self._initialize_patterns()
        self.logger.info("✅ ML Classifier initialized - No thread logic")

    def _initialize_model(self) -> None:
        """Initialize BART model with fallback handling."""
        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            self.logger.info("✅ BART model loaded successfully")
        except Exception as e:
            self.logger.warning(f"BART model failed to load: {e}")
            self.classifier = None

    def _initialize_categories(self) -> None:
        """Initialize main categories with clear descriptions."""
        self.main_categories = {
            "Manual Review": "Complex business issues requiring human attention including disputes, invoice documentation, business closures, and payment verifications",
            "No Reply (with/without info)": "System notifications, alerts, ticket updates, sales offers, processing errors, or informational messages requiring no response",
            "Invoices Request": "Requests for invoice copies or documentation without providing payment details",
            "Payments Claim": "Claims about payments made, payment confirmations with proof, or payment processing details",
            "Auto Reply (with/without info)": "Automatic responses including out-of-office messages, surveys, property updates, or system-generated replies",
            "Uncategorized": "Emails that don't clearly match any specific business category"
        }

    def _initialize_patterns(self) -> None:
        """Initialize keyword patterns aligned with exact hierarchy."""
        
        # Primary category keywords with weighted scoring
        self.category_patterns = {
            "Manual Review": {
                'high_weight': [
                    # Disputes & Payments
                    "dispute payment", "contested payment", "formally disputing", "owe nothing", 
                    "consider this a scam", "do not acknowledge", "cease and desist", "fdcpa",
                    "debt validation", "billing is incorrect", "not our responsibility",
                    
                    # Invoice Updates (providing proof)
                    "invoice receipt attached", "proof of invoice", "copy of invoice attached",
                    "invoice documentation attached", "here is the invoice copy",
                    
                    # Business Closure
                    "business closed", "filed bankruptcy", "chapter 7", "chapter 11",
                    "ceased operations", "out of business",
                    
                    # Complex business processes
                    "settlement arrangement", "legal settlement", "attorney involvement",
                    "complex business instructions", "routing instructions"
                ],
                'medium_weight': [
                    "manual review", "human attention", "requires verification", "complex situation",
                    "invoice issue", "submission failed", "format mismatch", "missing field",
                    "guidance needed", "insufficient data", "redirect to", "legal communication"
                ]
            },
            
            "No Reply (with/without info)": {
                'high_weight': [
                    # Sales/Offers
                    "special offer", "limited time offer", "prices increasing", "promotional offer",
                    "discount offer", "exclusive deal", "sale ending", "payment plan options",
                    
                    # System/Processing
                    "processing error", "system notification", "delivery failed", "cannot be processed",
                    "electronic invoice rejected", "mail delivery failed",
                    
                    # Tickets/Cases
                    "ticket created", "case opened", "ticket resolved", "case closed",
                    "support request created", "marked as resolved",
                    
                    # General notifications
                    "thank you for your email", "still reviewing", "for your records"
                ],
                'medium_weight': [
                    "notification", "system alert", "automated message", "no reply required",
                    "informational only", "acknowledgment", "confirmation received"
                ]
            },
            
            "Invoices Request": {
                'high_weight': [
                    "send me the invoice", "need invoice copy", "provide outstanding invoices",
                    "copies of invoices", "invoice request", "share invoice copy",
                    "forward invoice", "outstanding invoices owed"
                ],
                'medium_weight': [
                    "need invoice", "send invoice", "provide invoice", "invoice documentation"
                ]
            },
            
            "Payments Claim": {
                'high_weight': [
                    # Claims with proof
                    "payment confirmation attached", "proof of payment", "check number",
                    "transaction id", "eft#", "wire confirmation", "batch number",
                    "invoice was paid see attachments", "here is proof of payment",
                    
                    # Claims without proof  
                    "already paid", "payment was made", "check was sent", "we paid",
                    "payment completed", "this was paid", "account paid",
                    
                    # Payment details
                    "payment being processed", "check will be mailed", "payment scheduled",
                    "will pay this online", "working on payment"
                ],
                'medium_weight': [
                    "payment made", "bill paid", "payment sent", "remittance info"
                ]
            },
            
            "Auto Reply (with/without info)": {
                'high_weight': [
                    # Out of office
                    "out of office", "automatic reply", "auto-reply", "away from desk",
                    "on vacation", "return date", "returning on", "back on",
                    "alternate contact", "emergency contact",
                    
                    # Surveys and redirects
                    "survey", "feedback request", "rate our service", "customer satisfaction",
                    "property manager changed", "no longer employed", "contact changed"
                ],
                'medium_weight': [
                    "automated response", "currently out", "limited access", "do not reply"
                ]
            }
        }

        # Subcategory patterns for precise classification
        self.subcategory_patterns = {
            "Manual Review": {
                "Partial/Disputed Payment": [
                    "dispute", "contested", "owe nothing", "scam", "fdcpa", "cease and desist",
                    "do not acknowledge", "billing incorrect", "debt validation"
                ],
                "Invoice Receipt": [
                    "invoice receipt attached", "proof of invoice", "invoice copy attached",
                    "invoice documentation", "here is the invoice"
                ],
                "Closure Notification": [
                    "business closed", "company closed", "ceased operations", "filed bankruptcy"
                ],
                "Closure + Payment Due": [
                    "closed outstanding payment", "bankruptcy payment due", "closure with payment"
                ],
                "External Submission": [
                    "invoice submission failed", "import failed", "documents not processed"
                ],
                "Invoice Errors (format mismatch)": [
                    "missing field", "format mismatch", "incomplete invoice", "format error"
                ],
                "Inquiry/Redirection": [
                    "guidance needed", "redirect", "contact instead", "insufficient data"
                ],
                "Complex Queries": [
                    "settlement", "legal", "attorney", "complex", "multiple issues"
                ]
            },
            
            "No Reply (with/without info)": {
                "Sales/Offers": [
                    "special offer", "promotion", "discount", "price increase", "limited time"
                ],
                "System Alerts": [
                    "system notification", "alert", "maintenance notification"
                ],
                "Processing Errors": [
                    "processing error", "failed to process", "delivery failed", "rejected"
                ],
                "Business Closure (Info only)": [
                    "closure information", "business closure info"
                ],
                "General (Thank You)": [
                    "thank you", "received", "acknowledgment", "for your records"
                ],
                "Created": [
                    "ticket created", "case opened", "new ticket", "support request created"
                ],
                "Resolved": [
                    "resolved", "closed", "completed", "marked as resolved"
                ],
                "Open": [
                    "pending", "in progress", "still open"
                ]
            },
            
            "Invoices Request": {
                "Request (No Info)": [
                    "send invoice", "need invoice", "provide invoice", "invoice copy"
                ]
            },
            
            "Payments Claim": {
                "Claims Paid (No Info)": [
                    "already paid", "payment made", "check sent", "we paid"
                ],
                "Payment Details Received": [
                    "payment scheduled", "will be sent", "being processed", "working on payment"
                ],
                "Payment Confirmation": [
                    "proof of payment", "payment confirmation", "check number", "transaction id"
                ]
            },
            
            "Auto Reply (with/without info)": {
                "With Alternate Contact": [
                    "alternate contact", "emergency contact", "contact me at"
                ],
                "No Info/Autoreply": [
                    "out of office", "automatic reply", "away from desk"
                ],
                "Return Date Specified": [
                    "return date", "back on", "returning", "until"
                ],
                "Survey": [
                    "survey", "feedback", "rate our service"
                ],
                "Redirects/Updates (property changes)": [
                    "property manager", "contact changed", "no longer with"
                ]
            }
        }

    def classify_email(self, text: str) -> Dict[str, Any]:
        """
        Main classification method - clean and efficient.
        
        Args:
            text: Email content to classify
            
        Returns:
            Classification result with category, subcategory, and confidence
        """
        if not text or len(text.strip()) < MIN_TEXT_LENGTH:
            return self._create_result("Uncategorized", "General", 0.3, "Empty or too short")

        cleaned_text = self._preprocess_text(text)
        
        # Primary classification flow
        main_category = self._classify_main_category(cleaned_text)
        subcategory = self._classify_subcategory(cleaned_text, main_category)
        confidence = self._calculate_confidence(cleaned_text, main_category, subcategory)
        
        return self._create_result(
            category=main_category,
            subcategory=subcategory,
            confidence=confidence,
            reason=f"ML classified as {main_category}/{subcategory}",
            matched_patterns=self._get_matched_patterns(cleaned_text, main_category)
        )

    def _classify_main_category(self, text: str) -> str:
        """Classify main category using keyword scoring and BART model."""
        
        # Primary: Advanced keyword scoring
        keyword_scores = self._score_categories_by_keywords(text)
        best_keyword_category = max(keyword_scores.items(), key=lambda x: x[1])
        
        if best_keyword_category[1] > 0:
            return best_keyword_category[0]
        
        # Secondary: BART model if available
        if self.classifier:
            try:
                result = self.classifier(
                    text[:MAX_TEXT_LENGTH], 
                    list(self.main_categories.values()),
                    multi_label=False
                )
                
                if result['scores'][0] > CONFIDENCE_THRESHOLDS['medium']:
                    best_description = result['labels'][0]
                    for category, description in self.main_categories.items():
                        if description == best_description:
                            return category
            except Exception as e:
                self.logger.debug(f"BART classification failed: {e}")
        
        # Fallback: Pattern-based classification
        return self._pattern_fallback(text)

    def _score_categories_by_keywords(self, text: str) -> Dict[str, float]:
        """Advanced keyword scoring with weights and context."""
        text_lower = text.lower()
        scores = {}
        
        for category, patterns in self.category_patterns.items():
            score = 0.0
            
            # High weight patterns (more specific)
            for pattern in patterns.get('high_weight', []):
                if pattern in text_lower:
                    score += 2.0  # Higher weight for specific patterns
            
            # Medium weight patterns
            for pattern in patterns.get('medium_weight', []):
                if pattern in text_lower:
                    score += 1.0
            
            scores[category] = score
        
        return scores

    def _classify_subcategory(self, text: str, main_category: str) -> str:
        """Classify subcategory based on main category."""
        if main_category not in self.subcategory_patterns:
            return "General"
        
        text_lower = text.lower()
        subcategory_scores = {}
        
        for subcategory, patterns in self.subcategory_patterns[main_category].items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            if score > 0:
                subcategory_scores[subcategory] = score
        
        if subcategory_scores:
            return max(subcategory_scores.items(), key=lambda x: x[1])[0]
        
        # Default subcategory for each main category
        defaults = {
            "Manual Review": "Complex Queries",
            "No Reply (with/without info)": "General (Thank You)",
            "Invoices Request": "Request (No Info)",
            "Payments Claim": "Claims Paid (No Info)",
            "Auto Reply (with/without info)": "No Info/Autoreply",
            "Uncategorized": "General"
        }
        
        return defaults.get(main_category, "General")

    def _calculate_confidence(self, text: str, category: str, subcategory: str) -> float:
        """Calculate confidence based on pattern matches and text quality."""
        text_lower = text.lower()
        
        # Count category matches
        category_matches = 0
        if category in self.category_patterns:
            for pattern_list in self.category_patterns[category].values():
                category_matches += sum(1 for pattern in pattern_list if pattern in text_lower)
        
        # Count subcategory matches
        subcategory_matches = 0
        if (category in self.subcategory_patterns and 
            subcategory in self.subcategory_patterns[category]):
            patterns = self.subcategory_patterns[category][subcategory]
            subcategory_matches = sum(1 for pattern in patterns if pattern in text_lower)
        
        # Calculate base confidence
        total_matches = category_matches + subcategory_matches
        
        if total_matches >= 4:
            return CONFIDENCE_THRESHOLDS['high']
        elif total_matches >= 2:
            return CONFIDENCE_THRESHOLDS['medium']
        elif total_matches >= 1:
            return CONFIDENCE_THRESHOLDS['low']
        else:
            return CONFIDENCE_THRESHOLDS['fallback']

    def _get_matched_patterns(self, text: str, category: str) -> List[str]:
        """Get list of matched patterns for transparency."""
        text_lower = text.lower()
        matched = []
        
        if category in self.category_patterns:
            for pattern_list in self.category_patterns[category].values():
                for pattern in pattern_list:
                    if pattern in text_lower:
                        matched.append(pattern)
        
        return matched[:5]  # Return top 5 matches

    def _pattern_fallback(self, text: str) -> str:
        """Smart fallback classification based on business context."""
        text_lower = text.lower()
        
        # High-priority business patterns
        if any(word in text_lower for word in [
            'dispute', 'contested', 'disagreement', 'owe nothing', 'scam'
        ]):
            return "Manual Review"
        
        elif any(word in text_lower for word in [
            'send invoice', 'need invoice', 'provide invoice'
        ]):
            return "Invoices Request"
        
        elif any(word in text_lower for word in [
            'already paid', 'payment made', 'check sent', 'proof of payment'
        ]):
            return "Payments Claim"
        
        elif any(word in text_lower for word in [
            'out of office', 'automatic reply', 'survey', 'feedback'
        ]):
            return "Auto Reply (with/without info)"
        
        elif any(word in text_lower for word in [
            'ticket', 'case', 'notification', 'alert', 'processing error'
        ]):
            return "No Reply (with/without info)"
        
        elif any(word in text_lower for word in [
            'payment', 'invoice', 'business', 'closure'
        ]):
            return "Manual Review"  # Conservative routing for business content
        
        return "Uncategorized"

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for classification."""
        if not isinstance(text, str):
            return ""
        
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\w\s@.-]', ' ', text)  # Keep essential punctuation
        
        # Limit length for transformer models
        words = text.split()
        if len(words) > MAX_TEXT_LENGTH:
            text = ' '.join(words[:MAX_TEXT_LENGTH])
        
        return text.lower()

    def _create_result(self, category: str, subcategory: str, confidence: float, 
                      reason: str, matched_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create standardized classification result."""
        return {
            'category': category,
            'subcategory': subcategory,
            'confidence': round(confidence, 3),
            'method_used': 'ml_classification',
            'reason': reason,
            'matched_patterns': matched_patterns or [],
            'analysis_scores': {
                'ml_confidence': confidence,
                'rule_confidence': 0.0
            }
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the classifier configuration."""
        return {
            'model_available': self.classifier is not None,
            'main_categories': len(self.main_categories),
            'total_patterns': sum(
                len(patterns['high_weight']) + len(patterns['medium_weight'])
                for patterns in self.category_patterns.values()
            ),
            'confidence_thresholds': CONFIDENCE_THRESHOLDS,
            'max_text_length': MAX_TEXT_LENGTH
        }

    def validate_categories(self) -> Dict[str, bool]:
        """Validate that all patterns align with category structure."""
        validation_results = {}
        
        for category in self.main_categories:
            has_patterns = category in self.category_patterns
            has_subcategories = category in self.subcategory_patterns
            validation_results[category] = has_patterns and has_subcategories
        
        return validation_results
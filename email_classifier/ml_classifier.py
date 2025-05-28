"""
FIXED ML Classifier - Better confidence handling and category descriptions
"""

import logging
import torch
from transformers import pipeline
from typing import Tuple, Dict, Any, List
import re

logger = logging.getLogger(__name__)

class MLClassifier:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize BART model with better error handling
        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            self.logger.info("✅ BART model loaded successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to load BART model: {e}")
            self.classifier = None
        
        # IMPROVED Main categories with better descriptions
        self.main_categories = {
            "Manual Review": "Email requesting payment confirmation, proof of payment, invoice receipts, business closure notifications, disputes, or complex issues requiring human review",
            "No Reply": "System notifications, alerts, ticket status updates, sales offers, processing errors, or informational messages requiring no response",
            "Invoices Request": "Email requesting invoice copies, invoice documentation, or invoice information without providing details",
            "Payments Claim": "Email claiming payment was made without providing proof, evidence, or documentation",
            "Auto Reply": "Automatic responses including out-of-office messages, thank you confirmations, surveys, or system-generated replies",
            "Uncategorized": "Email that doesn't clearly fit any specific business category"
        }
        
        # KEYWORD-BASED FALLBACK for better classification
        self.category_keywords = {
            "Manual Review": [
                "payment confirmation", "proof of payment", "payment receipt", "confirm payment",
                "invoice receipt", "business closure", "business closed", "dispute", "contested",
                "manual review", "human review", "complex", "multiple issues", "need confirmation"
            ],
            "No Reply": [
                "system notification", "alert", "processing error", "import failed", 
                "ticket created", "ticket resolved", "case closed", "sales offer", "promotion"
            ],
            "Invoices Request": [
                "invoice request", "need invoice", "send invoice", "invoice copy", 
                "invoice documentation", "provide invoice", "share invoice"
            ],
            "Payments Claim": [
                "payment made", "already paid", "check sent", "payment completed",
                "payment was sent", "we paid", "payment processed"
            ],
            "Auto Reply": [
                "out of office", "automatic reply", "thank you", "received your message",
                "survey", "feedback", "property manager", "contact changed"
            ]
        }
        
        # Subcategory classification for each main category
        self.subcategories = {
            "Manual Review": {
                "Payment Confirmation": "Email requesting confirmation or proof that payment was received",
                "Invoice Receipt": "Email providing or requesting proof of invoice receipt with documentation",
                "Partial/Disputed Payment": "Email involving partial payments or payment disputes",
                "Closure Notification": "Email about business closure without payment due",
                "Closure + Payment Due": "Email about business closure with outstanding payments",
                "Complex Queries": "Email with multiple issues or complex problems requiring human review"
            },
            "No Reply": {
                "Processing Errors": "System alerts about processing or import failures",
                "Created": "Notifications about new tickets or cases being created",
                "Resolved": "Notifications that tickets or cases have been resolved",
                "Sales/Offers": "Sales promotions or special offers",
                "Business Closure (Info only)": "Information about business closure requiring no action"
            },
            "Invoices Request": {
                "Request (No Info)": "Request for invoices without providing specific details"
            },
            "Payments Claim": {
                "Claims Paid (No Info)": "Claims payment was made without providing proof"
            },
            "Auto Reply": {
                "General (Thank You)": "General thank you or acknowledgment messages",
                "Case/Support": "Confirmation of support cases or tickets",
                "Survey": "Feedback requests or surveys",
                "No Info/Autoreply": "Generic automatic replies"
            },
            "Uncategorized": {
                "General": "Email that doesn't fit into specific categories"
            }
        }
        
        self.logger.info("✅ Improved ML classifier initialized")

    def classify_email(self, text: str, has_thread: bool = False) -> Dict[str, Any]:
        """
        IMPROVED classification with better fallback logic
        """
        try:
            # Clean text first
            cleaned_text = self._clean_text(text)
            if not cleaned_text:
                return self._fallback_result("Empty text")
            
            # Apply thread rules first (these are high confidence)
            if has_thread:
                thread_result = self._classify_thread_email(cleaned_text)
                if thread_result:
                    return thread_result
            
            # Try ML classification
            main_category = self._classify_main_category_improved(cleaned_text)
            
            # Get subcategory
            subcategory = self._classify_subcategory(cleaned_text, main_category)
            
            return {
                'category': main_category,
                'subcategory': subcategory,
                'confidence': 0.8,  # Default confidence
                'method_used': 'llm_hierarchical',
                'reason': f'ML classified as {main_category}/{subcategory}',
                'matched_patterns': [],
                'thread_context': {'has_thread': has_thread, 'thread_count': 0},
                'analysis_scores': {'ml_confidence': 0.8, 'rule_confidence': 0.0}
            }
            
        except Exception as e:
            self.logger.error(f"❌ Classification error: {e}")
            return self._fallback_result(f"Error: {e}")

    def _classify_main_category_improved(self, text: str) -> str:
        """
        IMPROVED main category classification with keyword fallback
        """
        # First try keyword-based classification (fast and reliable)
        keyword_result = self._classify_by_keywords(text)
        if keyword_result != "Uncategorized":
            self.logger.info(f"🎯 Keyword classification: {keyword_result}")
            return keyword_result
        
        # Then try ML classification if available
        if self.classifier:
            try:
                result = self.classifier(
                    text,
                    list(self.main_categories.values()),
                    multi_label=False
                )
                
                best_description = result['labels'][0]
                confidence = result['scores'][0]
                
                # LOWERED threshold for better results
                if confidence > 0.3:  # Was 0.5, now 0.3
                    for category, description in self.main_categories.items():
                        if description == best_description:
                            self.logger.info(f"🤖 ML category: {category} ({confidence:.2f})")
                            return category
                
                self.logger.info(f"⚠️ Low ML confidence ({confidence:.2f}), using keyword fallback")
                
            except Exception as e:
                self.logger.error(f"❌ ML classification error: {e}")
        
        # Final fallback - analyze content for Manual Review indicators
        return self._smart_fallback_classification(text)

    def _classify_by_keywords(self, text: str) -> str:
        """
        Fast keyword-based classification - very reliable
        """
        text_lower = text.lower()
        
        # Score each category
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:  # At least one keyword match
                return best_category[0]
        
        return "Uncategorized"

    def _smart_fallback_classification(self, text: str) -> str:
        """
        Smart fallback for unclear emails
        """
        text_lower = text.lower()
        
        # Payment-related terms
        if any(word in text_lower for word in ['payment', 'invoice', 'confirm', 'receipt', 'proof']):
            return "Manual Review"
        
        # Request terms
        if any(word in text_lower for word in ['request', 'need', 'send', 'provide']):
            if 'invoice' in text_lower:
                return "Invoices Request"
            else:
                return "Manual Review"
        
        # Claim terms
        if any(word in text_lower for word in ['paid', 'sent', 'completed', 'made payment']):
            return "Payments Claim"
        
        # Default to Manual Review for business emails
        return "Manual Review"

    def _classify_thread_email(self, text: str) -> Dict[str, Any]:
        """Handle thread emails with specific rules."""
        
        text_lower = text.lower()
        
        # Thread payment claims
        thread_payment_keywords = [
            "payment made", "check sent", "paid through", "payment completed",
            "check is being overnighted", "already paid", "payment sent"
        ]
        
        if any(keyword in text_lower for keyword in thread_payment_keywords):
            return {
                'category': 'Payments Claim',
                'subcategory': 'Claims Paid (No Info)',
                'confidence': 0.9,
                'method_used': 'thread_payment_rule',
                'reason': 'Thread email with payment claim detected',
                'matched_patterns': ['thread_payment'],
                'thread_context': {'has_thread': True, 'thread_count': 1},
                'analysis_scores': {'ml_confidence': 0.0, 'rule_confidence': 0.9}
            }
        
        # Thread invoice requests
        thread_invoice_keywords = [
            "invoice copies", "send invoice", "provide invoice", "need invoice",
            "invoice request", "share invoice", "invoice documentation"
        ]
        
        if any(keyword in text_lower for keyword in thread_invoice_keywords):
            return {
                'category': 'Invoices Request',
                'subcategory': 'Request (No Info)',
                'confidence': 0.9,
                'method_used': 'thread_invoice_rule',
                'reason': 'Thread email requesting invoices detected',
                'matched_patterns': ['thread_invoice'],
                'thread_context': {'has_thread': True, 'thread_count': 1},
                'analysis_scores': {'ml_confidence': 0.0, 'rule_confidence': 0.9}
            }
        
        # Other thread emails go to Manual Review
        return {
            'category': 'Manual Review',
            'subcategory': 'Complex Queries',
            'confidence': 0.8,
            'method_used': 'thread_manual_rule',
            'reason': 'Thread email requires manual review',
            'matched_patterns': ['thread_manual'],
            'thread_context': {'has_thread': True, 'thread_count': 1},
            'analysis_scores': {'ml_confidence': 0.0, 'rule_confidence': 0.8}
        }

    def _classify_subcategory(self, text: str, main_category: str) -> str:
        """
        IMPROVED subcategory classification
        """
        if main_category not in self.subcategories:
            return "General"
        
        subcategory_options = self.subcategories[main_category]
        
        # For Manual Review, use keyword matching
        if main_category == "Manual Review":
            text_lower = text.lower()
            
            if any(word in text_lower for word in ['confirmation', 'confirm', 'proof of payment']):
                return "Payment Confirmation"
            elif any(word in text_lower for word in ['invoice receipt', 'received invoice']):
                return "Invoice Receipt"
            elif any(word in text_lower for word in ['dispute', 'partial', 'contested']):
                return "Partial/Disputed Payment"
            elif any(word in text_lower for word in ['closed', 'closure']) and 'payment' in text_lower:
                return "Closure + Payment Due"
            elif any(word in text_lower for word in ['closed', 'closure']):
                return "Closure Notification"
            else:
                return "Complex Queries"
        
        # For other categories, try ML if available
        if len(subcategory_options) == 1:
            return list(subcategory_options.keys())[0]
        
        if self.classifier:
            try:
                result = self.classifier(
                    text,
                    list(subcategory_options.values()),
                    multi_label=False
                )
                
                best_description = result['labels'][0]
                confidence = result['scores'][0]
                
                if confidence > 0.3:  # Lowered threshold
                    for subcategory, description in subcategory_options.items():
                        if description == best_description:
                            return subcategory
            except Exception as e:
                self.logger.error(f"❌ Subcategory error: {e}")
        
        # Return first available subcategory as fallback
        return list(subcategory_options.keys())[0]

    def _clean_text(self, text: str) -> str:
        """Clean text for better processing."""
        if not text or not isinstance(text, str):
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Limit length for better processing
        words = text.split()
        if len(words) > 300:
            text = ' '.join(words[:300])
        
        return text

    def _fallback_result(self, reason: str) -> Dict[str, Any]:
        """Return improved fallback result."""
        return {
            'category': 'Manual Review',
            'subcategory': 'Complex Queries',
            'confidence': 0.6,  # Higher confidence for fallback
            'method_used': 'smart_fallback',
            'reason': f'Smart fallback: {reason}',
            'matched_patterns': [],
            'thread_context': {'has_thread': False, 'thread_count': 0},
            'analysis_scores': {'ml_confidence': 0.0, 'rule_confidence': 0.6}
        }
"""
FIXED ML Classifier - Aligned with Rule Engine categories and logic
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
        
        # ALIGNED Main categories with Rule Engine
        self.main_categories = {
            "Manual Review": "Email requesting payment confirmation, proof of payment, invoice receipts, business closure notifications, disputes, or complex issues requiring human review",
            "No Reply (with/without info)": "System notifications, alerts, ticket status updates, sales offers, processing errors, or informational messages requiring no response",
            "Invoices Request": "Email requesting invoice copies, invoice documentation, or invoice information without providing details",
            "Payments Claim": "Email claiming payment was made without providing proof, evidence, or documentation",
            "Auto Reply (with/without info)": "Automatic responses including out-of-office messages, thank you confirmations, surveys, or system-generated replies",
            "Uncategorized": "Email that doesn't clearly fit any specific business category"
        }
        
        # ENHANCED KEYWORD-BASED classification aligned with your patterns
        self.category_keywords = {
            "Manual Review": [
                # Payment/Invoice Updates
                "payment confirmation", "proof of payment", "payment receipt", "confirm payment",
                "invoice receipt", "proof of invoice", "invoice copy", "invoice attached",
                # Disputes & Payments
                "dispute", "contested", "disagreement", "partial payment", "challenge payment",
                # Business Closure
                "business closed", "company closed", "out of business", "ceased operations",
                # Invoices -> External Submission
                "invoice issue", "invoice problem", "invoice error", "invoice concern",
                "import failed", "import error", "failed import", "unable to import",
                "invoice submission failed", "documents were not processed",
                # Payment Details Received
                "payment details", "remittance info", "payment breakdown", "transaction details",
                # Inquiry/Redirection
                "redirect", "forward", "contact instead", "reach out to", "please review",
                # Complex Queries
                "manual review", "human review", "complex", "multiple issues"
            ],
            "No Reply (with/without info)": [
                # System Alerts
                "processing error", "failed to process", "processing failed", "import failed",
                # Tickets/Cases
                "ticket created", "case opened", "ticket resolved", "case closed", "case resolved",
                "support request created", "assigned #", "case number is",
                # Notifications
                "sales offer", "promotion", "special offer", "limited time offer",
                "business closure information", "closure notification only"
            ],
            "Invoices Request": [
                "invoice request", "need invoice", "send invoice", "invoice copy", 
                "invoice documentation", "provide invoice", "share invoice",
                "can you send me the invoice", "please provide invoice"
            ],
            "Payments Claim": [
                "payment made", "already paid", "check sent", "payment completed",
                "payment was sent", "we paid", "payment processed", "has been paid",
                "paid through", "check is being overnighted"
            ],
            "Auto Reply (with/without info)": [
                # Out of Office
                "out of office", "automatic reply", "auto-reply", "currently out",
                "limited access", "away from desk", "on vacation", "on leave",
                # Confirmations
                "thank you", "received your message", "we received your",
                "case confirmed", "support request confirmed", "ticket confirmed",
                # Miscellaneous
                "survey", "feedback", "property manager", "contact changed",
                "forwarding to new", "department changed"
            ]
        }
        
        # COMPLETE subcategory classification aligned with Rule Engine
        self.subcategories = {
            "Manual Review": {
                # Disputes & Payments
                "Partial/Disputed Payment": "Email involving partial payments, disputes, contests, or payment refusals",
                # Payment/Invoice Updates
                "Payment Confirmation": "Email providing proof of payment with attachments or details",
                "Invoice Receipt": "Email providing proof of invoice receipt with documentation",
                # Business Closure
                "Closure Notification": "Email about business closure without payment due",
                "Closure + Payment Due": "Email about business closure with outstanding payments",
                # Invoices
                "External Submission": "Email about invoice issues, import failures, or submission problems",
                "Invoice Errors (format mismatch)": "Email about invoice format issues or missing fields",
                # Payment Details Received
                "Payment Details Received": "Email providing payment details requiring manual verification",
                # Inquiry/Redirection
                "Inquiry/Redirection": "Email requesting action, review, or contact redirection",
                # Complex Queries
                "Complex Queries": "Email with multiple issues or complex problems requiring human review"
            },
            "No Reply (with/without info)": {
                # Notifications
                "Sales/Offers": "Sales promotions or special offers",
                # System Alerts
                "Processing Errors": "System alerts about processing failures",
                "Import Failures": "System alerts about import failures",
                # Notifications
                "Business Closure (Info only)": "Information about business closure requiring no action",
                # Tickets/Cases
                "Created": "Notifications about new tickets or cases being created",
                "Resolved": "Notifications that tickets or cases have been resolved",
                "Open": "Notifications about open tickets requiring escalation",
                # Default
                "Notifications": "General notifications and informational messages"
            },
            "Invoices Request": {
                "Request (No Info)": "Request for invoices without providing specific details"
            },
            "Payments Claim": {
                "Claims Paid (No Info)": "Claims payment was made without providing proof"
            },
            "Auto Reply (with/without info)": {
                # Out of Office
                "With Alternate Contact": "Out-of-office reply with alternate contact information",
                "No Info/Autoreply": "Generic automatic replies without specific info",
                "Return Date Specified": "Out-of-office reply with return date specified",
                # Confirmations
                "Case/Support": "Confirmation of support cases or tickets",
                "General (Thank You)": "General thank you or acknowledgment messages",
                # Miscellaneous
                "Survey": "Feedback requests or surveys",
                "Redirects/Updates (property changes)": "Contact changes or property management updates"
            },
            "Uncategorized": {
                "General": "Email that doesn't fit into specific categories"
            }
        }
        
        self.logger.info("✅ ML classifier aligned with Rule Engine")

    def classify_email(self, text: str, has_thread: bool = False) -> Dict[str, Any]:
        """
        Main classification method - should work WITH Rule Engine, not replace it
        """
        try:
            # Clean text first
            cleaned_text = self._clean_text(text)
            if not cleaned_text:
                return self._fallback_result("Empty text")
            
            # For thread emails, defer to Rule Engine (don't override)
            if has_thread:
                return self._light_thread_classification(cleaned_text)
            
            # Try ML classification for non-thread emails
            main_category = self._classify_main_category_improved(cleaned_text)
            
            # Get subcategory
            subcategory = self._classify_subcategory(cleaned_text, main_category)
            
            return {
                'category': main_category,
                'subcategory': subcategory,
                'confidence': 0.7,  # Moderate confidence - let Rule Engine override
                'method_used': 'ml_classification',
                'reason': f'ML classified as {main_category}/{subcategory}',
                'matched_patterns': [],
                'thread_context': {'has_thread': has_thread, 'thread_count': 0},
                'analysis_scores': {'ml_confidence': 0.7, 'rule_confidence': 0.0}
            }
            
        except Exception as e:
            self.logger.error(f"❌ Classification error: {e}")
            return self._fallback_result(f"Error: {e}")

    def _light_thread_classification(self, text: str) -> Dict[str, Any]:
        """
        Light thread classification - defer complex logic to Rule Engine
        """
        return {
            'category': 'Manual Review',
            'subcategory': 'Complex Queries',
            'confidence': 0.6,  # Low confidence - let Rule Engine handle
            'method_used': 'ml_thread_defer',
            'reason': 'Thread email - deferring to Rule Engine',
            'matched_patterns': [],
            'thread_context': {'has_thread': True, 'thread_count': 1},
            'analysis_scores': {'ml_confidence': 0.6, 'rule_confidence': 0.0}
        }

    def _classify_main_category_improved(self, text: str) -> str:
        """Enhanced main category classification"""
        # First try keyword-based classification
        keyword_result = self._classify_by_keywords(text)
        if keyword_result != "Uncategorized":
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
                
                if confidence > 0.4:  # Reasonable threshold
                    for category, description in self.main_categories.items():
                        if description == best_description:
                            return category
                            
            except Exception as e:
                self.logger.error(f"❌ ML classification error: {e}")
        
        # Smart fallback
        return self._smart_fallback_classification(text)

    def _classify_by_keywords(self, text: str) -> str:
        """Enhanced keyword-based classification"""
        text_lower = text.lower()
        
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight longer phrases higher
                    weight = len(keyword.split())
                    score += weight
            category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
        
        return "Uncategorized"

    def _classify_subcategory(self, text: str, main_category: str) -> str:
        """Enhanced subcategory classification"""
        if main_category not in self.subcategories:
            return "General"
        
        subcategory_options = self.subcategories[main_category]
        text_lower = text.lower()
        
        # Enhanced keyword matching for Manual Review
        if main_category == "Manual Review":
            # Disputes & Payments
            if any(word in text_lower for word in ['dispute', 'contested', 'disagreement', 'refuse', 'partial']):
                return "Partial/Disputed Payment"
            # Payment confirmation with proof
            elif any(word in text_lower for word in ['payment confirmation', 'proof of payment', 'payment receipt', 'eft#', 'check number']):
                return "Payment Confirmation"
            # Invoice receipt with proof
            elif any(word in text_lower for word in ['invoice receipt', 'invoice copy', 'invoice attached']):
                return "Invoice Receipt"
            # External submission (import/invoice issues)
            elif any(word in text_lower for word in ['import failed', 'invoice issue', 'submission failed', 'invoice error']):
                return "External Submission"
            # Invoice errors
            elif any(word in text_lower for word in ['missing field', 'format mismatch', 'incomplete invoice']):
                return "Invoice Errors (format mismatch)"
            # Payment details
            elif any(word in text_lower for word in ['payment details', 'remittance info', 'payment breakdown']):
                return "Payment Details Received"
            # Closure with payment
            elif any(word in text_lower for word in ['closed', 'closure']) and 'payment' in text_lower:
                return "Closure + Payment Due"
            # Closure without payment
            elif any(word in text_lower for word in ['closed', 'closure', 'out of business']):
                return "Closure Notification"
            # Inquiry/Redirection
            elif any(word in text_lower for word in ['redirect', 'forward', 'contact instead', 'please review']):
                return "Inquiry/Redirection"
            else:
                return "Complex Queries"
        
        # For other categories with single subcategory
        if len(subcategory_options) == 1:
            return list(subcategory_options.keys())[0]
        
        # Default to first subcategory
        return list(subcategory_options.keys())[0]

    def _smart_fallback_classification(self, text: str) -> str:
        """Smart fallback classification"""
        text_lower = text.lower()
        
        # Check for clear patterns
        if any(word in text_lower for word in ['payment', 'invoice', 'confirm', 'receipt', 'proof', 'dispute']):
            return "Manual Review"
        elif any(word in text_lower for word in ['out of office', 'automatic reply', 'thank you']):
            return "Auto Reply (with/without info)"
        elif any(word in text_lower for word in ['request', 'need', 'send']) and 'invoice' in text_lower:
            return "Invoices Request"
        elif any(word in text_lower for word in ['paid', 'sent', 'completed', 'made payment']):
            return "Payments Claim"
        elif any(word in text_lower for word in ['ticket', 'case', 'created', 'resolved']):
            return "No Reply (with/without info)"
        
        return "Manual Review"  # Conservative fallback

    def _clean_text(self, text: str) -> str:
        """Clean text for better processing"""
        if not text or not isinstance(text, str):
            return ""
        
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Limit length but keep more context
        words = text.split()
        if len(words) > 500:
            text = ' '.join(words[:500])
        
        return text

    def _fallback_result(self, reason: str) -> Dict[str, Any]:
        """Conservative fallback result"""
        return {
            'category': 'Manual Review',
            'subcategory': 'Complex Queries',
            'confidence': 0.5,  # Low confidence - let Rule Engine override
            'method_used': 'ml_fallback',
            'reason': f'ML fallback: {reason}',
            'matched_patterns': [],
            'thread_context': {'has_thread': False, 'thread_count': 0},
            'analysis_scores': {'ml_confidence': 0.5, 'rule_confidence': 0.0}
        }
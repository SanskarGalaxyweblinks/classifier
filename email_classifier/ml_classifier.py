"""
Updated ML Classifier - Aligned with New Hierarchical Structure
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
        
        # Initialize BART model with error handling
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
        
        # Main categories aligned with new hierarchy
        self.main_categories = {
            "Manual Review": "Complex issues requiring human attention including disputes, invoice receipts, business closures, and payment confirmations",
            "No Reply (with/without info)": "System notifications, alerts, ticket updates, sales offers, or informational messages requiring no response",
            "Invoices Request": "Requests for invoice copies or documentation without providing details",
            "Payments Claim": "Claims about payments made, payment confirmations, or payment details requiring verification",
            "Auto Reply (with/without info)": "Automatic responses including out-of-office messages, confirmations, surveys, or system-generated replies",
            "Uncategorized": "Emails that don't clearly fit any specific business category"
        }
        
        # Enhanced keyword-based classification aligned with new structure
        self.category_keywords = {
            "Manual Review": [
                # Disputes & Payments
                "dispute", "contested", "disagreement", "partial payment", "challenge payment", "refuse payment",
                # Invoice Updates - Invoice Receipt
                "invoice receipt", "proof of invoice", "invoice copy attached", "invoice documentation",
                # Business Closure
                "business closed", "company closed", "out of business", "ceased operations", "closure notification",
                # Invoices - External Submission & Errors
                "invoice issue", "invoice problem", "invoice error", "invoice concern", "import failed", 
                "import error", "failed import", "unable to import", "invoice submission failed",
                "missing field", "format mismatch", "incomplete invoice", "invoice format error",
                # Inquiry/Redirection
                "redirect", "forward", "contact instead", "reach out to", "please review", "manual review",
                # Complex Queries
                "human review", "complex", "multiple issues", "requires attention"
            ],
            "No Reply (with/without info)": [
                # Notifications - Sales/Offers
                "sales offer", "promotion", "special offer", "limited time offer", "discount",
                # System Alerts & Processing Errors
                "processing error", "failed to process", "processing failed", "system alert",
                # Business Closure (Info only)
                "business closure information", "closure notification only", "informational closure",
                # General (Thank You)
                "thank you for", "we received", "acknowledgment", "confirmation received",
                # Tickets/Cases
                "ticket created", "case opened", "ticket resolved", "case closed", "case resolved",
                "support request created", "assigned #", "case number is", "ticket status"
            ],
            "Invoices Request": [
                "invoice request", "need invoice", "send invoice", "invoice copy", 
                "invoice documentation", "provide invoice", "share invoice",
                "can you send me the invoice", "please provide invoice", "request invoice"
            ],
            "Payments Claim": [
                # Claims Paid (No Info)
                "payment made", "already paid", "check sent", "payment completed",
                "payment was sent", "we paid", "payment processed", "has been paid",
                "paid through", "check is being overnighted",
                # Payment Details Received/Payment Confirmation
                "payment confirmation", "proof of payment", "payment receipt", "eft#",
                "check number", "payment details", "remittance info", "payment breakdown",
                "transaction details", "wire transfer", "bank transfer"
            ],
            "Auto Reply (with/without info)": [
                # Out of Office
                "out of office", "automatic reply", "auto-reply", "currently out",
                "limited access", "away from desk", "on vacation", "on leave",
                "return date", "alternate contact", "back on",
                # Miscellaneous
                "survey", "feedback", "property manager", "contact changed",
                "forwarding to new", "department changed", "redirects", "updates"
            ]
        }
        
        # Complete subcategory classification aligned with new hierarchy
        self.subcategories = {
            "Manual Review": {
                "Partial/Disputed Payment": "Emails involving partial payments, disputes, contests, or payment refusals",
                "Invoice Receipt": "Emails providing proof of invoice receipt with documentation",
                "Closure Notification": "Emails about business closure without payment due",
                "Closure + Payment Due": "Emails about business closure with outstanding payments",
                "External Submission": "Emails about invoice issues, import failures, or submission problems",
                "Invoice Errors (format mismatch)": "Emails about invoice format issues or missing fields",
                "Inquiry/Redirection": "Emails requesting action, review, or contact redirection",
                "Complex Queries": "Emails with multiple issues or complex problems requiring human review"
            },
            "No Reply (with/without info)": {
                "Sales/Offers": "Sales promotions or special offers",
                "System Alerts": "System alerts and notifications",
                "Processing Errors": "System alerts about processing failures",
                "Business Closure (Info only)": "Information about business closure requiring no action",
                "General (Thank You)": "General thank you or acknowledgment messages",
                "Created": "Notifications about new tickets or cases being created",
                "Resolved": "Notifications that tickets or cases have been resolved",
                "Open": "Notifications about open tickets requiring escalation"
            },
            "Invoices Request": {
                "Request (No Info)": "Requests for invoices without providing specific details"
            },
            "Payments Claim": {
                "Claims Paid (No Info)": "Claims payment was made without providing proof",
                "Payment Details Received": "Payment details requiring manual verification",
                "Payment Confirmation": "Payment proof and confirmation documentation"
            },
            "Auto Reply (with/without info)": {
                "With Alternate Contact": "Out-of-office reply with alternate contact information",
                "No Info/Autoreply": "Generic automatic replies without specific info",
                "Return Date Specified": "Out-of-office reply with return date specified",
                "Survey": "Feedback requests or surveys",
                "Redirects/Updates (property changes)": "Contact changes or property management updates"
            },
            "Uncategorized": {
                "General": "Emails that don't fit into specific categories"
            }
        }
        
        self.logger.info("✅ ML classifier updated with new hierarchy structure")

    def classify_email(self, text: str, has_thread: bool = False) -> Dict[str, Any]:
        """
        Main classification method aligned with new hierarchy
        """
        try:
            # Clean text first
            cleaned_text = self._clean_text(text)
            if not cleaned_text:
                return self._fallback_result("Empty text")
            
            # For thread emails, use conservative approach
            if has_thread:
                return self._thread_classification(cleaned_text)
            
            # Classify main category
            main_category = self._classify_main_category(cleaned_text)
            
            # Classify subcategory
            subcategory = self._classify_subcategory(cleaned_text, main_category)
            
            # Calculate confidence based on keyword matches
            confidence = self._calculate_confidence(cleaned_text, main_category, subcategory)
            
            return {
                'category': main_category,
                'subcategory': subcategory,
                'confidence': confidence,
                'method_used': 'ml_classification',
                'reason': f'ML classified as {main_category}/{subcategory}',
                'matched_patterns': self._get_matched_keywords(cleaned_text, main_category),
                'thread_context': {'has_thread': has_thread, 'thread_count': 0},
                'analysis_scores': {'ml_confidence': confidence, 'rule_confidence': 0.0}
            }
            
        except Exception as e:
            self.logger.error(f"❌ Classification error: {e}")
            return self._fallback_result(f"Error: {e}")

    def _thread_classification(self, text: str) -> Dict[str, Any]:
        """
        Conservative thread classification - defer to Rule Engine
        """
        return {
            'category': 'Manual Review',
            'subcategory': 'Complex Queries',
            'confidence': 0.6,
            'method_used': 'ml_thread_defer',
            'reason': 'Thread email - deferring to Rule Engine for complex logic',
            'matched_patterns': [],
            'thread_context': {'has_thread': True, 'thread_count': 1},
            'analysis_scores': {'ml_confidence': 0.6, 'rule_confidence': 0.0}
        }

    def _classify_main_category(self, text: str) -> str:
        """Enhanced main category classification"""
        # Keyword-based classification first
        keyword_result = self._classify_by_keywords(text)
        if keyword_result != "Uncategorized":
            return keyword_result
        
        # ML classification if available
        if self.classifier:
            try:
                result = self.classifier(
                    text,
                    list(self.main_categories.values()),
                    multi_label=False
                )
                
                best_description = result['labels'][0]
                confidence = result['scores'][0]
                
                if confidence > 0.4:
                    for category, description in self.main_categories.items():
                        if description == best_description:
                            return category
                            
            except Exception as e:
                self.logger.error(f"❌ ML classification error: {e}")
        
        # Smart fallback
        return self._smart_fallback(text)

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
        """Enhanced subcategory classification aligned with new hierarchy"""
        if main_category not in self.subcategories:
            return "General"
        
        text_lower = text.lower()
        
        # Manual Review subcategories
        if main_category == "Manual Review":
            # Disputes & Payments
            if any(word in text_lower for word in ['dispute', 'contested', 'disagreement', 'refuse', 'partial']):
                return "Partial/Disputed Payment"
            # Invoice Updates - Invoice Receipt
            elif any(word in text_lower for word in ['invoice receipt', 'invoice copy', 'invoice attached', 'proof of invoice']):
                return "Invoice Receipt"
            # Business Closure with payment
            elif any(word in text_lower for word in ['closed', 'closure']) and any(word in text_lower for word in ['payment', 'due', 'outstanding']):
                return "Closure + Payment Due"
            # Business Closure without payment
            elif any(word in text_lower for word in ['closed', 'closure', 'out of business', 'ceased']):
                return "Closure Notification"
            # External Submission (import/invoice issues)
            elif any(word in text_lower for word in ['import failed', 'invoice issue', 'submission failed', 'unable to import']):
                return "External Submission"
            # Invoice Errors
            elif any(word in text_lower for word in ['missing field', 'format mismatch', 'incomplete invoice', 'format error']):
                return "Invoice Errors (format mismatch)"
            # Inquiry/Redirection
            elif any(word in text_lower for word in ['redirect', 'forward', 'contact instead', 'please review']):
                return "Inquiry/Redirection"
            else:
                return "Complex Queries"
        
        # No Reply subcategories
        elif main_category == "No Reply (with/without info)":
            if any(word in text_lower for word in ['sales', 'offer', 'promotion', 'discount']):
                return "Sales/Offers"
            elif any(word in text_lower for word in ['processing error', 'failed to process']):
                return "Processing Errors"
            elif any(word in text_lower for word in ['system alert', 'alert']):
                return "System Alerts"
            elif any(word in text_lower for word in ['closure information', 'closure notification']) and 'payment' not in text_lower:
                return "Business Closure (Info only)"
            elif any(word in text_lower for word in ['thank you', 'received', 'acknowledgment']):
                return "General (Thank You)"
            elif any(word in text_lower for word in ['ticket created', 'case opened']):
                return "Created"
            elif any(word in text_lower for word in ['resolved', 'closed', 'completed']):
                return "Resolved"
            elif any(word in text_lower for word in ['open', 'pending']):
                return "Open"
            else:
                return "System Alerts"  # Default for No Reply
        
        # Payments Claim subcategories
        elif main_category == "Payments Claim":
            # Payment confirmation with proof
            if any(word in text_lower for word in ['payment confirmation', 'proof of payment', 'payment receipt', 'eft#']):
                return "Payment Confirmation"
            # Payment details received
            elif any(word in text_lower for word in ['payment details', 'remittance info', 'payment breakdown']):
                return "Payment Details Received"
            else:
                return "Claims Paid (No Info)"  # Default for payment claims
        
        # Auto Reply subcategories
        elif main_category == "Auto Reply (with/without info)":
            if any(word in text_lower for word in ['alternate contact', 'contact information']):
                return "With Alternate Contact"
            elif any(word in text_lower for word in ['return date', 'back on', 'until']):
                return "Return Date Specified"
            elif any(word in text_lower for word in ['survey', 'feedback']):
                return "Survey"
            elif any(word in text_lower for word in ['property manager', 'contact changed', 'redirects']):
                return "Redirects/Updates (property changes)"
            else:
                return "No Info/Autoreply"  # Default for auto replies
        
        # Single subcategory categories
        subcategory_options = self.subcategories[main_category]
        return list(subcategory_options.keys())[0]

    def _calculate_confidence(self, text: str, category: str, subcategory: str) -> float:
        """Calculate confidence based on keyword matches"""
        text_lower = text.lower()
        
        # Check category keywords
        category_matches = 0
        if category in self.category_keywords:
            for keyword in self.category_keywords[category]:
                if keyword in text_lower:
                    category_matches += 1
        
        # Base confidence calculation
        if category_matches >= 3:
            return 0.9
        elif category_matches == 2:
            return 0.8
        elif category_matches == 1:
            return 0.7
        else:
            return 0.6

    def _get_matched_keywords(self, text: str, category: str) -> List[str]:
        """Get list of matched keywords for transparency"""
        text_lower = text.lower()
        matched = []
        
        if category in self.category_keywords:
            for keyword in self.category_keywords[category]:
                if keyword in text_lower:
                    matched.append(keyword)
        
        return matched[:5]  # Limit to top 5 matches

    def _smart_fallback(self, text: str) -> str:
        """Smart fallback classification"""
        text_lower = text.lower()
        
        # Check for clear patterns
        if any(word in text_lower for word in ['payment', 'invoice', 'dispute', 'closure']):
            return "Manual Review"
        elif any(word in text_lower for word in ['out of office', 'automatic reply', 'survey']):
            return "Auto Reply (with/without info)"
        elif any(word in text_lower for word in ['request', 'need']) and 'invoice' in text_lower:
            return "Invoices Request"
        elif any(word in text_lower for word in ['paid', 'sent', 'completed', 'confirmation']):
            return "Payments Claim"
        elif any(word in text_lower for word in ['ticket', 'case', 'notification', 'alert']):
            return "No Reply (with/without info)"
        
        return "Uncategorized"  # Conservative fallback

    def _clean_text(self, text: str) -> str:
        """Clean text for better processing"""
        if not text or not isinstance(text, str):
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Limit length but keep context
        words = text.split()
        if len(words) > 500:
            text = ' '.join(words[:500])
        
        return text

    def _fallback_result(self, reason: str) -> Dict[str, Any]:
        """Conservative fallback result"""
        return {
            'category': 'Uncategorized',
            'subcategory': 'General',
            'confidence': 0.5,
            'method_used': 'ml_fallback',
            'reason': f'ML fallback: {reason}',
            'matched_patterns': [],
            'thread_context': {'has_thread': False, 'thread_count': 0},
            'analysis_scores': {'ml_confidence': 0.5, 'rule_confidence': 0.0}
        }

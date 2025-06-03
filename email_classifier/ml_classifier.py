"""
Updated ML Classifier - Clean, Aligned with Hierarchy, Quality-Focused
"""

import logging
import torch
from transformers import pipeline
from typing import Dict, Any, List
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
        
        # Main categories - EXACT hierarchy match
        self.main_categories = {
            "Manual Review": "Complex issues requiring human attention including disputes, invoice receipts, business closures, and payment confirmations",
            "No Reply (with/without info)": "System notifications, alerts, ticket updates, sales offers, or informational messages requiring no response",
            "Invoices Request": "Requests for invoice copies or documentation without providing details",
            "Payments Claim": "Claims about payments made, payment confirmations, or payment details requiring verification",
            "Auto Reply (with/without info)": "Automatic responses including out-of-office messages, confirmations, surveys, or system-generated replies",
            "Uncategorized": "Emails that don't clearly fit any specific business category"
        }
        
        # ENHANCED keyword classification - FIXED with missing patterns from analysis
        self.category_keywords = {
            "Manual Review": [
                # ENHANCED Disputes & Payments - ADDED missing patterns from Email 1
                "dispute", "contested", "disagreement", "partial payment", "challenge payment", "refuse payment",
                "owe nothing", "owe them nothing", "consider this a scam", "looks like a scam", 
                "is this legitimate", "verify this debt", "do not acknowledge", "formally disputing",
                "dispute this debt", "billing is incorrect", "not our responsibility", "cease and desist",
                "fdcpa", "not properly billed", "wrong entity", "debt is disputed",
                
                # Invoice Receipt (proof provided)
                "invoice receipt", "proof of invoice", "invoice copy attached", "invoice documentation", "invoice attached",
                "invoice receipt attached", "copy of invoice attached for your records",
                
                # Business Closure
                "business closed", "company closed", "out of business", "ceased operations", "closure notification",
                "filed bankruptcy", "bankruptcy protection", "chapter 7", "chapter 11",
                
                # External Submission (invoice issues)
                "invoice issue", "invoice problem", "invoice error", "import failed", "submission failed", "unable to import",
                "documents not processed", "submission unsuccessful", "error importing invoice",
                
                # Invoice Format Errors
                "missing field", "format mismatch", "incomplete invoice", "invoice format error", "required field missing",
                "missing required field", "field missing from invoice",
                
                # Inquiry/Redirection
                "redirect", "forward", "contact instead", "reach out to", "please review", "guidance needed",
                "please check with", "insufficient data to research", "need guidance", "please advise",
                "what documentation needed", "where to send payment",
                
                # Complex Queries
                "human review", "complex", "multiple issues", "requires attention", "manual review",
                "settle for", "settlement offer", "negotiate payment", "attorney", "law firm", "legal counsel"
            ],
            "No Reply (with/without info)": [
                # ENHANCED Sales/Offers - ADDED missing patterns from Email 119
                "sales offer", "promotion", "special offer", "limited time offer", "discount", "marketing",
                "prices increasing", "price increase", "limited time", "hours left", "sale ending",
                "special pricing", "promotional offer", "exclusive deal", "promotional pricing", "discount offer",
                
                # System Alerts & Processing Errors
                "processing error", "failed to process", "system alert", "delivery failed", "import error",
                "system notification", "automated notification", "security alert", "maintenance notification",
                "cannot be processed", "electronic invoice rejected", "request couldn't be created",
                "system unable to process", "mail delivery failed", "email bounced",
                
                # Business Closure (Info only)
                "business closure information", "closure notification only", "informational closure",
                
                # General Thank You
                "thank you for", "we received", "acknowledgment", "confirmation received", "received your message",
                "thank you for your email", "thanks for contacting", "still reviewing", "currently reviewing",
                "under review", "we are reviewing", "for your records",
                
                # Tickets/Cases
                "ticket created", "case opened", "ticket resolved", "case closed", "case resolved", "ticket status",
                "new ticket opened", "support request created", "case has been created",
                "ticket has been resolved", "marked as resolved", "status resolved"
            ],
            "Invoices Request": [
                "invoice request", "need invoice", "send invoice", "invoice copy", "provide invoice", 
                "share invoice", "outstanding invoices", "copies of invoices", "invoice documentation",
                # ENHANCED - but excluding proof scenarios
                "send me the invoice", "provide the invoice", "need invoice copy", "outstanding invoices owed",
                "copies of any invoices", "send invoices that are due", "provide outstanding invoices"
            ],
            "Payments Claim": [
                # ENHANCED Claims Paid (No Info)
                "payment made", "already paid", "check sent", "payment completed", "we paid", "payment processed",
                "payment was made", "bill was paid", "payment was sent", "this was paid", "account paid",
                "made payment", "been paid",
                
                # ENHANCED Payment Confirmation (with proof) - ADDED patterns from Email 4
                "payment confirmation", "proof of payment", "payment receipt", "eft#", "check number",
                "invoice was paid see attachments", "payment confirmation attached", "transaction id",
                "here is proof of payment", "payment receipt attached", "wire confirmation", "batch number",
                "paid via transaction number",
                
                # Payment Details Received
                "payment details", "remittance info", "payment breakdown", "payment timeline", "payment scheduled",
                "payment will be sent", "payment being processed", "check will be mailed",
                "in process of issuing payment", "invoices being processed for payment", "will pay this online",
                "working on payment", "need time to pay"
            ],
            "Auto Reply (with/without info)": [
                # Out of Office
                "out of office", "automatic reply", "auto-reply", "currently out", "away from desk", 
                "on vacation", "return date", "alternate contact", "limited access to email",
                "do not reply", "automated response", "out of office until", "will be back", "returning on",
                "emergency contact number", "urgent matters contact", "immediate assistance contact",
                
                # ENHANCED Miscellaneous - ADDED survey patterns from Email 2
                "survey", "feedback", "property manager", "contact changed", "no longer with", "redirects",
                "feedback request", "rate our service", "customer satisfaction", "take our survey",
                "your feedback is important", "please rate", "questionnaire",
                "no longer employed", "department changed", "property manager changed"
            ]
        }
        
        # ENHANCED subcategory mapping - FIXED with missing patterns
        self.subcategories = {
            "Manual Review": {
                "Partial/Disputed Payment": [
                    "dispute", "contested", "disagreement", "refuse payment", "partial payment",
                    # ADDED: Missing dispute patterns from Email 1
                    "owe nothing", "owe them nothing", "consider this a scam", "looks like a scam",
                    "is this legitimate", "verify this debt", "do not acknowledge", "formally disputing",
                    "dispute this debt", "billing is incorrect", "not our responsibility", "cease and desist"
                ],
                "Invoice Receipt": [
                    "invoice receipt", "proof of invoice", "invoice attached", "invoice copy attached",
                    "invoice receipt attached", "copy of invoice attached for your records"
                ],
                "Closure Notification": [
                    "business closed", "company closed", "out of business", "ceased operations",
                    "filed bankruptcy", "bankruptcy protection", "chapter 7", "chapter 11"
                ],
                "Closure + Payment Due": [
                    "closed", "closure", "bankruptcy", "payment", "due", "outstanding",
                    "business closed outstanding", "closure with outstanding payment"
                ],
                "External Submission": [
                    "invoice issue", "invoice problem", "import failed", "submission failed",
                    "documents not processed", "submission unsuccessful", "error importing invoice",
                    "invoice submission failed"
                ],
                "Invoice Errors (format mismatch)": [
                    "missing field", "format mismatch", "incomplete invoice", "format error",
                    "missing required field", "invoice format error", "field missing from invoice"
                ],
                "Inquiry/Redirection": [
                    "redirect", "forward", "contact instead", "guidance needed", "please review",
                    "reach out to", "please check with", "insufficient data to research",
                    "need guidance", "please advise", "what documentation needed"
                ],
                "Complex Queries": [
                    "complex", "multiple issues", "human review", "requires attention",
                    "settle for", "settlement offer", "negotiate payment", "attorney", "legal counsel"
                ]
            },
            "No Reply (with/without info)": {
                "Sales/Offers": [
                    "sales offer", "promotion", "discount", "special offer",
                    # ADDED: Missing sales patterns from Email 119
                    "prices increasing", "price increase", "limited time offer", "hours left",
                    "sale ending", "special pricing", "promotional offer", "exclusive deal"
                ],
                "System Alerts": [
                    "system alert", "notification", "alert", "system notification",
                    "automated notification", "security alert", "maintenance notification"
                ],
                "Processing Errors": [
                    "processing error", "failed to process", "delivery failed", "import error",
                    "cannot be processed", "electronic invoice rejected", "request couldn't be created",
                    "system unable to process", "mail delivery failed", "email bounced"
                ],
                "Business Closure (Info only)": [
                    "closure information", "business closure info", "closure notification only"
                ],
                "General (Thank You)": [
                    "thank you", "received", "acknowledgment", "thank you for your email",
                    "thanks for contacting", "still reviewing", "currently reviewing", "under review"
                ],
                "Created": [
                    "ticket created", "case opened", "case created", "new ticket opened",
                    "support request created", "case has been created"
                ],
                "Resolved": [
                    "resolved", "closed", "completed", "solved", "ticket has been resolved",
                    "marked as resolved", "status resolved"
                ],
                "Open": [
                    "open", "pending", "in progress", "still pending", "case pending"
                ]
            },
            "Invoices Request": {
                "Request (No Info)": [
                    "invoice request", "need invoice", "send invoice", "provide invoice",
                    "send me the invoice", "provide the invoice", "need invoice copy",
                    "outstanding invoices owed", "copies of any invoices"
                ]
            },
            "Payments Claim": {
                "Claims Paid (No Info)": [
                    "already paid", "payment made", "check sent", "we paid",
                    "payment was made", "bill was paid", "payment was sent", "this was paid",
                    "account paid", "made payment", "been paid"
                ],
                "Payment Details Received": [
                    "payment details", "payment timeline", "payment scheduled",
                    "payment will be sent", "payment being processed", "check will be mailed",
                    "in process of issuing payment", "will pay this online", "need time to pay"
                ],
                "Payment Confirmation": [
                    "payment confirmation", "proof of payment", "payment receipt", "eft#",
                    # ADDED: Enhanced proof patterns from Email 4
                    "invoice was paid see attachments", "payment confirmation attached",
                    "check number", "transaction id", "here is proof of payment",
                    "wire confirmation", "batch number", "paid via transaction number"
                ]
            },
            "Auto Reply (with/without info)": {
                "With Alternate Contact": [
                    "alternate contact", "contact information", "emergency contact",
                    "emergency contact number", "urgent matters contact", "immediate assistance contact"
                ],
                "No Info/Autoreply": [
                    "out of office", "automatic reply", "auto-reply", "currently out",
                    "away from desk", "on vacation", "limited access to email", "do not reply"
                ],
                "Return Date Specified": [
                    "return date", "back on", "until", "returning", "out of office until",
                    "will be back", "returning on"
                ],
                "Survey": [
                    "survey", "feedback", "questionnaire",
                    # ADDED: Enhanced survey patterns from Email 2
                    "feedback request", "rate our service", "customer satisfaction",
                    "take our survey", "your feedback is important", "please rate"
                ],
                "Redirects/Updates (property changes)": [
                    "property manager", "contact changed", "no longer with",
                    "no longer employed", "department changed", "property manager changed"
                ]
            },
            "Uncategorized": {
                "General": ["uncategorized", "unclear", "unknown"]
            }
        }
        
        self.logger.info("✅ ML classifier updated with enhanced patterns for misclassification fixes")

    def classify_email(self, text: str, has_thread: bool = False) -> Dict[str, Any]:
        """Main classification method - clean and efficient"""
        try:
            cleaned_text = self._clean_text(text)
            if not cleaned_text:
                return self._fallback_result("Empty text")
            
            # Thread emails - conservative approach
            if has_thread:
                return self._thread_classification(cleaned_text)
            
            # Main classification flow
            main_category = self._classify_main_category(cleaned_text)
            subcategory = self._classify_subcategory(cleaned_text, main_category)
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
        """Conservative thread handling - defer to Rule Engine"""
        return {
            'category': 'Manual Review',
            'subcategory': 'Complex Queries',
            'confidence': 0.6,
            'method_used': 'ml_thread_defer',
            'reason': 'Thread email - deferring to Rule Engine',
            'matched_patterns': [],
            'thread_context': {'has_thread': True, 'thread_count': 1},
            'analysis_scores': {'ml_confidence': 0.6, 'rule_confidence': 0.0}
        }

    def _classify_main_category(self, text: str) -> str:
        """Clean main category classification"""
        # Primary: Keyword-based classification
        keyword_result = self._classify_by_keywords(text)
        if keyword_result != "Uncategorized":
            return keyword_result
        
        # Secondary: BART model (if available)
        if self.classifier:
            try:
                result = self.classifier(text, list(self.main_categories.values()), multi_label=False)
                best_description = result['labels'][0]
                confidence = result['scores'][0]
                
                if confidence > 0.5:  # Higher threshold for BART
                    for category, description in self.main_categories.items():
                        if description == best_description:
                            return category
            except Exception as e:
                self.logger.error(f"❌ BART classification error: {e}")
        
        # Fallback: Smart pattern matching
        return self._smart_fallback(text)

    def _classify_by_keywords(self, text: str) -> str:
        """Enhanced keyword classification with scoring"""
        text_lower = text.lower()
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight longer phrases higher (more specific)
                    weight = len(keyword.split())
                    score += weight
            category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
        
        return "Uncategorized"

    def _classify_subcategory(self, text: str, main_category: str) -> str:
        """FIXED subcategory classification - exact hierarchy match"""
        if main_category not in self.subcategories:
            return "General"
        
        text_lower = text.lower()
        
        # Score-based subcategory selection
        subcategory_scores = {}
        
        for subcategory, keywords in self.subcategories[main_category].items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Longer phrases get higher weight
                    weight = len(keyword.split())
                    score += weight
            subcategory_scores[subcategory] = score
        
        # Return highest scoring subcategory
        if subcategory_scores:
            best_subcategory = max(subcategory_scores.items(), key=lambda x: x[1])
            if best_subcategory[1] > 0:
                return best_subcategory[0]
        
        # Fallback to first subcategory for the category
        return list(self.subcategories[main_category].keys())[0]

    def _calculate_confidence(self, text: str, category: str, subcategory: str) -> float:
        """Clean confidence calculation"""
        text_lower = text.lower()
        
        # Count category keyword matches
        category_matches = 0
        if category in self.category_keywords:
            for keyword in self.category_keywords[category]:
                if keyword in text_lower:
                    category_matches += 1
        
        # Count subcategory keyword matches
        subcategory_matches = 0
        if category in self.subcategories and subcategory in self.subcategories[category]:
            for keyword in self.subcategories[category][subcategory]:
                if keyword in text_lower:
                    subcategory_matches += 1
        
        # Combined confidence calculation
        total_matches = category_matches + subcategory_matches
        
        if total_matches >= 3:
            return 0.9
        elif total_matches == 2:
            return 0.8
        elif total_matches == 1:
            return 0.7
        else:
            return 0.6

    def _get_matched_keywords(self, text: str, category: str) -> List[str]:
        """Get matched keywords for transparency"""
        text_lower = text.lower()
        matched = []
        
        if category in self.category_keywords:
            for keyword in self.category_keywords[category]:
                if keyword in text_lower:
                    matched.append(keyword)
        
        return matched[:5]  # Top 5 matches

    def _smart_fallback(self, text: str) -> str:
        """Smart fallback with clear business logic"""
        text_lower = text.lower()
        
        # High-priority business patterns
        if any(word in text_lower for word in ['dispute', 'disagreement', 'contested']):
            return "Manual Review"
        elif any(word in text_lower for word in ['invoice request', 'need invoice', 'send invoice']):
            return "Invoices Request"
        elif any(word in text_lower for word in ['already paid', 'payment made', 'check sent']):
            return "Payments Claim"
        elif any(word in text_lower for word in ['out of office', 'automatic reply', 'auto-reply']):
            return "Auto Reply (with/without info)"
        elif any(word in text_lower for word in ['ticket', 'case', 'notification', 'alert']):
            return "No Reply (with/without info)"
        elif any(word in text_lower for word in ['payment', 'invoice', 'business', 'closure']):
            return "Manual Review"  # Conservative routing for business content
        
        return "Uncategorized"

    def _clean_text(self, text: str) -> str:
        """Clean text preprocessing"""
        if not text or not isinstance(text, str):
            return ""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Reasonable length limit
        words = text.split()
        if len(words) > 300:  # Reduced from 500 for efficiency
            text = ' '.join(words[:300])
        
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
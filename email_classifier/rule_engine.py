"""
Enhanced RuleEngine with Thread Logic and Attachment Handling
Priority: Attachments → Thread Logic → Regular Classification
"""
import logging
import time
import re
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

from .patterns import PatternMatcher
from .nlp_utils import TextAnalysis, NLPProcessor

logger = logging.getLogger(__name__)

@dataclass
class RuleResult:
    category: str
    subcategory: str
    confidence: float
    reason: str
    matched_rules: list

class RuleEngine:
    """
    Enhanced RuleEngine with Thread Logic and Attachment Handling
    Priority Flow: Attachments → Thread Routing → Regular Classification
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pattern_matcher = PatternMatcher()
        self.nlp_processor = NLPProcessor()
        
        # Initialize enhanced rules
        self._initialize_hierarchy_rules()
        self._initialize_thread_patterns()
        self._initialize_noreply_patterns()
        
        self.logger.info("✅ Enhanced RuleEngine with Thread Logic initialized")

    def _initialize_hierarchy_rules(self) -> None:
        """Initialize exact hierarchy structure for classification rules."""
        
        self.hierarchy_structure = {
            "Manual Review": {
                "Disputes & Payments": ["Partial/Disputed Payment"],
                "Invoice Updates": ["Invoice Receipt"],
                "Business Closure": ["Closure Notification", "Closure + Payment Due"],
                "Invoices": ["External Submission", "Invoice Errors (format mismatch)"],
                "Direct": ["Inquiry/Redirection", "Complex Queries"]
            },
            "No Reply (with/without info)": {
                "Notifications": ["Sales/Offers", "System Alerts", "Processing Errors", "Business Closure (Info only)"],
                "Tickets/Cases": ["Created", "Resolved", "Open"]
            },
            "Invoices Request": {
                "Direct": ["Request (No Info)"]
            },
            "Payments Claim": {
                "Direct": ["Claims Paid (No Info)", "Payment Details Received", "Payment Confirmation"]
            },
            "Auto Reply (with/without info)": {
                "Out of Office": ["With Alternate Contact", "No Info/Autoreply", "Return Date Specified"],
                "Miscellaneous": ["Survey", "Redirects/Updates (property changes)"]
            }
        }
        
        self.default_subcategories = {
            "Manual Review": "Complex Queries",
            "No Reply (with/without info)": "System Alerts",
            "Invoices Request": "Request (No Info)", 
            "Payments Claim": "Claims Paid (No Info)",
            "Auto Reply (with/without info)": "No Info/Autoreply"
        }

    def _initialize_thread_patterns(self) -> None:
        """Initialize thread-specific patterns by REUSING existing patterns from pattern_matcher and nlp_processor."""
        
        # REUSE PATTERNS FROM EXISTING COMPONENTS - NO DUPLICATION!
        self.thread_patterns = {
            "Manual Review": {
                # Get dispute patterns from pattern matcher
                "dispute_patterns": self._get_patterns_from_matcher("Manual Review", "Partial/Disputed Payment"),
                # Get complex patterns from pattern matcher  
                "complex_patterns": self._get_patterns_from_matcher("Manual Review", "Complex Queries"),
                # Get closure patterns from pattern matcher
                "closure_patterns": self._get_patterns_from_matcher("Manual Review", "Closure Notification"),
                # Get invoice proof patterns from pattern matcher
                "invoice_proof_patterns": self._get_patterns_from_matcher("Manual Review", "Invoice Receipt")
            },
            
            "Payments Claim": {
                # Get payment claim patterns from pattern matcher
                "claim_patterns": self._get_patterns_from_matcher("Payments Claim", "Claims Paid (No Info)"),
                # Get payment proof patterns from pattern matcher
                "proof_patterns": self._get_patterns_from_matcher("Payments Claim", "Payment Confirmation"),
                # Get payment details patterns from pattern matcher
                "details_patterns": self._get_patterns_from_matcher("Payments Claim", "Payment Details Received")
            },
            
            "Invoices Request": {
                # Get invoice request patterns from pattern matcher
                "request_patterns": self._get_patterns_from_matcher("Invoices Request", "Request (No Info)")
            }
        }

    def _initialize_noreply_patterns(self) -> None:
        """Initialize no-reply sender patterns and thread edge cases by REUSING existing patterns."""
        
        # NO-REPLY SENDER PATTERNS - Keep these simple ones here since they're sender-specific
        self.noreply_patterns = [
            r'noreply@', r'no-reply@', r'donotreply@', r'do-not-reply@',
            r'notifications@', r'system@', r'alerts@', r'automated@',
            r'support-noreply@', r'billing-noreply@'
        ]
        
        # REUSE EDGE CASE PATTERNS FROM NLP PROCESSOR
        self.thread_edge_patterns = {
            "out_of_office": self._get_nlp_patterns("Auto Reply", "OOO"),
            "no_reply_warnings": self._get_nlp_patterns("No Reply", "System"),
            "contact_changes": self._get_nlp_patterns("Auto Reply", "Contact Changes")
        }

    def _get_patterns_from_matcher(self, main_category: str, subcategory: str) -> List[str]:
        """Extract patterns from existing PatternMatcher to avoid duplication."""
        try:
            if hasattr(self.pattern_matcher, 'patterns') and main_category in self.pattern_matcher.patterns:
                if subcategory in self.pattern_matcher.patterns[main_category]:
                    # Convert regex patterns to simple strings for thread matching
                    patterns = self.pattern_matcher.patterns[main_category][subcategory]
                    # Remove regex word boundaries and convert to simple strings
                    simple_patterns = []
                    for pattern in patterns:
                        if isinstance(pattern, str):
                            # Remove regex syntax like \b and convert to simple string
                            clean_pattern = pattern.replace(r'\b', '').replace(r'.*', ' ').strip()
                            if clean_pattern:
                                simple_patterns.append(clean_pattern)
                    return simple_patterns
            return []
        except Exception as e:
            self.logger.warning(f"Could not extract patterns for {main_category}/{subcategory}: {e}")
            return []

    def _get_nlp_patterns(self, category_type: str, pattern_type: str) -> List[str]:
        """Extract patterns from NLP processor to avoid duplication."""
        try:
            if hasattr(self.nlp_processor, 'hierarchy_indicators'):
                # Map to actual NLP sublabel names
                nlp_mapping = {
                    ("Auto Reply", "OOO"): ["No Info/Autoreply", "Return Date Specified", "With Alternate Contact"],
                    ("No Reply", "System"): ["System Alerts", "Processing Errors"],
                    ("Auto Reply", "Contact Changes"): ["Redirects/Updates (property changes)"]
                }
                
                sublabels = nlp_mapping.get((category_type, pattern_type), [])
                all_patterns = []
                
                for sublabel in sublabels:
                    if sublabel in self.nlp_processor.hierarchy_indicators:
                        all_patterns.extend(self.nlp_processor.hierarchy_indicators[sublabel])
                
                return all_patterns
            return []
        except Exception as e:
            self.logger.warning(f"Could not extract NLP patterns for {category_type}/{pattern_type}: {e}")
            return []

    def classify_sublabel(
        self,
        main_category: str,
        text: str,
        analysis: Optional[TextAnalysis] = None,
        ml_result: Optional[Dict[str, Any]] = None,
        subject: str = "",
        had_threads: bool = False,
        has_attachments: bool = False,
        sender: str = ""
    ) -> RuleResult:
        """
        ENHANCED MAIN CLASSIFICATION WITH THREAD LOGIC
        Priority: Attachments → Thread Logic → Regular Classification
        """
        start_time = time.time()
        text_lower = text.lower().strip() if isinstance(text, str) else ""
        subject_lower = subject.lower().strip() if isinstance(subject, str) else ""
        sender_lower = sender.lower().strip() if isinstance(sender, str) else ""

        try:
            # Input validation
            if not text_lower and not subject_lower:
                return RuleResult("Uncategorized", "General", 0.1, "Empty input", ["empty_input"])

            # ==========================================
            # STEP 1: ATTACHMENT RULE (HIGHEST PRIORITY)
            # ==========================================
            if has_attachments:
                # Attachments go directly to Manual Review
                # Choose appropriate subcategory based on content
                if any(dispute in text_lower for dispute in ['dispute', 'owe nothing', 'contested']):
                    return RuleResult("Manual Review", "Partial/Disputed Payment", 0.95, 
                                    "Attachment + Dispute content", ["attachment_dispute"])
                elif any(invoice in text_lower for invoice in ['invoice', 'proof', 'documentation']):
                    return RuleResult("Manual Review", "Invoice Receipt", 0.95, 
                                    "Attachment + Invoice documentation", ["attachment_invoice"])
                elif any(payment in text_lower for payment in ['payment', 'paid', 'settlement']):
                    return RuleResult("Manual Review", "Complex Queries", 0.95, 
                                    "Attachment + Payment content", ["attachment_payment"])
                else:
                    return RuleResult("Manual Review", "Complex Queries", 0.95, 
                                    "Email with attachment", ["attachment_general"])

            # ==========================================
            # STEP 2: NO-REPLY SENDER CHECK
            # ==========================================
            if sender_lower and any(re.search(pattern, sender_lower) for pattern in self.noreply_patterns):
                # No-reply senders are usually system notifications
                if any(error in text_lower for error in ['error', 'failed', 'processing', 'delivery']):
                    return RuleResult("No Reply (with/without info)", "Processing Errors", 0.90,
                                    "No-reply sender + Error content", ["noreply_error"])
                elif any(ticket in text_lower for ticket in ['ticket', 'case', 'created', 'resolved']):
                    if any(word in text_lower for word in ['created', 'opened', 'new']):
                        return RuleResult("No Reply (with/without info)", "Created", 0.90,
                                        "No-reply sender + Ticket creation", ["noreply_ticket_created"])
                    elif any(word in text_lower for word in ['resolved', 'closed', 'completed']):
                        return RuleResult("No Reply (with/without info)", "Resolved", 0.90,
                                        "No-reply sender + Ticket resolved", ["noreply_ticket_resolved"])
                    else:
                        return RuleResult("No Reply (with/without info)", "Open", 0.85,
                                        "No-reply sender + Ticket update", ["noreply_ticket_open"])
                elif any(sale in text_lower for sale in ['offer', 'discount', 'sale', 'promotion']):
                    return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.90,
                                    "No-reply sender + Sales content", ["noreply_sales"])
                else:
                    return RuleResult("No Reply (with/without info)", "System Alerts", 0.85,
                                    "No-reply sender", ["noreply_system"])

            # ==========================================
            # STEP 3: THREAD LOGIC (CORE FEATURE)
            # ==========================================
            if had_threads:
                self.logger.info("🧵 Processing email with threads - applying thread logic")
                
                # 3A: Try MANUAL REVIEW patterns first (highest priority in threads)
                manual_result = self._classify_thread_manual_review(text_lower)
                if manual_result:
                    return manual_result
                
                # 3B: Try PAYMENTS CLAIM patterns (very common in threads)
                payment_result = self._classify_thread_payments(text_lower)
                if payment_result:
                    return payment_result
                
                # 3C: Try INVOICES REQUEST patterns (common in threads)
                invoice_result = self._classify_thread_invoices(text_lower)
                if invoice_result:
                    return invoice_result
                
                # 3D: Check thread edge cases (OOO, no-reply warnings in threads)
                edge_result = self._classify_thread_edge_cases(text_lower)
                if edge_result:
                    return edge_result
                
                # 3E: If thread doesn't match main 3 + edge cases, use regular classification
                # but with thread context boost
                self.logger.info("🧵 Thread email didn't match main patterns, using regular classification")

            # ==========================================
            # STEP 4: REGULAR CLASSIFICATION (EXISTING LOGIC)
            # ==========================================
            
            # 4A: HIGH-PRIORITY BUSINESS RULES
            regular_result = self._apply_regular_classification(text_lower, subject_lower)
            if regular_result:
                # If this was a thread email, add thread context to confidence
                if had_threads:
                    regular_result.confidence = min(regular_result.confidence + 0.05, 0.95)
                    regular_result.reason += " (thread context)"
                    regular_result.matched_rules.append("thread_context_boost")
                return regular_result

            # 4B: PATTERN MATCHER (Secondary Classification)
            if hasattr(self, 'pattern_matcher'):
                main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(text_lower)
                
                if main_cat and confidence >= 0.50:
                    if self._validate_hierarchy_match(main_cat, subcat):
                        # Thread context boost
                        if had_threads:
                            confidence = min(confidence + 0.05, 0.95)
                        return RuleResult(main_cat, subcat, confidence, f"Pattern: {subcat}", patterns)

            # 4C: NLP ANALYSIS (if available)
            if analysis and analysis.topics:
                nlp_result = self._classify_with_nlp_analysis(text_lower, analysis)
                if nlp_result:
                    # Thread context boost
                    if had_threads:
                        nlp_result.confidence = min(nlp_result.confidence + 0.05, 0.95)
                        nlp_result.reason += " (thread)"
                    return nlp_result

            # ==========================================
            # STEP 5: FALLBACK LOGIC
            # ==========================================
            return self._apply_fallback_logic(text_lower, had_threads)

        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return RuleResult("Manual Review", "Complex Queries", 0.30, f"Error: {e}", ["error_fallback"])

    def _classify_thread_manual_review(self, text: str) -> Optional[RuleResult]:
        """Classify thread emails for Manual Review category using EXISTING patterns."""
        
        patterns = self.thread_patterns["Manual Review"]
        
        # Use pattern matcher directly for better accuracy
        if hasattr(self.pattern_matcher, 'match_text'):
            main_cat, subcat, confidence, matched_patterns = self.pattern_matcher.match_text(text)
            
            # If pattern matcher found Manual Review with good confidence, use it
            if main_cat == "Manual Review" and confidence >= 0.70:
                return RuleResult("Manual Review", subcat, confidence + 0.10,  # Thread boost
                                f"Thread + Pattern: {subcat}", ["thread_pattern_match"] + matched_patterns)
        
        # Fallback: Simple pattern checking if pattern matcher didn't work
        dispute_matches = sum(1 for pattern in patterns.get("dispute_patterns", []) if pattern in text)
        if dispute_matches >= 1:
            confidence = min(0.85 + (dispute_matches * 0.02), 0.95)
            return RuleResult("Manual Review", "Partial/Disputed Payment", confidence,
                            "Thread: Dispute detected", ["thread_dispute"])
        
        invoice_proof_matches = sum(1 for pattern in patterns.get("invoice_proof_patterns", []) if pattern in text)
        if invoice_proof_matches >= 1:
            return RuleResult("Manual Review", "Invoice Receipt", 0.85,
                            "Thread: Invoice proof provided", ["thread_invoice_proof"])
        
        closure_matches = sum(1 for pattern in patterns.get("closure_patterns", []) if pattern in text)
        if closure_matches >= 1:
            if any(payment in text for payment in ['outstanding payment', 'payment due', 'owed']):
                return RuleResult("Manual Review", "Closure + Payment Due", 0.87,
                                "Thread: Closure with payment due", ["thread_closure_payment"])
            else:
                return RuleResult("Manual Review", "Closure Notification", 0.85,
                                "Thread: Business closure", ["thread_closure"])
        
        complex_matches = sum(1 for pattern in patterns.get("complex_patterns", []) if pattern in text)
        if complex_matches >= 1:
            return RuleResult("Manual Review", "Complex Queries", 0.82,
                            "Thread: Complex business content", ["thread_complex"])
        
        return None

    def _classify_thread_payments(self, text: str) -> Optional[RuleResult]:
        """Classify thread emails for Payments Claim category using ENHANCED patterns."""
        
        # ENHANCED: Add common payment-related phrases that are missed
        common_payment_claims = [
            # Past payment claims
            'already paid', 'payment was made', 'check was sent', 'we paid',
            'account paid', 'this was paid', 'been paid', 'payment completed',
            'paid this outstanding balance', 'has been paid', 'we have paid',
            'paid this', 'paid the', 'payment made', 'balance paid',
            
            # Payment verification requests
            'verify this has been paid', 'please verify', 'confirm payment',
            'check if paid', 'verify payment', 'confirm this has been paid',
            
            # Future payment intentions
            'will pay', 'i will pay', 'we will pay', 'going to pay',
            'can we do the first payment', 'payment this upcoming',
            'when can we pay', 'payment plan', 'issue a payment plan',
            'schedule payment', 'arrange payment', 'payment arrangement',
            
            # Payment questions/help
            'help me for payment', 'payment help', 'payment issue',
            'tried to pay', 'error when paying', 'payment error',
            'payment link error', 'cannot pay', 'trouble paying'
        ]
        
        # ENHANCED: Dispute/responsibility phrases (should go to Manual Review instead)
        dispute_responsibility_phrases = [
            'do not owe', 'not responsible', 'not our responsibility',
            'we don\'t owe', 'are not responsible', 'not liable',
            'unaware of this charge', 'researching this charge',
            'no record of', 'never received', 'dispute this'
        ]
        
        # Check for dispute/responsibility patterns FIRST (redirect to Manual Review)
        dispute_matches = sum(1 for pattern in dispute_responsibility_phrases if pattern in text)
        if dispute_matches >= 1:
            return RuleResult("Manual Review", "Partial/Disputed Payment", 0.90,
                            "Thread: Dispute/responsibility detected", ["thread_dispute_responsibility"])
        
        # Check for common payment patterns
        payment_matches = sum(1 for pattern in common_payment_claims if pattern in text)
        if payment_matches >= 1:
            # Determine subcategory based on context
            if any(proof in text for proof in ['receipt', 'confirmation', 'check number', 'transaction id', 'proof']):
                confidence = min(0.88 + (payment_matches * 0.02), 0.95)
                return RuleResult("Payments Claim", "Payment Confirmation", confidence,
                                "Thread: Payment proof provided", ["thread_payment_proof_enhanced"])
            elif any(future in text for future in ['will pay', 'going to pay', 'plan to pay', 'schedule', 'arrange']):
                confidence = min(0.85 + (payment_matches * 0.02), 0.92)
                return RuleResult("Payments Claim", "Payment Details Received", confidence,
                                "Thread: Future payment planned", ["thread_payment_future"])
            else:
                confidence = min(0.82 + (payment_matches * 0.02), 0.90)
                return RuleResult("Payments Claim", "Claims Paid (No Info)", confidence,
                                "Thread: Payment claim", ["thread_payment_claim_enhanced"])
        
        # Use pattern matcher directly for better accuracy
        if hasattr(self.pattern_matcher, 'match_text'):
            main_cat, subcat, confidence, matched_patterns = self.pattern_matcher.match_text(text)
            
            # If pattern matcher found Payments Claim with good confidence, use it
            if main_cat == "Payments Claim" and confidence >= 0.70:
                return RuleResult("Payments Claim", subcat, confidence + 0.10,  # Thread boost
                                f"Thread + Pattern: {subcat}", ["thread_pattern_match"] + matched_patterns)
        
        # Fallback: Use extracted patterns
        patterns = self.thread_patterns["Payments Claim"]
        
        proof_matches = sum(1 for pattern in patterns.get("proof_patterns", []) if pattern in text)
        if proof_matches >= 1:
            confidence = min(0.85 + (proof_matches * 0.02), 0.92)
            return RuleResult("Payments Claim", "Payment Confirmation", confidence,
                            "Thread: Payment proof provided", ["thread_payment_proof"])
        
        details_matches = sum(1 for pattern in patterns.get("details_patterns", []) if pattern in text)
        if details_matches >= 1:
            return RuleResult("Payments Claim", "Payment Details Received", 0.82,
                            "Thread: Payment details received", ["thread_payment_details"])
        
        claim_matches = sum(1 for pattern in patterns.get("claim_patterns", []) if pattern in text)
        if claim_matches >= 1:
            confidence = min(0.80 + (claim_matches * 0.02), 0.87)
            return RuleResult("Payments Claim", "Claims Paid (No Info)", confidence,
                            "Thread: Payment claim", ["thread_payment_claim"])
        
        return None

    def _classify_thread_invoices(self, text: str) -> Optional[RuleResult]:
        """Classify thread emails for Invoices Request category using EXISTING patterns."""
        
        # ENHANCED: Add common invoice request phrases that are missed
        common_invoice_requests = [
            'send a copy of the invoice', 'send copy of the invoice', 'send the invoice',
            'provide an invoice copy', 'provide invoice copy', 'copy of the invoice',
            'send me the invoice', 'need invoice copy', 'provide outstanding invoices',
            'copies of invoices', 'share invoice', 'forward invoice',
            'invoice request', 'need invoice documentation', 'send invoices',
            'invoice copy in pdf', 'copy of invoice', 'invoice that is due'
        ]
        
        # Check for common invoice request patterns FIRST
        invoice_request_matches = sum(1 for pattern in common_invoice_requests if pattern in text)
        if invoice_request_matches >= 1:
            # Make sure it's not providing proof (which would be Manual Review)
            if not any(proof in text for proof in ['attached', 'proof', 'documentation', 'receipt', 'was paid', 'see attached']):
                confidence = min(0.88 + (invoice_request_matches * 0.02), 0.95)
                return RuleResult("Invoices Request", "Request (No Info)", confidence,
                                "Thread: Invoice request detected", ["thread_invoice_request_enhanced"])
        
        # Use pattern matcher directly for better accuracy
        if hasattr(self.pattern_matcher, 'match_text'):
            main_cat, subcat, confidence, matched_patterns = self.pattern_matcher.match_text(text)
            
            # If pattern matcher found Invoices Request with good confidence, use it
            if main_cat == "Invoices Request" and confidence >= 0.70:
                return RuleResult("Invoices Request", subcat, confidence + 0.10,  # Thread boost
                                f"Thread + Pattern: {subcat}", ["thread_pattern_match"] + matched_patterns)
        
        # Fallback: Use extracted patterns
        patterns = self.thread_patterns["Invoices Request"]
        request_matches = sum(1 for pattern in patterns.get("request_patterns", []) if pattern in text)
        
        if request_matches >= 1:
            # Make sure it's not providing proof (which would be Manual Review)
            if not any(proof in text for proof in ['attached', 'proof', 'documentation', 'receipt']):
                confidence = min(0.82 + (request_matches * 0.02), 0.89)
                return RuleResult("Invoices Request", "Request (No Info)", confidence,
                                "Thread: Invoice request", ["thread_invoice_request"])
        
        return None

    def _classify_thread_edge_cases(self, text: str) -> Optional[RuleResult]:
        """Handle thread edge cases like OOO, no-reply warnings."""
        
        patterns = self.thread_edge_patterns
        
        # Out of office in threads
        ooo_matches = sum(1 for pattern in patterns["out_of_office"] if pattern in text)
        if ooo_matches >= 1:
            # Check for return date or contact info
            if any(date in text for date in ['return on', 'back on', 'returning', 'out until']):
                return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.85,
                                "Thread: OOO with return date", ["thread_ooo_date"])
            elif any(contact in text for contact in ['contact', 'reach', 'call', 'alternate']):
                return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.85,
                                "Thread: OOO with contact", ["thread_ooo_contact"])
            else:
                return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.80,
                                "Thread: Generic OOO", ["thread_ooo_generic"])
        
        # No-reply warnings in threads
        noreply_matches = sum(1 for pattern in patterns["no_reply_warnings"] if pattern in text)
        if noreply_matches >= 1:
            return RuleResult("No Reply (with/without info)", "System Alerts", 0.85,
                            "Thread: No-reply warning", ["thread_noreply_warning"])
        
        # Contact changes in threads
        contact_matches = sum(1 for pattern in patterns["contact_changes"] if pattern in text)
        if contact_matches >= 1:
            return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.85,
                            "Thread: Contact change", ["thread_contact_change"])
        
        return None

    def _apply_regular_classification(self, text: str, subject: str) -> Optional[RuleResult]:
        """Apply regular classification with CORRECT PRIORITY ORDER."""
        
        # PRIORITY 1: THREE MAIN THREAD LABELS (HIGHEST PRIORITY)
        
        # Manual Review
        dispute_phrases = [
            'formally disputing', 'dispute this debt', 'owe nothing', 'owe them nothing',
            'consider this a scam', 'billing is incorrect', 'cease and desist', 'fdcpa',
            'do not acknowledge', 'not our responsibility', 'contested payment', 'refuse payment',
            'we do not owe', 'are not responsible', 'unaware of this charge', 'researching this charge'
        ]
        if any(phrase in text for phrase in dispute_phrases):
            return RuleResult("Manual Review", "Partial/Disputed Payment", 0.95, "Dispute detected", ["dispute_rule"])

        invoice_proof_phrases = [
            'invoice receipt attached', 'proof of invoice attached', 'invoice copy attached',
            'invoice documentation attached', 'error payment proof', 'payment error documentation'
        ]
        if any(phrase in text for phrase in invoice_proof_phrases):
            return RuleResult("Manual Review", "Invoice Receipt", 0.90, "Invoice proof provided", ["invoice_proof_rule"])

        closure_phrases = ['business closed', 'filed bankruptcy', 'out of business', 'ceased operations']
        if any(phrase in text for phrase in closure_phrases):
            if any(payment in text for payment in ['outstanding payment', 'payment due', 'amount owed']):
                return RuleResult("Manual Review", "Closure + Payment Due", 0.90, "Closure with payment due", ["closure_payment_rule"])
            else:
                return RuleResult("Manual Review", "Closure Notification", 0.90, "Business closure", ["closure_rule"])

        # Payments Claim
        payment_proof_phrases = [
            'proof of payment', 'payment confirmation attached', 'check number', 'transaction id',
            'receipt attached', 'paid see attachments', 'here is proof of payment'
        ]
        if any(phrase in text for phrase in payment_proof_phrases):
            return RuleResult("Payments Claim", "Payment Confirmation", 0.90, "Payment proof provided", ["payment_proof_rule"])
        
        payment_details_phrases = [
            'payment will be sent', 'payment being processed', 'working on payment',
            'will pay the remainder', 'can we do the first payment', 'issue a payment plan',
            'help me for payment', 'tried to pay', 'payment error'
        ]
        if any(phrase in text for phrase in payment_details_phrases):
            return RuleResult("Payments Claim", "Payment Details Received", 0.85, "Payment details received", ["payment_details_rule"])
        
        payment_claim_phrases = [
            'already paid', 'payment was made', 'check was sent', 'account paid',
            'this was paid', 'has been paid', 'paid this outstanding balance',
            'verify this has been paid', 'please verify'
        ]
        if any(phrase in text for phrase in payment_claim_phrases):
            return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.85, "Payment claimed without proof", ["payment_claim_rule"])

        # Invoice Request
        invoice_request_phrases = [
            'send me the invoice', 'need invoice copy', 'provide outstanding invoices',
            'send a copy of the invoice', 'provide an invoice copy', 'copies of invoices',
            'invoice that is due', 'invoice copy in pdf'
        ]
        if any(phrase in text for phrase in invoice_request_phrases):
            if not any(proof in text for proof in ['paid', 'proof', 'attached', 'was paid']):
                return RuleResult("Invoices Request", "Request (No Info)", 0.85, "Invoice request", ["invoice_request_rule"])

        # PRIORITY 2: MANUAL REVIEW & OOO
        
        # Out of Office with Return Date
        return_date_phrases = [
            'return on monday', 'back on monday', 'returning on', 'out until', 'away until',
            'back on friday', 'return monday', 'back monday', 'return next week', 'back next week',
            'will be out of office monday', 'expected return date', 'back from vacation on'
        ]
        if any(phrase in text for phrase in return_date_phrases):
            if any(ooo in text for ooo in ['out of office', 'away from desk', 'automatic reply', 'auto-reply']):
                return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.90, 
                                "OOO with return date", ["ooo_return_date_rule"])
        
        # Out of Office with Contact Info
        contact_phrases = [
            'alternate contact', 'emergency contact', 'contact me at', 'reach me at',
            'for urgent matters contact', 'immediate assistance contact', 'call me at'
        ]
        if any(phrase in text for phrase in contact_phrases):
            if any(ooo in text for ooo in ['out of office', 'away from desk', 'automatic reply', 'auto-reply']):
                return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.90, 
                                "OOO with contact info", ["ooo_contact_rule"])
        
        # Generic Out of Office
        ooo_phrases = [
            'out of office', 'automatic reply', 'auto-reply', 'away from desk', 
            'currently out', 'limited access to email', 'temporarily unavailable'
        ]
        if any(phrase in text for phrase in ooo_phrases):
            business_terms = ['payment', 'invoice', 'dispute', 'collection', 'debt']
            business_count = sum(1 for term in business_terms if term in text)
            if business_count < 2:
                return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.85, 
                                "Generic OOO", ["ooo_generic_rule"])

        # PRIORITY 3: TICKET MANAGEMENT
        
        ticket_creation_phrases = [
            'ticket created', 'case opened', 'new ticket opened', 'support request created',
            'case number assigned', 'ticket submitted successfully', 'new case created'
        ]
        if any(phrase in text for phrase in ticket_creation_phrases):
            return RuleResult("No Reply (with/without info)", "Created", 0.85, "Ticket created", ["ticket_created_rule"])
        
        ticket_resolved_phrases = [
            'ticket resolved', 'case resolved', 'case closed', 'marked as resolved',
            'issue resolved', 'request completed', 'ticket has been resolved'
        ]
        if any(phrase in text for phrase in ticket_resolved_phrases):
            return RuleResult("No Reply (with/without info)", "Resolved", 0.85, "Ticket resolved", ["ticket_resolved_rule"])
        
        ticket_open_phrases = [
            'ticket open', 'case pending', 'under investigation', 'being processed', 'in progress'
        ]
        if any(phrase in text for phrase in ticket_open_phrases):
            return RuleResult("No Reply (with/without info)", "Open", 0.80, "Open ticket", ["ticket_open_rule"])

        # PRIORITY 4: SURVEY
        
        survey_phrases = ['survey', 'feedback request', 'rate our service', 'customer satisfaction']
        if any(phrase in text for phrase in survey_phrases):
            business_terms = ['payment', 'invoice', 'dispute', 'collection']
            if not any(business in text for business in business_terms):
                return RuleResult("Auto Reply (with/without info)", "Survey", 0.85, "Survey detected", ["survey_rule"])

        # PRIORITY 5: REMAINING LABELS
        
        # Contact Changes
        contact_change_phrases = [
            'no longer employed', 'contact changed', 'property manager changed',
            'please quit contacting', 'do not contact me further', 'contact information updated'
        ]
        if any(phrase in text for phrase in contact_change_phrases):
            return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.85, 
                            "Contact change", ["contact_change_rule"])

        # Processing Errors
        processing_phrases = [
            'processing error', 'failed to process', 'delivery failed', 'electronic invoice rejected',
            'system unable to process', 'cannot be processed'
        ]
        if any(phrase in text for phrase in processing_phrases):
            return RuleResult("No Reply (with/without info)", "Processing Errors", 0.85, "Processing error", ["processing_rule"])
        
        # Sales/Marketing
        sales_phrases = [
            'special offer', 'limited time offer', 'promotional offer', 'discount offer',
            'prices increasing', 'sale ending', 'payment plan options'
        ]
        if any(phrase in text for phrase in sales_phrases):
            return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.80, "Sales/marketing", ["sales_rule"])

        return None

    def _apply_fallback_logic(self, text: str, had_threads: bool) -> RuleResult:
        """Apply conservative fallback logic."""
        
        business_terms = ['payment', 'invoice', 'dispute', 'collection', 'debt', 'billing']
        business_count = sum(1 for term in business_terms if term in text)
        
        if business_count >= 2:
            confidence = 0.65 if had_threads else 0.60
            return RuleResult("Manual Review", "Complex Queries", confidence, 
                            "Multiple business terms", ["business_fallback"])
        elif business_count == 1:
            confidence = 0.60 if had_threads else 0.55
            if 'payment' in text:
                return RuleResult("Payments Claim", "Claims Paid (No Info)", confidence, 
                                "Payment term", ["payment_fallback"])
            elif 'invoice' in text:
                return RuleResult("Invoices Request", "Request (No Info)", confidence, 
                                "Invoice term", ["invoice_fallback"])
            else:
                return RuleResult("Manual Review", "Inquiry/Redirection", confidence, 
                                "Business term", ["business_term_fallback"])
        else:
            confidence = 0.55 if had_threads else 0.50
            return RuleResult("No Reply (with/without info)", "System Alerts", confidence, 
                            "General notification", ["general_fallback"])

    def _classify_with_nlp_analysis(self, text: str, analysis: TextAnalysis) -> Optional[RuleResult]:
        """NLP Analysis - same as before but with exact hierarchy names."""
        # [Previous NLP analysis code remains the same]
        try:
            for topic in analysis.topics:
                
                # MANUAL REVIEW TOPICS
                if topic == 'Partial/Disputed Payment':
                    return RuleResult("Manual Review", "Partial/Disputed Payment", 0.80, "NLP: Dispute", ["nlp_dispute"])
                elif topic == 'Invoice Receipt':
                    return RuleResult("Manual Review", "Invoice Receipt", 0.80, "NLP: Invoice proof", ["nlp_invoice_proof"])
                # ... [rest of NLP topics remain same]
                
            return None
        except Exception as e:
            self.logger.error(f"NLP analysis error: {e}")
            return None

    def _validate_hierarchy_match(self, main_cat: str, subcat: str) -> bool:
        """Validate that subcategory belongs to main category in hierarchy."""
        if main_cat not in self.hierarchy_structure:
            return False
        
        for group_name, subcategories in self.hierarchy_structure[main_cat].items():
            if subcat in subcategories:
                return True
        
        return False

    def get_thread_classification_stats(self) -> Dict[str, Any]:
        """Get statistics about thread classification patterns."""
        return {
            'thread_patterns_loaded': {
                'manual_review': len(self.thread_patterns["Manual Review"]),
                'payments_claim': len(self.thread_patterns["Payments Claim"]),
                'invoices_request': len(self.thread_patterns["Invoices Request"])
            },
            'noreply_patterns': len(self.noreply_patterns),
            'edge_case_patterns': len(self.thread_edge_patterns),
            'hierarchy_structure': {
                main_cat: len(groups) for main_cat, groups in self.hierarchy_structure.items()
            }
        }
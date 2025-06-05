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
        """Enhanced classification with improved thread logic and human vs automated detection."""
        
        start_time = time.time()
        text_lower = text.lower().strip() if isinstance(text, str) else ""
        subject_lower = subject.lower().strip() if isinstance(subject, str) else ""
        sender_lower = sender.lower().strip() if isinstance(sender, str) else ""

        try:
            if not text_lower and not subject_lower:
                return RuleResult("Uncategorized", "General", 0.1, "Empty input", ["empty_input"])

            if has_attachments:
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

            if sender_lower and any(re.search(pattern, sender_lower) for pattern in self.noreply_patterns):
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

            if had_threads:
                self.logger.info("🧵 Processing email with threads - applying enhanced thread logic")
                
                manual_result = self._classify_thread_manual_review(text_lower)
                if manual_result:
                    self.logger.info(f"🧵 Thread matched Manual Review: {manual_result.subcategory}")
                    return manual_result
                
                payment_result = self._classify_thread_payments(text_lower)
                if payment_result:
                    self.logger.info(f"🧵 Thread matched Payment: {payment_result.subcategory}")
                    return payment_result
                
                invoice_result = self._classify_thread_invoices(text_lower)
                if invoice_result:
                    self.logger.info(f"🧵 Thread matched Invoice: {invoice_result.subcategory}")
                    return invoice_result
                
                edge_result = self._classify_thread_edge_cases(text_lower)
                if edge_result:
                    self.logger.info(f"🧵 Thread matched Edge Case: {edge_result.subcategory}")
                    return edge_result
                
                self.logger.info("🧵 Thread email didn't match any thread patterns, using regular classification")

            regular_result = self._apply_regular_classification(text_lower, subject_lower, sender_lower)
            if regular_result:
                if had_threads:
                    regular_result.confidence = min(regular_result.confidence + 0.05, 0.95)
                    regular_result.reason += " (thread context)"
                    regular_result.matched_rules.append("thread_context_boost")
                return regular_result

            if hasattr(self, 'pattern_matcher'):
                main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(text_lower)
                
                if main_cat and confidence >= 0.50:
                    if self._validate_hierarchy_match(main_cat, subcat):
                        if had_threads:
                            confidence = min(confidence + 0.05, 0.95)
                        return RuleResult(main_cat, subcat, confidence, f"Pattern: {subcat}", patterns)

            if analysis and analysis.topics:
                nlp_result = self._classify_with_nlp_analysis(text_lower, analysis)
                if nlp_result:
                    if had_threads:
                        nlp_result.confidence = min(nlp_result.confidence + 0.05, 0.95)
                        nlp_result.reason += " (thread)"
                    return nlp_result

            return self._apply_fallback_logic(text_lower, had_threads)

        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return RuleResult("Manual Review", "Complex Queries", 0.30, f"Error: {e}", ["error_fallback"])

    def _classify_thread_manual_review(self, text: str) -> Optional[RuleResult]:
        """Classify thread emails for Manual Review category using NLP patterns."""
        
        # Use NLP hierarchy indicators for better pattern matching
        if hasattr(self.nlp_processor, 'hierarchy_indicators'):
            nlp_indicators = self.nlp_processor.hierarchy_indicators
            
            # Check dispute patterns from NLP
            if 'Partial/Disputed Payment' in nlp_indicators:
                dispute_matches = sum(1 for pattern in nlp_indicators['Partial/Disputed Payment'] if pattern in text)
                if dispute_matches >= 1:
                    confidence = min(0.85 + (dispute_matches * 0.02), 0.95)
                    return RuleResult("Manual Review", "Partial/Disputed Payment", confidence,
                                    "Thread: Dispute detected", ["thread_dispute"])
            
            # Check invoice receipt patterns from NLP
            if 'Invoice Receipt' in nlp_indicators:
                invoice_matches = sum(1 for pattern in nlp_indicators['Invoice Receipt'] if pattern in text)
                if invoice_matches >= 1:
                    return RuleResult("Manual Review", "Invoice Receipt", 0.85,
                                    "Thread: Invoice proof provided", ["thread_invoice_proof"])
            
            # Check closure patterns from NLP
            if 'Closure Notification' in nlp_indicators:
                closure_matches = sum(1 for pattern in nlp_indicators['Closure Notification'] if pattern in text)
                if closure_matches >= 1:
                    if any(payment in text for payment in ['outstanding payment', 'payment due', 'owed']):
                        return RuleResult("Manual Review", "Closure + Payment Due", 0.87,
                                        "Thread: Closure with payment due", ["thread_closure_payment"])
                    else:
                        return RuleResult("Manual Review", "Closure Notification", 0.85,
                                        "Thread: Business closure", ["thread_closure"])
            
            # Check complex queries patterns from NLP
            if 'Complex Queries' in nlp_indicators:
                complex_matches = sum(1 for pattern in nlp_indicators['Complex Queries'] if pattern in text)
                if complex_matches >= 1:
                    return RuleResult("Manual Review", "Complex Queries", 0.82,
                                    "Thread: Complex business content", ["thread_complex"])
            
            # Check inquiry/redirection patterns from NLP
            if 'Inquiry/Redirection' in nlp_indicators:
                inquiry_matches = sum(1 for pattern in nlp_indicators['Inquiry/Redirection'] if pattern in text)
                if inquiry_matches >= 1:
                    return RuleResult("Manual Review", "Inquiry/Redirection", 0.80,
                                    "Thread: Inquiry/redirection", ["thread_inquiry"])
        
        # Use pattern matcher as fallback
        if hasattr(self.pattern_matcher, 'match_text'):
            main_cat, subcat, confidence, matched_patterns = self.pattern_matcher.match_text(text)
            
            if main_cat == "Manual Review" and confidence >= 0.70:
                return RuleResult("Manual Review", subcat, confidence + 0.10,
                                f"Thread + Pattern: {subcat}", ["thread_pattern_match"] + matched_patterns)
        
        # Fallback: Use extracted patterns
        patterns = self.thread_patterns.get("Manual Review", {})
        
        dispute_matches = sum(1 for pattern in patterns.get("dispute_patterns", []) if pattern in text)
        if dispute_matches >= 1:
            confidence = min(0.85 + (dispute_matches * 0.02), 0.95)
            return RuleResult("Manual Review", "Partial/Disputed Payment", confidence,
                            "Thread: Dispute detected", ["thread_dispute"])
        
        return None

    def _classify_thread_payments(self, text: str) -> Optional[RuleResult]:
        """Classify thread emails for Payments Claim category using NLP patterns."""
        
        # First check NLP patterns for disputes (redirect to Manual Review)
        if hasattr(self.nlp_processor, 'hierarchy_indicators'):
            nlp_indicators = self.nlp_processor.hierarchy_indicators
            
            if 'Partial/Disputed Payment' in nlp_indicators:
                dispute_matches = sum(1 for pattern in nlp_indicators['Partial/Disputed Payment'] if pattern in text)
                if dispute_matches >= 1:
                    return RuleResult("Manual Review", "Partial/Disputed Payment", 0.90,
                                    "Thread: Dispute/responsibility detected", ["thread_dispute_responsibility"])
            
            # Check payment confirmation patterns from NLP
            if 'Payment Confirmation' in nlp_indicators:
                proof_matches = sum(1 for pattern in nlp_indicators['Payment Confirmation'] if pattern in text)
                if proof_matches >= 1:
                    confidence = min(0.88 + (proof_matches * 0.02), 0.95)
                    return RuleResult("Payments Claim", "Payment Confirmation", confidence,
                                    "Thread: Payment proof provided", ["thread_payment_proof_enhanced"])
            
            # Check payment details patterns from NLP
            if 'Payment Details Received' in nlp_indicators:
                details_matches = sum(1 for pattern in nlp_indicators['Payment Details Received'] if pattern in text)
                if details_matches >= 1:
                    confidence = min(0.85 + (details_matches * 0.02), 0.92)
                    return RuleResult("Payments Claim", "Payment Details Received", confidence,
                                    "Thread: Future payment planned", ["thread_payment_future"])
            
            # Check past payment claims from NLP
            if 'Claims Paid (No Info)' in nlp_indicators:
                claim_matches = sum(1 for pattern in nlp_indicators['Claims Paid (No Info)'] if pattern in text)
                if claim_matches >= 1:
                    confidence = min(0.82 + (claim_matches * 0.02), 0.90)
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", confidence,
                                    "Thread: Payment claim without proof", ["thread_payment_claim_enhanced"])
        
        # Use pattern matcher as fallback
        if hasattr(self.pattern_matcher, 'match_text'):
            main_cat, subcat, confidence, matched_patterns = self.pattern_matcher.match_text(text)
            
            if main_cat == "Payments Claim" and confidence >= 0.70:
                return RuleResult("Payments Claim", subcat, confidence + 0.10,
                                f"Thread + Pattern: {subcat}", ["thread_pattern_match"] + matched_patterns)
        
        # Enhanced patterns for specific cases
        dispute_responsibility_phrases = [
            'do not owe', 'not responsible', 'not our responsibility', 'we don\'t owe', 
            'are not responsible', 'not liable', 'dispute this', 'disputing this',
            'formally disputing', 'dispute this debt', 'contested payment', 'refuse payment',
            'unaware of this charge', 'researching this charge', 'no record of any charge',
            'no record of', 'never received', 'havent done business with', 'haven\'t done business',
            'dont have record', 'don\'t have record', 'unaware of', 'no knowledge of',
            'error on your end', 'this is an error', 'write off this amount', 'write off amount',
            'billing error', 'incorrect charge', 'mistake on', 'charge is bogus', 'bogus charge',
            'looks like a scam', 'consider this a scam', 'this seems like a scam'
        ]
        
        past_payment_claims = [
            'already paid', 'payment was made', 'check was sent', 'we paid', 'account paid',
            'this was paid', 'been paid', 'payment completed', 'paid this outstanding balance',
            'has been paid', 'we have paid', 'paid this', 'paid the', 'payment made', 'balance paid',
            'account was paid', 'invoice was paid', 'bill was paid', 'check mailed',
            'payment sent', 'paid in full', 'settled this account', 'cleared this balance'
        ]
        
        future_payment_phrases = [
            'will pay', 'will make payment', 'going to pay', 'plan to pay', 'intend to pay',
            'we will pay', 'i will pay', 'planning to pay', 'will send payment',
            'payment will be sent', 'payment being processed', 'working on payment',
            'payment scheduled', 'schedule payment', 'arrange payment', 'payment arrangement',
            'payment this upcoming', 'payment next week', 'payment from next week',
            'make payment next', 'can we do the first payment', 'first payment this',
            'issue a payment plan', 'payment plan', 'installment plan', 'when can we pay',
            'payment awaiting', 'payment is awaiting', 'waiting for payment information',
            'will issue payment', 'processing payment', 'payment in process'
        ]
        
        payment_proof_indicators = [
            'receipt', 'confirmation', 'check number', 'transaction id', 'proof of payment',
            'payment confirmation', 'eft#', 'wire confirmation', 'batch number', 'reference number',
            'payment receipt', 'proof attached', 'confirmation attached', 'receipt attached',
            'bank confirmation', 'transfer confirmation', 'payment verification'
        ]
        
        # Check for dispute/responsibility patterns FIRST
        dispute_matches = sum(1 for pattern in dispute_responsibility_phrases if pattern in text)
        if dispute_matches >= 1:
            return RuleResult("Manual Review", "Partial/Disputed Payment", 0.90,
                            "Thread: Dispute/responsibility detected", ["thread_dispute_responsibility"])
        
        # Check for future payment patterns
        future_matches = sum(1 for pattern in future_payment_phrases if pattern in text)
        if future_matches >= 1:
            confidence = min(0.88 + (future_matches * 0.02), 0.95)
            return RuleResult("Payments Claim", "Payment Details Received", confidence,
                            "Thread: Future payment planned", ["thread_payment_future"])
        
        # Check for past payment claims with proof
        past_matches = sum(1 for pattern in past_payment_claims if pattern in text)
        if past_matches >= 1:
            proof_indicators = sum(1 for pattern in payment_proof_indicators if pattern in text)
            
            if proof_indicators >= 1:
                confidence = min(0.90 + (proof_indicators * 0.02), 0.95)
                return RuleResult("Payments Claim", "Payment Confirmation", confidence,
                                "Thread: Payment proof provided", ["thread_payment_proof_enhanced"])
            else:
                confidence = min(0.82 + (past_matches * 0.02), 0.90)
                return RuleResult("Payments Claim", "Claims Paid (No Info)", confidence,
                                "Thread: Payment claim without proof", ["thread_payment_claim_enhanced"])
        
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
        """Handle thread edge cases using NLP patterns."""
        
        # Use NLP hierarchy indicators for better pattern matching
        if hasattr(self.nlp_processor, 'hierarchy_indicators'):
            nlp_indicators = self.nlp_processor.hierarchy_indicators
            
            # Check return date specified patterns from NLP
            if 'Return Date Specified' in nlp_indicators:
                return_matches = sum(1 for pattern in nlp_indicators['Return Date Specified'] if pattern in text)
                if return_matches >= 1:
                    return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.85,
                                    "Thread: OOO with return date", ["thread_ooo_date"])
            
            # Check alternate contact patterns from NLP
            if 'With Alternate Contact' in nlp_indicators:
                contact_matches = sum(1 for pattern in nlp_indicators['With Alternate Contact'] if pattern in text)
                if contact_matches >= 1:
                    return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.85,
                                    "Thread: OOO with contact", ["thread_ooo_contact"])
            
            # Check generic OOO patterns from NLP
            if 'No Info/Autoreply' in nlp_indicators:
                ooo_matches = sum(1 for pattern in nlp_indicators['No Info/Autoreply'] if pattern in text)
                if ooo_matches >= 1:
                    return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.80,
                                    "Thread: Generic OOO", ["thread_ooo_generic"])
            
            # Check contact changes patterns from NLP
            if 'Redirects/Updates (property changes)' in nlp_indicators:
                redirect_matches = sum(1 for pattern in nlp_indicators['Redirects/Updates (property changes)'] if pattern in text)
                if redirect_matches >= 1:
                    return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.85,
                                    "Thread: Contact change", ["thread_contact_change"])
            
            # Check system alerts patterns from NLP
            if 'System Alerts' in nlp_indicators:
                alert_matches = sum(1 for pattern in nlp_indicators['System Alerts'] if pattern in text)
                if alert_matches >= 1:
                    return RuleResult("No Reply (with/without info)", "System Alerts", 0.85,
                                    "Thread: No-reply warning", ["thread_noreply_warning"])
        
        # Fallback: Use extracted patterns
        patterns = self.thread_edge_patterns
        
        ooo_matches = sum(1 for pattern in patterns.get("out_of_office", []) if pattern in text)
        if ooo_matches >= 1:
            if any(date in text for date in ['return on', 'back on', 'returning', 'out until']):
                return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.85,
                                "Thread: OOO with return date", ["thread_ooo_date"])
            elif any(contact in text for contact in ['contact', 'reach', 'call', 'alternate']):
                return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.85,
                                "Thread: OOO with contact", ["thread_ooo_contact"])
            else:
                return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.80,
                                "Thread: Generic OOO", ["thread_ooo_generic"])
        
        return None


    # ADD THIS NEW METHOD TO rule_engine.py
    def _detect_email_type(self, text: str, subject: str, sender: str = "") -> str:
        """
        Detect if email is human-written vs automated/system generated.
        Returns: 'human', 'automated', 'mixed'
        """
        text_lower = text.lower()
        subject_lower = subject.lower()
        sender_lower = sender.lower()
        
        # AUTOMATED/SYSTEM EMAIL INDICATORS
        automated_indicators = [
            # System notifications
            'your request has been received', 'ticket has been created', 'case has been opened',
            'automated notification', 'system notification', 'do not reply to this email',
            'this is an automated', 'automatically generated', 'system generated',
            
            # Ticket/Case management
            'ticket id', 'case number', 'reference number', 'your ticket', 'case id',
            'ticket created', 'case opened', 'support request created',
            
            # Standard acknowledgments
            'we will get back to you', 'member of our team will', 'will investigate and get back',
            'within the next.*business days', 'thank you for contacting', 'thanks for reaching out',
            
            # System responses
            'knowledge base', 'self-help articles', 'visit our website', 'for more information visit',
            'powered by', 'this email was sent from', 'unsubscribe', 'manage preferences'
        ]
        
        # HUMAN COMMUNICATION INDICATORS
        human_indicators = [
            # Personal pronouns and direct communication
            'i am at a loss', 'i received this message', 'i did not work', 'i\'m not sure',
            'unfortunately it is not me', 'i don\'t know', 'i have issues', 'i cannot',
            
            # Questions and requests
            'why don\'t you call me', 'can you help', 'please let me know', 'when you have received',
            'issues logging in', 'having trouble', 'need help with', 'problem with',
            
            # Personal context
            'my name is', 'i work for', 'i represent', 'our company', 'we work with',
            'i am the', 'my role is', 'i handle', 'i manage', 'i oversee',
            
            # Emotional language
            'frustrated', 'confused', 'disappointed', 'concerned', 'worried',
            'at a loss', 'don\'t understand', 'unclear about'
        ]
        
        # COUNT INDICATORS
        automated_count = sum(1 for indicator in automated_indicators if indicator in text_lower)
        human_count = sum(1 for indicator in human_indicators if indicator in text_lower)
        
        # SENDER ANALYSIS
        automated_senders = [
            'noreply', 'no-reply', 'donotreply', 'support@', 'notifications@',
            'system@', 'automated@', 'bot@', 'service@', 'help@'
        ]
        is_automated_sender = any(pattern in sender_lower for pattern in automated_senders)
        
        # SUBJECT ANALYSIS
        automated_subjects = [
            'ticket', 'case', 'notification', 'alert', 'automated', 'system',
            'do not reply', 'confirmation', 'receipt', 'acknowledgment'
        ]
        has_automated_subject = any(pattern in subject_lower for pattern in automated_subjects)
        
        # DECISION LOGIC
        if automated_count >= 2 or is_automated_sender or has_automated_subject:
            if human_count >= 2:
                return 'mixed'
            return 'automated'
        elif human_count >= 1:
            return 'human'
        else:
            return 'mixed'

    def _apply_regular_classification(self, text: str, subject: str, sender: str = "") -> Optional[RuleResult]: 
        """Apply regular classification with FIXED PRIORITY ORDER."""

        email_type = self._detect_email_type(text, subject, sender)

        # STEP 1: SYSTEM/AUTOMATED EMAIL PATTERNS (HIGH PRIORITY)
        if email_type == 'automated':
            # System ticket notifications
            if any(phrase in text.lower() for phrase in [
                'ticket has been created', 'case has been opened', 'your request has been received',
                'ticket id', 'case number', 'support request created', 'member of our team will'
            ]):
                return RuleResult("No Reply (with/without info)", "Created", 0.90, 
                                "Automated ticket notification", ["automated_ticket_rule"])
            
            # System acknowledgments with info
            if any(phrase in text.lower() for phrase in [
                'knowledge base', 'self-help articles', 'within.*business days',
                'will investigate and get back', 'team will contact you'
            ]):
                return RuleResult("No Reply (with/without info)", "System Alerts", 0.85,
                                "Automated acknowledgment with info", ["automated_ack_rule"])

        # STEP 2: HUMAN INQUIRY PATTERNS (HIGH PRIORITY)
        elif email_type == 'human':
            # Technical issues/problems
            if any(phrase in text.lower() for phrase in [
                'issues logging in', 'having trouble', 'cannot log in', 'problem with',
                'not working', 'error when', 'unable to access', 'login issues'
            ]):
                return RuleResult("Manual Review", "Inquiry/Redirection", 0.85,
                                "Human technical inquiry", ["human_tech_issue_rule"])
            
            # Contact/redirection requests
            if any(phrase in text.lower() for phrase in [
                'i did not work for', 'not sure who your contact should be', 'unfortunately it is not me',
                'i am not the right person', 'please contact someone else', 'wrong person'
            ]):
                return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.85,
                                "Human contact redirection", ["human_redirect_rule"])
            
            # Human requests for action/response
            if any(phrase in text.lower() for phrase in [
                'why don\'t you call me', 'please call me', 'need you to contact me',
                'please let me know when', 'at a loss as to why', 'don\'t understand why'
            ]):
                return RuleResult("Manual Review", "Inquiry/Redirection", 0.85,
                                "Human request for contact", ["human_contact_request_rule"])

        # STEP 3: BUSINESS CONTENT DETECTION (HIGHEST PRIORITY FOR BUSINESS TERMS)
        
        # INVOICE REQUESTS (MUST COME BEFORE OOO DETECTION)
        invoice_request_phrases = [
            'send me the invoice', 'need invoice copy', 'provide outstanding invoices',
            'send a copy of the invoice', 'provide an invoice copy', 'copies of invoices',
            'invoice that is due', 'invoice copy in pdf', 'send invoice copy',
            'forward invoice', 'share invoice', 'invoice documentation',
            # CRITICAL: Add the missing pattern from your example
            'please share the invoice copy', 'share the invoice copy', 'provide invoice copy'
        ]
        if any(phrase in text.lower() for phrase in invoice_request_phrases):
            # Make sure it's not providing proof (which would be Manual Review)
            if not any(proof in text.lower() for proof in ['paid', 'proof', 'attached', 'was paid', 'receipt']):
                return RuleResult("Invoices Request", "Request (No Info)", 0.90,
                                "Invoice request detected", ["invoice_request_rule"])

        # DISPUTES (HIGHEST PRIORITY)
        dispute_phrases = [
            'formally disputing', 'dispute this debt', 'owe nothing', 'owe them nothing',
            'consider this a scam', 'billing is incorrect', 'cease and desist', 'fdcpa',
            'do not acknowledge', 'not our responsibility', 'contested payment', 'refuse payment',
            'we do not owe', 'are not responsible', 'we don\'t owe', 'not liable',
            'unaware of this charge', 'researching this charge', 'no record of any charge',
            'havent done business with', 'haven\'t done business', 'error on your end',
            'this is an error', 'write off this amount', 'charge is bogus', 'bogus charge',
            'dont have record', 'don\'t have record', 'never received invoice', 'no knowledge of'
        ]
        if any(phrase in text.lower() for phrase in dispute_phrases):
            return RuleResult("Manual Review", "Partial/Disputed Payment", 0.95, 
                            "Dispute detected", ["dispute_rule"])

        # PAYMENT CLASSIFICATION (HIGH PRIORITY)
        
        # Payment proof patterns
        payment_proof_phrases = [
            'proof of payment', 'payment confirmation attached', 'check number', 'transaction id',
            'receipt attached', 'paid see attachments', 'here is proof of payment',
            'payment receipt', 'confirmation attached', 'eft#', 'wire confirmation',
            'batch number', 'reference number', 'bank confirmation'
        ]
        if any(phrase in text.lower() for phrase in payment_proof_phrases):
            return RuleResult("Payments Claim", "Payment Confirmation", 0.90, 
                            "Payment proof provided", ["payment_proof_rule"])
        
        # Future payment patterns
        payment_details_phrases = [
            'payment will be sent', 'payment being processed', 'working on payment',
            'will pay the remainder', 'can we do the first payment', 'issue a payment plan',
            'help me for payment', 'tried to pay', 'payment error',
            'will make payment', 'will pay', 'going to pay', 'plan to pay', 'payment next week',
            'payment this upcoming', 'make payment from next week', 'payment scheduled',
            'schedule payment', 'arrange payment', 'payment arrangement', 'payment awaiting',
            'payment is awaiting', 'when can we pay', 'payment plan', 'installment plan'
        ]
        if any(phrase in text.lower() for phrase in payment_details_phrases):
            return RuleResult("Payments Claim", "Payment Details Received", 0.85, 
                            "Payment details received", ["payment_details_rule"])
        
        # Past payment claims
        payment_claim_phrases = [
            'already paid', 'payment was made', 'check was sent', 'account paid',
            'this was paid', 'has been paid', 'paid this outstanding balance',
            'verify this has been paid', 'please verify', 'we paid', 'been paid',
            'payment completed', 'account was paid', 'invoice was paid', 'bill was paid'
        ]
        if any(phrase in text.lower() for phrase in payment_claim_phrases):
            return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.85, 
                            "Payment claimed without proof", ["payment_claim_rule"])

        # BUSINESS CLOSURE
        closure_phrases = [
            'business closed', 'filed bankruptcy', 'out of business', 'ceased operations',
            'company closed', 'permanently closed', 'filing for bankruptcy', 'bankruptcy protection',
            'chapter 7', 'chapter 11', 'business shutting down', 'liquidated', 'dissolved'
        ]
        if any(phrase in text.lower() for phrase in closure_phrases):
            if any(payment in text.lower() for payment in ['outstanding payment', 'payment due', 'amount owed', 'balance due']):
                return RuleResult("Manual Review", "Closure + Payment Due", 0.90, 
                                "Closure with payment due", ["closure_payment_rule"])
            else:
                return RuleResult("Manual Review", "Closure Notification", 0.90, 
                                "Business closure", ["closure_rule"])

        # STEP 4: OUT OF OFFICE DETECTION (LOWER PRIORITY - MOVED DOWN)
        
        # Enhanced OOO detection - check subject first
        subject_ooo_indicators = ['automatic reply', 'auto reply', 'out of office', 'ooo']
        has_ooo_subject = any(indicator in subject.lower() for indicator in subject_ooo_indicators)
        
        # Enhanced OOO phrases
        ooo_phrases = [
            'out of office', 'automatic reply', 'auto-reply', 'auto reply', 'away from desk',
            'currently out', 'limited access to email', 'temporarily unavailable',
            'away from office', 'out of the office', 'currently unavailable',
            'attending meetings', 'attending company meetings', 'offsite', 'away until',
            'will be out', 'i will be out', 'currently attending', 'away from email'
        ]
        
        has_ooo_content = any(phrase in text.lower() for phrase in ooo_phrases)
        
        # CRITICAL: Only classify as OOO if NO BUSINESS CONTENT is present
        business_terms = ['payment', 'invoice', 'dispute', 'collection', 'debt', 'billing']
        business_count = sum(1 for term in business_terms if term in text.lower())
        
        if (has_ooo_subject or has_ooo_content) and business_count == 0:
            # Check for return date patterns
            return_date_phrases = [
                'return on', 'back on', 'returning on', 'out until', 'away until',
                'return monday', 'back monday', 'return next week', 'back next week',
                'will be back', 'expected return', 'back from vacation', 'return after',
                'out from.*to', 'away from.*to', 'until.*return', 'back.*on'
            ]
            
            # Check for contact info patterns
            contact_phrases = [
                'contact me at', 'reach me at', 'call me at', 'text me at',
                'alternate contact', 'emergency contact', 'for urgent matters contact',
                'immediate assistance contact', 'urgent.*contact', 'please contact',
                'phone number', 'cell phone', 'mobile phone', 'direct line'
            ]
            
            # Enhanced return date detection
            has_return_date = any(phrase in text.lower() for phrase in return_date_phrases)
            # Enhanced contact detection  
            has_contact_info = any(phrase in text.lower() for phrase in contact_phrases)
            
            # Also check for phone numbers or email addresses as contact indicators
            import re
            phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            has_phone = bool(re.search(phone_pattern, text))
            has_email_contact = bool(re.search(email_pattern, text))
            
            # Determine OOO subcategory
            if has_return_date:
                return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.90,
                                "OOO with return date", ["ooo_return_date_rule"])
            elif has_contact_info or has_phone or has_email_contact:
                return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.90,
                                "OOO with contact info", ["ooo_contact_rule"])
            else:
                return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.85,
                                "Generic OOO", ["ooo_generic_rule"])

        # STEP 5: TICKET MANAGEMENT
        
        ticket_creation_phrases = [
            'ticket created', 'case opened', 'new ticket opened', 'support request created',
            'case number assigned', 'ticket submitted successfully', 'new case created',
            'case has been created', 'ticket logged', 'case logged'
        ]
        if any(phrase in text.lower() for phrase in ticket_creation_phrases):
            return RuleResult("No Reply (with/without info)", "Created", 0.85, 
                            "Ticket created", ["ticket_created_rule"])
        
        ticket_resolved_phrases = [
            'ticket resolved', 'case resolved', 'case closed', 'marked as resolved',
            'issue resolved', 'request completed', 'ticket has been resolved',
            'case completed', 'ticket closed', 'resolved successfully'
        ]
        if any(phrase in text.lower() for phrase in ticket_resolved_phrases):
            return RuleResult("No Reply (with/without info)", "Resolved", 0.85, 
                            "Ticket resolved", ["ticket_resolved_rule"])
        
        ticket_open_phrases = [
            'ticket open', 'case pending', 'under investigation', 'being processed', 'in progress',
            'case open', 'still pending', 'awaiting response', 'under review'
        ]
        if any(phrase in text.lower() for phrase in ticket_open_phrases):
            return RuleResult("No Reply (with/without info)", "Open", 0.80, 
                            "Open ticket", ["ticket_open_rule"])

        # STEP 6: PROCESSING ERRORS
        
        processing_phrases = [
            'processing error', 'failed to process', 'delivery failed', 'electronic invoice rejected',
            'system unable to process', 'cannot be processed', 'email bounced', 'delivery failure',
            'processing failed', 'system error', 'unable to import', 'import failed'
        ]
        if any(phrase in text.lower() for phrase in processing_phrases):
            return RuleResult("No Reply (with/without info)", "Processing Errors", 0.85, 
                            "Processing error", ["processing_rule"])

        # STEP 7: SURVEYS AND CONTACT CHANGES
        
        survey_phrases = ['survey', 'feedback request', 'rate our service', 'customer satisfaction',
                        'take our survey', 'service evaluation', 'your feedback']
        if any(phrase in text.lower() for phrase in survey_phrases):
            business_terms = ['payment', 'invoice', 'dispute', 'collection']
            if not any(business in text.lower() for business in business_terms):
                return RuleResult("Auto Reply (with/without info)", "Survey", 0.85, 
                                "Survey detected", ["survey_rule"])

        contact_change_phrases = [
            'no longer employed', 'contact changed', 'property manager changed',
            'please quit contacting', 'do not contact me further', 'contact information updated',
            'no longer with', 'no longer affiliated', 'please remove me', 'unsubscribe'
        ]
        if any(phrase in text.lower() for phrase in contact_change_phrases):
            return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.85,
                            "Contact change", ["contact_change_rule"])
        
        # STEP 8: SALES/MARKETING
        
        sales_phrases = [
            'special offer', 'limited time offer', 'promotional offer', 'discount offer',
            'prices increasing', 'sale ending', 'payment plan options', 'exclusive deal',
            'pricing', 'promotion', 'marketing', 'sales representative'
        ]
        if any(phrase in text.lower() for phrase in sales_phrases):
            return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.80, 
                            "Sales/marketing", ["sales_rule"])

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
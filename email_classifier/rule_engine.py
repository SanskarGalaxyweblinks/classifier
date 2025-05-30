"""
Clean rule engine for email classification with performance and error handling improvements.
"""

import logging
import time
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from functools import lru_cache
import re

# Import existing components with correct paths
from .patterns import PatternMatcher
from .nlp_utils import TextAnalysis, NLPProcessor

logger = logging.getLogger(__name__)

# Custom Exception Types
class RuleEngineError(Exception):
    """Base exception for rule engine errors."""
    pass

class PatternValidationError(RuleEngineError):
    """Exception for pattern validation issues."""
    pass

class ClassificationError(RuleEngineError):
    """Exception for classification processing errors."""
    pass

@dataclass
class RuleResult:
    category: str
    subcategory: str
    confidence: float
    reason: str
    matched_rules: list

@dataclass 
class PerformanceMetrics:
    total_processed: int = 0
    successful_classifications: int = 0
    errors: int = 0
    avg_processing_time: float = 0.0
    pattern_cache_hits: int = 0
    pattern_cache_misses: int = 0

class RuleEngine:
    """
    Enhanced rule engine with NLP integration and performance optimization.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize pattern matcher
        try:
            self.pattern_matcher = PatternMatcher()
        except Exception as e:
            raise RuleEngineError(f"Failed to initialize pattern matcher: {e}")
        
        # Initialize NLP processor
        try:
            self.nlp_processor = NLPProcessor()
        except Exception as e:
            self.logger.warning(f"Failed to initialize NLP processor: {e}")
            self.nlp_processor = None
        
        # Performance metrics tracking
        self.metrics = PerformanceMetrics()
        
        # Pattern cache for performance
        self._pattern_cache = {}
        
        # Thread keywords for specific routing
        self.thread_payment_keywords = [
            "has been paid", "already paid", "payment made", "check sent", "paid through", 
            "payment completed", "payment sent", "check is being overnighted", "we paid",
            "this have already been paid", "account has been paid in full", "this has been paid",
            "paid in full", "payment was made", "payment is done", "we have paid", "settled"
        ]

        self.thread_invoice_keywords = [
            "invoice copies", "send invoice", "provide invoice", "need invoice",
            "invoice request", "share invoice", "invoice documentation",
            "invoices", "all invoices", "copies of invoices", "past due invoices", "all invoices due", "multiple invoices"
        ]

        # Validate patterns on initialization
        self._validate_patterns()
        
        self.logger.info("✅ Enhanced RuleEngine initialized with NLP integration")

    def _validate_patterns(self) -> None:
        """Validate all patterns for correctness."""
        try:
            validation_errors = []
            
            # Test thread keywords
            for keyword in self.thread_payment_keywords + self.thread_invoice_keywords:
                if not isinstance(keyword, str) or len(keyword.strip()) == 0:
                    validation_errors.append(f"Invalid thread keyword: {keyword}")
            
            # Test pattern matcher
            if hasattr(self.pattern_matcher, 'patterns'):
                for category, subcategories in self.pattern_matcher.patterns.items():
                    for subcategory, patterns in subcategories.items():
                        for pattern in patterns:
                            try:
                                re.compile(pattern, re.IGNORECASE)
                            except re.error as e:
                                validation_errors.append(f"Invalid regex pattern in {category}/{subcategory}: {pattern} - {e}")
            
            if validation_errors:
                error_msg = f"Pattern validation failed: {'; '.join(validation_errors[:5])}"
                if len(validation_errors) > 5:
                    error_msg += f" and {len(validation_errors) - 5} more errors"
                raise PatternValidationError(error_msg)
                
            self.logger.info(f"✅ Pattern validation successful")
            
        except Exception as e:
            if isinstance(e, PatternValidationError):
                raise
            raise PatternValidationError(f"Pattern validation error: {e}")

    @lru_cache(maxsize=1000)
    def _cached_pattern_match(self, text_hash: str, text: str) -> tuple:
        """Cached pattern matching for performance."""
        try:
            self.metrics.pattern_cache_misses += 1
            result = self.pattern_matcher.match_text(text)
            return result
        except Exception as e:
            self.logger.error(f"❌ Cached pattern match error: {e}")
            return None, None, 0.0, []

    def _get_text_hash(self, text: str) -> str:
        """Generate hash for text caching."""
        return str(hash(text.lower().strip()))

    def _handle_thread_email(self, text: str) -> RuleResult:
        """Clean thread handler using comprehensive PatternMatcher"""
        text_lower = text.lower().strip()
        
        # 1. Out of Office Detection (Keep existing - works well)
        ooo_phrases = [
            "out of office", "automatic reply", "auto-reply", "auto reply",
            "i am currently out", "i will be out", "away from desk",
            "limited access to my email", "will be returning", "on leave", "at our convention"
        ]
        ooo_contact_words = [
            "forward", "contact", "reach out", "alternate", "assistance", "replacement", "help"
        ]
        
        if any(ooo in text_lower for ooo in ooo_phrases):
            if any(word in text_lower for word in ooo_contact_words):
                return RuleResult(
                    category="Auto Reply (with/without info)",
                    subcategory="With Alternate Contact",
                    confidence=0.92,
                    reason="Threaded out of office with alternate contact",
                    matched_rules=["thread_ooo_with_contact"]
                )
            else:
                return RuleResult(
                    category="Auto Reply (with/without info)",
                    subcategory="No Info/Autoreply",
                    confidence=0.89,
                    reason="Threaded generic OOO/auto-reply",
                    matched_rules=["thread_ooo"]
                )

        # 2. Use Enhanced PatternMatcher for Main Classification
        if hasattr(self, 'pattern_matcher'):
            main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                text_lower, exclude_external_proof=True
            )
            
            if main_cat and confidence > 0.85:
                return RuleResult(
                    category=main_cat,
                    subcategory=subcat,
                    confidence=confidence,
                    reason=f"Pattern matched: {subcat}",
                    matched_rules=[f"pattern_{subcat.lower().replace(' ', '_').replace('/', '_')}"]
                )

        # 3. High-Value Amount Detection (Keep existing)
        amount_pattern = re.compile(r'\$[\d,]+\.?\d*')
        amounts = amount_pattern.findall(text_lower)
        if amounts:
            for amount_str in amounts:
                try:
                    amount_value = float(amount_str.replace('$', '').replace(',', ''))
                    if amount_value > 10000:
                        return RuleResult(
                            category="Manual Review",
                            subcategory="Complex Queries",
                            confidence=0.94,
                            reason=f"High-value amount detected: {amount_str}",
                            matched_rules=["high_value_amount"]
                        )
                except (ValueError, AttributeError):
                    continue

        # 4. Legal/Attorney Detection (Keep existing)
        legal_phrases = [
            'attorney', 'law firm', 'attorney at law', 'esq.', 'law office', 'legal counsel',
            'law llp', 'attorney representing', 'legal representation', 'counsel for'
        ]
        if any(phrase in text_lower for phrase in legal_phrases):
            return RuleResult(
                category="Manual Review",
                subcategory="Complex Queries",
                confidence=0.95,
                reason="Legal/attorney communication requires manual review",
                matched_rules=["thread_legal_communication"]
            )

        # 5. Fallback Pattern Checks (if PatternMatcher didn't match)
        
        # Payment Claims (flexible)
        payment_claim_patterns = [
            "payment.*sent", "was.*paid", "been.*paid", "already.*paid", "payment.*made",
            "settled", "paid.*by", "paid.*via", "sent.*check", "made.*payment"
        ]
        if any(re.search(pattern, text_lower) for pattern in payment_claim_patterns):
            return RuleResult(
                category="Payments Claim",
                subcategory="Claims Paid (No Info)",
                confidence=0.92,
                reason="Payment claim detected",
                matched_rules=["thread_payment_claim"]
            )
        
        # Dispute Detection (flexible)
        dispute_patterns = [
            "dispute", "contested", "disagreement", "not.*ours", "not.*accurate", 
            "do.*not.*owe", "balance.*not"
        ]
        if any(re.search(pattern, text_lower) for pattern in dispute_patterns):
            return RuleResult(
                category="Manual Review",
                subcategory="Partial/Disputed Payment",
                confidence=0.95,
                reason="Dispute detected",
                matched_rules=["thread_dispute_detected"]
            )
        
        # Invoice Requests (flexible)
        invoice_request_patterns = [
            "send.*invoice", "provide.*invoice", "need.*invoice", "invoice.*copy",
            "copies.*of.*invoices", "outstanding.*invoices"
        ]
        if any(re.search(pattern, text_lower) for pattern in invoice_request_patterns):
            return RuleResult(
                category="Invoices Request",
                subcategory="Request (No Info)",
                confidence=0.91,
                reason="Invoice request detected",
                matched_rules=["thread_invoice_request"]
            )
        
        # Processing Errors
        processing_error_patterns = [
            "pdf.*not.*attached", "error.*reason", "processing.*error", "cannot.*be.*processed",
            "failed.*to.*process", "case.*rejection"
        ]
        if any(re.search(pattern, text_lower) for pattern in processing_error_patterns):
            return RuleResult(
                category="No Reply (with/without info)",
                subcategory="Processing Errors",
                confidence=0.92,
                reason="Processing error detected",
                matched_rules=["thread_processing_error"]
            )

        # Payment Status/Inquiry Detection
        payment_inquiry_patterns = [
            "waiting.*to.*receive.*payment", "waiting.*for.*payment",
            "should.*this.*be.*paid", "how.*should.*we.*pay",
            "where.*to.*send.*payment", "when.*will.*payment",
            "hope.*to.*have.*resolved", "payment.*delayed"
        ]
        if any(re.search(pattern, text_lower) for pattern in payment_inquiry_patterns):
            return RuleResult(
                category="Manual Review",
                subcategory="Inquiry/Redirection",
                confidence=0.93,
                reason="Payment inquiry or status update",
                matched_rules=["thread_payment_inquiry"]
            )

        # 6. Contact Redirection (Keep existing)
        redirect_phrases = [
            "no longer with", "please contact", "direct inquiries to", "no longer employed",
            "starting may", "no longer be accepted", "now using", "please submit all future"
        ]
        if any(phrase in text_lower for phrase in redirect_phrases):
            return RuleResult(
                category="Auto Reply (with/without info)",
                subcategory="Redirects/Updates (property changes)",
                confidence=0.91,
                reason="Contact redirection detected",
                matched_rules=["thread_redirect"]
            )
        # Contact Information Updates
        contact_update_patterns = [
            r"our.*return.*#.*is", r"our.*phone.*is", r"our.*number.*is",
            r"correct.*number.*is", r"updated.*contact", r"new.*phone",
            r"please.*use.*number", r"contact.*us.*at"
        ]
        if any(re.search(pattern, text_lower) for pattern in contact_update_patterns):
            # Check if it's internal (from collection agency)
            if any(domain in text_lower for domain in ['@abc-amega.com', 'abc-amega']):
                return RuleResult(
                    category="No Reply (with/without info)",
                    subcategory="Notifications",
                    confidence=0.90,
                    reason="Internal contact information update",
                    matched_rules=["thread_contact_info_update"]
                )
        # 7. Business Response Requiring Manual Review
        business_response_phrases = [
            "insufficient data provided", "i need guidance", "please advise what is needed",
            "please ask", "there is insufficient data"
        ]
        if any(phrase in text_lower for phrase in business_response_phrases):
            return RuleResult(
                category="Manual Review",
                subcategory="Inquiry/Redirection",
                confidence=0.92,
                reason="Business response requiring manual review",
                matched_rules=["thread_business_response"]
            )

        # 8. Ticket Creation
        ticket_phrases = ["ticket created", "case opened", "assigned #", "case number is"]
        if any(phrase in text_lower for phrase in ticket_phrases):
            return RuleResult(
                category="No Reply (with/without info)",
                subcategory="Created",
                confidence=0.90,
                reason="Ticket/case created",
                matched_rules=["thread_ticket_created"]
            )

        # 9. Auto-Reply Support (Very restrictive)
        support_phrases = ["thank you for reaching out", "we have received your request"]
        business_exclusion = ["insufficient", "data", "research", "guidance", "invoice", "payment"]
        if (any(phrase in text_lower for phrase in support_phrases) and 
            not any(word in text_lower for word in business_exclusion)):
            return RuleResult(
                category="Auto Reply (with/without info)",
                subcategory="Case/Support",
                confidence=0.85,
                reason="Auto-reply support confirmation",
                matched_rules=["thread_auto_reply_support"]
            )

        # 10. Payment/Invoice with proof patterns (with external proof exclusion)
        payment_proof_patterns = [r"\battach(ed|ment|ments)?\b", r"\bproof\b", r"\breceipt\b"]
        payment_proof_hit = any(re.search(pattern, text_lower) for pattern in payment_proof_patterns)
        payment_hit = any(keyword in text_lower for keyword in self.thread_payment_keywords)
        invoice_hit = any(keyword in text_lower for keyword in self.thread_invoice_keywords)

        # External proof exclusion
        if hasattr(self, 'pattern_matcher') and self.pattern_matcher.has_external_proof_reference(text_lower):
            external_proof_reference = True
        else:
            external_proof_reference = False

        if payment_hit and payment_proof_hit and not external_proof_reference:
            return RuleResult(
                category="Manual Review",
                subcategory="Payment Confirmation",
                confidence=0.93,
                reason="Payment claim with proof/attachment",
                matched_rules=["thread_payment_with_proof"]
            )
        elif invoice_hit and payment_proof_hit and not external_proof_reference:
            return RuleResult(
                category="Manual Review",
                subcategory="Invoice Receipt",
                confidence=0.92,
                reason="Invoice request with attachment",
                matched_rules=["thread_invoice_with_attachment"]
            )
        elif payment_hit:
            return RuleResult(
                category="Payments Claim",
                subcategory="Claims Paid (No Info)",
                confidence=0.91,
                reason="Payment claim without proof",
                matched_rules=["thread_payment_rule"]
            )
        elif invoice_hit:
            return RuleResult(
                category="Invoices Request",
                subcategory="Request (No Info)",
                confidence=0.90,
                reason="Invoice request without details",
                matched_rules=["thread_invoice_rule"]
            )

        # 11. Restrictive Manual Review Fallback
        specific_manual_words = ["case", "ticket", "support", "complex", "escalate"]
        if any(word in text_lower for word in specific_manual_words):
            return RuleResult(
                category="Manual Review",
                subcategory="Complex Queries",
                confidence=0.81,
                reason="Specific case/support/complex content",
                matched_rules=["thread_manual_rule"]
            )
    
        # 12. Final Fallback (Very restrictive)
        if len(text_lower.split()) < 5:
            return RuleResult(
                category="Manual Review",
                subcategory="Complex Queries",
                confidence=0.70,
                reason="Very short threaded email",
                matched_rules=["thread_short_fallback"]
            )
        
        return RuleResult(
            category="Manual Review",
            subcategory="Complex Queries",
            confidence=0.60,
            reason="Threaded email - needs review",
            matched_rules=["thread_final_fallback"]
        )
    def classify_sublabel(
    self,
    main_category: str,
    text: str,
    has_thread: bool = False,
    analysis: Optional[TextAnalysis] = None,
    ml_result: Optional[Dict[str, Any]] = None,
    retry_count: int = 3,
    subject: str = ""  # ADD SUBJECT PARAMETER
    ) -> RuleResult:
        """
        Advanced sublabel classification with strict priority on OOO/Auto-Reply,
        Ticket Creation, Thread-aware routing, then NLP, rule, and pattern fallback.
        """
        start_time = time.time()
        text_lower = text.lower().strip() if isinstance(text, str) else ""
        subject_lower = subject.lower().strip() if isinstance(subject, str) else ""

        # 0. THREAD-AWARE ROUTING (highest priority!)
        if has_thread:
            return self._handle_thread_email(text)

        # Common patterns for attachment/proof
        payment_proof_patterns = [
            r"\battach(ed|ment|ments)?\b", r"\benclosed\b", r"\bproof\b", r"\breceipt\b", 
            r"\bscreenshot\b", r"\bdocument\b", r"see (the )?(attached|enclosed)", 
            r"find (the )?(attached|enclosed)", r"attached (is|are|please|copy|herewith)?"
        ]
        invoice_proof_patterns = [
            r"\battach(ed|ment|ments)?\b", r"\benclosed\b", r"\bcopy\b", r"see (the )?(attached|enclosed)",
            r"find (the )?(attached|enclosed)", r"attached (is|are|please|invoice|copy|herewith)?", 
            r"\binvoice attached\b"
        ]
        payment_proof_hit = any(re.search(pattern, text_lower) for pattern in payment_proof_patterns)
        invoice_proof_hit = any(re.search(pattern, text_lower) for pattern in invoice_proof_patterns)
        payment_hit = any(keyword in text_lower for keyword in self.thread_payment_keywords)
        invoice_hit = any(keyword in text_lower for keyword in self.thread_invoice_keywords)

        for attempt in range(retry_count):
            try:
                self.metrics.total_processed += 1

                # Input validation
                if not text_lower and not subject_lower:
                    raise ClassificationError("Invalid input: both text and subject are empty")
                if not main_category or not isinstance(main_category, str) or not main_category.strip():
                    raise ClassificationError("Invalid input: main_category must be non-empty string")

                # Early exit for spam/empty
                if text_lower in ["", "n/a", "unsubscribe"]:
                    self._update_metrics(start_time, success=True)
                    return RuleResult("Uncategorized", "General", 0.1, "Text empty or ignorable", ["uncategorized_empty"])

                # 1. AUTO-REPLY SUBJECT Detection (HIGHEST PRIORITY - FIXED)
                if ("automatic reply:" in subject_lower or "auto-reply:" in subject_lower or 
                    "automatic reply" in subject_lower or "auto reply" in subject_lower):
                    
                    # Enhanced OOO detection for non-threaded emails
                    ooo_phrases = [
                        "out of office", "out of the office", "i will be out", "i am currently out",
                        "limited access to my email", "will return", "returning to the office", 
                        "on vacation", "on leave", "currently traveling", "away from desk"
                    ]
                    
                    # Enhanced contact detection
                    contact_phrases = [
                        "contact", "reach out", "alternate", "replacement", "for assistance", 
                        "please contact", "call me", "if you need immediate assistance",
                        "call my cell", "call my mobile", "if urgent", "urgent please contact"
                    ]
                    
                    # Enhanced return date detection
                    return_phrases = [
                        "return", "back on", "until", "returning", "will be back", "available after",
                        "tuesday", "monday", "friday", "thursday", "wednesday", "when i return"
                    ]
                    
                    ooo_hit = any(ooo in text_lower for ooo in ooo_phrases)
                    contact_hit = any(c in text_lower for c in contact_phrases)
                    return_hit = any(r in text_lower for r in return_phrases)
                    
                    if ooo_hit:
                        if contact_hit:
                            return RuleResult(
                                "Auto Reply (with/without info)", "With Alternate Contact", 0.93,
                                "Auto-reply with alternate contact info", ["auto_reply_with_contact"]
                            )
                        elif return_hit:
                            return RuleResult(
                                "Auto Reply (with/without info)", "Return Date Specified", 0.91,
                                "Auto-reply with return date", ["auto_reply_with_return_date"]
                            )
                        else:
                            return RuleResult(
                                "Auto Reply (with/without info)", "No Info/Autoreply", 0.9,
                                "Generic auto-reply", ["auto_reply_generic"]
                            )
                    
                    # Check for process changes/redirects
                    redirect_phrases = [
                        "no longer with", "no longer employed", "please forward", "please contact",
                        "starting may", "no longer be accepted", "now using", "please submit all future"
                    ]
                    if any(phrase in text_lower for phrase in redirect_phrases):
                        return RuleResult(
                            "Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.91,
                            "Auto-reply process change/redirection", ["auto_reply_redirect"]
                        )
                    
                    # Fallback for other auto-replies
                    return RuleResult(
                        "Auto Reply (with/without info)", "No Info/Autoreply", 0.9,
                        "Auto-reply detected from subject line", ["auto_reply_subject"]
                    )
                # Check for no-reply/service account indicators
                no_reply_indicators = [
                    "donotreply", "do-not-reply", "noreply", "no-reply", 
                    "automated", "service account", "system generated"
                ]

                # Check sender email (if available) or text content
                if any(indicator in text_lower for indicator in no_reply_indicators):
                    # Even if it contains business language, it's still a no-reply
                    return RuleResult(
                        "No Reply (with/without info)", "Notifications", 0.93,
                        "No-reply service account detected", ["no_reply_service_account"]
                    )
                # 2. NO-REPLY EMAIL Detection
                if "this is a no-reply email" in text_lower:
                    return RuleResult(
                        "No Reply (with/without info)", "Notifications", 0.9,
                        "No-reply email detected", ["no_reply_content"]
                    )

                # 3. Processing Error Detection (EARLY)
                processing_error_phrases = [
                    "electronic invoice rejected", "your email message cannot be processed",
                    "cannot be processed", "processing error", "rejected for no attachment",
                    "pdf file is not attached", "error reason"
                ]
                if any(phrase in text_lower for phrase in processing_error_phrases):
                    return RuleResult(
                        "No Reply (with/without info)", "Processing Errors", 0.92,
                        "Processing error detected", ["processing_error_detected"]
                    )

                # 4. Enhanced Dispute Detection (EARLY)
                dispute_phrases = [
                    "amount is in dispute", "this amount is in dispute", "balance is not ours",
                    "balance is not accurate", "not our responsibility", "do not owe", "contested",
                    "disagreement", "refuse", "formally disputing", "not accurate", "that not my bill",
                    "due to a sale of property", "not ours due to"
                ]
                if any(phrase in text_lower for phrase in dispute_phrases):
                    return RuleResult(
                        "Manual Review", "Partial/Disputed Payment", 0.95,
                        "Dispute/contest detected", ["dispute_detected"]
                    )

                # 4.5. Payment with Transaction/Proof Details (HIGHER PRIORITY than claims)
                transaction_proof_patterns = [
                    r"transaction.*number", r"batch.*number", r"reference.*number",
                    r"confirmation.*number", r"transaction.*id", r"payment.*reference",
                    r"transaction.*and.*batch", r"paid.*via.*\w+.*transaction"
                ]
                if any(re.search(pattern, text_lower) for pattern in transaction_proof_patterns):
                    # Check if it's about payment
                    if any(word in text_lower for word in ['paid', 'payment', 'settled']):
                        return RuleResult(
                            "Manual Review", "Payment Confirmation", 0.94,
                            "Payment with transaction/proof details", ["payment_with_transaction_proof"]
                        )
                    
                # 5. Enhanced Payment Claims (EARLY)  
                payment_claims = [
                    "its been paid", "has been settled", "this has been settled", "already paid", 
                    "been paid to them", "payment was made", "we paid", "bill was paid", 
                    "paid directly to", "settled with", "we sent check on", "sent check on"
                ]
                if any(phrase in text_lower for phrase in payment_claims):
                    return RuleResult(
                        "Payments Claim", "Claims Paid (No Info)", 0.93,
                        "Payment claim without proof", ["payment_claim_detected"]
                    )

                # 6. Enhanced Invoice Requests (EARLY)
                invoice_request_phrases = [
                    "can you please provide me with outstanding invoices", "provide me with outstanding invoices",
                    "can you please send me copies of any invoices", "send me copies of any invoices",
                    "can you send me the invoice", "provide us with the invoice", "send me the invoice copy",
                    "need invoice copy", "provide invoice copy", "outstanding invoices owed"
                ]
                if any(phrase in text_lower for phrase in invoice_request_phrases):
                    return RuleResult(
                        "Invoices Request", "Request (No Info)", 0.93,
                        "Invoice request detected", ["invoice_request_detected"]
                    )

                # 7. Auto-reply detection (text-based)
                if "automatic reply" in text_lower or "auto-reply" in text_lower:
                    auto_reply_result = self._classify_auto_reply_sublabels(text)
                    if auto_reply_result and auto_reply_result.confidence >= 0.8:
                        self._update_metrics(start_time, success=True)
                        return auto_reply_result

                # 8. OOO / Auto-Reply detection (text-based)
                ooo_phrases = [
                    "out of office", "automatic reply", "auto-reply", "i am currently out",
                    "limited access to my email", "will return", "returning to the office", 
                    "on vacation", "on leave", "currently traveling", "i will be in meetings"
                ]
                if any(ooo in text_lower for ooo in ooo_phrases):
                    auto_reply_result = self._classify_auto_reply_sublabels(text)
                    if auto_reply_result and auto_reply_result.confidence >= 0.8:
                        self._update_metrics(start_time, success=True)
                        return auto_reply_result

                # 9. Ticket/Case Creation
                ticket_creation_phrases = [
                    "ticket created", "case opened", "support request created", "assigned #",
                    "ticket opened", "case number is", "support ticket opened", "case has been created",
                    "thank you for submitting your case"
                ]
                if any(phrase in text_lower for phrase in ticket_creation_phrases):
                    return RuleResult(
                        "No Reply (with/without info)", "Created", 0.88,
                        "Support/case/ticket creation detected", ["ticket_created_pattern"]
                    )

                # 10. Ticket Resolution Detection
                ticket_resolution_phrases = [
                    "support ticket has been moved to solved", "ticket resolved", "case resolved",
                    "case has been resolved", "moved to solved"
                ]
                if any(phrase in text_lower for phrase in ticket_resolution_phrases):
                    return RuleResult(
                        "No Reply (with/without info)", "Resolved", 0.9,
                        "Ticket/case resolution detected", ["ticket_resolved_pattern"]
                    )

                # 11. Payment Plan/Negotiation Detection
                payment_plan_phrases = [
                    "payment plan", "scheduled payments", "monthly payment", "settle", "payment schedule",
                    "able to make this payment", "in two weeks", "budget constraints", "working out",
                    "payment timeline", "set up a payment", "we can set up"
                ]
                if any(phrase in text_lower for phrase in payment_plan_phrases):
                    return RuleResult(
                        "Manual Review", "Partial/Disputed Payment", 0.93,
                        "Payment plan/negotiation detected", ["payment_plan_detected"]
                    )

                # 12. Information Request Detection
                info_request_phrases = [
                    "what invoices were not paid", "let me know what invoices", "can you let me know",
                    "research payment history", "which invoices", "what invoices"
                ]
                if any(phrase in text_lower for phrase in info_request_phrases):
                    return RuleResult(
                        "Manual Review", "Inquiry/Redirection", 0.9,
                        "Information request detected", ["info_request_detected"]
                    )

                # 13. Account Cancellation/Dispute Detection
                cancellation_phrases = [
                    "canceled their account", "cancel the account", "do not owe", "previously canceled",
                    "waive the charges"
                ]
                if any(phrase in text_lower for phrase in cancellation_phrases):
                    return RuleResult(
                        "Manual Review", "Partial/Disputed Payment", 0.92,
                        "Account cancellation/dispute detected", ["cancellation_dispute"]
                    )

                # 14. Business Response Requiring Manual Review
                business_response_phrases = [
                    "insufficient data provided to research", "there is insufficient data", 
                    "please ask", "i need guidance", "please advise what is needed"
                ]
                if any(phrase in text_lower for phrase in business_response_phrases):
                    return RuleResult(
                        "Manual Review", "Inquiry/Redirection", 0.92,
                        "Business response requiring manual review", ["business_response_detected"]
                    )

                # 15. Payment/Invoice with proof/attachment (non-threaded)
                if main_category in ["Manual Review", "Payments Claim", "Invoices Request"]:
                    # Payment claim with proof
                    if payment_hit and payment_proof_hit:
                        self._update_metrics(start_time, success=True)
                        return RuleResult(
                            "Manual Review", "Payment Confirmation", 0.92,
                            "Non-threaded payment claim with proof/attachment", ["nonthread_payment_with_proof"]
                        )
                    # Invoice request with proof
                    if invoice_hit and invoice_proof_hit:
                        self._update_metrics(start_time, success=True)
                        return RuleResult(
                            "Manual Review", "Invoice Receipt", 0.92,
                            "Non-threaded invoice request with attachment", ["nonthread_invoice_with_attachment_rule"]
                        )

                # 16. NLP analysis, if available
                if analysis is None and self.nlp_processor:
                    try:
                        analysis = self.nlp_processor.analyze_text(text)
                        self.logger.debug(f"🧠 NLP analysis: topics={getattr(analysis,'topics',None)}, urgency={getattr(analysis,'urgency_score',0):.2f}")
                    except Exception as e:
                        self.logger.warning(f"NLP analysis failed: {e}")
                        analysis = None

                if analysis:
                    nlp_result = self._classify_with_nlp_analysis(main_category, text, analysis)
                    if nlp_result:
                        if ml_result and 'confidence' in ml_result:
                            nlp_result.confidence = round((nlp_result.confidence * 0.7) + (ml_result['confidence'] * 0.3), 2)
                        self._update_metrics(start_time, success=True)
                        return nlp_result

                # 17. Specific sublabel function (rule-based)
                if main_category == "Manual Review":
                    sublabel_result = self._classify_manual_review_sublabels(text)
                elif main_category == "No Reply (with/without info)":
                    sublabel_result = self._classify_no_reply_sublabels(text)
                elif main_category == "Auto Reply (with/without info)":
                    sublabel_result = self._classify_auto_reply_sublabels(text)
                else:
                    sublabel_result = None

                if sublabel_result:
                    self._update_metrics(start_time, success=True)
                    return sublabel_result

                # 18. Pattern matcher as fallback
                pattern_result = self._classify_with_cached_patterns(text)
                if pattern_result:
                    if ml_result and 'confidence' in ml_result:
                        pattern_result.confidence = round((pattern_result.confidence * 0.6) + (ml_result['confidence'] * 0.4), 2)
                    self._update_metrics(start_time, success=True)
                    return pattern_result

                # 19. Default fallback
                default_result = self._get_default_result(main_category)
                self._update_metrics(start_time, success=True)
                return default_result

            except (ClassificationError, PatternValidationError) as e:
                self.logger.error(f"Classification error (attempt {attempt + 1}): {e}")
                if attempt == retry_count - 1:
                    self.metrics.errors += 1
                    self._update_metrics(start_time, success=False)
                    return self._get_fallback_result(str(e))
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                if attempt == retry_count - 1:
                    self.metrics.errors += 1
                    self._update_metrics(start_time, success=False)
                    return self._get_fallback_result(f"Unexpected error: {e}")
                continue

    def _classify_with_nlp_analysis(self, main_category: str, text: str, analysis: TextAnalysis) -> Optional[RuleResult]:
        """Use NLP analysis to make intelligent classification decisions, including robust OOO mapping."""
        try:
            # Manual Review sublabels (strict mapping)
            for topic in analysis.topics:
                if topic == 'partial_disputed_payment':
                    return RuleResult("Manual Review", "Partial/Disputed Payment", 0.9, "NLP detected dispute topic", ["nlp_dispute_topic"])
                elif topic == 'payment_confirmation':
                    return RuleResult("Manual Review", "Payment Confirmation", 0.9, "NLP detected payment proof", ["nlp_payment_proof"])
                elif topic == 'invoice_receipt':
                    return RuleResult("Manual Review", "Invoice Receipt", 0.9, "NLP detected invoice proof", ["nlp_invoice_proof"])
                elif topic == 'closure_notification':
                    return RuleResult("Manual Review", "Closure Notification", 0.9, "NLP detected closure topic", ["nlp_closure"])
                elif topic == 'external_submission':
                    return RuleResult("Manual Review", "External Submission", 0.9, "NLP detected invoice issue", ["nlp_invoice_issue"])
                elif topic == 'invoice_errors':
                    return RuleResult("Manual Review", "Invoice Errors (format mismatch)", 0.9, "NLP detected format error", ["nlp_format_error"])
                elif topic == 'payment_details_received':
                    return RuleResult("Manual Review", "Payment Details Received", 0.9, "NLP detected payment details", ["nlp_payment_details"])
                elif topic == 'inquiry_redirection':
                    return RuleResult("Manual Review", "Inquiry/Redirection", 0.9, "NLP detected redirection", ["nlp_redirection"])

                # No Reply sublabels
                elif topic == 'sales_offers':
                    return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.9, "NLP detected sales offer", ["nlp_sales"])
                elif topic == 'processing_errors':
                    return RuleResult("No Reply (with/without info)", "Processing Errors", 0.9, "NLP detected processing error", ["nlp_processing_error"])
                elif topic == 'import_failures':
                    return RuleResult("No Reply (with/without info)", "Import Failures", 0.9, "NLP detected import failure", ["nlp_import_failure"])
                elif topic == 'ticket_created':
                    return RuleResult("No Reply (with/without info)", "Created", 0.9, "NLP detected ticket creation", ["nlp_ticket_created"])
                elif topic == 'ticket_resolved':
                    return RuleResult("No Reply (with/without info)", "Resolved", 0.9, "NLP detected ticket resolution", ["nlp_ticket_resolved"])
                elif topic == 'ticket_open':
                    return RuleResult("Manual Review", "Complex Queries", 0.9, "NLP detected open ticket - escalating", ["nlp_ticket_escalation"])
                
                # FIXED: General Thank You moved to No Reply category
                elif topic == 'general_thank_you':
                    return RuleResult("No Reply (with/without info)", "Notifications", 0.9, "NLP detected thank you", ["nlp_thank_you"])

                # NEW: Invoice Request sublabels
                elif topic == 'invoice_request':
                    return RuleResult("Invoices Request", "Request (No Info)", 0.9, "NLP detected invoice request", ["nlp_invoice_request"])
                
                # NEW: Payment Claim sublabels  
                elif topic == 'payment_claim':
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.9, "NLP detected payment claim", ["nlp_payment_claim"])

                # Auto Reply sublabels - handle composite and atomic topics for OOO
                if topic.startswith('out_of_office'):
                    # Check for specific subtypes as either separate topics or embedded in topic string
                    if 'with_alternate_contact' in topic or 'with_alternate_contact' in analysis.topics:
                        return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.9, "NLP detected OOO with contact", ["nlp_ooo_contact"])
                    if 'return_date_specified' in topic or 'return_date_specified' in analysis.topics:
                        return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.9, "NLP detected OOO with date", ["nlp_ooo_date"])
                    return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.9, "NLP detected generic OOO", ["nlp_ooo_generic"])

                elif topic == 'case_support_confirmation':
                    return RuleResult("Auto Reply (with/without info)", "Case/Support", 0.9, "NLP detected case confirmation", ["nlp_case_confirm"])
                elif topic == 'survey':
                    return RuleResult("Auto Reply (with/without info)", "Survey", 0.9, "NLP detected survey", ["nlp_survey"])
                elif topic == 'redirects_updates':
                    return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.9, "NLP detected redirect/update", ["nlp_redirect"])

            # Use urgency and complexity scores for classification enhancement
            if analysis.urgency_score > 0.7:
                return RuleResult("Manual Review", "Complex Queries", 0.8,
                                f"High urgency detected (score: {analysis.urgency_score:.2f})", ["nlp_high_urgency"])

            if analysis.complexity_score > 0.8:
                return RuleResult("Manual Review", "Complex Queries", 0.8,
                                f"High complexity detected (score: {analysis.complexity_score:.2f})", ["nlp_high_complexity"])

            # Check financial terms for payment/invoice classification
            financial_terms = getattr(analysis, "financial_terms", [])
            if len(financial_terms) > 3 and main_category in ["Manual Review", "Payments Claim", "Invoices Request"]:
                return RuleResult("Manual Review", "Payment Details Received", 0.7,
                                f"Multiple financial terms detected: {financial_terms[:3]}", ["nlp_financial_terms"])

            return None

        except Exception as e:
            self.logger.error(f"❌ NLP classification error: {e}")
            return None

    def _classify_with_cached_patterns(self, text: str) -> Optional[RuleResult]:
        """Use cached pattern matching for performance."""
        try:
            text_hash = self._get_text_hash(text)
            
            # Check cache first
            if text_hash in self._pattern_cache:
                self.metrics.pattern_cache_hits += 1
                cached_result = self._pattern_cache[text_hash]
                main_cat, sub_cat, confidence, matched_patterns = cached_result
            else:
                # Use cached LRU function
                main_cat, sub_cat, confidence, matched_patterns = self._cached_pattern_match(text_hash, text)
                
                # Cache the result
                self._pattern_cache[text_hash] = (main_cat, sub_cat, confidence, matched_patterns)
                
                # Limit cache size
                if len(self._pattern_cache) > 5000:
                    # Remove oldest 1000 entries
                    items = list(self._pattern_cache.items())
                    self._pattern_cache = dict(items[1000:])
            
            if main_cat and confidence > 0.5:
                return RuleResult(
                    category=main_cat,
                    subcategory=sub_cat,
                    confidence=confidence,
                    reason=f"Cached pattern matched: {sub_cat}",
                    matched_rules=matched_patterns
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Cached pattern matching error: {e}")
            return None

    def _update_metrics(self, start_time: float, success: bool) -> None:
        """Update performance metrics."""
        processing_time = time.time() - start_time
        
        if success:
            self.metrics.successful_classifications += 1
        
        # Update average processing time
        total_operations = self.metrics.successful_classifications + self.metrics.errors
        if total_operations > 0:
            self.metrics.avg_processing_time = (
                (self.metrics.avg_processing_time * (total_operations - 1) + processing_time) / total_operations
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        total_operations = self.metrics.successful_classifications + self.metrics.errors
        success_rate = (self.metrics.successful_classifications / max(total_operations, 1)) * 100
        
        cache_total = self.metrics.pattern_cache_hits + self.metrics.pattern_cache_misses
        cache_hit_rate = (self.metrics.pattern_cache_hits / max(cache_total, 1)) * 100
        
        return {
            'total_processed': self.metrics.total_processed,
            'successful_classifications': self.metrics.successful_classifications,
            'errors': self.metrics.errors,
            'success_rate_percent': round(success_rate, 2),
            'avg_processing_time_ms': round(self.metrics.avg_processing_time * 1000, 2),
            'pattern_cache_hits': self.metrics.pattern_cache_hits,
            'pattern_cache_misses': self.metrics.pattern_cache_misses,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'cache_size': len(self._pattern_cache)
        }

    def classify_batch_optimized(self, emails: List[Dict[str, Any]], batch_size: int = 100) -> List[RuleResult]:
        """Optimized batch processing with performance monitoring."""
        results = []
        total_emails = len(emails)
        
        self.logger.info(f"🚀 Starting optimized batch processing of {total_emails} emails")
        
        # Process in batches for memory efficiency
        for i in range(0, total_emails, batch_size):
            batch = emails[i:i + batch_size]
            batch_start_time = time.time()
            
            batch_results = []
            for j, email in enumerate(batch):
                try:
                    result = self.classify_sublabel(
                        email.get('main_category', ''),
                        email.get('text', ''),
                        email.get('has_thread', False),
                        email.get('analysis', None),
                        email.get('ml_result', None),
                        retry_count=2  # Reduce retries for batch processing
                    )
                    batch_results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"❌ Batch processing error for email {i + j + 1}: {e}")
                    batch_results.append(self._get_fallback_result(f"Batch error: {e}"))
            
            results.extend(batch_results)
            
            batch_time = time.time() - batch_start_time
            progress = ((i + len(batch)) / total_emails) * 100
            
            self.logger.info(f"📊 Batch {i//batch_size + 1} completed: {progress:.1f}% ({batch_time:.2f}s)")
        
        # Log final performance metrics
        metrics = self.get_performance_metrics()
        self.logger.info(f"✅ Batch processing complete. Metrics: {metrics}")
        
        return results

    def _classify_with_patterns(self, text: str) -> Optional[RuleResult]:
        """Use existing PatternMatcher for classification."""
        
        try:
            # Use the comprehensive pattern matcher
            main_cat, sub_cat, confidence, matched_patterns = self.pattern_matcher.match_text(text)
            
            if main_cat and confidence > 0.5:
                return RuleResult(
                    category=main_cat,
                    subcategory=sub_cat,
                    confidence=confidence,
                    reason=f"Pattern matched: {sub_cat}",
                    matched_rules=matched_patterns
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Pattern matching error: {e}")
            return None

    def _classify_manual_review_sublabels(self, text: str) -> Optional[RuleResult]:
        """SIMPLIFIED Manual Review classifier - focused on clear, distinct patterns only."""
        text_lower = text.lower().strip()

        # 1. CLEAR Disputes (HIGHEST PRIORITY)
        dispute_phrases = [
            'amount is in dispute', 'this amount is in dispute', 'balance is not ours',
            'balance is not accurate', 'not our responsibility', 'dispute', 'contested',
            'disagreement', 'formally disputing', 'not accurate', 'that not my bill'
        ]
        if any(phrase in text_lower for phrase in dispute_phrases):
            return RuleResult(
                "Manual Review", "Partial/Disputed Payment", 0.95,
                "Clear dispute detected", ["dispute_detected"]
            )

        # 2. CLEAR Payment Confirmation (with proof/details)
        payment_confirmation_phrases = [
            'proof of payment', 'payment confirmation', 'i have a receipt', 'check number',
            'eft#', 'confirmation #', 'payment has been released', 'was reconciled',
            'here is proof', 'attached proof', 'payment evidence'
        ]
        if any(phrase in text_lower for phrase in payment_confirmation_phrases):
            return RuleResult(
                "Manual Review", "Payment Confirmation", 0.92,
                "Payment confirmation with proof", ["payment_confirmation_detected"]
            )

        # 3. CLEAR Invoice Receipt (providing invoices)
        invoice_receipt_phrases = [
            'invoice attached', 'invoice copy attached', 'see attached invoice',
            'invoice is attached', 'here is the invoice', 'proof of invoice'
        ]
        if any(phrase in text_lower for phrase in invoice_receipt_phrases):
            return RuleResult(
                "Manual Review", "Invoice Receipt", 0.91,
                "Invoice receipt/proof provided", ["invoice_receipt_detected"]
            )

        # 4. CLEAR Business Closure
        closure_phrases = ['business closed', 'company closed', 'out of business', 'ceased operations']
        if any(phrase in text_lower for phrase in closure_phrases):
            # Check if payment-related
            if any(word in text_lower for word in ['payment', 'due', 'outstanding', 'balance', 'owe']):
                return RuleResult(
                    "Manual Review", "Closure + Payment Due", 0.92,
                    "Business closure with payment implications", ["closure_with_payment"]
                )
            else:
                return RuleResult(
                    "Manual Review", "Closure Notification", 0.90,
                    "Business closure notification", ["closure_notification"]
                )

        # 5. CLEAR Invoice Issues/Problems
        invoice_issue_phrases = [
            'invoice issue', 'invoice problem', 'invoice error', 'import failed',
            'failed import', 'invoice submission failed', 'documents were not processed'
        ]
        if any(phrase in text_lower for phrase in invoice_issue_phrases):
            return RuleResult(
                "Manual Review", "External Submission", 0.88,
                "Invoice submission/processing issue", ["invoice_issue_detected"]
            )

        # 6. CLEAR Format Errors
        format_error_phrases = [
            'missing field', 'format mismatch', 'incomplete invoice', 'required field'
        ]
        if any(phrase in text_lower for phrase in format_error_phrases):
            return RuleResult(
                "Manual Review", "Invoice Errors (format mismatch)", 0.87,
                "Invoice format issue", ["format_error_detected"]
            )

        # 7. CLEAR Payment Timeline/Status
        payment_timeline_phrases = [
            'payment will be sent', 'payment is being processed', 'check will be mailed',
            'payment scheduled', 'checks will be mailed by', 'payment timeline',
            'payment being processed', 'invoice being processed'
        ]
        if any(phrase in text_lower for phrase in payment_timeline_phrases):
            return RuleResult(
                "Manual Review", "Payment Details Received", 0.89,
                "Payment timeline/status provided", ["payment_timeline_detected"]
            )

        # 8. CLEAR Business Responses Requiring Review
        business_response_phrases = [
            'insufficient data provided', 'i need guidance', 'please advise what is needed',
            'please check with', 'please refer to', 'contact our office'
        ]
        if any(phrase in text_lower for phrase in business_response_phrases):
            return RuleResult(
                "Manual Review", "Inquiry/Redirection", 0.90,
                "Business response requiring review", ["business_response_detected"]
            )

        # 9. DEFAULT - Much more restrictive
        # Only if it contains clear business/financial terms
        business_terms = ['account', 'invoice', 'payment', 'balance', 'amount', 'bill', 'due']
        if any(term in text_lower for term in business_terms):
            return RuleResult(
                "Manual Review", "Complex Queries", 0.70,
                "Business-related content requiring review", ["business_content_detected"]
            )

        # Final fallback - very low confidence
        return RuleResult(
            "Manual Review", "Complex Queries", 0.50,
            "Generic manual review needed", ["generic_manual_review"]
        )

    def _classify_auto_reply_sublabels(self, text: str) -> Optional[RuleResult]:
        """Classify Auto Reply sublabels with strict priority order and robust coverage."""
        text_lower = text.lower().strip()

        # Early escalation for payment negotiation language
        payment_negotiation_phrases = [
            'partial payment', 'we will pay this just not at this moment', 'we will get it paid', 'will get it paid however',
            'payment plan', 'delayed payment', 'put that money in other places', 'we paid because', 'not paying right now',
            'balance is not accurate', 'not accurate', 'that not my bill', 'dispute', 'disagreement', 'challenge payment',
            'will get it paid', 'working out a payment', 'we will pay this', 'waiting for funds', 'awaiting funds'
        ]
        if any(phrase in text_lower for phrase in payment_negotiation_phrases):
            return None  # Escalate to Manual Review

        # 1. OOO/Automatic Reply Detection (PRIORITY: contact > return date > generic)
        ooo_phrases = [
            'out of office', 'automatic reply', 'auto-reply', 'auto reply', 'i am currently out',
            'i will be out', 'i am away', 'not available', 'limited access to email', 'will return',
            'returning to the office', 'i\'ll be out', 'will be unavailable', 'away from desk',
            'currently unavailable', 'currently traveling', 'i will be in meetings', 'in meetings',
            'out of the office', 'on leave', 'on vacation', 'on pto'
        ]

        # Enhanced alternate contact detection
        contact_phrases = [
            'contact', 'reach out', 'alternate', 'replacement', 'for assistance', 'for help',
            'forward your email', 'please forward', 'email to', 'in my absence', 'instead', 'alternate email',
            'please direct all future inquiries to', 'please direct', 'direct all future correspondence to',
            'please contact', 'call me', 'text me', 'if you need immediate assistance', 'for all of your a/p needs',
            'please contact:', 'call my cell', 'call my mobile', 'call me at', 'my cell', 'my mobile', 'cell:', 'mobile:',
            'if urgent', 'if this is urgent', 'urgent please contact', 'for immediate help', 'immediate assistance'
        ]
        
        # Enhanced return date detection
        return_phrases = [
            'return', 'back on', 'until', 'returning', 'will be back', 'available after', 'rejoin on',
            'tuesday', 'monday', 'friday', 'thursday', 'wednesday', 'saturday', 'sunday',
            'when i return', 'as soon as i return', 'upon my return'
        ]

        # Regex patterns for better detection
        contact_regex = re.compile(r"(call|mobile|cell|contact)[^\n]{0,40}\d{3,}", re.I)
        return_regex = re.compile(
            r'return(ing)?[^\n]{0,40}(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}(st|nd|rd|th)?|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}-\d{1,2}-\d{2,4})',
            re.I)
        date_range_regex = re.compile(
            r'(out of|from).*?(\d{1,2}/\d{1,2}|\d{1,2}(st|nd|rd|th)?).*?(to|through|until).*?(\d{1,2}/\d{1,2}|\d{1,2}(st|nd|rd|th)?)',
            re.I)

        ooo_hit = any(ooo in text_lower for ooo in ooo_phrases)
        contact_hit = any(c in text_lower for c in contact_phrases) or bool(contact_regex.search(text_lower))
        return_hit = any(r in text_lower for r in return_phrases) or bool(return_regex.search(text_lower))
        date_range_hit = bool(date_range_regex.search(text_lower))

        if ooo_hit:
            if contact_hit:
                return RuleResult(
                    "Auto Reply (with/without info)", "With Alternate Contact", 0.93,
                    "OOO with alternate contact info", ["ooo_with_contact"]
                )
            elif return_hit or date_range_hit:
                return RuleResult(
                    "Auto Reply (with/without info)", "Return Date Specified", 0.91,
                    "OOO with return date or date range", ["ooo_with_return_date"]
                )
            else:
                return RuleResult(
                    "Auto Reply (with/without info)", "No Info/Autoreply", 0.9,
                    "Generic OOO or auto-reply", ["ooo_generic_pattern"]
                )

        # 2. Service Account / No-Reply Detection (HIGH PRIORITY - CLIENT REQUIREMENT)
        service_account_phrases = [
            'do not reply', 'no-reply', 'noreply', 'donotreply', 'service account',
            'please do not tamper', 'do not tamper the subject', 'automated response',
            'this is an automated', 'accounts payable department', 'please do not respond',
            'this is an automated email address', 'automated email address',
            'insufficient data provided', 'system generated'
        ]
        domain_indicators = ['noreply@', 'donotreply@', 'no-reply@', 'service@']

        if (any(phrase in text_lower for phrase in service_account_phrases) or 
            any(domain in text_lower for domain in domain_indicators)):
            return RuleResult(
                "Auto Reply (with/without info)", "No Info/Autoreply", 0.91,
                "Service account / no-reply email", ["service_account_noreply"]
            )

        # 3. Standalone OOO/Auto-Reply patterns
        standalone_ooo_phrases = [
            'currently unavailable', 'limited access to my email', 'will respond when back',
            'away from my desk', 'attending a conference', 'in training'
        ]
        if any(phrase in text_lower for phrase in standalone_ooo_phrases):
            return RuleResult(
                "Auto Reply (with/without info)", "No Info/Autoreply", 0.88,
                "Generic OOO/auto-reply fallback", ["ooo_catchall"]
            )

        # 4. Contact Changes/Redirects (HIGH PRIORITY - before case/support)
        contact_change_phrases = [
            'no longer with', 'no longer employed', 'is no longer employed here', 'no longer works here',
            'please direct all future inquiries to', 'please direct', 'forward your correspondence',
            'new contact', 'contact changed', 'contact update', 'please update your',
            'email address is no longer monitored', 'no longer monitored', 'mailbox is no longer monitored'
        ]
        if any(phrase in text_lower for phrase in contact_change_phrases):
            return RuleResult(
                "Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.91,
                "Contact change/redirection detected", ["contact_change_pattern"]
            )

        # 5. Complex Business/Process Changes (escalate to Manual Review)
        complex_business_phrases = [
            'process change', 'new system', 'workflow tool', 'submit all future invoices',
            'invoices sent to', 'will no longer be accepted', 'starting', 'new process',
            'please update your records', 'system change', 'procedure change',
            'the attached invoice will be processed', 'for emailing invoice images'
        ]
        if any(phrase in text_lower for phrase in complex_business_phrases):
            return None  # Escalate to Manual Review

        # 6. Emergency/Facilities Instructions (HIGH PRIORITY)
        emergency_phrases = [
            'facilities emergency', 'emergency please call', 'maintenance request form',
            'for immediate assistance', 'emergency contact', 'if this is a facilities emergency',
            'for maintenance requests', 'emergency for these issues'
        ]
        if any(phrase in text_lower for phrase in emergency_phrases):
            return RuleResult(
                "Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.89,
                "Emergency/facilities instructions", ["emergency_instructions"]
            )

        # 7. Case/Support Confirmations (enhanced with better patterns)
        support_phrases = [
            'thanks for reaching out', 'thank you for contacting', 'we have received your request',
            'you can usually expect a reply', 'our business hours are', 'we\'ll get back to you',
            'support team', 'customer support', 'support representative will be reviewing',
            'member of our team will follow up', 'team will follow up with you shortly',
            'we have received your message', 'thank you for reaching out to us'
        ]
        # Enhanced exclusion to prevent business conflicts
        business_exclusion_words = [
            'invoice', 'payment', 'bill', 'amount', 'balance', 'paid', 'check', 'account',
            'due', 'receipt', 'proof', 'confirmation', 'insufficient data', 'research',
            'location contact', 'responsible for the bill'
        ]
        if (any(phrase in text_lower for phrase in support_phrases) and 
            not any(word in text_lower for word in business_exclusion_words)):
            return RuleResult(
                "Auto Reply (with/without info)", "Case/Support", 0.85,
                "Case/support confirmation", ["case_confirm_pattern"]
            )

        # 8. Case/Request Closed detection
        case_closed_phrases = [
            'case is now closed', 'case closed', 'case has been closed', 'request completed', 
            'no further action', 'ticket resolved', 'case resolved'
        ]
        if any(phrase in text_lower for phrase in case_closed_phrases):
            return RuleResult(
                "Auto Reply (with/without info)", "Case/Support", 0.89,
                "Case or request closure confirmation", ["case_closed_pattern"]
            )

        # 9. Property/Department Changes
        property_change_phrases = [
            'property manager', 'department changed', 'forwarded to', 'change of contact',
            'new point of contact', 'assigned new contact'
        ]
        if any(phrase in text_lower for phrase in property_change_phrases):
            return RuleResult(
                "Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.85,
                "Property/department change detected", ["property_change_pattern"]
            )

        # 10. Survey/Feedback
        survey_phrases = [
            'survey', 'feedback', 'rate', 'customer satisfaction', 'please rate', 'your opinion', 
            'take a short survey', 'rate our service', 'skin quiz', 'quiz'
        ]
        if any(phrase in text_lower for phrase in survey_phrases):
            return RuleResult(
                "Auto Reply (with/without info)", "Survey", 0.8,
                "Survey/feedback request", ["survey_pattern"]
            )

        # 11. Quarantine Reports
        if "quarantined email report" in text_lower or "quarantine report" in text_lower:
            return RuleResult(
                "Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.9,
                "Email quarantine/security report", ["quarantine_report"]
            )

        # 12. General Thank You (VERY RESTRICTIVE - LOWEST PRIORITY)
        pure_thank_you_phrases = [
            'thank you for your email and we will get back to you',
            'thank you for contacting us and we will respond',
            'thank you for your inquiry and we will follow up'
        ]       
        # Default fallback
        return RuleResult(
            "Auto Reply (with/without info)", "No Info/Autoreply", 0.6,
            "General auto reply (fallback)", ["auto_reply_default"]
        )

    def _classify_no_reply_sublabels(self, text: str) -> Optional[RuleResult]:
        """Classify No Reply sublabels using business-aware logic and escalation rules."""
        text_lower = text.lower().strip()

        # 1. Service Account Detection (decide if No Reply or escalate to Auto Reply)
        service_account_phrases = [
            'automated system', 'system generated', 'do not reply to this email',
            'this is an automated message', 'automated notification', 'automated email'
        ]
        contact_indicators = ['call', 'contact', 'email', 'phone', 'assistance', 'help']
        
        # If pure system notification (no contact info), keep in No Reply
        if any(phrase in text_lower for phrase in service_account_phrases):
            if not any(contact in text_lower for contact in contact_indicators):
                return RuleResult(
                    "No Reply (with/without info)", "Notifications", 0.89,
                    "Automated system notification", ["automated_system_notification"]
                )
            # If has contact info, let it go to Auto Reply for proper classification
            return None

        # 2. Processing Errors (HIGH PRIORITY - system/technical failures)
        processing_error_phrases = [
            'processing error', 'failed to process', 'processing failed', 'unable to process',
            'error processing', 'electronic invoice rejected', 'your email message cannot be processed',
            'cannot be processed', 'rejected for no attachment', 'mail delivery failed',
            'delivery failure', 'message undelivered', 'bounce back', 'email bounced',
            'email cannot be delivered', 'delivery unsuccessful', 'message failed',
            'pdf file is not attached', 'error reason', 'case rejection'
        ]
        if any(phrase in text_lower for phrase in processing_error_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Processing Errors", 0.92,
                "Processing/delivery error detected", ["processing_errors_pattern"]
            )

        # 3. Import Failures (escalate business-critical, otherwise no-reply)
        import_failure_phrases = ['import failed', 'import error', 'failed import', 'import unsuccessful']
        if any(phrase in text_lower for phrase in import_failure_phrases):
            # Escalate if business-critical terms present
            if any(word in text_lower for word in ['invoice', 'payment', 'submission', 'manual', 'business']):
                return RuleResult(
                    "Manual Review", "External Submission", 0.85,
                    "Business-critical import failure", ["import_failure_escalated"]
                )
            return RuleResult(
                "No Reply (with/without info)", "Import Failures", 0.83,
                "Import failure notification", ["import_failures_pattern"]
            )

        # 4. Ticket/Case Creation (automated confirmations)
        ticket_creation_phrases = [
            'ticket created', 'case opened', 'new ticket', 'support request created',
            'case number is', 'ticket #', 'support ticket opened', 'case has been opened',
            'request has been created', 'assigned #', 'case number', 'ticket number',
            'support request has been received', 'your request has been logged',
            'ticket has been created', 'case has been created', 'we have received your request and a ticket has been created'
        ]
        if any(phrase in text_lower for phrase in ticket_creation_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Created", 0.91,
                "Ticket/case creation confirmation", ["ticket_created_pattern"]
            )

        # 5. Ticket/Case Resolution (automated closure notifications)
        ticket_resolution_phrases = [
            'ticket resolved', 'case closed', 'case resolved', 'case has been resolved',
            'ticket has been resolved', 'case is now closed', 'request completed', 
            'issue closed', 'request closed', 'support ticket closed', 'ticket closed',
            'moved to solved', 'marked as resolved', 'ticket has been moved to solved'
        ]
        if any(phrase in text_lower for phrase in ticket_resolution_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Resolved", 0.9,
                "Ticket/case resolution notification", ["ticket_resolved_pattern"]
            )

        # 6. Open Tickets (escalate - requires manual attention)
        open_ticket_phrases = [
            'ticket still open', 'case remains open', 'ticket pending', 'pending support ticket', 
            'open ticket', 'awaiting response', 'ticket in progress'
        ]
        if any(phrase in text_lower for phrase in open_ticket_phrases):
            return RuleResult(
                "Manual Review", "Complex Queries", 0.87,
                "Open ticket requiring attention", ["ticket_open_escalated"]
            )

        # 7. System Alerts/Notifications (automated system messages)
        system_alert_phrases = [
            'system notification', 'system alert', 'auto notification', 'notification only',
            'automated email', 'automated notification', 'system message', 'alert notification',
            'system update', 'maintenance notification', 'service update', 'server maintenance',
            'scheduled maintenance'
        ]
        if any(phrase in text_lower for phrase in system_alert_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.88,
                "Automated system notification", ["system_notification_pattern"]
            )

        # 8. Sales/Offers/Marketing (promotional content)
        sales_phrases = [
            'special offer', 'limited time offer', 'promotional offer', 'sales promotion', 'discount offer',
            'buy now', 'save big', 'limited offer', 'exclusive deal', 'exclusive offer', 'flash sale',
            'promotion', 'marketing', 'newsletter', 'advertisement', 'promo code', 'sale event'
        ]
        if any(phrase in text_lower for phrase in sales_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Sales/Offers", 0.86,
                "Sales/promotional content", ["sales_offers_pattern"]
            )

        # 9. Business Closure (info-only vs payment-related)
        closure_phrases = ['business closed', 'company closed', 'out of business', 'ceased operations']
        if any(phrase in text_lower for phrase in closure_phrases):
            # Escalate if payment/financial terms present
            if any(word in text_lower for word in ['payment', 'due', 'outstanding', 'balance', 'owed', 'invoice']):
                return RuleResult(
                    "Manual Review", "Closure + Payment Due", 0.85,
                    "Business closure with payment implications", ["closure_payment_escalated"]
                )
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.78,
                "Business closure information only", ["business_closure_info"]
            )

        # 10. Email Management (unsubscribe, preferences, delivery)
        email_management_phrases = [
            'unsubscribe', 'update preferences', 'email preferences', 'subscription',
            'opt out', 'remove from list', 'manage subscription', 'email settings'
        ]
        if any(phrase in text_lower for phrase in email_management_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.85,
                "Email management/subscription notification", ["email_management_pattern"]
            )

        # 11. Invoice/Payment Processing Issues (escalate to Manual Review)
        invoice_payment_issues = [
            'invoice canceled', 'invoice cancelled', 'payment canceled', 'payment cancelled',
            'account canceled', 'account cancelled', 'your payment cannot be processed',
            'invoice issue', 'unable to accept payment', 'payment not accepted', 'payment rejected',
            'invoice rejected', 'waived', 'payment waived', 'processing issue'
        ]
        if any(phrase in text_lower for phrase in invoice_payment_issues):
            return RuleResult(
                "Manual Review", "Complex Queries", 0.84,
                "Invoice/payment processing issue requires review", ["invoice_payment_issue_escalated"]
            )

        # 12. Security/Authentication Notifications
        security_phrases = [
            'security alert', 'login attempt', 'password reset', 'account security',
            'unauthorized access', 'security notification', 'verification required',
            'security breach', 'account locked', 'suspicious activity'
        ]
        if any(phrase in text_lower for phrase in security_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.87,
                "Security/authentication notification", ["security_notification_pattern"]
            )

        # 13. Delivery/Shipping Notifications
        delivery_phrases = [
            'delivery notification', 'shipped', 'tracking', 'order status',
            'package delivered', 'delivery confirmation', 'shipment update',
            'out for delivery', 'package in transit', 'delivery attempt'
        ]
        if any(phrase in text_lower for phrase in delivery_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.82,
                "Delivery/shipping notification", ["delivery_notification_pattern"]
            )

        # 14. Legal/Compliance Notifications (info-only, not requiring action)
        legal_notification_phrases = [
            'legal notice', 'compliance notification', 'regulatory update', 'policy change',
            'terms of service', 'privacy policy update', 'legal disclaimer'
        ]
        if any(phrase in text_lower for phrase in legal_notification_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.83,
                "Legal/compliance notification", ["legal_notification_pattern"]
            )

        # 15. Backup/Archive Notifications
        backup_phrases = [
            'backup completed', 'archive notification', 'data backup', 'system backup',
            'backup successful', 'backup failed', 'archive complete'
        ]
        if any(phrase in text_lower for phrase in backup_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.81,
                "Backup/archive notification", ["backup_notification_pattern"]
            )

        # 16. General Thank You (MOVED FROM AUTO REPLY - CORRECT HIERARCHY PLACEMENT)
        thank_you_phrases = [
            'thank you for your email and we will get back to you',
            'thank you for contacting us and we will respond',
            'thank you for your inquiry and we will follow up',
            'thank you for your email', 'thanks for your email', 'thank you for contacting',
            'thank you for reaching out', 'thank you for submitting'
        ]
        # Strong business exclusion to prevent misclassification of business responses
        business_exclusion_words = [
            'insufficient data', 'research', 'guidance', 'advise', 'provide', 'contact',
            'invoice', 'payment', 'bill', 'amount', 'balance', 'due', 'paid', 'check', 
            'account', 'dispute', 'case', 'ticket', 'support', 'office', 'out', 'away'
        ]
        if (any(phrase in text_lower for phrase in thank_you_phrases) and 
            not any(word in text_lower for word in business_exclusion_words)):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.82,
                "General thank you notification", ["general_thank_you"]
            )

        # Default: General Notifications
        return RuleResult(
            "No Reply (with/without info)", "Notifications", 0.6,
            "General notification", ["no_reply_default"]
        )

    def _get_default_result(self, main_category: str) -> RuleResult:
        """Get default result with proper sublabel classification."""
        
        # Use specific sublabel classification for each main category
        if main_category == "Manual Review":
            return RuleResult("Manual Review", "Complex Queries", 0.6, "Default manual review", ["manual_default"])
        elif main_category == "No Reply (with/without info)":
            return RuleResult("No Reply (with/without info)", "Notifications", 0.6, "Default notification", ["no_reply_default"])
        elif main_category == "Invoices Request":
            return RuleResult("Invoices Request", "Request (No Info)", 0.6, "Default invoice request", ["invoice_req_default"])
        elif main_category == "Payments Claim":
            return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.6, "Default payment claim", ["payment_claim_default"])
        elif main_category == "Auto Reply (with/without info)":
            return RuleResult("Auto Reply (with/without info)", "General (Thank You)", 0.6, "Default auto reply", ["auto_reply_default"])
        else:
            return RuleResult("Uncategorized", "General", 0.5, "Uncategorized email", ["uncategorized_default"])

    def _get_fallback_result(self, error_reason: str = "Unknown error") -> RuleResult:
        """Enhanced fallback result with error details."""
        return RuleResult(
            category="Manual Review",
            subcategory="Complex Queries",
            confidence=0.3,
            reason=f"Rule engine fallback: {error_reason}",
            matched_rules=["error_fallback"]
        )

    def clear_cache(self) -> None:
        """Clear pattern cache and reset metrics."""
        self._pattern_cache.clear()
        self.metrics = PerformanceMetrics()
        self.logger.info("🧹 Cache cleared and metrics reset")

    def validate_system_health(self) -> Dict[str, Any]:
        """Validate system health and return diagnostics."""
        health_status = {
            'pattern_matcher_status': 'healthy',
            'cache_status': 'healthy',
            'validation_status': 'healthy',
            'issues': []
        }
        
        try:
            # Test pattern matcher
            if not hasattr(self.pattern_matcher, 'match_text'):
                health_status['pattern_matcher_status'] = 'error'
                health_status['issues'].append('Pattern matcher missing match_text method')
            
            # Test cache
            if len(self._pattern_cache) > 10000:
                health_status['cache_status'] = 'warning'
                health_status['issues'].append('Pattern cache size is large')
            
            # Re-validate patterns
            self._validate_patterns()
            
        except Exception as e:
            health_status['validation_status'] = 'error'
            health_status['issues'].append(f'Validation error: {e}')
        
        return health_status
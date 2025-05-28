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
            "payment made", "check sent", "paid through", "already paid",
            "check is being overnighted", "payment completed", "payment sent",
            "has been paid", "paid", "payment", "settled"
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
        text_lower = text.lower()

        # 1. Out of Office (Auto Reply) detection first!
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
                    reason="Threaded out of office with alternate contact (thread logic)",
                    matched_rules=["thread_ooo_with_contact"]
                )
            else:
                return RuleResult(
                    category="Auto Reply (with/without info)",
                    subcategory="No Info/Autoreply",
                    confidence=0.89,
                    reason="Threaded generic OOO/auto-reply (thread logic)",
                    matched_rules=["thread_ooo"]
                )

        # 2. Ticket/Case Creation (No Reply > Created)
        ticket_creation_phrases = [
            "case opened", "ticket created", "support has been created", "assigned #",
            "request has been created", "support ticket opened", "ticket opened",
            "case number is", "status : waiting for support", "representative will follow-up",
            "support request", "new ticket", "case opened", "support ticket", "view this ticket"
        ]
        if any(phrase in text_lower for phrase in ticket_creation_phrases):
            return RuleResult(
                category="No Reply (with/without info)",
                subcategory="Created",
                confidence=0.9,
                reason="Threaded ticket/case created (thread logic)",
                matched_rules=["thread_ticket_created"]
            )

        # 3. Payment claim (threaded, with/without proof/attachment)
        payment_proof_patterns = [
            r"\battach(ed|ment|ments)?\b", r"\benclosed\b", r"\bproof\b", r"\breceipt\b", r"\bscreenshot\b", r"\bdocument\b",
            r"see (the )?(attached|enclosed)", r"find (the )?(attached|enclosed)", r"attached (is|are|please|copy|herewith)?"
        ]
        payment_hit = any(keyword in text_lower for keyword in self.thread_payment_keywords)
        payment_proof_hit = any(re.search(pattern, text_lower) for pattern in payment_proof_patterns)
        if payment_hit:
            if payment_proof_hit:
                return RuleResult(
                    category="Manual Review",
                    subcategory="Payment Confirmation",
                    confidence=0.93,
                    reason="Threaded payment claim with proof/attachment (thread logic)",
                    matched_rules=["thread_payment_with_proof"]
                )
            return RuleResult(
                category="Payments Claim",
                subcategory="Claims Paid (No Info)",
                confidence=0.92,
                reason="Threaded payment claim without proof (thread logic)",
                matched_rules=["thread_payment_rule"]
            )

        # 4. Invoice request (threaded, with/without attachment)
        invoice_proof_patterns = [
            r"\battach(ed|ment|ments)?\b", r"\benclosed\b", r"\bcopy\b", r"see (the )?(attached|enclosed)",
            r"find (the )?(attached|enclosed)", r"attached (is|are|please|invoice|copy|herewith)?", r"\binvoice attached\b"
        ]
        invoice_hit = any(keyword in text_lower for keyword in self.thread_invoice_keywords)
        invoice_proof_hit = any(re.search(pattern, text_lower) for pattern in invoice_proof_patterns)
        if invoice_hit:
            if invoice_proof_hit:
                return RuleResult(
                    category="Manual Review",
                    subcategory="Invoice Receipt",
                    confidence=0.92,
                    reason="Threaded invoice request with attachment (thread logic)",
                    matched_rules=["thread_invoice_with_attachment_rule"]
                )
            return RuleResult(
                category="Invoices Request",
                subcategory="Request (No Info)",
                confidence=0.91,
                reason="Threaded invoice request without details (thread logic)",
                matched_rules=["thread_invoice_rule"]
            )

        # 5. Manual review for other thread-related business issues (complex fallback)
        manual_review_words = [
            "case", "ticket", "support", "complex", "question", "issue", "problem",
            "follow up", "escalate", "inquiry"
        ]
        if any(word in text_lower for word in manual_review_words):
            return RuleResult(
                category="Manual Review",
                subcategory="Complex Queries",
                confidence=0.81,
                reason="Threaded case/support/complex (thread logic)",
                matched_rules=["thread_manual_rule"]
            )

        # Default thread fallback (catch-all)
        return RuleResult(
            category="Manual Review",
            subcategory="Complex Queries",
            confidence=0.8,
            reason="Threaded fallback (thread logic)",
            matched_rules=["thread_manual_fallback"]
        )

    def classify_sublabel(
    self,
    main_category: str,
    text: str,
    has_thread: bool = False,
    analysis: Optional[TextAnalysis] = None,
    ml_result: Optional[Dict[str, Any]] = None,
    retry_count: int = 3
    ) -> RuleResult:
        """
        Advanced sublabel classification with strict priority on OOO/Auto-Reply,
        Ticket Creation, Thread-aware routing, then NLP, rule, and pattern fallback.
        Attachment/proof is now handled for both threaded and non-threaded mails.
        """
        start_time = time.time()

        text_lower = text.lower().strip() if isinstance(text, str) else ""

        # 0. THREAD-AWARE ROUTING (highest priority!)
        if has_thread:
            return self._handle_thread_email(text)

        # Common patterns for attachment/proof
        payment_proof_patterns = [
            r"\battach(ed|ment|ments)?\b", r"\benclosed\b", r"\bproof\b", r"\breceipt\b", r"\bscreenshot\b", r"\bdocument\b",
            r"see (the )?(attached|enclosed)", r"find (the )?(attached|enclosed)", r"attached (is|are|please|copy|herewith)?"
        ]
        invoice_proof_patterns = [
            r"\battach(ed|ment|ments)?\b", r"\benclosed\b", r"\bcopy\b", r"see (the )?(attached|enclosed)",
            r"find (the )?(attached|enclosed)", r"attached (is|are|please|invoice|copy|herewith)?", r"\binvoice attached\b"
        ]
        payment_proof_hit = any(re.search(pattern, text_lower) for pattern in payment_proof_patterns)
        invoice_proof_hit = any(re.search(pattern, text_lower) for pattern in invoice_proof_patterns)
        payment_hit = any(keyword in text_lower for keyword in self.thread_payment_keywords)
        invoice_hit = any(keyword in text_lower for keyword in self.thread_invoice_keywords)

        for attempt in range(retry_count):
            try:
                self.metrics.total_processed += 1

                # Input validation
                if not text_lower:
                    raise ClassificationError("Invalid input: text must be non-empty string")
                if not main_category or not isinstance(main_category, str) or not main_category.strip():
                    raise ClassificationError("Invalid input: main_category must be non-empty string")

                # Early exit for spam/empty
                if text_lower in ["", "n/a", "unsubscribe"]:
                    self._update_metrics(start_time, success=True)
                    return RuleResult("Uncategorized", "General", 0.1, "Text empty or ignorable", ["uncategorized_empty"])

                # (1) OOO / Auto-Reply: **force this as the very first logic**
                ooo_phrases = [
                    "out of office", "automatic reply", "auto-reply", "i am currently out",
                    "limited access to my email", "will return", "returning to the office", "on vacation", "on leave"
                ]
                if any(ooo in text_lower for ooo in ooo_phrases):
                    auto_reply_result = self._classify_auto_reply_sublabels(text)
                    if auto_reply_result and auto_reply_result.confidence >= 0.8:
                        self._update_metrics(start_time, success=True)
                        return auto_reply_result

                # (2) Support Ticket/Case Creation: run this next to catch "opened/assigned"
                ticket_creation_phrases = [
                    "ticket created", "case opened", "support request created", "request for support has been created",
                    "assigned #", "ticket opened", "case number is", "support ticket opened"
                ]
                if any(phrase in text_lower for phrase in ticket_creation_phrases):
                    return RuleResult(
                        "No Reply (with/without info)", "Created", 0.88,
                        "Support/case/ticket creation detected", ["ticket_created_pattern"]
                    )

                # (3) Payment claim or invoice request with proof/attachment (non-threaded)
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

                # (4) NLP analysis, if available
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

                # (5) Specific sublabel function (rule-based)
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

                # (6) Pattern matcher as fallback
                pattern_result = self._classify_with_cached_patterns(text)
                if pattern_result:
                    if ml_result and 'confidence' in ml_result:
                        pattern_result.confidence = round((pattern_result.confidence * 0.6) + (ml_result['confidence'] * 0.4), 2)
                    self._update_metrics(start_time, success=True)
                    return pattern_result

                # (7) Default fallback
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

                # Auto Reply sublabels - handle composite and atomic topics for OOO
                # Composite topic examples: 'out_of_office_with_alternate_contact'
                if topic.startswith('out_of_office'):
                    # Check for specific subtypes as either separate topics or embedded in topic string
                    if 'with_alternate_contact' in topic or 'with_alternate_contact' in analysis.topics:
                        return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.9, "NLP detected OOO with contact", ["nlp_ooo_contact"])
                    if 'return_date_specified' in topic or 'return_date_specified' in analysis.topics:
                        return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.9, "NLP detected OOO with date", ["nlp_ooo_date"])
                    return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.9, "NLP detected generic OOO", ["nlp_ooo_generic"])

                elif topic == 'case_support_confirmation':
                    return RuleResult("Auto Reply (with/without info)", "Case/Support", 0.9, "NLP detected case confirmation", ["nlp_case_confirm"])
                elif topic == 'general_thank_you':
                    return RuleResult("Auto Reply (with/without info)", "General (Thank You)", 0.9, "NLP detected thank you", ["nlp_thank_you"])
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
        """Classify Manual Review sublabels using specific logic."""
        text_lower = text.lower()

        if any(phrase in text_lower for phrase in [
            'import failed', 'import error', 'failed import', 'unable to import', 'import unsuccessful',
            'not imported', 'was not imported', 'could not import', 'failed to import', 'error importing', 'failure importing'
        ]):
            return RuleResult("Manual Review", "External Submission", 0.85, "Detected import failure", ["import_failure_pattern"])
        # 1. Payment claim with/without proof
        if any(phrase in text_lower for phrase in [
            "i have paid", "payment sent", "already paid", "check sent", "payment completed", "payment is done"
        ]):
            if not any(proof in text_lower for proof in [
                "attached", "attachment", "enclosed", "proof", "receipt", "screenshot", "document"
            ]):
                return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.95, "Payment claim without proof", ["claim_paid_no_proof"])
            else:
                return RuleResult("Manual Review", "Payment Confirmation", 0.92, "Payment claim with proof", ["payment_proof_provided"])

        # 2. Disputes & Payments -> Partial/Disputed Payment
        if any(word in text_lower for word in ['partial payment', 'dispute', 'contested', 'disagreement']):
            return RuleResult("Manual Review", "Partial/Disputed Payment", 0.8, "Dispute/partial payment detected", ["dispute_pattern"])

        # 3. Payment/Invoice Updates -> Payment Confirmation (with proof)
        if any(phrase in text_lower for phrase in [
            'payment confirmation', 'proof of payment', 'payment receipt', 'payment evidence'
        ]):
            return RuleResult("Manual Review", "Payment Confirmation", 0.8, "Payment proof provided", ["payment_proof_pattern"])

        # 4. Multiple invoice request, no info
        if any(word in text_lower for word in ["invoices", "all invoices", "multiple invoices"]) \
            and not any(info in text_lower for info in [
                "invoice #", "inv#", "attached", "attachment", "enclosed", "details", "copy"
            ]):
            return RuleResult("Invoices Request", "Request (No Info)", 0.92, "Multiple invoice request with no info", ["multi_invoice_no_info"])

        # 5. Single invoice request with no info
        if "invoice" in text_lower and not any(info in text_lower for info in [
            "invoice #", "inv#", "attached", "attachment", "enclosed", "details", "copy", "invoices"
        ]):
            return RuleResult("Invoices Request", "Request (No Info)", 0.9, "Single invoice request with no info", ["single_invoice_no_info"])

        # 6. Invoice request with info (push to Manual Review / Invoice Receipt)
        if "invoice" in text_lower and any(info in text_lower for info in [
            "invoice #", "inv#", "attached", "attachment", "enclosed", "details", "copy"
        ]):
            return RuleResult("Manual Review", "Invoice Receipt", 0.92, "Invoice request with supporting info", ["invoice_request_with_info"])

        # 7. Payment/Invoice Updates -> Invoice Receipt (with proof)
        if any(phrase in text_lower for phrase in [
            'invoice receipt', 'proof of invoice', 'invoice copy', 'invoice attached'
        ]):
            return RuleResult("Manual Review", "Invoice Receipt", 0.8, "Invoice proof provided", ["invoice_proof_pattern"])

        # 8. Business Closure -> Closure Notification
        if any(phrase in text_lower for phrase in [
            'business closed', 'company closed', 'out of business', 'ceased operations'
        ]):
            if any(word in text_lower for word in ['payment due', 'outstanding', 'balance']):
                return RuleResult("Manual Review", "Closure + Payment Due", 0.8, "Closure with payment due", ["closure_payment_pattern"])
            else:
                return RuleResult("Manual Review", "Closure Notification", 0.8, "Business closure notification", ["closure_pattern"])

        # 9. Invoices -> External Submission (invoice issues)
        if any(phrase in text_lower for phrase in [
            'invoice issue', 'invoice problem', 'invoice error', 'invoice concern'
        ]):
            return RuleResult("Manual Review", "External Submission", 0.8, "Invoice issue reported", ["invoice_issue_pattern"])

        # 10. Invoices -> Invoice Errors (missing fields)
        if any(phrase in text_lower for phrase in [
            'missing field', 'format mismatch', 'incomplete invoice', 'required field'
        ]):
            return RuleResult("Manual Review", "Invoice Errors (format mismatch)", 0.8, "Invoice format issue", ["invoice_format_pattern"])

        # 11. Payment Details Received
        if any(phrase in text_lower for phrase in [
            'payment details', 'remittance info', 'payment breakdown', 'transaction details'
        ]):
            return RuleResult("Manual Review", "Payment Details Received", 0.8, "Payment details provided", ["payment_details_pattern"])

        # 12. Action/Review/Redirection (Your NEW logic, more specific than the generic inquiry/redirection)
        if any(word in text_lower for word in [
            'review', 'please review', 'forward', 'see below', 'check', 'assist'
        ]):
            return RuleResult("Manual Review", "Inquiry/Redirection", 0.9, "Action requested or redirection", ["manual_review_redirection"])

        # 13. Inquiry/Redirection (generic, catch-all)
        if any(word in text_lower for word in [
            'redirect', 'forward', 'contact instead', 'reach out to'
        ]):
            return RuleResult("Manual Review", "Inquiry/Redirection", 0.8, "Inquiry redirection", ["redirect_pattern"])

        # Default to Complex Queries
        return RuleResult("Manual Review", "Complex Queries", 0.6, "Complex manual review needed", ["complex_default"])

    def _classify_auto_reply_sublabels(self, text: str) -> Optional[RuleResult]:
        """Classify Auto Reply sublabels with strict priority order and robust coverage."""
        text_lower = text.lower()

        # ----- 1. Out of Office / Automatic Reply (with alternate contact and/or return date) -----
        ooo_phrases = [
            'out of office', 'automatic reply', 'auto-reply', 'i am currently out', 'i will be out',
            'i am away', 'not available', 'limited access to email', 'will return', 'returning to the office',
            'i’ll be out', 'will be unavailable', 'away from desk', 'currently unavailable'
        ]
        contact_phrases = [
            'contact', 'reach out', 'alternate', 'replacement', 'for assistance', 'for help',
            'forward your email', 'please forward', 'email to', 'in my absence', 'instead', 'alternate email'
        ]
        return_phrases = [
            'return', 'back on', 'until', 'returning', 'will be back', 'available after', 'rejoin on'
        ]

        # Detect OOO - allow for any OOO phrase to trigger this block
        ooo_hit = any(ooo in text_lower for ooo in ooo_phrases)
        contact_hit = any(c in text_lower for c in contact_phrases)
        return_hit = any(r in text_lower for r in return_phrases)

        if ooo_hit:
            # Both alternate contact and return date
            if contact_hit and return_hit:
                return RuleResult(
                    "Auto Reply (with/without info)", "With Alternate Contact", 0.93,
                    "OOO with alternate contact and return date", ["ooo_with_contact_and_return"]
                )
            # Only alternate contact
            elif contact_hit:
                return RuleResult(
                    "Auto Reply (with/without info)", "With Alternate Contact", 0.92,
                    "OOO with alternate contact info", ["ooo_with_contact"]
                )
            # Only return date
            elif return_hit:
                return RuleResult(
                    "Auto Reply (with/without info)", "Return Date Specified", 0.91,
                    "OOO with return date", ["ooo_with_return_date"]
                )
            # Generic OOO/auto-reply
            else:
                return RuleResult(
                    "Auto Reply (with/without info)", "No Info/Autoreply", 0.9,
                    "Generic OOO or auto-reply", ["ooo_generic_pattern"]
                )

        # ----- 2. Standalone OOO/Auto-Reply Catch-all (if OOO missed above) -----
        if any(phrase in text_lower for phrase in [
            'out of the office', 'currently unavailable', 'limited access to my email',
            'on leave', 'on vacation', 'will respond when back', 'auto reply', 'auto-reply'
        ]):
            return RuleResult(
                "Auto Reply (with/without info)", "No Info/Autoreply", 0.88,
                "Generic OOO/auto-reply fallback", ["ooo_catchall"]
            )

        # ----- 3. Case/Support Confirmations -----
        if any(phrase in text_lower for phrase in [
            'case confirmed', 'support request', 'ticket confirmed', 'request acknowledged',
            'request has been received', 'ticket has been created', 'case has been opened'
        ]):
            return RuleResult(
                "Auto Reply (with/without info)", "Case/Support", 0.85,
                "Case/support confirmation", ["case_confirm_pattern"]
            )

        # ----- 4. Redirects/Updates (property changes, new contact, etc.) -----
        if any(phrase in text_lower for phrase in [
            'property manager', 'contact changed', 'forwarding', 'new contact',
            'department changed', 'forwarded to', 'change of contact', 'contact update'
        ]):
            return RuleResult(
                "Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.8,
                "Contact update", ["redirect_update_pattern"]
            )

        # ----- 5. Survey / Feedback -----
        if any(word in text_lower for word in [
            'survey', 'feedback', 'rate', 'customer satisfaction', 'please rate', 'your opinion'
        ]):
            return RuleResult(
                "Auto Reply (with/without info)", "Survey", 0.8,
                "Survey/feedback request", ["survey_pattern"]
            )

        # ----- 6. General (Thank You) -----
        thank_you = any(phrase in text_lower for phrase in [
            'thank you', 'thanks', 'received your message', 'got your request', 'we received your'
        ])
        # Don't fire "General Thank You" if there's evidence of business action/redirection
        action_words = [
            'review', 'check', 'see below', 'please review', 'forward', 'assist', 'help',
            'bill', 'invoice', 'payment', 'due', 'paid', 'send', 'process', 'attached'
        ]
        if thank_you and not any(word in text_lower for word in action_words):
            return RuleResult(
                "Auto Reply (with/without info)", "General (Thank You)", 0.82,
                "Thank you message", ["thanks_pattern"]
            )

        # ----- 7. Default fallback -----
        return RuleResult(
            "Auto Reply (with/without info)", "General (Thank You)", 0.6,
            "General auto reply (fallback)", ["auto_reply_default"]
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
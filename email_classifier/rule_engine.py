"""
Clean, focused RuleEngine for email classification
"""

import logging
import time
from typing import Dict, Optional, Any, List, re
from dataclasses import dataclass

# Fixed import paths
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

@dataclass 
class PerformanceMetrics:
    total_processed: int = 0
    successful_classifications: int = 0
    errors: int = 0
    avg_processing_time: float = 0.0

class ClassificationError(Exception):
    """Exception for classification processing errors."""
    pass

class RuleEngine:
    """
    Clean RuleEngine - uses your PatternMatcher and NLP classes
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize your components
        self.pattern_matcher = PatternMatcher()
        self.nlp_processor = NLPProcessor()
        
        # Performance metrics
        self.metrics = PerformanceMetrics()
        
        # Basic thread keywords for fallback only
        self.thread_payment_keywords = ["payment", "paid", "check", "settled"]
        self.thread_invoice_keywords = ["invoice", "bill", "statement", "copy"]
        
        self.logger.info("✅ RuleEngine initialized successfully")

    def _update_metrics(self, start_time: float, success: bool) -> None:
        """Update performance metrics."""
        processing_time = time.time() - start_time
        
        if success:
            self.metrics.successful_classifications += 1
        else:
            self.metrics.errors += 1

    def _get_fallback_result(self, reason: str) -> RuleResult:
        """Fallback result."""
        return RuleResult(
            category="Manual Review",
            subcategory="Complex Queries",
            confidence=0.50,
            reason=f"Fallback: {reason}",
            matched_rules=["fallback"]
        )

    def _get_default_result(self, main_category: str) -> RuleResult:
        """Default result."""
        category_defaults = {
            "Manual Review": "Complex Queries",
            "No Reply (with/without info)": "Notifications", 
            "Auto Reply (with/without info)": "No Info/Autoreply",
            "Invoices Request": "Request (No Info)",
            "Payments Claim": "Claims Paid (No Info)"
        }
        
        subcategory = category_defaults.get(main_category, "Complex Queries")
        
        return RuleResult(
            category=main_category,
            subcategory=subcategory,
            confidence=0.60,
            reason=f"Default classification for {main_category}",
            matched_rules=["default"]
        )

    # Add your classification methods here
    def classify_sublabel(
    self,
    main_category: str,
    text: str,
    has_thread: bool = False,
    analysis: Optional[TextAnalysis] = None,
    ml_result: Optional[Dict[str, Any]] = None,
    retry_count: int = 3,
    subject: str = ""
    ) -> RuleResult:
        """
        Advanced sublabel classification with PatternMatcher integration
        Fixed to use pattern files properly and work with thread handler
        """
        start_time = time.time()
        text_lower = text.lower().strip() if isinstance(text, str) else ""
        subject_lower = subject.lower().strip() if isinstance(subject, str) else ""

        # 0. THREAD-AWARE ROUTING (highest priority!)
        if has_thread:
            return self._handle_thread_email(text)

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

                # 1. AUTO-REPLY SUBJECT Detection (HIGHEST PRIORITY)
                if ("automatic reply:" in subject_lower or "auto-reply:" in subject_lower or 
                    "automatic reply" in subject_lower or "auto reply" in subject_lower):
                    
                    # Enhanced OOO detection for non-threaded emails
                    ooo_phrases = [
                        "out of office", "out of the office", "i will be out", "i am currently out",
                        "limited access to my email", "will return", "returning to the office", 
                        "on vacation", "on leave", "currently traveling", "away from desk"
                    ]
                    
                    contact_phrases = [
                        "contact", "reach out", "alternate", "replacement", "for assistance", 
                        "please contact", "call me", "if you need immediate assistance",
                        "call my cell", "call my mobile", "if urgent", "urgent please contact"
                    ]
                    
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
                    
                    # Check for redirects
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

                # 2. NO-REPLY SERVICE ACCOUNT Detection
                no_reply_indicators = [
                    "donotreply", "do-not-reply", "noreply", "no-reply", 
                    "automated", "service account", "system generated", "this is a no-reply email"
                ]
                if any(indicator in text_lower for indicator in no_reply_indicators):
                    return RuleResult(
                        "No Reply (with/without info)", "Notifications", 0.93,
                        "No-reply service account detected", ["no_reply_service_account"]
                    )

                # 3. HIGH PRIORITY: Use PatternMatcher EARLY (after essential checks)
                if hasattr(self, 'pattern_matcher'):
                    main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                        text_lower, exclude_external_proof=True
                    )
                    
                    # High confidence from patterns - trust it!
                    if main_cat and confidence >= 0.85:
                        return RuleResult(
                            main_cat, subcat, confidence,
                            f"High-confidence pattern match: {subcat}", patterns
                        )

                # 4. Processing Error Detection (EARLY - but after patterns)
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

                # 5. Enhanced Dispute Detection (EARLY)
                dispute_phrases = [
                    "amount is in dispute", "this amount is in dispute", "balance is not ours",
                    "balance is not accurate", "not our responsibility", "do not owe", "contested",
                    "disagreement", "refuse", "formally disputing", "not accurate"
                ]
                if any(phrase in text_lower for phrase in dispute_phrases):
                    return RuleResult(
                        "Manual Review", "Partial/Disputed Payment", 0.95,
                        "Dispute/contest detected", ["dispute_detected"]
                    )
                
                # 6. Sales/Promotional Detection
                sales_phrases = [
                    "sale ends", "% off", "discount", "save now", "shop now", 
                    "limited time offer", "memorial day sale", "summer sale",
                    "unsubscribe", "no longer want to receive"
                ]
                if any(phrase in text_lower for phrase in sales_phrases):
                    return RuleResult(
                        "No Reply (with/without info)", "Sales/Offers", 0.95,
                        "Promotional/sales email detected", ["sales_email_detected"]
                    )

                # 7. MEDIUM PRIORITY: PatternMatcher again with lower confidence
                if hasattr(self, 'pattern_matcher'):
                    main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                        text_lower, exclude_external_proof=True
                    )
                    
                    # Medium confidence from patterns
                    if main_cat and confidence >= 0.70:
                        return RuleResult(
                            main_cat, subcat, confidence,
                            f"Medium-confidence pattern match: {subcat}", patterns
                        )

                # 8. Transaction/Proof Details Detection
                transaction_proof_patterns = [
                    r"transaction.*number", r"batch.*number", r"reference.*number",
                    r"confirmation.*number", r"transaction.*id", r"payment.*reference",
                    r"transaction.*and.*batch", r"paid.*via.*\w+.*transaction"
                ]
                if any(re.search(pattern, text_lower) for pattern in transaction_proof_patterns):
                    if not any(phrase in text_lower for phrase in ["% off", "sale ends", "shop now", "unsubscribe"]):
                        if any(word in text_lower for word in ['paid', 'payment', 'settled']):
                            return RuleResult(
                                "Manual Review", "Payment Confirmation", 0.94,
                                "Payment with transaction/proof details", ["payment_with_transaction_proof"]
                            )

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

                # 11. LOWER PRIORITY: PatternMatcher fallback
                if hasattr(self, 'pattern_matcher'):
                    main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                        text_lower, exclude_external_proof=True
                    )
                    
                    # Lower confidence from patterns - with boost
                    if main_cat and confidence >= 0.50:
                        boosted_confidence = min(confidence + 0.15, 0.85)
                        return RuleResult(
                            main_cat, subcat, boosted_confidence,
                            f"Fallback pattern match: {subcat}", patterns
                        )

                # 12. Essential Fallback Patterns (if PatternMatcher misses)
                
                # Payment claims fallback
                payment_claims = [
                    "its been paid", "has been settled", "this has been settled", "already paid", 
                    "been paid to them", "payment was made", "we paid", "bill was paid", 
                    "paid directly to", "settled with", "we sent check on", "sent check on"
                ]
                if any(phrase in text_lower for phrase in payment_claims):
                    return RuleResult(
                        "Payments Claim", "Claims Paid (No Info)", 0.88,
                        "Payment claim detected (fallback)", ["payment_claim_fallback"]
                    )

                # Invoice request fallback
                invoice_request_phrases = [
                    "can you please provide me with outstanding invoices", "provide me with outstanding invoices",
                    "can you please send me copies of any invoices", "send me copies of any invoices",
                    "can you send me the invoice", "provide us with the invoice", "send me the invoice copy",
                    "need invoice copy", "provide invoice copy", "outstanding invoices owed"
                ]
                if any(phrase in text_lower for phrase in invoice_request_phrases):
                    return RuleResult(
                        "Invoices Request", "Request (No Info)", 0.88,
                        "Invoice request detected (fallback)", ["invoice_request_fallback"]
                    )

                # 13. NLP analysis, if available
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

                # 14. Specific sublabel functions (your existing rule-based methods)
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

                # 15. Legacy pattern matcher as final fallback
                pattern_result = self._classify_with_cached_patterns(text)
                if pattern_result:
                    if ml_result and 'confidence' in ml_result:
                        pattern_result.confidence = round((pattern_result.confidence * 0.6) + (ml_result['confidence'] * 0.4), 2)
                    self._update_metrics(start_time, success=True)
                    return pattern_result

                # 16. Default fallback
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


    def _handle_thread_email(self, text: str) -> RuleResult:
        """
        Clean thread handler - Uses PatternMatcher FIRST, then essential fallbacks
        Works properly with classify_sublabel function
        """
        text_lower = text.lower().strip()
        
        # 1. OUT OF OFFICE - MUST WORK (High priority check)
        ooo_phrases = ["out of office", "automatic reply", "auto-reply", "auto reply", "away from desk", "on leave"]
        if any(phrase in text_lower for phrase in ooo_phrases):
            contact_words = ["contact", "reach out", "alternate", "assistance", "forward"]
            if any(word in text_lower for word in contact_words):
                return RuleResult(
                    category="Auto Reply (with/without info)",
                    subcategory="With Alternate Contact",
                    confidence=0.92,
                    reason="OOO with contact info",
                    matched_rules=["ooo_with_contact"]
                )
            else:
                return RuleResult(
                    category="Auto Reply (with/without info)",
                    subcategory="No Info/Autoreply",
                    confidence=0.89,
                    reason="Generic OOO",
                    matched_rules=["ooo_basic"]
                )
        
        # 2. USE YOUR PATTERN FILES (Primary method)
        if hasattr(self, 'pattern_matcher'):
            main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                text_lower, exclude_external_proof=True
            )
            
            # Trust your patterns if confidence is good
            if main_cat and confidence >= 0.75:
                return RuleResult(
                    category=main_cat,
                    subcategory=subcat,
                    confidence=confidence,
                    reason=f"Thread pattern match: {subcat}",
                    matched_rules=patterns
                )
        
        # 3. PROCESSING ERRORS & NOTIFICATIONS (Must work for No Reply)
        if any(phrase in text_lower for phrase in ["pdf not attached", "processing error", "case rejection", "ticket created"]):
            if "ticket created" in text_lower or "case opened" in text_lower:
                return RuleResult(
                    category="No Reply (with/without info)",
                    subcategory="Created",
                    confidence=0.90,
                    reason="Ticket/case created",
                    matched_rules=["ticket_created"]
                )
            else:
                return RuleResult(
                    category="No Reply (with/without info)",
                    subcategory="Processing Errors",
                    confidence=0.92,
                    reason="Processing error detected",
                    matched_rules=["processing_error"]
                )
        
        # 4. SALES/OFFERS (Must work for No Reply)
        sales_phrases = ["special offer", "promotional offer", "limited time", "discount", "flash sale"]
        if any(phrase in text_lower for phrase in sales_phrases):
            return RuleResult(
                category="No Reply (with/without info)",
                subcategory="Sales/Offers",
                confidence=0.88,
                reason="Sales/promotional content",
                matched_rules=["sales_offer"]
            )
        
        # 5. HIGH-VALUE AMOUNT (Can't be in patterns - dynamic)
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
                            reason=f"High-value amount: {amount_str}",
                            matched_rules=["high_value_amount"]
                        )
                except (ValueError, AttributeError):
                    continue
        
        # 6. LEGAL OVERRIDE (High priority)
        legal_phrases = ['attorney', 'law firm', 'esq.', 'legal counsel']
        if any(phrase in text_lower for phrase in legal_phrases):
            return RuleResult(
                category="Manual Review",
                subcategory="Complex Queries",
                confidence=0.95,
                reason="Legal communication",
                matched_rules=["legal_communication"]
            )
        
        # 7. TRY PATTERN MATCHER AGAIN (Lower confidence)
        if hasattr(self, 'pattern_matcher'):
            main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                text_lower, exclude_external_proof=True
            )
            
            # Accept lower confidence for threads
            if main_cat and confidence >= 0.50:
                boosted_confidence = min(confidence + 0.15, 0.90)
                return RuleResult(
                    category=main_cat,
                    subcategory=subcat,
                    confidence=boosted_confidence,
                    reason=f"Thread pattern match: {subcat}",
                    matched_rules=patterns
                )
        
        # 8. ESSENTIAL FALLBACKS (Payment/Invoice/Dispute)
        
        # Payment claims
        if any(word in text_lower for word in ["payment sent", "already paid", "been paid", "check sent"]):
            return RuleResult(
                category="Payments Claim",
                subcategory="Claims Paid (No Info)",
                confidence=0.85,
                reason="Payment claim detected",
                matched_rules=["payment_claim"]
            )
        
        # Disputes
        if any(word in text_lower for word in ["dispute", "contested", "not ours", "do not owe"]):
            return RuleResult(
                category="Manual Review",
                subcategory="Partial/Disputed Payment",
                confidence=0.92,
                reason="Dispute detected",
                matched_rules=["dispute_detected"]
            )
        
        # Invoice requests
        if any(phrase in text_lower for phrase in ["send invoice", "need invoice", "invoice copy"]):
            return RuleResult(
                category="Invoices Request",
                subcategory="Request (No Info)",
                confidence=0.88,
                reason="Invoice request detected",
                matched_rules=["invoice_request"]
            )
        
        # Contact redirections
        if any(phrase in text_lower for phrase in ["no longer with", "please contact", "direct inquiries"]):
            return RuleResult(
                category="Auto Reply (with/without info)",
                subcategory="Redirects/Updates (property changes)",
                confidence=0.90,
                reason="Contact redirection",
                matched_rules=["contact_redirect"]
            )
        
        # 9. BASIC KEYWORD SAFETY NET
        # Basic payment fallback
        if "payment" in text_lower and any(word in text_lower for word in ["sent", "paid", "made"]):
            return RuleResult(
                category="Payments Claim",
                subcategory="Claims Paid (No Info)",
                confidence=0.75,
                reason="Basic payment detected",
                matched_rules=["payment_basic"]
            )
        
        # Basic invoice fallback
        if "invoice" in text_lower and any(word in text_lower for word in ["send", "need", "copy"]):
            return RuleResult(
                category="Invoices Request",
                subcategory="Request (No Info)",
                confidence=0.73,
                reason="Basic invoice request",
                matched_rules=["invoice_basic"]
            )
        
        # 10. FINAL FALLBACK
        return RuleResult(
            category="Manual Review",
            subcategory="Complex Queries",
            confidence=0.60,
            reason="Thread email - manual review",
            matched_rules=["thread_fallback"]
        )

    def _classify_with_nlp_analysis(self, main_category: str, text: str, analysis: TextAnalysis) -> Optional[RuleResult]:
        """
        Use NLP analysis to make intelligent classification decisions
        Fixed to work with PatternMatcher and pattern files properly
        """
        try:
            # Check if PatternMatcher already found something with high confidence
            # If so, use NLP to enhance/validate rather than override
            if hasattr(self, 'pattern_matcher'):
                pattern_cat, pattern_subcat, pattern_conf, pattern_rules = self.pattern_matcher.match_text(
                    text.lower(), exclude_external_proof=True
                )
                if pattern_cat and pattern_conf >= 0.85:
                    # High confidence pattern match - NLP just validates
                    self.logger.debug(f"High confidence pattern found, NLP validates: {pattern_subcat}")
                    return None  # Let pattern result stand
            
            # Manual Review sublabels (matching your pattern file structure)
            for topic in analysis.topics:
                # Manual Review categories
                if topic in ['partial_disputed_payment', 'dispute', 'contested_payment']:
                    return RuleResult("Manual Review", "Partial/Disputed Payment", 0.88, 
                                    "NLP detected dispute topic", ["nlp_dispute_topic"])
                
                elif topic in ['payment_confirmation', 'payment_proof', 'transaction_proof']:
                    return RuleResult("Manual Review", "Payment Confirmation", 0.88, 
                                    "NLP detected payment proof", ["nlp_payment_proof"])
                
                elif topic in ['invoice_receipt', 'invoice_attachment', 'invoice_proof']:
                    return RuleResult("Manual Review", "Invoice Receipt", 0.88, 
                                    "NLP detected invoice proof", ["nlp_invoice_proof"])
                
                elif topic in ['closure_notification', 'business_closed', 'bankruptcy']:
                    return RuleResult("Manual Review", "Closure Notification", 0.88, 
                                    "NLP detected closure topic", ["nlp_closure"])
                
                elif topic in ['external_submission', 'invoice_issue', 'import_failed']:
                    return RuleResult("Manual Review", "External Submission", 0.88, 
                                    "NLP detected submission issue", ["nlp_submission_issue"])
                
                elif topic in ['invoice_errors', 'format_mismatch', 'format_error']:
                    return RuleResult("Manual Review", "Invoice Errors (format mismatch)", 0.88, 
                                    "NLP detected format error", ["nlp_format_error"])
                
                elif topic in ['payment_details_received', 'payment_timeline', 'payment_schedule']:
                    return RuleResult("Manual Review", "Payment Details Received", 0.88, 
                                    "NLP detected payment details", ["nlp_payment_details"])
                
                elif topic in ['inquiry_redirection', 'information_request', 'guidance_needed']:
                    return RuleResult("Manual Review", "Inquiry/Redirection", 0.88, 
                                    "NLP detected inquiry/redirection", ["nlp_inquiry"])
                
                elif topic in ['complex_queries', 'legal_communication', 'escalation']:
                    return RuleResult("Manual Review", "Complex Queries", 0.88, 
                                    "NLP detected complex content", ["nlp_complex"])

                # No Reply categories
                elif topic in ['sales_offers', 'promotional', 'marketing', 'discount']:
                    return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.88, 
                                    "NLP detected sales/promotional content", ["nlp_sales"])
                
                elif topic in ['processing_errors', 'system_error', 'pdf_not_attached']:
                    return RuleResult("No Reply (with/without info)", "Processing Errors", 0.88, 
                                    "NLP detected processing error", ["nlp_processing_error"])
                
                elif topic in ['import_failures', 'import_error', 'upload_failed']:
                    return RuleResult("No Reply (with/without info)", "Import Failures", 0.88, 
                                    "NLP detected import failure", ["nlp_import_failure"])
                
                elif topic in ['created', 'ticket_created', 'case_opened', 'case_created']:
                    return RuleResult("No Reply (with/without info)", "Created", 0.88, 
                                    "NLP detected ticket/case creation", ["nlp_ticket_created"])
                
                elif topic in ['resolved', 'ticket_resolved', 'case_closed', 'case_resolved']:
                    return RuleResult("No Reply (with/without info)", "Resolved", 0.88, 
                                    "NLP detected resolution", ["nlp_resolved"])
                
                elif topic in ['notifications', 'system_notification', 'automated_message', 'general_thank_you']:
                    return RuleResult("No Reply (with/without info)", "Notifications", 0.88, 
                                    "NLP detected notification/automated message", ["nlp_notification"])

                # Invoice Request categories
                elif topic in ['request_no_info', 'invoice_request', 'need_invoice', 'send_invoice']:
                    return RuleResult("Invoices Request", "Request (No Info)", 0.88, 
                                    "NLP detected invoice request", ["nlp_invoice_request"])

                # Payment Claim categories
                elif topic in ['claims_paid_no_info', 'payment_claim', 'already_paid', 'payment_sent']:
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.88, 
                                    "NLP detected payment claim", ["nlp_payment_claim"])

                # Auto Reply categories (simplified OOO handling)
                elif topic in ['with_alternate_contact', 'ooo_with_contact', 'out_of_office_contact']:
                    return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.88, 
                                    "NLP detected OOO with contact", ["nlp_ooo_contact"])
                
                elif topic in ['return_date_specified', 'ooo_with_date', 'return_date']:
                    return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.88, 
                                    "NLP detected OOO with return date", ["nlp_ooo_date"])
                
                elif topic in ['no_info_autoreply', 'out_of_office', 'ooo_generic', 'auto_reply']:
                    return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.88, 
                                    "NLP detected generic auto-reply", ["nlp_auto_reply"])
                
                elif topic in ['redirects_updates', 'contact_change', 'property_change', 'redirection']:
                    return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.88, 
                                    "NLP detected redirect/update", ["nlp_redirect"])
                
                elif topic in ['case_support', 'support_confirmation', 'case_confirmation']:
                    return RuleResult("Auto Reply (with/without info)", "Case/Support", 0.88, 
                                    "NLP detected case/support confirmation", ["nlp_case_support"])
                
                elif topic in ['survey', 'feedback_request', 'customer_satisfaction']:
                    return RuleResult("Auto Reply (with/without info)", "Survey", 0.88, 
                                    "NLP detected survey/feedback request", ["nlp_survey"])

            # Use urgency and complexity scores for classification enhancement
            if hasattr(analysis, 'urgency_score') and analysis.urgency_score > 0.8:
                return RuleResult("Manual Review", "Complex Queries", 0.82,
                                f"High urgency detected (score: {analysis.urgency_score:.2f})", ["nlp_high_urgency"])

            if hasattr(analysis, 'complexity_score') and analysis.complexity_score > 0.8:
                return RuleResult("Manual Review", "Complex Queries", 0.82,
                                f"High complexity detected (score: {analysis.complexity_score:.2f})", ["nlp_high_complexity"])

            # Check financial terms for payment/invoice classification
            financial_terms = getattr(analysis, "financial_terms", [])
            if len(financial_terms) > 3 and main_category in ["Manual Review", "Payments Claim", "Invoices Request"]:
                return RuleResult("Manual Review", "Payment Details Received", 0.75,
                                f"Multiple financial terms detected: {financial_terms[:3]}", ["nlp_financial_terms"])

            # Business keywords that suggest manual review
            business_keywords = getattr(analysis, "business_keywords", [])
            if len(business_keywords) > 5:
                return RuleResult("Manual Review", "Complex Queries", 0.75,
                                f"Complex business content detected", ["nlp_business_complexity"])

            return None

        except Exception as e:
            self.logger.error(f"❌ NLP classification error: {e}")
            return None

    def _classify_with_cached_patterns(self, text: str) -> Optional[RuleResult]:
        """Final fallback - just use PatternMatcher one more time"""
        try:
            if hasattr(self, 'pattern_matcher'):
                main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                    text.lower(), exclude_external_proof=True
                )
                
                # Very low confidence for absolute final fallback
                if main_cat and confidence >= 0.30:
                    return RuleResult(
                        category=main_cat,
                        subcategory=subcat, 
                        confidence=min(confidence + 0.10, 0.75),  # Slight boost
                        reason=f"Final pattern fallback: {subcat}",
                        matched_rules=patterns
                    )
            return None
        except Exception as e:
            self.logger.error(f"❌ Final pattern fallback error: {e}")
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
        """
        CLEAN Manual Review classifier - handles only cases PatternMatcher can't
        No duplication with pattern files - lets PatternMatcher do the heavy lifting
        """
        text_lower = text.lower().strip()
        
        # 1. TRY PATTERNMATCHER FIRST (Your patterns are comprehensive!)
        if hasattr(self, 'pattern_matcher'):
            main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                text_lower, exclude_external_proof=True
            )
            
            # If PatternMatcher found Manual Review category, trust it
            if main_cat == "Manual Review" and confidence >= 0.70:
                return RuleResult(
                    main_cat, subcat, confidence,
                    f"Pattern match: {subcat}", patterns
                )
        
        # 2. DYNAMIC HIGH-VALUE AMOUNTS (Can't be in patterns - amounts change)
        amount_pattern = re.compile(r'\$[\d,]+\.?\d*')
        amounts = amount_pattern.findall(text_lower)
        if amounts:
            for amount_str in amounts:
                try:
                    amount_value = float(amount_str.replace('$', '').replace(',', ''))
                    if amount_value > 50000:  # Very high value
                        return RuleResult(
                            "Manual Review", "Complex Queries", 0.95,
                            f"Very high-value amount: {amount_str}", ["high_value_detected"]
                        )
                    elif amount_value > 10000:  # High value  
                        return RuleResult(
                            "Manual Review", "Complex Queries", 0.88,
                            f"High-value amount: {amount_str}", ["medium_high_value_detected"]
                        )
                except (ValueError, AttributeError):
                    continue
        
        # 3. LEGAL/ATTORNEY OVERRIDE (High priority)
        legal_phrases = ['attorney', 'law firm', 'esq.', 'legal counsel', 'counsel for']
        if any(phrase in text_lower for phrase in legal_phrases):
            return RuleResult(
                "Manual Review", "Complex Queries", 0.95,
                "Legal/attorney communication", ["legal_communication_detected"]
            )
        
        # 4. BUSINESS CLOSURE WITH PAYMENT (Dynamic combination)
        closure_words = ['closed', 'bankruptcy', 'ceased operations', 'out of business']
        payment_words = ['payment', 'due', 'outstanding', 'balance', 'owe']
        
        closure_hit = any(word in text_lower for word in closure_words)
        payment_hit = any(word in text_lower for word in payment_words)
        
        if closure_hit and payment_hit:
            return RuleResult(
                "Manual Review", "Closure + Payment Due", 0.92,
                "Business closure with payment implications", ["closure_payment_combo"]
            )
        elif closure_hit:
            return RuleResult(
                "Manual Review", "Closure Notification", 0.88,
                "Business closure notification", ["closure_only"]
            )
        
        # 5. MULTIPLE COMPLEX INDICATORS (Dynamic analysis)
        complex_indicators = ['dispute', 'attorney', 'closure', 'error', 'escalate', 'urgent']
        indicator_count = sum(1 for indicator in complex_indicators if indicator in text_lower)
        
        if indicator_count >= 3:  # Multiple complex issues
            return RuleResult(
                "Manual Review", "Complex Queries", 0.85,
                f"Multiple complexity indicators ({indicator_count})", ["multi_complexity"]
            )
        
        # 6. LONG BUSINESS COMMUNICATION (Dynamic length analysis)
        word_count = len(text_lower.split())
        if word_count > 150:  # Long email
            business_terms = ['payment', 'invoice', 'account', 'balance', 'dispute', 'business']
            business_count = sum(1 for term in business_terms if term in text_lower)
            
            if business_count >= 3:  # Multiple business terms in long email
                return RuleResult(
                    "Manual Review", "Complex Queries", 0.80,
                    f"Long business communication ({word_count} words)", ["long_business_text"]
                )
        
        # 7. ESCALATION KEYWORD COMBINATIONS (Dynamic combos)
        escalation_combos = [
            ['urgent', 'payment'], ['immediate', 'attention'], ['escalate', 'manager'],
            ['supervisor', 'complaint'], ['legal', 'action']
        ]
        
        for combo in escalation_combos:
            if all(word in text_lower for word in combo):
                return RuleResult(
                    "Manual Review", "Complex Queries", 0.90,
                    f"Escalation combo: {' + '.join(combo)}", ["escalation_combo"]
                )
        
        # 8. TRY PATTERNMATCHER AGAIN (Lower confidence)
        if hasattr(self, 'pattern_matcher'):
            main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                text_lower, exclude_external_proof=True
            )
            
            # Accept lower confidence if it's Manual Review
            if main_cat == "Manual Review" and confidence >= 0.50:
                boosted_confidence = min(confidence + 0.15, 0.85)
                return RuleResult(
                    main_cat, subcat, boosted_confidence,
                    f"Pattern match (boosted): {subcat}", patterns
                )
        
        # 9. BASIC BUSINESS CONTENT (Very restrictive fallback)
        essential_business = ['invoice', 'payment', 'account', 'balance']
        if any(term in text_lower for term in essential_business):
            return RuleResult(
                "Manual Review", "Complex Queries", 0.65,
                "Basic business content", ["basic_business_content"]
            )
        
        # 10. FINAL FALLBACK (Very low confidence)
        return RuleResult(
            "Manual Review", "Complex Queries", 0.50,
            "Generic manual review", ["generic_fallback"]
        )

    def _classify_auto_reply_sublabels(self, text: str) -> Optional[RuleResult]:
        """
        CLEAN Auto Reply classifier with complete regex patterns
        """
        text_lower = text.lower().strip()
        
        # 1. EARLY ESCALATION - Payment negotiation
        payment_negotiation_phrases = [
            'partial payment', 'payment plan', 'delayed payment', 'we will pay this just not at this moment',
            'will get it paid however', 'not paying right now', 'working out a payment', 'awaiting funds'
        ]
        if any(phrase in text_lower for phrase in payment_negotiation_phrases):
            return None  # Escalate to Manual Review
        
        # 2. COMPLEX BUSINESS CHANGES - Should escalate
        complex_business_phrases = [
            'process change', 'new system', 'workflow tool', 'submit all future invoices',
            'will no longer be accepted', 'new process', 'system change', 'procedure change'
        ]
        if any(phrase in text_lower for phrase in complex_business_phrases):
            return None  # Escalate to Manual Review
        
        # 3. USE YOUR PATTERN FILES (Primary method)
        if hasattr(self, 'pattern_matcher'):
            main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                text_lower, exclude_external_proof=True
            )
            
            if main_cat == "Auto Reply (with/without info)" and confidence >= 0.75:
                return RuleResult(
                    main_cat, subcat, confidence,
                    f"Pattern match: {subcat}", patterns
                )
        
        # 4. COMPLETE OOO WITH REGEX DETECTION (Dynamic - can't be in patterns)
        import re
        
        # All your original regex patterns
        contact_regex = re.compile(r"(call|mobile|cell|contact)[^\n]{0,40}\d{3,}", re.I)
        return_regex = re.compile(
            r'return(ing)?[^\n]{0,40}(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}(st|nd|rd|th)?|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}-\d{1,2}-\d{2,4})',
            re.I)
        date_range_regex = re.compile(
            r'(out of|from).*?(\d{1,2}/\d{1,2}|\d{1,2}(st|nd|rd|th)?).*?(to|through|until).*?(\d{1,2}/\d{1,2}|\d{1,2}(st|nd|rd|th)?)',
            re.I)
        
        # Basic OOO detection
        ooo_phrases = ['out of office', 'automatic reply', 'auto-reply', 'auto reply', 'away', 'vacation', 'leave']
        ooo_found = any(phrase in text_lower for phrase in ooo_phrases)
        
        # Regex-based detection
        contact_found = bool(contact_regex.search(text_lower))
        return_found = bool(return_regex.search(text_lower))
        date_range_found = bool(date_range_regex.search(text_lower))
        
        # Basic contact keywords
        contact_keywords = ['contact', 'reach out', 'alternate', 'please contact', 'call me']
        contact_keyword_found = any(word in text_lower for word in contact_keywords)
        
        if ooo_found:
            if contact_found or contact_keyword_found:
                return RuleResult(
                    "Auto Reply (with/without info)", "With Alternate Contact", 0.93,
                    "OOO with contact info (regex + keywords)", ["ooo_contact_complete"]
                )
            elif return_found or date_range_found:
                return RuleResult(
                    "Auto Reply (with/without info)", "Return Date Specified", 0.91,
                    "OOO with return date/range (regex)", ["ooo_date_complete"]
                )
            else:
                return RuleResult(
                    "Auto Reply (with/without info)", "No Info/Autoreply", 0.90,
                    "Generic OOO", ["ooo_generic_complete"]
                )
        
        # 5. SERVICE ACCOUNT DETECTION
        service_domains = ['noreply@', 'donotreply@', 'no-reply@', 'service@', 'automated@']
        if any(domain in text_lower for domain in service_domains):
            return RuleResult(
                "Auto Reply (with/without info)", "No Info/Autoreply", 0.91,
                "Service account email", ["service_account_domain"]
            )
        
        # 6. CASE/SUPPORT WITH CASE NUMBERS
        case_number_patterns = [
            r'case\s*#?\s*\d+', r'ticket\s*#?\s*\d+', r'reference\s*#?\s*\d+',
            r'case\s+number\s*:?\s*\d+', r'support\s+id\s*:?\s*\d+'
        ]
        
        case_number_found = any(re.search(pattern, text_lower) for pattern in case_number_patterns)
        support_words = ['support', 'case', 'ticket', 'request', 'thank you for contacting']
        
        if case_number_found and any(word in text_lower for word in support_words):
            business_exclusion = ['invoice', 'payment', 'bill', 'insufficient data']
            if not any(word in text_lower for word in business_exclusion):
                return RuleResult(
                    "Auto Reply (with/without info)", "Case/Support", 0.89,
                    "Support case with case number", ["support_case_number"]
                )
        
        # 7. EMERGENCY/FACILITIES
        emergency_phrases = ['facilities emergency', 'emergency please call', 'emergency contact']
        if any(phrase in text_lower for phrase in emergency_phrases):
            return RuleResult(
                "Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.89,
                "Emergency/facilities instructions", ["emergency_instructions"]
            )
        
        # 8. QUARANTINE REPORTS
        if "quarantined email report" in text_lower or "quarantine report" in text_lower:
            return RuleResult(
                "Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.90,
                "Email quarantine report", ["quarantine_report"]
            )
        
        # 9. TRY PATTERN MATCHER AGAIN (Lower confidence)
        if hasattr(self, 'pattern_matcher'):
            main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                text_lower, exclude_external_proof=True
            )
            
            if main_cat == "Auto Reply (with/without info)" and confidence >= 0.50:
                boosted_confidence = min(confidence + 0.15, 0.85)
                return RuleResult(
                    main_cat, subcat, boosted_confidence,
                    f"Pattern match (boosted): {subcat}", patterns
                )
        
        # 10. BASIC FALLBACKS
        if any(phrase in text_lower for phrase in ['no longer with', 'please contact', 'contact changed']):
            return RuleResult(
                "Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.75,
                "Basic contact change", ["basic_contact_change"]
            )
        
        if any(phrase in text_lower for phrase in ['thank you for contacting', 'we have received your request']):
            business_exclusion = ['invoice', 'payment', 'insufficient data']
            if not any(word in text_lower for word in business_exclusion):
                return RuleResult(
                    "Auto Reply (with/without info)", "Case/Support", 0.70,
                    "Basic support confirmation", ["basic_support_fallback"]
                )
        
        # 11. FINAL FALLBACK
        return RuleResult(
            "Auto Reply (with/without info)", "No Info/Autoreply", 0.60,
            "Generic auto reply fallback", ["auto_reply_final_fallback"]
    )

    def _classify_no_reply_sublabels(self, text: str) -> Optional[RuleResult]:
        """
        CLEAN No Reply classifier - uses PatternMatcher first, handles only dynamic cases
        No duplication with pattern files
        """
        text_lower = text.lower().strip()
        
        # 1. BUSINESS-CRITICAL ESCALATIONS (Must go to Manual Review)
        
        # Import failures with business impact
        if 'import failed' in text_lower or 'import error' in text_lower:
            business_critical = ['invoice', 'payment', 'submission', 'manual', 'business']
            if any(word in text_lower for word in business_critical):
                return RuleResult(
                    "Manual Review", "External Submission", 0.88,
                    "Business-critical import failure", ["import_failure_escalated"]
                )
        
        # Open tickets requiring attention
        open_ticket_phrases = ['ticket still open', 'case remains open', 'ticket pending', 'awaiting response']
        if any(phrase in text_lower for phrase in open_ticket_phrases):
            return RuleResult(
                "Manual Review", "Complex Queries", 0.87,
                "Open ticket requiring attention", ["ticket_open_escalated"]
            )
        
        # Invoice/payment processing issues
        payment_issues = ['invoice canceled', 'payment canceled', 'payment rejected', 'invoice rejected', 'payment waived']
        if any(phrase in text_lower for phrase in payment_issues):
            return RuleResult(
                "Manual Review", "Complex Queries", 0.86,
                "Invoice/payment processing issue", ["payment_issue_escalated"]
            )
        
        # Business closure with payment implications
        closure_phrases = ['business closed', 'company closed', 'out of business', 'ceased operations']
        if any(phrase in text_lower for phrase in closure_phrases):
            payment_terms = ['payment', 'due', 'outstanding', 'balance', 'owed', 'invoice']
            if any(word in text_lower for word in payment_terms):
                return RuleResult(
                    "Manual Review", "Closure + Payment Due", 0.88,
                    "Business closure with payment implications", ["closure_payment_escalated"]
                )
        
        # 2. USE YOUR PATTERN FILES (Primary method)
        if hasattr(self, 'pattern_matcher'):
            main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                text_lower, exclude_external_proof=True
            )
            
            # If PatternMatcher found No Reply category, trust it
            if main_cat == "No Reply (with/without info)" and confidence >= 0.75:
                return RuleResult(
                    main_cat, subcat, confidence,
                    f"Pattern match: {subcat}", patterns
                )
        
        # 3. SERVICE ACCOUNT ROUTING (Dynamic decision)
        service_account_phrases = [
            'automated system', 'system generated', 'do not reply to this email',
            'this is an automated message', 'automated notification'
        ]
        contact_indicators = ['call', 'contact', 'email', 'phone', 'assistance', 'help']
        
        if any(phrase in text_lower for phrase in service_account_phrases):
            if not any(contact in text_lower for contact in contact_indicators):
                return RuleResult(
                    "No Reply (with/without info)", "Notifications", 0.89,
                    "Pure automated system notification", ["automated_system_pure"]
                )
            # If has contact info, escalate to Auto Reply
            return None
        
        # 4. DYNAMIC TICKET/CASE NUMBER DETECTION
        import re
        ticket_patterns = [
            r'ticket\s*#?\s*\d+', r'case\s*#?\s*\d+', r'case\s+number\s*:?\s*\d+',
            r'support\s+id\s*:?\s*\d+', r'assigned\s*#\s*\d+'
        ]
        
        ticket_number_found = any(re.search(pattern, text_lower) for pattern in ticket_patterns)
        
        # Ticket creation with numbers
        if ticket_number_found and any(word in text_lower for word in ['created', 'opened', 'received']):
            return RuleResult(
                "No Reply (with/without info)", "Created", 0.90,
                "Ticket creation with number", ["ticket_created_numbered"]
            )
        
        # Ticket resolution with numbers
        if ticket_number_found and any(word in text_lower for word in ['resolved', 'closed', 'solved']):
            return RuleResult(
                "No Reply (with/without info)", "Resolved", 0.90,
                "Ticket resolution with number", ["ticket_resolved_numbered"]
            )
        
        # 5. EMAIL DOMAIN DETECTION (Dynamic)
        no_reply_domains = ['noreply@', 'donotreply@', 'no-reply@', 'system@', 'automated@']
        if any(domain in text_lower for domain in no_reply_domains):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.88,
                "No-reply email domain", ["no_reply_domain"]
            )
        
        # 6. SECURITY ALERTS (High priority)
        security_phrases = ['security alert', 'login attempt', 'password reset', 'unauthorized access']
        if any(phrase in text_lower for phrase in security_phrases):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.87,
                "Security/authentication notification", ["security_notification"]
            )
        
        # 7. TRY PATTERN MATCHER AGAIN (Lower confidence)
        if hasattr(self, 'pattern_matcher'):
            main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                text_lower, exclude_external_proof=True
            )
            
            # Accept lower confidence for No Reply
            if main_cat == "No Reply (with/without info)" and confidence >= 0.50:
                boosted_confidence = min(confidence + 0.15, 0.85)
                return RuleResult(
                    main_cat, subcat, boosted_confidence,
                    f"Pattern match (boosted): {subcat}", patterns
                )
        
        # 8. BASIC NO-REPLY FALLBACKS (Safety net)
        
        # Basic processing errors
        if any(word in text_lower for word in ['processing error', 'failed to process', 'delivery failed']):
            return RuleResult(
                "No Reply (with/without info)", "Processing Errors", 0.80,
                "Basic processing error", ["basic_processing_error"]
            )
        
        # Basic sales/promotional
        if any(word in text_lower for word in ['special offer', 'limited time', 'discount', 'promotion']):
            return RuleResult(
                "No Reply (with/without info)", "Sales/Offers", 0.78,
                "Basic promotional content", ["basic_sales_offer"]
            )
        
        # Basic system notifications
        if any(word in text_lower for word in ['notification', 'alert', 'system', 'automated']):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.75,
                "Basic system notification", ["basic_notification"]
            )
        
        # Basic thank you (with strong business exclusion)
        thank_you_phrases = ['thank you for your email', 'thanks for contacting', 'thank you for reaching out']
        business_exclusion = [
            'insufficient data', 'research', 'guidance', 'invoice', 'payment', 'bill', 
            'case', 'ticket', 'support', 'out of office', 'away'
        ]
        
        if (any(phrase in text_lower for phrase in thank_you_phrases) and 
            not any(word in text_lower for word in business_exclusion)):
            return RuleResult(
                "No Reply (with/without info)", "Notifications", 0.70,
                "Basic thank you notification", ["basic_thank_you"]
            )
        
        # 9. FINAL FALLBACK
        return RuleResult(
            "No Reply (with/without info)", "Notifications", 0.60,
            "General notification fallback", ["no_reply_final_fallback"]
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
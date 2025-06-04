"""
Clean, focused RuleEngine for email classification
"""
import logging
import time
import re
from typing import Dict, Optional, Any, List
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
    pattern_cache_hits: int = 0
    pattern_cache_misses: int = 0

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
        
        # Pattern cache
        self._pattern_cache = {}
        
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
        """Enhanced email classification with strengthened payment claims, invoice requests, and manual review detection"""
        start_time = time.time()
        text_lower = text.lower().strip() if isinstance(text, str) else ""
        subject_lower = subject.lower().strip() if isinstance(subject, str) else ""

        try:
            self.metrics.total_processed += 1

            if not text_lower and not subject_lower:
                return RuleResult("Uncategorized", "General", 0.1, "Empty input", ["empty_input"])
            
            if not main_category or not isinstance(main_category, str):
                return RuleResult("Uncategorized", "General", 0.1, "Invalid main category", ["invalid_category"])

            # STEP 1: Auto-reply subject detection
            auto_reply_subjects = ["automatic reply:", "auto-reply:", "automatic reply", "auto reply"]
            if any(indicator in subject_lower for indicator in auto_reply_subjects):
                business_terms = ["dispute", "owe nothing", "payment made", "check sent", "invoice"]
                if not any(term in text_lower for term in business_terms):
                    if "out of office" in text_lower or "away from" in text_lower:
                        if self._has_return_date(text_lower):
                            return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.88, "OOO with return date", ["auto_reply_return"])
                        elif self._has_contact_person(text_lower):
                            return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.88, "OOO with contact", ["auto_reply_contact"])
                        else:
                            return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.85, "Generic OOO", ["auto_reply_generic"])
                    return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.82, "Auto-reply subject", ["auto_reply_subject"])

            # STEP 2: Legal and dispute detection (highest priority)
            legal_terms = ['attorney', 'law firm', 'legal counsel', 'cease and desist', 'fdcpa', 'legal action']
            strong_disputes = [
                'owe nothing', 'owe them nothing', 'consider this a scam', 'not legitimate', 
                'formally disputing', 'dispute this debt', 'refuse payment', 'will not pay'
            ]
            
            if any(term in text_lower for term in legal_terms):
                if any(dispute in text_lower for dispute in strong_disputes):
                    return RuleResult("Manual Review", "Partial/Disputed Payment", 0.95, "Legal dispute detected", ["legal_dispute"])
                else:
                    return RuleResult("Manual Review", "Complex Queries", 0.95, "Legal communication", ["legal_communication"])
            
            if any(dispute in text_lower for dispute in strong_disputes):
                return RuleResult("Manual Review", "Partial/Disputed Payment", 0.90, "Strong dispute detected", ["strong_dispute"])

            # STEP 3: Payment claims with proof (enhanced detection)
            payment_proof_indicators = [
                'see attachments', 'proof attached', 'payment confirmation attached',
                'use as proof of payment', 'please use as proof', 'they have everything',
                'transaction#', 'ach amount', 'remittance details', 'check number',
                'wire confirmation', 'cancelled check attached', 'proof of payment'
            ]
            
            past_payment_claims = [
                'already paid', 'payment was made', 'we paid', 'bill was paid',
                'payment was sent', 'check sent', 'this was paid', 'been paid',
                'account paid', 'invoice was paid', 'balance is paid'
            ]
            
            if any(proof in text_lower for proof in payment_proof_indicators):
                if any(claim in text_lower for claim in ['paid', 'payment']):
                    return RuleResult("Payments Claim", "Payment Confirmation", 0.90, "Payment with proof detected", ["payment_proof"])
            
            if any(claim in text_lower for claim in past_payment_claims):
                future_indicators = ['will pay', 'going to pay', 'planning to pay']
                if not any(future in text_lower for future in future_indicators):
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.85, "Payment claim detected", ["payment_claim"])

            # STEP 4: Payment status inquiries
            payment_inquiry_patterns = [
                'did you receive', 'have you received payment', 'check was mailed',
                'i mailed a check', 'payment was sent', 'ups delivered this check'
            ]
            
            if any(pattern in text_lower for pattern in payment_inquiry_patterns):
                return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.85, "Payment inquiry", ["payment_inquiry"])

            # STEP 5: Future payment details
            future_payment_patterns = [
                'payment will be sent', 'check will be mailed', 'payment being processed',
                'in process of issuing payment', 'working on payment', 'payment scheduled'
            ]
            
            if any(pattern in text_lower for pattern in future_payment_patterns):
                return RuleResult("Payments Claim", "Payment Details Received", 0.85, "Future payment details", ["future_payment"])

            # STEP 6: Invoice requests (enhanced detection)
            clear_invoice_requests = [
                'send me the invoice', 'provide the invoice', 'share the invoice',
                'share invoice copy', 'share the past due invoice copy', 'need invoice copy',
                'provide outstanding invoices', 'copies of invoices', 'send invoice'
            ]
            
            if any(request in text_lower for request in clear_invoice_requests):
                payment_context = ['paid', 'payment made', 'attached', 'proof']
                if not any(context in text_lower for context in payment_context):
                    return RuleResult("Invoices Request", "Request (No Info)", 0.88, "Invoice request detected", ["invoice_request"])

            # STEP 7: Customer questions and inquiries
            customer_questions = [
                'what bills?', 'what is this for?', 'what are they charging me for?',
                'what i need to know', 'what service', 'what product', 'never had a contract',
                'no agreement with', 'what documentation needed', 'can you provide'
            ]
            
            if any(question in text_lower for question in customer_questions):
                return RuleResult("Manual Review", "Inquiry/Redirection", 0.85, "Customer question detected", ["customer_question"])

            # STEP 8: Documentation requests
            documentation_requests = [
                'backup documentation', 'supporting documents', 'provide backup',
                'backup required', 'need documentation', 'statement of account'
            ]
            
            if any(request in text_lower for request in documentation_requests):
                return RuleResult("Manual Review", "Inquiry/Redirection", 0.85, "Documentation request", ["documentation_request"])

            # STEP 9: Survey and feedback
            survey_indicators = ['survey', 'feedback', 'rate our service', 'customer satisfaction']
            if any(indicator in text_lower for indicator in survey_indicators):
                if not any(dispute in text_lower for dispute in strong_disputes):
                    return RuleResult("Auto Reply (with/without info)", "Survey", 0.85, "Survey detected", ["survey"])

            # STEP 10: Sales and marketing content
            sales_indicators = [
                'prices increasing', 'price increase', 'limited time', 'hours left',
                'special offer', 'promotional offer', 'discount offer', 'sale ending'
            ]
            
            if any(indicator in text_lower for indicator in sales_indicators):
                return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.85, "Sales content", ["sales"])

            # STEP 11: System errors and notifications
            system_errors = [
                'processing error', 'system unable to process', 'delivery failed',
                'electronic invoice rejected', 'cannot be processed', 'import failed'
            ]
            
            if any(error in text_lower for error in system_errors):
                return RuleResult("No Reply (with/without info)", "Processing Errors", 0.85, "System error", ["system_error"])

            # STEP 12: Ticket and case management
            ticket_creation = ['ticket created', 'case opened', 'support request created', 'new ticket']
            ticket_resolution = ['resolved', 'case closed', 'ticket closed', 'completed']
            
            if any(pattern in text_lower for pattern in ticket_creation):
                return RuleResult("No Reply (with/without info)", "Created", 0.85, "Ticket created", ["ticket_created"])
            
            if any(pattern in text_lower for pattern in ticket_resolution):
                return RuleResult("No Reply (with/without info)", "Resolved", 0.85, "Ticket resolved", ["ticket_resolved"])

            # STEP 13: Pattern matcher fallback
            if hasattr(self, 'pattern_matcher'):
                main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(text_lower)
                if main_cat and confidence >= 0.65:
                    return RuleResult(main_cat, subcat, confidence, f"Pattern match: {subcat}", patterns)

            # STEP 14: Business content classification
            business_terms = ["payment", "invoice", "account", "bill", "debt"]
            business_count = sum(1 for term in business_terms if term in text_lower)
            
            if business_count >= 2:
                return RuleResult("Manual Review", "Inquiry/Redirection", 0.70, "Multiple business terms", ["business_content"])
            
            if "payment" in text_lower:
                return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.60, "Payment-related", ["payment_related"])
            elif "invoice" in text_lower:
                return RuleResult("Invoices Request", "Request (No Info)", 0.60, "Invoice-related", ["invoice_related"])

            # STEP 15: Final fallback
            return RuleResult("No Reply (with/without info)", "General (Thank You)", 0.50, "General fallback", ["general_fallback"])

        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return RuleResult("Manual Review", "Complex Queries", 0.30, f"Error: {e}", ["error_fallback"])
        finally:
            self._update_metrics(start_time, success=True)

    def _has_return_date(self, text: str) -> bool:
        """Check if text contains return date information"""
        return_patterns = ['return on', 'back on', 'returning', 'will be back', 'out until']
        return any(pattern in text for pattern in return_patterns)

    def _has_contact_person(self, text: str) -> bool:
        """Check if text contains contact person information"""
        import re
        contact_patterns = [
            r'contact\s+[A-Z][a-z]+',  # "contact Jessica"
            r'reach out to\s+[A-Z][a-z]+',  # "reach out to Jessica"
            r'urgent.*contact\s+[A-Z][a-z]+'  # "urgent contact Jessica"
        ]
        return any(re.search(pattern, text) for pattern in contact_patterns)

    def _classify_with_nlp_analysis(self, main_category: str, text: str, analysis: TextAnalysis) -> Optional[RuleResult]:
        """
        FIXED: Use EXACT sublabel names to match your updated NLP utils
        No more topic name mismatch - uses exact hierarchy names
        """
        try:
            # Check if PatternMatcher already found something with high confidence
            if hasattr(self, 'pattern_matcher'):
                pattern_cat, pattern_subcat, pattern_conf, pattern_rules = self.pattern_matcher.match_text(
                    text.lower(), exclude_external_proof=True
                )
                if pattern_cat and pattern_conf >= 0.80:  # Lower threshold - trust patterns more
                    self.logger.debug(f"High confidence pattern found, NLP validates: {pattern_subcat}")
                    return None  # Let pattern result stand

            # Use EXACT sublabel names (matching your fixed NLP utils)
            for topic in analysis.topics:
                
                # === MANUAL REVIEW CATEGORIES - EXACT NAMES ===
                if topic == 'Partial/Disputed Payment':
                    return RuleResult("Manual Review", "Partial/Disputed Payment", 0.85, 
                                    "NLP detected dispute", ["nlp_dispute"])
                
                elif topic == 'Invoice Receipt':
                    return RuleResult("Manual Review", "Invoice Receipt", 0.85, 
                                    "NLP detected invoice proof", ["nlp_invoice_proof"])
                
                elif topic == 'Closure Notification':
                    return RuleResult("Manual Review", "Closure Notification", 0.85, 
                                    "NLP detected closure", ["nlp_closure"])
                
                elif topic == 'Closure + Payment Due':
                    return RuleResult("Manual Review", "Closure + Payment Due", 0.85, 
                                    "NLP detected closure with payment", ["nlp_closure_payment"])
                
                elif topic == 'External Submission':
                    return RuleResult("Manual Review", "External Submission", 0.85, 
                                    "NLP detected submission issue", ["nlp_submission"])
                
                elif topic == 'Invoice Errors (format mismatch)':
                    return RuleResult("Manual Review", "Invoice Errors (format mismatch)", 0.85, 
                                    "NLP detected format error", ["nlp_format_error"])
                
                elif topic == 'Inquiry/Redirection':
                    return RuleResult("Manual Review", "Inquiry/Redirection", 0.85, 
                                    "NLP detected inquiry", ["nlp_inquiry"])
                
                elif topic == 'Complex Queries':
                    return RuleResult("Manual Review", "Complex Queries", 0.85, 
                                    "NLP detected complex content", ["nlp_complex"])

                # === PAYMENTS CLAIM CATEGORIES - EXACT NAMES ===
                elif topic == 'Claims Paid (No Info)':
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.85, 
                                    "NLP detected payment claim", ["nlp_payment_claim"])
                
                elif topic == 'Payment Confirmation':
                    return RuleResult("Payments Claim", "Payment Confirmation", 0.85, 
                                    "NLP detected payment proof", ["nlp_payment_proof"])
                
                elif topic == 'Payment Details Received':
                    return RuleResult("Payments Claim", "Payment Details Received", 0.85, 
                                    "NLP detected payment details", ["nlp_payment_details"])

                # === INVOICES REQUEST CATEGORY - EXACT NAME ===
                elif topic == 'Request (No Info)':
                    return RuleResult("Invoices Request", "Request (No Info)", 0.85, 
                                    "NLP detected invoice request", ["nlp_invoice_request"])

                # === NO REPLY CATEGORIES - EXACT NAMES ===
                elif topic == 'Sales/Offers':
                    return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.85, 
                                    "NLP detected sales content", ["nlp_sales"])
                
                elif topic == 'System Alerts':
                    return RuleResult("No Reply (with/without info)", "System Alerts", 0.85, 
                                    "NLP detected system alert", ["nlp_system_alert"])
                
                elif topic == 'Processing Errors':
                    return RuleResult("No Reply (with/without info)", "Processing Errors", 0.85, 
                                    "NLP detected processing error", ["nlp_processing_error"])
                
                elif topic == 'Business Closure (Info only)':
                    return RuleResult("No Reply (with/without info)", "Business Closure (Info only)", 0.85, 
                                    "NLP detected closure info", ["nlp_closure_info"])
                
                elif topic == 'General (Thank You)':
                    return RuleResult("No Reply (with/without info)", "General (Thank You)", 0.85, 
                                    "NLP detected thank you", ["nlp_thank_you"])
                
                elif topic == 'Created':
                    return RuleResult("No Reply (with/without info)", "Created", 0.85, 
                                    "NLP detected ticket creation", ["nlp_created"])
                
                elif topic == 'Resolved':
                    return RuleResult("No Reply (with/without info)", "Resolved", 0.85, 
                                    "NLP detected resolution", ["nlp_resolved"])
                
                elif topic == 'Open':
                    return RuleResult("No Reply (with/without info)", "Open", 0.85, 
                                    "NLP detected open ticket", ["nlp_open"])

                # === AUTO REPLY CATEGORIES - EXACT NAMES ===
                elif topic == 'With Alternate Contact':
                    return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.85, 
                                    "NLP detected OOO with contact", ["nlp_ooo_contact"])
                
                elif topic == 'No Info/Autoreply':
                    return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.85, 
                                    "NLP detected generic auto-reply", ["nlp_auto_reply"])
                
                elif topic == 'Return Date Specified':
                    return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.85, 
                                    "NLP detected OOO with date", ["nlp_ooo_date"])
                
                elif topic == 'Survey':
                    return RuleResult("Auto Reply (with/without info)", "Survey", 0.85, 
                                    "NLP detected survey", ["nlp_survey"])
                
                elif topic == 'Redirects/Updates (property changes)':
                    return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.85, 
                                    "NLP detected redirect/update", ["nlp_redirect"])

                # === FINANCIAL CATEGORY INDICATORS (from NLP financial_keywords) ===
                elif topic == 'payment_terms':
                    # Don't auto-classify financial terms - let other logic handle it
                    continue
                elif topic == 'invoice_terms':
                    continue
                elif topic == 'dispute_terms':
                    continue
                elif topic == 'amount_terms':
                    continue
                elif topic == 'closure_terms':
                    continue

            # === ENHANCED ANALYSIS SCORES ===
            
            # High urgency detection (reduced threshold)
            if hasattr(analysis, 'urgency_score') and analysis.urgency_score > 0.7:  # Lower from 0.8
                return RuleResult("Manual Review", "Complex Queries", 0.80,
                                f"High urgency: {analysis.urgency_score:.2f}", ["nlp_urgency"])

            # High complexity detection (reduced threshold)  
            if hasattr(analysis, 'complexity_score') and analysis.complexity_score > 0.7:  # Lower from 0.8
                return RuleResult("Manual Review", "Complex Queries", 0.80,
                                f"High complexity: {analysis.complexity_score:.2f}", ["nlp_complexity"])

            # Multiple financial terms (MORE SPECIFIC ROUTING)
            financial_terms = getattr(analysis, "financial_terms", [])
            if len(financial_terms) > 3:
                # Route based on specific financial terms, not always Manual Review
                if any(term in financial_terms for term in ['payment', 'paid', 'check']):
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.75,
                                    f"Multiple payment terms: {financial_terms[:3]}", ["nlp_payment_terms"])
                elif any(term in financial_terms for term in ['invoice', 'bill', 'statement']):
                    return RuleResult("Invoices Request", "Request (No Info)", 0.75,
                                    f"Multiple invoice terms: {financial_terms[:3]}", ["nlp_invoice_terms"])
                else:
                    return RuleResult("Manual Review", "Complex Queries", 0.75,
                                    f"Multiple financial terms: {financial_terms[:3]}", ["nlp_financial_complex"])

            return None

        except Exception as e:
            self.logger.error(f"NLP classification error: {e}")
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
            return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.6, "Default auto reply", ["auto_reply_default"])
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

    def _validate_patterns(self) -> None:
        """Validate pattern integrity."""
        try:
            # Test pattern matcher with sample text
            test_result = self.pattern_matcher.match_text("test email")
            self.logger.debug("Pattern validation completed successfully")
        except Exception as e:
            self.logger.error(f"Pattern validation failed: {e}")
            raise
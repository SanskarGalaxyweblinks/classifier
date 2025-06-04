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
    analysis: Optional[TextAnalysis] = None,
    ml_result: Optional[Dict[str, Any]] = None,
    retry_count: int = 3,
    subject: str = ""
    ) -> RuleResult:
        """
        UPDATED: Removed thread logic - addresses survey, dispute, payment proof, and sales detection
        Improved conflict resolution and pattern priority
        FIXES: Legal disputes, settlement arrangements, payment plans, return dates, ticket creation
        """
        start_time = time.time()
        text_lower = text.lower().strip() if isinstance(text, str) else ""
        subject_lower = subject.lower().strip() if isinstance(subject, str) else ""

        try:
            self.metrics.total_processed += 1

            # Input validation
            if not text_lower and not subject_lower:
                return RuleResult("Uncategorized", "General", 0.1, "Empty input", ["empty_input"])
            
            if not main_category or not isinstance(main_category, str):
                return RuleResult("Uncategorized", "General", 0.1, "Invalid main category", ["invalid_category"])

            # STEP 1: High-priority edge cases (before pattern matcher)
            
            # 1A: ENHANCED Legal/Attorney communications - CRITICAL FIX (Emails 5, 6)
            enhanced_legal_phrases = [
                'attorney', 'law firm', 'esq.', 'legal counsel', 'cease and desist', 'fdcpa', 'legal action',
                'cease and desist letter', 'legal notice', 'debt validation', 'collection agency violation',
                'fair debt collection', 'attorney correspondence', 'legal representation'
            ]
            if any(phrase in text_lower for phrase in enhanced_legal_phrases):
                # Legal disputes go to Partial/Disputed Payment, not Complex Queries
                if any(dispute in text_lower for dispute in ['dispute', 'owe nothing', 'do not acknowledge', 'contested']):
                    return RuleResult("Manual Review", "Partial/Disputed Payment", 0.95, "Legal dispute communication", ["legal_dispute_detected"])
                else:
                    return RuleResult("Manual Review", "Complex Queries", 0.95, "Legal communication detected", ["legal_detected"])
            
            # 1B: ENHANCED Settlement detection - CRITICAL FIX (Email 31)
            settlement_phrases = [
                'settlement arrangement', 'legal settlement', 'payment settlement', 'settlement negotiation',
                'settlement terms', 'attorney settlement', 'legal resolution', 'settlement discussion',
                'court settlement', 'mediation settlement', 'settlement agreement'
            ]
            if any(phrase in text_lower for phrase in settlement_phrases):
                return RuleResult("Manual Review", "Complex Queries", 0.93, "Settlement arrangement detected", ["settlement_detected"])
            
            # 1C: High-value amounts (immediate Manual Review)
            amount_pattern = re.compile(r'\$[\d,]+\.?\d*')
            amounts = amount_pattern.findall(text_lower)
            for amount_str in amounts:
                try:
                    amount_value = float(amount_str.replace('$', '').replace(',', ''))
                    if amount_value > 15000:
                        return RuleResult("Manual Review", "Complex Queries", 0.90, f"High-value amount: {amount_str}", ["high_value"])
                except (ValueError, AttributeError):
                    continue

            # 1D: PRIORITY FIX - Survey detection (before dispute patterns)
            survey_indicators = ['survey', 'feedback', 'rate our service', 'customer satisfaction', 'please rate']
            if any(indicator in text_lower for indicator in survey_indicators):
                # Only classify as survey if no strong dispute language
                strong_disputes = ['owe nothing', 'scam', 'formally disputing', 'do not acknowledge']
                if not any(dispute in text_lower for dispute in strong_disputes):
                    return RuleResult("Auto Reply (with/without info)", "Survey", 0.88, "Survey/feedback detected", ["survey_priority"])

            # 1E: PRIORITY FIX - Enhanced dispute detection (including missed patterns)
            enhanced_dispute_phrases = [
                'owe them nothing', 'owe nothing', 'consider this a scam', 'looks like a scam',
                'is this legitimate', 'verify this debt', 'formally disputing', 'dispute this debt',
                'do not acknowledge', 'billing is incorrect', 'not our responsibility',
                'cease and desist', 'fdcpa violation', 'debt validation request'
            ]
            if any(phrase in text_lower for phrase in enhanced_dispute_phrases):
                return RuleResult("Manual Review", "Partial/Disputed Payment", 0.90, "Enhanced dispute detection", ["enhanced_dispute"])

            # 1F: ENHANCED Payment proof vs Invoice request distinction
            if 'invoice' in text_lower:
                # Check for payment proof first (higher priority)
                payment_proof_patterns = [
                    'invoice was paid', 'payment was made', 'see attachments', 'proof attached',
                    'here is proof', 'payment confirmation', 'check was sent', 'wire was sent',
                    'payment made in error', 'error payment proof', 'documentation for payment error'
                ]
                if any(pattern in text_lower for pattern in payment_proof_patterns):
                    # CRITICAL FIX: Payment error documentation should go to Invoice Receipt (Email 139)
                    if any(error in text_lower for error in ['error', 'mistake', 'incorrect payment']):
                        return RuleResult("Manual Review", "Invoice Receipt", 0.88, "Payment error documentation", ["payment_error_doc"])
                    else:
                        return RuleResult("Payments Claim", "Payment Confirmation", 0.88, "Payment proof provided", ["payment_proof_priority"])
                
                # Then check for invoice requests (excluding proof scenarios)
                invoice_request_patterns = [
                    'send me the invoice', 'need invoice copy', 'provide outstanding invoices',
                    'copies of invoices', 'share the invoice'
                ]
                if any(pattern in text_lower for pattern in invoice_request_patterns):
                    # Exclude if providing documentation/proof
                    if not any(proof in text_lower for proof in ['paid', 'see attachments', 'proof']):
                        return RuleResult("Invoices Request", "Request (No Info)", 0.85, "Clear invoice request", ["invoice_request_priority"])

            # 1G: ENHANCED Sales/Marketing detection - CRITICAL FIX (Email 94)
            enhanced_sales_patterns = [
                'prices increasing', 'price increase', 'limited time', 'hours left', 'sale ending',
                'special pricing', 'promotional offer', 'discount offer', 'exclusive deal',
                'payment plan options', 'payment plan discussion', 'installment plan',
                'financing options', 'payment arrangement offer', 'flexible payment options'
            ]
            if any(pattern in text_lower for pattern in enhanced_sales_patterns):
                return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.85, "Sales/marketing content", ["sales_marketing_priority"])

            # 1H: ENHANCED Auto-reply with return date detection - CRITICAL FIX (8 emails)
            return_date_patterns = [
                'return on', 'back on', 'returning', 'will be back', 'return date',
                'back monday', 'return monday', 'back next week', 'return next week',
                'out until', 'away until', 'return after', 'back after'
            ]
            if any(pattern in text_lower for pattern in return_date_patterns):
                if any(ooo in text_lower for ooo in ['out of office', 'away from desk', 'on vacation']):
                    return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.88, "OOO with return date", ["return_date_priority"])

            # 1I: Clear auto-reply subject lines (early detection)
            auto_reply_indicators = ["automatic reply:", "auto-reply:", "automatic reply", "auto reply"]
            if any(indicator in subject_lower for indicator in auto_reply_indicators):
                # Only classify as auto-reply if no strong business context
                business_context = any(term in text_lower for term in ["payment", "invoice", "dispute", "collection", "debt"])
                if not business_context:
                    # Enhanced OOO detection with return dates
                    if any(phrase in text_lower for phrase in ["out of office", "away from desk", "on vacation"]):
                        if any(date_pattern in text_lower for date_pattern in return_date_patterns):
                            return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.88, "OOO with return date", ["ooo_return_date"])
                        elif any(word in text_lower for word in ["contact", "call", "reach", "assistance"]):
                            return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.88, "OOO with contact", ["ooo_contact"])
                        else:
                            return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.85, "Generic OOO", ["ooo_generic"])
                    return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.82, "Auto-reply subject", ["auto_reply_subject"])

            # STEP 2: Pattern Matcher (PRIMARY CLASSIFICATION - Trust it more, but with fixes!)
            if hasattr(self, 'pattern_matcher'):
                main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(
                    text_lower, exclude_external_proof=True
                )
                
                # STANDARD CONFIDENCE THRESHOLD - No thread logic
                min_confidence = 0.45
                
                if main_cat and confidence >= min_confidence:
                    
                    # ENHANCED conflict resolution with specific fixes
                    
                    # Fix: Auto-reply vs Business content (major conflict source)
                    if main_cat == "Auto Reply (with/without info)":
                        strong_business_terms = ['payment dispute', 'invoice issue', 'debt collection', 'billing error']
                        business_terms = ['payment', 'invoice', 'dispute', 'collection', 'debt', 'bill']
                        
                        # Strong business terms override auto-reply
                        if any(term in text_lower for term in strong_business_terms):
                            return RuleResult("Manual Review", "Inquiry/Redirection", confidence, "Strong business override", patterns)
                        # Payment claims override auto-reply
                        elif any(phrase in text_lower for phrase in ['already paid', 'payment made', 'check sent']):
                            return RuleResult("Payments Claim", "Claims Paid (No Info)", confidence, "Payment claim override", patterns)
                        # Dispute claims override auto-reply
                        elif any(phrase in text_lower for phrase in enhanced_dispute_phrases):
                            return RuleResult("Manual Review", "Partial/Disputed Payment", confidence, "Dispute override", patterns)
                        # Weak business terms in clear auto-reply context - trust auto-reply
                        elif any(phrase in text_lower for phrase in ['out of office', 'automatic reply', 'away from desk']):
                            # Keep auto-reply classification
                            pass
                        # Mixed business content - route to manual review
                        elif len([term for term in business_terms if term in text_lower]) >= 2:
                            return RuleResult("Manual Review", "Inquiry/Redirection", confidence, "Mixed business content", patterns)
                    
                    # Fix: Survey misclassification override
                    if subcat == "Partial/Disputed Payment" and any(survey in text_lower for survey in survey_indicators):
                        if not any(dispute in text_lower for dispute in enhanced_dispute_phrases):
                            return RuleResult("Auto Reply (with/without info)", "Survey", confidence, "Survey override dispute", patterns)
                    
                    # Fix: Ticket context resolution (common issue)
                    if subcat == "Created" and any(word in text_lower for word in ['resolved', 'closed', 'completed', 'solved']):
                        return RuleResult("No Reply (with/without info)", "Resolved", confidence, "Ticket resolved (context fix)", patterns)
                    
                    # CRITICAL FIX: Complex business instructions vs format errors (Email 41)
                    if subcat == "Invoice Errors (format mismatch)":
                        complex_business_terms = [
                            'routing instructions', 'business process', 'special handling', 'complex procedure',
                            'multi step process', 'detailed process', 'workflow'
                        ]
                        if any(term in text_lower for term in complex_business_terms):
                            return RuleResult("Manual Review", "Complex Queries", confidence, "Complex business instructions", patterns)
                    
                    # Fix: Documentation vs Invoice Request (common conflict)
                    if subcat == "Request (No Info)" and any(word in text_lower for word in ['backup', 'documentation', 'supporting']):
                        return RuleResult("Manual Review", "Inquiry/Redirection", confidence, "Documentation request (context fix)", patterns)
                    
                    # Fix: Invoice Request when actually providing payment proof
                    if subcat == "Request (No Info)" and any(proof in text_lower for proof in ['was paid', 'see attachments', 'proof attached']):
                        return RuleResult("Payments Claim", "Payment Confirmation", confidence, "Payment proof fix", patterns)
                    
                    # TRUST THE PATTERN MATCHER - this is the key fix!
                    return RuleResult(main_cat, subcat, confidence, f"Pattern match: {subcat}", patterns)

            # STEP 3: ENHANCED NLP Analysis (if pattern matcher found nothing)
            if analysis and analysis.topics:
                for topic in analysis.topics:
                    # Use EXACT sublabel names (fixed from your NLP mismatch)
                    if topic == 'Partial/Disputed Payment':
                        return RuleResult("Manual Review", "Partial/Disputed Payment", 0.82, "NLP detected dispute", ["nlp_dispute"])
                    elif topic == 'Payment Confirmation':
                        return RuleResult("Payments Claim", "Payment Confirmation", 0.82, "NLP payment proof", ["nlp_payment_proof"])
                    elif topic == 'Claims Paid (No Info)':
                        return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.82, "NLP payment claim", ["nlp_payment_claim"])
                    elif topic == 'Request (No Info)':
                        return RuleResult("Invoices Request", "Request (No Info)", 0.82, "NLP invoice request", ["nlp_invoice_request"])
                    elif topic == 'No Info/Autoreply':
                        return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.82, "NLP auto-reply", ["nlp_auto_reply"])
                    elif topic == 'Processing Errors':
                        return RuleResult("No Reply (with/without info)", "Processing Errors", 0.82, "NLP processing error", ["nlp_processing"])
                    elif topic == 'Sales/Offers':
                        return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.82, "NLP sales/marketing", ["nlp_sales"])
                    # ADDED: More NLP topic coverage
                    elif topic == 'Survey':
                        return RuleResult("Auto Reply (with/without info)", "Survey", 0.82, "NLP survey detected", ["nlp_survey"])
                    elif topic == 'Return Date Specified':
                        return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.82, "NLP return date", ["nlp_return_date"])
                    elif topic == 'Created':
                        return RuleResult("No Reply (with/without info)", "Created", 0.82, "NLP ticket creation", ["nlp_created"])

            # STEP 4: ENHANCED business fallbacks (MUCH more specific than before)
            
            # 4A: Clear payment claims (past tense only)
            past_payment_phrases = ["already paid", "payment was made", "check was sent", "we paid", "been paid", "this was paid"]
            if any(phrase in text_lower for phrase in past_payment_phrases):
                # Exclude future payments
                if not any(future in text_lower for future in ["will pay", "going to pay", "planning to pay"]):
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.75, "Clear payment claim", ["payment_fallback"])
            
            # 4B: Enhanced dispute fallback (using enhanced patterns)
            if any(phrase in text_lower for phrase in enhanced_dispute_phrases):
                return RuleResult("Manual Review", "Partial/Disputed Payment", 0.80, "Enhanced dispute fallback", ["enhanced_dispute_fallback"])
            
            # 4C: Clear invoice requests (specific language, excluding proof)
            clear_invoice_requests = ["send me the invoice", "need invoice copy", "provide outstanding invoices", "copies of invoices"]
            if any(phrase in text_lower for phrase in clear_invoice_requests):
                # Exclude documentation requests and payment proof
                if not any(doc in text_lower for doc in ["backup documentation", "supporting documents", "was paid", "proof"]):
                    return RuleResult("Invoices Request", "Request (No Info)", 0.75, "Clear invoice request", ["invoice_request_fallback"])
            
            # 4D: Clear system errors
            clear_system_errors = ["processing error", "system unable to process", "delivery failed", "electronic invoice rejected"]
            if any(phrase in text_lower for phrase in clear_system_errors):
                return RuleResult("No Reply (with/without info)", "Processing Errors", 0.78, "Clear system error", ["system_error_fallback"])
            
            # 4E: ENHANCED Sales/Marketing fallback
            if any(phrase in text_lower for phrase in enhanced_sales_patterns):
                return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.75, "Sales/marketing fallback", ["sales_fallback"])

            # 4F: ENHANCED Ticket creation fallback - CRITICAL FIX (Emails 75, 77)
            ticket_creation_phrases = [
                'ticket created', 'case opened', 'new ticket', 'support request created',
                'ticket has been opened', 'new case created', 'case number assigned',
                'ticket submitted successfully', 'support request received'
            ]
            if any(phrase in text_lower for phrase in ticket_creation_phrases):
                return RuleResult("No Reply (with/without info)", "Created", 0.78, "Ticket creation detected", ["ticket_creation_fallback"])

            # STEP 5: Final conservative fallback (MUCH more restrictive)
            
            # Only send to Manual Review if there are MULTIPLE business indicators
            complex_business_indicators = ["payment", "invoice", "dispute", "collection", "debt", "billing"]
            business_indicator_count = sum(1 for term in complex_business_indicators if term in text_lower)
            
            if business_indicator_count >= 3:  # Multiple business terms
                return RuleResult("Manual Review", "Inquiry/Redirection", 0.60, "Multiple business terms", ["complex_business_fallback"])
            elif business_indicator_count >= 1:  # Single business term - try to classify
                if "payment" in text_lower:
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.55, "Payment-related fallback", ["payment_related_fallback"])
                elif "invoice" in text_lower:
                    return RuleResult("Invoices Request", "Request (No Info)", 0.55, "Invoice-related fallback", ["invoice_related_fallback"])
                else:
                    return RuleResult("Manual Review", "Inquiry/Redirection", 0.55, "Business-related fallback", ["business_related_fallback"])
            else:
                # No business terms - likely notification or general
                return RuleResult("No Reply (with/without info)", "General (Thank You)", 0.50, "General fallback", ["general_fallback"])

        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return self._get_fallback_result(str(e))
        finally:
            self._update_metrics(start_time, success=True)

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

            # Multiple business keywords (REMOVED - was too aggressive)
            # This was sending too much to Manual Review

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
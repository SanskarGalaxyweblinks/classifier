"""
Clean Pattern Matcher - Aligned with updated hierarchy structure
No conflicts, quality patterns only
"""

from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

class PatternMatcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Your existing patterns - organized by new hierarchy structure
        self.patterns = {
            "manual_review": {
                # Disputes & Payments
                "partial_disputed_payment": [
                    # From your original patterns
                    r"amount.*is.*in.*dispute", r"this.*amount.*is.*in.*dispute", r"balance.*is.*not.*ours",
                    r"balance.*is.*not.*accurate", r"not.*our.*responsibility", r"do.*not.*owe", 
                    r"contested", r"disagreement", r"refuse", r"formally.*disputing", 
                    r"not.*accurate", r"that.*not.*my.*bill", r"due.*to.*a.*sale.*of.*property",
                    r"not.*ours.*due.*to",
                    
                    # Additional flexible patterns
                    r"partial.*payment", r"dispute.*payment", r"contested.*payment", 
                    r"disagreement.*payment", r"challenge.*payment", r"waive.*charges", 
                    r"cancel.*account", r"charges.*and.*cancel", r"material.*breach",
                    r"breach.*of.*contract", r"owes.*me", r"owes.*us",
                    
                    # Additional patterns
                    r"debt.*is.*disputed", r"this.*debt.*is.*disputed",
                    r"disputed.*and.*not.*properly.*billed", r"billing.*error",
                    r"not.*properly.*billed", r"billed.*to.*wrong",
                    r"appropriate.*payor", r"wrong.*entity", r"wrong.*party",
                    r"dispute.*billing", r"incorrect.*billing",
                    r"must.*correct.*their.*billing", r"correct.*billing.*error",
                    r"not.*the.*appropriate", r"billed.*incorrectly",
                    r"disputing.*this.*debt", r"disputing.*these.*charges"
                ],
                
                # Invoice Updates  
                "invoice_receipt": [
                    r"invoice.*attached", r"invoice.*copy.*attached", r"see.*attached.*invoice",
                    r"invoice.*is.*attached", r"here.*is.*invoice", r"proof.*of.*invoice",
                    r"invoice.*receipt", r"invoice.*documentation", r"copy.*of.*invoice.*attached"
                ],
                
                # Business Closure
                "closure_notification": [
                    r"business.*closed", r"company.*closed", r"out.*of.*business", r"ceased.*operations",
                    r"filed.*bankruptcy", r"bankruptcy.*protection", r"chapter.*7", r"chapter.*11"
                ],
                
                "closure_payment_due": [
                    r"closed.*payment.*due", r"business.*closed.*outstanding", r"closure.*payment.*required",
                    r"bankruptcy.*payment", r"filed.*bankruptcy.*payment", r"closure.*with.*payment"
                ],
                
                # Invoices
                "external_submission": [
                    r"invoice.*issue", r"invoice.*problem", r"invoice.*error", r"import.*failed",
                    r"failed.*import", r"invoice.*submission.*failed", r"documents.*not.*processed",
                    r"submission.*failed", r"unable.*to.*import", r"import.*unsuccessful",
                    r"could.*not.*import", r"failed.*to.*import", r"error.*importing"
                ],
                
                "invoice_errors_format": [
                    r"missing.*field", r"format.*mismatch", r"incomplete.*invoice", r"required.*field",
                    r"invoice.*format.*issue", r"format.*error", r"field.*missing"
                ],
                
                # Other Manual Review
                "inquiry_redirection": [
                    # Existing patterns
                    r"insufficient.*data.*provided.*to.*research", r"there.*is.*insufficient.*data",
                    r"please.*ask", r"they.*are.*the.*who.*you.*must.*be.*reaching.*out",
                    r"i.*need.*guidance", r"please.*advise.*what.*is.*needed",
                    r"redirect.*to", r"forward.*to", r"contact.*instead", r"reach.*out.*to",
                    r"please.*check.*with", r"please.*refer.*to", r"contact.*our.*office",
                    r"is.*there.*any.*type.*of.*paperwork",
                    r"what.*documentation.*needed",
                    r"should.*this.*be.*paid.*to",
                    r"how.*should.*we.*pay",
                    r"where.*to.*send.*payment",
                    r"can.*meet.*this.*requirement",
                    
                    # Additional patterns
                    r"looks.*like.*a.*scam", r"think.*scam", r"verify.*legitimate",
                    r"are.*you.*legitimate", r"gotten.*scammed", r"verify.*authenticity",
                    r"please.*provide.*me.*with.*verification", r"verify.*with.*the.*sender",
                    r"if.*you.*are.*legitimate", r"consider.*this.*a.*scam", r"otherwise.*consider.*scam"
                ],
                
                "complex_queries": [
                    r"multiple.*issues", r"several.*questions", r"complex.*situation", r"detailed.*inquiry",
                    r"various.*concerns", r"legal.*communication", r"attorney.*communication"
                ]
            },
            
            "no_reply": {
                # Notifications
                "sales_offers": [
                    r"special.*offer", r"limited.*time.*offer", r"promotional.*offer", 
                    r"sales.*promotion", r"discount.*offer", r"exclusive.*deal", r"flash.*sale"
                ],
                
                "system_alerts": [
                    r"system.*notification", r"automated.*notification", r"system.*alert",
                    r"maintenance.*notification", r"service.*update", r"backup.*completed",
                    r"security.*alert", r"delivery.*notification", r"legal.*notice"
                ],
                
                "processing_errors": [
                    # From your original patterns
                    r"pdf.*file.*is.*not.*attached", r"error.*reason", r"processing.*error", 
                    r"cannot.*be.*processed", r"electronic.*invoice.*rejected", r"failed.*to.*process", 
                    r"case.*rejection",
                    
                    # Additional patterns
                    r"processing.*failed", r"unable.*to.*process", r"rejected.*for.*no.*attachment", 
                    r"mail.*delivery.*failed", r"email.*bounced", r"delivery.*failure", 
                    r"message.*undelivered", r"bounce.*back", r"email.*cannot.*be.*delivered"
                ],
                
                "business_closure_info": [
                    r"business.*closure.*information", r"closure.*notification.*only"
                ],
                
                "general_thank_you": [
                    # Your original patterns
                    r"unsubscribe", r"email.*preferences", r"thank.*you.*for.*your.*email",
                    r"thanks.*for.*your.*email", r"thank.*you.*for.*contacting",
                    
                    # Additional patterns
                    r"still.*reviewing", r"will.*get.*back.*to.*you", r"reviewing.*this.*invoice",
                    r"currently.*reviewing", r"under.*review", r"in.*progress", r"processing.*your.*request",
                    r"we.*are.*reviewing", r"our.*return.*#.*is", r"correct.*number.*is",
                    r"updated.*information", r"for.*your.*records"
                ],
                
                # Tickets/Cases
                "tickets_created": [
                    r"ticket.*created", r"case.*opened", r"new.*ticket", r"support.*request.*created",
                    r"case.*number.*is", r"assigned.*#", r"support.*ticket.*opened", 
                    r"case.*has.*been.*created", r"ticket.*has.*been.*created"
                ],
                
                "tickets_resolved": [
                    r"ticket.*resolved", r"case.*closed", r"case.*resolved", r"case.*has.*been.*resolved",
                    r"ticket.*has.*been.*resolved", r"case.*is.*now.*closed", r"request.*completed",
                    r"moved.*to.*solved", r"marked.*as.*resolved"
                ],
                
                "tickets_open": [
                    r"ticket.*open", r"case.*open", r"still.*pending", r"in.*progress", r"case.*pending"
                ]
            },
            
            "invoices_request": {
                "request_no_info": [
                    # Your specific patterns
                    r"can.*you.*please.*provide.*me.*with.*outstanding.*invoices",
                    r"provide.*me.*with.*outstanding.*invoices", r"can.*you.*please.*send.*me.*copies.*of.*any.*invoices",
                    r"send.*me.*copies.*of.*any.*invoices", r"can.*you.*send.*me.*the.*invoice",
                    r"provide.*us.*with.*the.*invoice", r"send.*me.*the.*invoice.*copy", r"need.*invoice.*copy",
                    r"provide.*invoice.*copy", r"send.*us.*invoice.*copy", r"copies.*of.*any.*invoices.*or.*po.*s",
                    r"outstanding.*invoices.*owed",
                    
                    # Additional flexible patterns
                    r"send.*invoice", r"need.*invoice", r"please.*send.*invoice", r"provide.*invoice",
                    r"invoice.*request", r"can.*you.*send.*invoice", r"send.*us.*invoice",
                    r"please.*provide.*invoice", r"invoice.*copy", r"copy.*of.*invoice"
                ]
            },
            
            "payments_claim": {
                "claims_paid_no_info": [
                    # Your specific patterns
                    r"its.*been.*paid", r"has.*been.*settled", r"this.*has.*been.*settled", 
                    r"already.*paid", r"been.*paid.*to.*them", r"payment.*was.*made", 
                    r"we.*paid", r"bill.*was.*paid", r"paid.*directly.*to", r"settled.*with",
                    r"been.*paid.*to", r"we.*sent.*check.*on", r"sent.*check.*on", 
                    r"check.*on.*april", r"check.*on.*may", r"check.*on.*march",
                    
                    # Flexible patterns
                    r"payment.*was.*sent", r"payment.*sent.*today", r"was.*paid.*by.*credit.*card",
                    r"we.*sent.*payment", r"we.*sent.*payment.*to", r"this.*payment.*has.*already.*been.*sent",
                    r"this.*was.*paid", r"it.*was.*paid", r"invoices.*are.*being.*processed.*for.*payment",
                    r"received.*invoices.*are.*being.*processed", r"i.*have.*paid.*my.*account",
                    r"paid.*my.*account.*via.*cc", r"paid.*via.*cc", r"paid.*last.*friday",
                    
                    # General patterns
                    r"payment.*sent", r"sent.*payment", r"payment.*made", r"was.*paid",
                    r"been.*paid", r"payment.*completed", r"payment.*processed", r"paid.*by",
                    r"paid.*via", r"paid.*through", r"paid.*on", r"paid.*to", r"sent.*check",
                    r"check.*sent", r"made.*payment", r"remitted", r"account.*paid",
                    r"paid.*by.*credit.*card", r"paid.*by.*check", r"wired.*payment", 
                    r"ach.*payment", r"electronic.*payment", r"settlement", r"resolved.*payment",
                    
                    # Frustrated responses
                    r"should.*not.*be.*getting.*this", r"already.*sent", r"this.*has.*already.*been.*paid",
                    r"payment.*has.*already.*been.*sent", r"get.*outlook.*for.*ios"
                ],
                
                "payment_confirmation": [
                    # Your original payment confirmation patterns (MOVED from manual_review)
                    r"proof.*of.*payment", r"payment.*confirmation", r"i.*have.*receipt",
                    r"check.*number", r"eft#", r"confirmation.*#", r"payment.*has.*been.*released",
                    r"was.*reconciled", r"here.*is.*proof", r"attached.*proof", r"payment.*evidence",
                    r"payment.*copy", r"wire.*document", r"receipt.*for", r"transaction.*id",
                    r"payment.*reference", r"voucher.*id", r"cleared.*bank",
                    r"paid.*via.*transaction.*number",
                    r"paid.*via.*batch.*number", 
                    r"transaction.*and.*batch.*numbers",
                    r"here.*is.*the.*record.*of.*payment",
                    r"record.*within.*our.*project.*files",
                    r"paid.*on.*\d+/\d+/\d+.*transaction",
                    r"paid.*via.*mastercard.*transaction",
                    r"paid.*via.*visa.*transaction",
                    r"payment.*record.*included",
                    r"transaction.*numbers.*included",
                    r"batch.*numbers.*included",
                    r"paid.*via.*mastercard",
                    r"paid.*via.*visa", 
                    r"paid.*via.*credit.*card",
                    r"paid.*on.*\d+/\d+/\d+",
                    r"transaction.*numbers.*are.*included",
                    r"batch.*numbers.*are.*included"
                ],
                
                "payment_details_received": [
                    # Your original patterns (MOVED from manual_review)
                    r"payment.*will.*be.*sent", r"payment.*is.*being.*processed", r"check.*will.*be.*mailed",
                    r"payment.*scheduled", r"checks.*will.*be.*mailed.*by", r"payment.*timeline",
                    r"payment.*being.*processed", r"invoice.*being.*processed", r"payment.*details",
                    r"remittance.*info", r"payment.*breakdown",
                    r"waiting.*to.*receive.*customer.*payments",
                    r"waiting.*for.*payment.*from",
                    r"hope.*to.*have.*resolved",
                    r"payment.*delayed.*due.*to",
                    r"expecting.*payment.*from"
                ]
            },
            
            "auto_reply": {
                # Out of Office
                "ooo_with_alternate_contact": [
                    r"out.*of.*office.*contact", r"out.*of.*office.*reach.*out", r"contact.*me.*at",
                    r"please.*contact.*\w+", r"call.*my.*cell", r"call.*my.*mobile", 
                    r"if.*you.*need.*immediate.*assistance", r"for.*all.*of.*your.*ap.*needs",
                    r"if.*urgent", r"urgent.*please.*contact", r"alternate.*contact"
                ],
                
                "ooo_return_date": [
                    r"out.*of.*office.*until", r"return.*on", r"back.*on", r"available.*after",
                    r"returning.*\w+", r"will.*be.*back", r"out.*until.*\w+", r"when.*i.*return"
                ],
                
                "ooo_no_info": [
                    r"out.*of.*office", r"automatic.*reply", r"auto-reply", r"auto.*reply",
                    r"i.*am.*currently.*out", r"i.*will.*be.*out", r"away.*from.*desk",
                    r"limited.*access.*to.*email", r"will.*return", r"on.*vacation", r"on.*leave",
                    r"currently.*traveling", r"do.*not.*reply", r"no-reply", r"noreply",
                    r"automated.*response", r"service.*account", r"system.*generated"
                ],
                
                # Miscellaneous
                "survey": [
                    # Your original patterns
                    r"survey", r"feedback.*request", r"rate.*our.*service", r"customer.*satisfaction",
                    r"please.*rate", r"take.*short.*survey",
                    
                    # Additional patterns
                    r"feedback.*is.*important", r"take.*our.*survey", r"complete.*the.*online.*survey",
                    r"please.*visit.*the.*survey", r"survey.*web.*site.*link", r"feedback.*on.*the.*support",
                    r"would.*appreciate.*your.*feedback", r"click.*here.*to.*complete.*survey"
                ],
                
                "redirects_updates": [
                    # Your original patterns
                    r"is.*no.*longer.*with", r"please.*direct.*all.*future.*inquiries.*to", r"not.*accounts.*payable",
                    r"please.*contact", r"direct.*inquiries.*to", r"no.*longer.*employed",
                    r"please.*contact.*hd.*supply", r"contact.*the.*vendor.*directly", r"starting.*may.*1",
                    r"no.*longer.*be.*accepted", r"now.*using", r"please.*submit.*all.*future",
                    
                    # Additional patterns
                    r"contact.*changed", r"new.*contact", r"property.*manager",
                    r"department.*changed", r"quarantine.*report", r"contact.*redirection", r"forwarding.*to"
                ]
            }
        }
        
        # Compile patterns for performance
        self.compiled_patterns = {}
        for main_cat, subcats in self.patterns.items():
            self.compiled_patterns[main_cat] = {}
            for subcat, patterns in subcats.items():
                self.compiled_patterns[main_cat][subcat] = [
                    re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in patterns
                ]
        
        # Clean category mappings
        self.main_categories = {
            "manual_review": "Manual Review",
            "no_reply": "No Reply (with/without info)",
            "invoices_request": "Invoices Request",
            "payments_claim": "Payments Claim",
            "auto_reply": "Auto Reply (with/without info)"
        }
        
        # Updated sublabel mappings aligned with new hierarchy
        self.sublabels = {
            # Manual Review sublabels
            "partial_disputed_payment": "Partial/Disputed Payment",
            "invoice_receipt": "Invoice Receipt",
            "closure_notification": "Closure Notification", 
            "closure_payment_due": "Closure + Payment Due",
            "external_submission": "External Submission",
            "invoice_errors_format": "Invoice Errors (format mismatch)",
            "inquiry_redirection": "Inquiry/Redirection",
            "complex_queries": "Complex Queries",
            
            # No Reply sublabels
            "sales_offers": "Sales/Offers",
            "system_alerts": "System Alerts", 
            "processing_errors": "Processing Errors",
            "business_closure_info": "Business Closure (Info only)",
            "general_thank_you": "General (Thank You)",
            "tickets_created": "Created",
            "tickets_resolved": "Resolved",
            "tickets_open": "Open",
            
            # Invoice Request sublabel
            "request_no_info": "Request (No Info)",
            
            # Payments Claim sublabels
            "claims_paid_no_info": "Claims Paid (No Info)",
            "payment_confirmation": "Payment Confirmation", 
            "payment_details_received": "Payment Details Received",
            
            # Auto Reply sublabels
            "ooo_with_alternate_contact": "With Alternate Contact",
            "ooo_return_date": "Return Date Specified",
            "ooo_no_info": "No Info/Autoreply", 
            "survey": "Survey",
            "redirects_updates": "Redirects/Updates (property changes)"
        }
        
        self.logger.info("✅ Clean PatternMatcher initialized")

    def match_text(self, text: str, exclude_external_proof: bool = False) -> Tuple[Optional[str], Optional[str], float, List[str]]:
        """Match text against patterns with conflict resolution"""
        if not text:
            return None, None, 0.0, []
        
        text_lower = text.lower()
        
        # External proof exclusion for payment confirmation
        if exclude_external_proof and self._has_external_proof_reference(text_lower):
            return None, None, 0.0, []
        
        all_matches = []
        
        # Collect all matches with scores
        for main_cat, subcats in self.compiled_patterns.items():
            for subcat, patterns in subcats.items():
                matches = 0
                matched_patterns = []
                
                for pattern in patterns:
                    if pattern.search(text_lower):
                        matches += 1
                        matched_patterns.append(pattern.pattern)
                
                if matches > 0:
                    # Calculate confidence based on matches and pattern specificity
                    base_confidence = 0.7
                    match_bonus = min(matches * 0.05, 0.2)
                    confidence = base_confidence + match_bonus
                    
                    all_matches.append({
                        'main_cat': main_cat,
                        'subcat': subcat,
                        'confidence': confidence,
                        'match_count': matches,
                        'patterns': matched_patterns
                    })
        
        if not all_matches:
            return None, None, 0.0, []
        
        # Resolve conflicts by priority and specificity
        best_match = self._resolve_conflicts(all_matches, text_lower)
        
        if best_match:
            return (
                self.main_categories[best_match['main_cat']],
                self.sublabels[best_match['subcat']],
                best_match['confidence'],
                best_match['patterns']
            )
        
        return None, None, 0.0, []

    def _resolve_conflicts(self, matches: List[Dict], text: str) -> Optional[Dict]:
        """Resolve conflicts between multiple matches using priority rules"""
        if not matches:
            return None
        
        if len(matches) == 1:
            return matches[0]
        
        # Priority rules to resolve conflicts
        priority_order = [
            # High priority - specific business actions
            ('payments_claim', 'payment_confirmation'),  # Providing proof vs claiming paid
            ('manual_review', 'partial_disputed_payment'),  # Disputes are high priority
            ('no_reply', 'processing_errors'),  # System errors
            
            # Medium priority - requests and claims  
            ('invoices_request', 'request_no_info'),
            ('payments_claim', 'claims_paid_no_info'),
            ('payments_claim', 'payment_details_received'),
            
            # Lower priority - notifications and auto replies
            ('no_reply', 'tickets_created'),
            ('no_reply', 'tickets_resolved'),
            ('auto_reply', 'ooo_with_alternate_contact'),
            ('auto_reply', 'survey'),
        ]
        
        # Check priority matches first
        for main_cat, subcat in priority_order:
            for match in matches:
                if match['main_cat'] == main_cat and match['subcat'] == subcat:
                    return match
        
        # If no priority match, return highest confidence
        return max(matches, key=lambda x: (x['confidence'], x['match_count']))

    def _has_external_proof_reference(self, text: str) -> bool:
        """Check if text refers to external proof rather than providing proof"""
        external_phrases = [
            "if you look at your own email", "you will see it was settled",
            "you sent an email confirming", "please consult your client",
            "check with your client", "you have the confirmation",
            "look at your records", "check your records"
        ]
        return any(phrase in text for phrase in external_phrases)

    # Quick match methods for specific categories
    def get_payment_claim_match(self, text: str) -> bool:
        """Quick check for payment claims"""
        if not text:
            return False
        patterns = self.compiled_patterns.get("payments_claim", {}).get("claims_paid_no_info", [])
        return any(pattern.search(text.lower()) for pattern in patterns)

    def get_dispute_match(self, text: str) -> bool:
        """Quick check for disputes"""
        if not text:
            return False
        patterns = self.compiled_patterns.get("manual_review", {}).get("partial_disputed_payment", [])
        return any(pattern.search(text.lower()) for pattern in patterns)

    def get_invoice_request_match(self, text: str) -> bool:
        """Quick check for invoice requests"""
        if not text:
            return False
        patterns = self.compiled_patterns.get("invoices_request", {}).get("request_no_info", [])
        return any(pattern.search(text.lower()) for pattern in patterns)

    def get_processing_error_match(self, text: str) -> bool:
        """Quick check for processing errors"""
        if not text:
            return False
        patterns = self.compiled_patterns.get("no_reply", {}).get("processing_errors", [])
        return any(pattern.search(text.lower()) for pattern in patterns)

    def get_pattern_info(self) -> Dict:
        """Get information about available patterns"""
        pattern_count = {}
        for main_cat, subcats in self.patterns.items():
            pattern_count[main_cat] = {}
            for subcat, patterns in subcats.items():
                pattern_count[main_cat][subcat] = len(patterns)
        
        return {
            'total_main_categories': len(self.patterns),
            'total_sublabels': len(self.sublabels),
            'pattern_counts': pattern_count
        }

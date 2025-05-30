"""
Enhanced Comprehensive Pattern Matcher - All sublabels with flexible regex patterns
"""

from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

class PatternMatcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        self.patterns = {
            "manual_review": {
                "partial_disputed_payment": [
                    # From your thread handler
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
                    
                    # NEW PATTERNS TO ADD
                    r"debt.*is.*disputed", r"this.*debt.*is.*disputed",
                    r"disputed.*and.*not.*properly.*billed", r"billing.*error",
                    r"not.*properly.*billed", r"billed.*to.*wrong",
                    r"appropriate.*payor", r"wrong.*entity", r"wrong.*party",
                    r"dispute.*billing", r"incorrect.*billing",
                    r"must.*correct.*their.*billing", r"correct.*billing.*error",
                    r"not.*the.*appropriate", r"billed.*incorrectly",
                    r"disputing.*this.*debt", r"disputing.*these.*charges"
                ],
                
                "payment_confirmation": [
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
                    r"batch.*numbers.*included"
                ],
                
                "invoice_receipt": [
                    r"invoice.*attached", r"invoice.*copy.*attached", r"see.*attached.*invoice",
                    r"invoice.*is.*attached", r"here.*is.*invoice", r"proof.*of.*invoice",
                    r"invoice.*receipt", r"invoice.*documentation", r"copy.*of.*invoice.*attached"
                ],
                
                "closure_notification": [
                    r"business.*closed", r"company.*closed", r"out.*of.*business", r"ceased.*operations",
                    r"filed.*bankruptcy", r"bankruptcy.*protection", r"chapter.*7", r"chapter.*11"
                ],
                
                "closure_payment_due": [
                    r"closed.*payment.*due", r"business.*closed.*outstanding", r"closure.*payment.*required",
                    r"bankruptcy.*payment", r"filed.*bankruptcy.*payment", r"closure.*with.*payment"
                ],
                
                "external_submission": [
                    r"invoice.*issue", r"invoice.*problem", r"invoice.*error", r"import.*failed",
                    r"failed.*import", r"invoice.*submission.*failed", r"documents.*not.*processed",
                    r"submission.*failed", r"unable.*to.*import", r"import.*unsuccessful",
                    r"could.*not.*import", r"failed.*to.*import", r"error.*importing"
                ],
                
                "invoice_errors": [
                    r"missing.*field", r"format.*mismatch", r"incomplete.*invoice", r"required.*field",
                    r"invoice.*format.*issue", r"format.*error", r"field.*missing"
                ],
                
                "payment_details_received": [
                    r"payment.*will.*be.*sent", r"payment.*is.*being.*processed", r"check.*will.*be.*mailed",
                    r"payment.*scheduled", r"checks.*will.*be.*mailed.*by", r"payment.*timeline",
                    r"payment.*being.*processed", r"invoice.*being.*processed", r"payment.*details",
                    r"remittance.*info", r"payment.*breakdown",
                    r"waiting.*to.*receive.*customer.*payments",
                    r"waiting.*for.*payment.*from",
                    r"hope.*to.*have.*resolved",
                    r"payment.*delayed.*due.*to",
                    r"expecting.*payment.*from"

                ],
                
                "inquiry_redirection": [
                    # EXISTING PATTERNS
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
                    
                    # ADD THESE NEW PATTERNS
                    r"looks.*like.*a.*scam", r"think.*scam", r"verify.*legitimate",
                    r"are.*you.*legitimate", r"gotten.*scammed", r"verify.*authenticity",
                    r"please.*provide.*me.*with.*verification", r"verify.*with.*the.*sender"
                ],
                
                "complex_queries": [
                    r"multiple.*issues", r"several.*questions", r"complex.*situation", r"detailed.*inquiry",
                    r"various.*concerns", r"legal.*communication", r"attorney.*communication"
                ]
            },
            
            "no_reply": {
                "processing_errors": [
                    # From your thread handler
                    r"pdf.*file.*is.*not.*attached", r"error.*reason", r"processing.*error", 
                    r"cannot.*be.*processed", r"electronic.*invoice.*rejected", r"failed.*to.*process", 
                    r"case.*rejection",
                    
                    # Additional patterns
                    r"processing.*failed", r"unable.*to.*process", r"rejected.*for.*no.*attachment", 
                    r"mail.*delivery.*failed", r"email.*bounced", r"delivery.*failure", 
                    r"message.*undelivered", r"bounce.*back", r"email.*cannot.*be.*delivered"
                ],
                
                "sales_offers": [
                    r"special.*offer", r"limited.*time.*offer", r"promotional.*offer", 
                    r"sales.*promotion", r"discount.*offer", r"exclusive.*deal", r"flash.*sale"
                ],
                
                "import_failures": [
                    r"import.*failed", r"import.*error", r"failed.*import", r"import.*unsuccessful"
                ],
                
                "created": [
                    r"ticket.*created", r"case.*opened", r"new.*ticket", r"support.*request.*created",
                    r"case.*number.*is", r"assigned.*#", r"support.*ticket.*opened", 
                    r"case.*has.*been.*created", r"ticket.*has.*been.*created"
                ],
                
                "resolved": [
                    r"ticket.*resolved", r"case.*closed", r"case.*resolved", r"case.*has.*been.*resolved",
                    r"ticket.*has.*been.*resolved", r"case.*is.*now.*closed", r"request.*completed",
                    r"moved.*to.*solved", r"marked.*as.*resolved"
                ],
                
                "notifications": [
                    # EXISTING PATTERNS
                    r"system.*notification", r"automated.*notification", r"system.*alert",
                    r"maintenance.*notification", r"service.*update", r"backup.*completed",
                    r"security.*alert", r"delivery.*notification", r"legal.*notice",
                    r"unsubscribe", r"email.*preferences", r"thank.*you.*for.*your.*email",
                    r"thanks.*for.*your.*email", r"thank.*you.*for.*contacting",
                    r"business.*closure.*information", r"closure.*notification.*only",
                    
                    # ADD THESE NEW PATTERNS
                    r"still.*reviewing", r"will.*get.*back.*to.*you", r"reviewing.*this.*invoice",
                    r"currently.*reviewing", r"under.*review", r"in.*progress", r"processing.*your.*request",
                    r"we.*are.*reviewing", r"our.*return.*#.*is", r"correct.*number.*is",
                    r"updated.*information", r"for.*your.*records"
                ]
            },
            
            "invoices_request": {
                "request_no_info": [
                    # From your thread handler (specific patterns)
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
                    # From your thread handler (specific patterns)
                    r"its.*been.*paid", r"has.*been.*settled", r"this.*has.*been.*settled", 
                    r"already.*paid", r"been.*paid.*to.*them", r"payment.*was.*made", 
                    r"we.*paid", r"bill.*was.*paid", r"paid.*directly.*to", r"settled.*with",
                    r"been.*paid.*to", r"we.*sent.*check.*on", r"sent.*check.*on", 
                    r"check.*on.*april", r"check.*on.*may", r"check.*on.*march",
                    
                    # From misclassified emails (flexible patterns)
                    r"payment.*was.*sent", r"payment.*sent.*today", r"was.*paid.*by.*credit.*card",
                    r"we.*sent.*payment", r"we.*sent.*payment.*to", r"this.*payment.*has.*already.*been.*sent",
                    r"this.*was.*paid", r"it.*was.*paid", r"invoices.*are.*being.*processed.*for.*payment",
                    r"received.*invoices.*are.*being.*processed", r"i.*have.*paid.*my.*account",
                    r"paid.*my.*account.*via.*cc", r"paid.*via.*cc", r"paid.*last.*friday",
                    
                    # Flexible patterns (work for any amount/date/method)
                    r"payment.*sent", r"sent.*payment", r"payment.*made", r"was.*paid",
                    r"been.*paid", r"payment.*completed", r"payment.*processed", r"paid.*by",
                    r"paid.*via", r"paid.*through", r"paid.*on", r"paid.*to", r"sent.*check",
                    r"check.*sent", r"made.*payment", r"remitted", r"account.*paid",
                    r"paid.*by.*credit.*card", r"paid.*by.*check", r"wired.*payment", 
                    r"ach.*payment", r"electronic.*payment", r"settlement", r"resolved.*payment",
                    
                    # Frustrated/negative responses
                    r"should.*not.*be.*getting.*this", r"already.*sent", r"this.*has.*already.*been.*paid",
                    r"payment.*has.*already.*been.*sent", r"get.*outlook.*for.*ios"
                ]
            },
            
            "auto_reply": {
                "with_alternate_contact": [
                    r"out.*of.*office.*contact", r"out.*of.*office.*reach.*out", r"contact.*me.*at",
                    r"please.*contact.*\w+", r"call.*my.*cell", r"call.*my.*mobile", 
                    r"if.*you.*need.*immediate.*assistance", r"for.*all.*of.*your.*ap.*needs",
                    r"if.*urgent", r"urgent.*please.*contact", r"alternate.*contact"
                ],
                
                "return_date_specified": [
                    r"out.*of.*office.*until", r"return.*on", r"back.*on", r"available.*after",
                    r"returning.*\w+", r"will.*be.*back", r"out.*until.*\w+", r"when.*i.*return"
                ],
                
                "no_info_autoreply": [
                    r"out.*of.*office", r"automatic.*reply", r"auto-reply", r"auto.*reply",
                    r"i.*am.*currently.*out", r"i.*will.*be.*out", r"away.*from.*desk",
                    r"limited.*access.*to.*email", r"will.*return", r"on.*vacation", r"on.*leave",
                    r"currently.*traveling", r"do.*not.*reply", r"no-reply", r"noreply",
                    r"automated.*response", r"service.*account", r"system.*generated"
                ],
                
                "redirects_updates": [
                    # From your thread handler
                    r"is.*no.*longer.*with", r"please.*direct.*all.*future.*inquiries.*to", r"not.*accounts.*payable",
                    r"please.*contact", r"direct.*inquiries.*to", r"no.*longer.*employed",
                    r"please.*contact.*hd.*supply", r"contact.*the.*vendor.*directly", r"starting.*may.*1",
                    r"no.*longer.*be.*accepted", r"now.*using", r"please.*submit.*all.*future",
                    
                    # Additional patterns
                    r"no.*longer.*employed", r"contact.*changed", r"new.*contact", r"property.*manager",
                    r"department.*changed", r"quarantine.*report", r"contact.*redirection", r"forwarding.*to"
                ],
                
                "case_support": [
                    r"thank.*you.*for.*reaching.*out.*to.*us", r"we.*have.*received.*your.*request",
                    r"support.*team.*will.*review", r"member.*of.*our.*team.*will.*follow.*up",
                    r"case.*confirmed", r"support.*request.*confirmed", r"ticket.*confirmed"
                ],
                
                "survey": [
                    # EXISTING PATTERNS
                    r"survey", r"feedback.*request", r"rate.*our.*service", r"customer.*satisfaction",
                    r"please.*rate", r"take.*short.*survey",
                    
                    # ADD THESE NEW PATTERNS
                    r"feedback.*is.*important", r"take.*our.*survey", r"complete.*the.*online.*survey",
                    r"please.*visit.*the.*survey", r"survey.*web.*site.*link", r"feedback.*on.*the.*support",
                    r"would.*appreciate.*your.*feedback", r"click.*here.*to.*complete.*survey"
                ]
            }
        }
        
        # Compile patterns
        self.compiled_patterns = {}
        for main_cat, subcats in self.patterns.items():
            self.compiled_patterns[main_cat] = {}
            for subcat, patterns in subcats.items():
                self.compiled_patterns[main_cat][subcat] = [
                    re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in patterns
                ]
        
        # Category mappings
        self.main_categories = {
            "manual_review": "Manual Review",
            "no_reply": "No Reply (with/without info)",
            "invoices_request": "Invoices Request", 
            "payments_claim": "Payments Claim",
            "auto_reply": "Auto Reply (with/without info)"
        }
        
        self.sublabels = {
            "partial_disputed_payment": "Partial/Disputed Payment",
            "payment_confirmation": "Payment Confirmation",
            "invoice_receipt": "Invoice Receipt", 
            "closure_notification": "Closure Notification",
            "closure_payment_due": "Closure + Payment Due",
            "external_submission": "External Submission",
            "invoice_errors": "Invoice Errors (format mismatch)",
            "payment_details_received": "Payment Details Received",
            "inquiry_redirection": "Inquiry/Redirection",
            "complex_queries": "Complex Queries",
            "processing_errors": "Processing Errors",
            "sales_offers": "Sales/Offers", 
            "import_failures": "Import Failures",
            "created": "Created",
            "resolved": "Resolved",
            "notifications": "Notifications",
            "request_no_info": "Request (No Info)",
            "claims_paid_no_info": "Claims Paid (No Info)",
            "with_alternate_contact": "With Alternate Contact",
            "return_date_specified": "Return Date Specified", 
            "no_info_autoreply": "No Info/Autoreply",
            "redirects_updates": "Redirects/Updates (property changes)",
            "case_support": "Case/Support",
            "survey": "Survey"
        }
        
        self.logger.info("Enhanced PatternMatcher initialized with comprehensive patterns")

    def match_text(self, text: str, exclude_external_proof: bool = False) -> Tuple[Optional[str], Optional[str], float, List[str]]:
        """Match text against patterns with optional external proof exclusion"""
        if not text:
            return None, None, 0.0, []
        
        text_lower = text.lower()
        
        # External proof exclusion for payment confirmation
        if exclude_external_proof and self.has_external_proof_reference(text_lower):
            return None, None, 0.0, []
        
        best_match = None
        best_confidence = 0.0
        best_patterns = []
        
        for main_cat, subcats in self.compiled_patterns.items():
            for subcat, patterns in subcats.items():
                matches = 0
                matched_patterns = []
                
                for pattern in patterns:
                    if pattern.search(text_lower):
                        matches += 1
                        matched_patterns.append(pattern.pattern)
                
                if matches > 0:
                    confidence = min(0.8 + (matches * 0.05), 0.95)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = (main_cat, subcat)
                        best_patterns = matched_patterns
        
        if best_match:
            main_cat, subcat = best_match
            return (
                self.main_categories[main_cat],
                self.sublabels[subcat],
                best_confidence,
                best_patterns
            )
        
        return None, None, 0.0, []

    def has_external_proof_reference(self, text: str) -> bool:
        """Check if text refers to external proof rather than providing proof"""
        external_proof_phrases = [
            "if you look at your own email", "you will see it was settled", 
            "you sent an email confirming", "please consult your client",
            "check with your client", "consult your client who hired you",
            "you have the confirmation", "look at your records", "check your records"
        ]
        return any(phrase in text.lower() for phrase in external_proof_phrases)

    def get_payment_claim_match(self, text: str) -> bool:
        """Quick check for payment claims"""
        if not text:
            return False
        
        patterns = self.compiled_patterns.get("payments_claim", {}).get("claims_paid_no_info", [])
        text_lower = text.lower()
        
        return any(pattern.search(text_lower) for pattern in patterns)

    def get_dispute_match(self, text: str) -> bool:
        """Quick check for disputes"""
        if not text:
            return False
        
        patterns = self.compiled_patterns.get("manual_review", {}).get("partial_disputed_payment", [])
        text_lower = text.lower()
        
        return any(pattern.search(text_lower) for pattern in patterns)

    def get_invoice_request_match(self, text: str) -> bool:
        """Quick check for invoice requests"""
        if not text:
            return False
        
        patterns = self.compiled_patterns.get("invoices_request", {}).get("request_no_info", [])
        text_lower = text.lower()
        
        return any(pattern.search(text_lower) for pattern in patterns)

    def get_processing_error_match(self, text: str) -> bool:
        """Quick check for processing errors"""
        if not text:
            return False
        
        patterns = self.compiled_patterns.get("no_reply", {}).get("processing_errors", [])
        text_lower = text.lower()
        
        return any(pattern.search(text_lower) for pattern in patterns)
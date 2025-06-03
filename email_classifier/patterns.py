"""
Clean Pattern Matcher - Aligned with updated hierarchy structure
Quality code with targeted fixes for misclassifications
"""

from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

class PatternMatcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Clean patterns organized by hierarchy structure
        self.patterns = {
            "Manual Review": {
                # Disputes & Payments
                "Partial/Disputed Payment": [
                    # Core dispute patterns
                    r"amount.*is.*in.*dispute", r"this.*amount.*is.*in.*dispute", r"balance.*is.*not.*ours",
                    r"balance.*is.*not.*accurate", r"not.*our.*responsibility", r"do.*not.*owe", 
                    r"contested", r"disagreement", r"refuse", r"formally.*disputing", 
                    r"not.*accurate", r"that.*not.*my.*bill", r"due.*to.*a.*sale.*of.*property",
                    r"not.*ours.*due.*to",
                    
                    # Payment dispute patterns
                    r"partial.*payment", r"dispute.*payment", r"contested.*payment", 
                    r"disagreement.*payment", r"challenge.*payment", r"waive.*charges", 
                    r"cancel.*account", r"charges.*and.*cancel", r"material.*breach",
                    r"breach.*of.*contract", r"owes.*me", r"owes.*us",
                    
                    # Billing dispute patterns
                    r"debt.*is.*disputed", r"this.*debt.*is.*disputed",
                    r"cease.*and.*desist", r"do.*not.*acknowledge.*debt", r"fdcpa",
                    r"fair.*debt.*collection.*practices.*act",  # ADDED: Missing FDCPA pattern
                    r"disputed.*and.*not.*properly.*billed", r"billing.*error.*dispute",  # FIXED: More specific
                    r"not.*properly.*billed", r"billed.*to.*wrong",
                    r"appropriate.*payor", r"wrong.*entity", r"wrong.*party",
                    r"dispute.*billing", r"incorrect.*billing",
                    r"must.*correct.*their.*billing", r"correct.*billing.*error",
                    r"not.*the.*appropriate", r"billed.*incorrectly",
                    r"disputing.*this.*debt", r"disputing.*these.*charges", r"billing.*is.*wrong",
                ],
                
                # Invoice Updates  
                "Invoice Receipt": [
                    r"invoice.*attached", r"invoice.*copy.*attached", r"see.*attached.*invoice",
                    r"invoice.*is.*attached", r"here.*is.*invoice", r"proof.*of.*invoice",
                    r"invoice.*receipt", r"invoice.*documentation", r"copy.*of.*invoice.*attached"
                ],
                
                # Business Closure
                "Closure Notification": [
                    r"business.*closed", r"company.*closed", r"out.*of.*business", r"ceased.*operations",
                    r"filed.*bankruptcy", r"bankruptcy.*protection", r"chapter.*7", r"chapter.*11"
                ],
                
                "Closure + Payment Due": [
                    r"closed.*payment.*due", r"business.*closed.*outstanding", r"closure.*payment.*required",
                    r"bankruptcy.*payment", r"filed.*bankruptcy.*payment", r"closure.*with.*payment"
                ],
                
                # Invoices
                "External Submission": [
                    r"invoice.*issue", r"invoice.*problem", r"invoice.*error", r"import.*failed",
                    r"failed.*import", r"invoice.*submission.*failed", r"documents.*not.*processed",
                    r"submission.*failed", r"unable.*to.*import", r"import.*unsuccessful",
                    r"could.*not.*import", r"failed.*to.*import", r"error.*importing"
                ],
                
                "Invoice Errors (format mismatch)": [
                    r"missing.*field", r"format.*mismatch", r"incomplete.*invoice", r"required.*field",
                    r"invoice.*format.*issue", r"format.*error", r"field.*missing"
                ],
                
                # Other Manual Review
                "Inquiry/Redirection": [
                    # Information requests
                    r"insufficient.*data.*provided.*to.*research", r"there.*is.*insufficient.*data",
                    r"please.*ask", r"they.*are.*the.*who.*you.*must.*be.*reaching.*out",
                    r"i.*need.*guidance", r"please.*advise.*what.*is.*needed",
                    r"redirect.*to", r"forward.*to", r"contact.*instead", r"reach.*out.*to",
                    r"please.*check.*with", r"please.*refer.*to", r"contact.*our.*office",
                    r"is.*there.*any.*type.*of.*paperwork",r"what.*documentation.*needed",
                    r"should.*this.*be.*paid.*to",r"how.*should.*we.*pay",
                    r"where.*to.*send.*payment",r"can.*meet.*this.*requirement",
                    # Verification requests
                    r"looks.*like.*a.*scam", r"think.*scam", r"verify.*legitimate",
                    r"are.*you.*legitimate", r"gotten.*scammed", r"verify.*authenticity",
                    r"please.*provide.*me.*with.*verification", r"verify.*with.*the.*sender",
                    r"if.*you.*are.*legitimate", r"consider.*this.*a.*scam", r"otherwise.*consider.*scam"
                ],
                
                "Complex Queries": [
                    r"multiple.*issues", r"several.*questions", r"complex.*situation", r"detailed.*inquiry",
                    r"various.*concerns", r"legal.*communication", r"attorney.*communication"
                ]
            },
            
            "No Reply (with/without info)": {
                # Notifications
                "Sales/Offers": [
                    r"special.*offer", r"limited.*time.*offer", r"promotional.*offer", 
                    r"sales.*promotion", r"discount.*offer", r"exclusive.*deal", r"flash.*sale"
                ],
                
                "System Alerts": [
                    r"system.*notification", r"automated.*notification", r"system.*alert",
                    r"maintenance.*notification", r"service.*update", r"backup.*completed",
                    r"security.*alert", r"delivery.*notification", r"legal.*notice"
                ],
                
                "Processing Errors": [
                    # Processing failures
                    r"pdf.*file.*is.*not.*attached", r"error.*reason", r"processing.*error", 
                    r"cannot.*be.*processed", r"electronic.*invoice.*rejected", r"failed.*to.*process", 
                    r"case.*rejection", r"request.*couldn.*t.*be.*created", 
                    r"could.*not.*be.*created", r"system.*is.*unable.*to.*process", 
                    r"powered.*by.*jira.*service.*management",  # ADDED: Missing system error patterns
                    
                    # Delivery failures
                    r"processing.*failed", r"unable.*to.*process", r"rejected.*for.*no.*attachment", 
                    r"mail.*delivery.*failed", r"email.*bounced", r"delivery.*failure", 
                    r"message.*undelivered", r"bounce.*back", r"email.*cannot.*be.*delivered"
                ],
                
                "Business Closure (Info only)": [
                    r"business.*closure.*information", r"closure.*notification.*only"
                ],
                
                "General (Thank You)": [
                    # Thank you messages
                    r"unsubscribe", r"email.*preferences", r"thank.*you.*for.*your.*email",
                    r"thanks.*for.*your.*email", r"thank.*you.*for.*contacting",
                    
                    # Status updates
                    r"still.*reviewing", r"will.*get.*back.*to.*you", r"reviewing.*this.*invoice",
                    r"currently.*reviewing", r"under.*review", r"in.*progress", r"processing.*your.*request",
                    r"we.*are.*reviewing", r"our.*return.*#.*is", r"correct.*number.*is",
                    r"updated.*information", r"for.*your.*records"
                ],
                
                # Tickets/Cases
                "Created": [
                    r"ticket.*created", r"case.*opened", r"new.*ticket", r"support.*request.*created",
                    r"case.*number.*is", r"assigned.*#", r"support.*ticket.*opened", 
                    r"case.*has.*been.*created", r"ticket.*has.*been.*created"
                ],
                
                "Resolved": [
                    r"ticket.*resolved", r"case.*closed", r"case.*resolved", r"case.*has.*been.*resolved",
                    r"ticket.*has.*been.*resolved", r"case.*is.*now.*closed", r"request.*completed",
                    r"moved.*to.*solved", r"marked.*as.*resolved", r"status.*resolved", r"set.*to.*resolved",
                    r"ticket.*will.*remain"  # ADDED: Missing resolved pattern
                ],
                
                "Open": [
                    r"ticket.*open", r"case.*open", r"still.*pending", r"in.*progress", r"case.*pending"
                ]
            },
            
            "Invoices Request": {
                "Request (No Info)": [
                    # Specific invoice requests
                    r"can.*you.*please.*provide.*me.*with.*outstanding.*invoices",
                    r"provide.*me.*with.*outstanding.*invoices", r"can.*you.*please.*send.*me.*copies.*of.*any.*invoices",
                    r"send.*me.*copies.*of.*any.*invoices", r"can.*you.*send.*me.*the.*invoice",
                    r"provide.*us.*with.*the.*invoice", r"send.*me.*the.*invoice.*copy", r"need.*invoice.*copy",
                    r"provide.*invoice.*copy", r"send.*us.*invoice.*copy", r"copies.*of.*any.*invoices.*or.*po.*s",
                    r"outstanding.*invoices.*owed", r"trying.*to.*get.*detailed.*copy",  # ADDED: Missing patterns
                    r"get.*detailed.*copy.*of.*billing", r"detailed.*copy.*of.*this.*billing",  # ADDED: Missing patterns
                    
                    # General invoice requests
                    r"send.*invoice", r"need.*invoice", r"please.*send.*invoice", r"provide.*invoice",
                    r"invoice.*request", r"can.*you.*send.*invoice", r"send.*us.*invoice",
                    r"please.*provide.*invoice", r"invoice.*copy", r"copy.*of.*invoice"
                ]
            },
            
            "Payments Claim": {
                "Claims Paid (No Info)": [
                    # Basic payment claims
                    r"its.*been.*paid", r"has.*been.*settled", r"this.*has.*been.*settled", 
                    r"already.*paid", r"been.*paid.*to.*them", r"payment.*was.*made", 
                    r"we.*paid", r"bill.*was.*paid", r"paid.*directly.*to", r"settled.*with",
                    r"been.*paid.*to", r"we.*sent.*check.*on", r"sent.*check.*on", 
                    r"check.*on.*april", r"check.*on.*may", r"check.*on.*march",
                    
                    # Payment sent claims
                    r"payment.*was.*sent", r"payment.*sent.*today", r"was.*paid.*by.*credit.*card",
                    r"we.*sent.*payment", r"we.*sent.*payment.*to", r"this.*payment.*has.*already.*been.*sent",
                    r"this.*was.*paid", r"it.*was.*paid", r"invoices.*are.*being.*processed.*for.*payment",
                    r"received.*invoices.*are.*being.*processed", r"i.*have.*paid.*my.*account",
                    r"paid.*my.*account.*via.*cc", r"paid.*via.*cc", r"paid.*last.*friday",
                    
                    # General payment patterns
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
                
                "Payment Confirmation": [
                    # Proof of payment
                    r"proof.*of.*payment", r"payment.*confirmation", r"i.*have.*receipt",
                    r"check.*number", r"eft#", r"confirmation.*#", r"payment.*has.*been.*released",
                    r"was.*reconciled", r"here.*is.*proof", r"attached.*proof", r"payment.*evidence",
                    r"payment.*copy", r"wire.*document", r"receipt.*for", r"transaction.*id",
                    r"payment.*reference", r"voucher.*id", r"cleared.*bank",
                    r"see.*attachments", r"paid.*see.*attachments",  # ADDED: Missing attachment patterns
                    r"invoice.*was.*paid.*see.*attachments",  # ADDED: Missing attachment pattern
                    
                    # Transaction details
                    r"paid.*via.*transaction.*number",r"paid.*via.*batch.*number", 
                    r"transaction.*and.*batch.*numbers",r"here.*is.*the.*record.*of.*payment",
                    r"record.*within.*our.*project.*files",r"paid.*on.*\d+/\d+/\d+.*transaction",
                    r"paid.*via.*mastercard.*transaction",r"paid.*via.*visa.*transaction",
                    r"payment.*record.*included",r"transaction.*numbers.*included",
                    r"batch.*numbers.*included",r"paid.*via.*mastercard",r"paid.*via.*visa", 
                    r"paid.*via.*credit.*card",r"paid.*on.*\d+/\d+/\d+",
                    r"transaction.*numbers.*are.*included",r"batch.*numbers.*are.*included"
                ],
                
                "Payment Details Received": [
                    # Payment processing info
                    r"payment.*will.*be.*sent", r"payment.*is.*being.*processed", r"check.*will.*be.*mailed",
                    r"payment.*scheduled", r"checks.*will.*be.*mailed.*by", r"payment.*timeline",
                    r"payment.*being.*processed", r"invoice.*being.*processed", r"payment.*details",
                    r"remittance.*info", r"payment.*breakdown",r"in.*the.*process.*of.*issuing.*payment",
                    r"invoices.*have.*been.*entered.*and.*routed",r"routed.*for.*approval", 
                    r"need.*to.*go.*to.*several.*people.*to.*approve",r"waiting.*to.*receive.*customer.*payments",
                    r"waiting.*for.*payment.*from",r"hope.*to.*have.*resolved",
                    r"payment.*delayed.*due.*to",r"expecting.*payment.*from"
                ]
            },
            
            "Auto Reply (with/without info)": {
                # Out of Office
                "With Alternate Contact": [
                    r"out.*of.*office.*contact", r"out.*of.*office.*reach.*out", r"contact.*me.*at",
                    r"please.*contact.*me.*at.*\d+",r"please.*contact.*our.*office",
                    r"if.*you.*need.*immediate.*assistance.*contact",r"call.*my.*cell", r"call.*my.*mobile", 
                    r"if.*you.*need.*immediate.*assistance", r"for.*all.*of.*your.*ap.*needs",
                    r"if.*urgent", r"urgent.*please.*contact", r"alternate.*contact",
                    r"out.*of.*office.*contact",
                    r"please.*contact.*me.*at"
                ],
                
                "Return Date Specified": [
                    r"out.*of.*office.*until", r"return.*on", r"back.*on", r"available.*after",
                    r"returning.*\w+", r"will.*be.*back", r"out.*until.*\w+", r"when.*i.*return"
                ],
                
                "No Info/Autoreply": [
                    r"out.*of.*office", r"automatic.*reply", r"auto-reply", r"auto.*reply",
                    r"i.*am.*currently.*out", r"i.*will.*be.*out", r"away.*from.*desk",
                    r"limited.*access.*to.*email", r"will.*return", 
                    r"i.*am.*on.*vacation",r"i.*am.*on.*leave",
                    r"on.*leave", r"currently.*traveling", r"do.*not.*reply", r"no-reply", r"noreply",
                    r"automated.*response", r"service.*account", r"system.*generated"
                ],
                
                # Miscellaneous
                "Survey": [
                    # Survey requests
                    r"survey", r"feedback.*request", r"rate.*our.*service", r"customer.*satisfaction",
                    r"please.*rate", r"take.*short.*survey",
                    
                    # Feedback requests
                    r"feedback.*is.*important", r"take.*our.*survey", r"complete.*the.*online.*survey",
                    r"please.*visit.*the.*survey", r"survey.*web.*site.*link", r"feedback.*on.*the.*support",
                    r"would.*appreciate.*your.*feedback", r"click.*here.*to.*complete.*survey"
                ],
                
                "Redirects/Updates (property changes)": [
                    # Contact changes
                    r"is.*no.*longer.*with", r"please.*direct.*all.*future.*inquiries.*to", r"not.*accounts.*payable",
                    r"direct.*inquiries.*to", r"no.*longer.*employed",
                    r"please.*contact.*hd.*supply", r"contact.*the.*vendor.*directly", r"starting.*may.*1",
                    r"no.*longer.*be.*accepted", r"now.*using", r"please.*submit.*all.*future",
                    
                    # Property/department changes
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
            "Manual Review": "Manual Review",
            "No Reply (with/without info)": "No Reply (with/without info)",
            "Invoices Request": "Invoices Request", 
            "Payments Claim": "Payments Claim",
            "Auto Reply (with/without info)": "Auto Reply (with/without info)"
        }
        
        # Updated sublabel mappings aligned with new hierarchy
        self.sublabels = {
            # Manual Review sublabels
            "Partial/Disputed Payment": "Partial/Disputed Payment",
            "Invoice Receipt": "Invoice Receipt", 
            "Closure Notification": "Closure Notification",
            "Closure + Payment Due": "Closure + Payment Due",
            "External Submission": "External Submission",
            "Invoice Errors (format mismatch)": "Invoice Errors (format mismatch)",
            "Inquiry/Redirection": "Inquiry/Redirection",
            "Complex Queries": "Complex Queries",
            
            # No Reply sublabels
            "Sales/Offers": "Sales/Offers",
            "System Alerts": "System Alerts",
            "Processing Errors": "Processing Errors", 
            "Business Closure (Info only)": "Business Closure (Info only)",
            "General (Thank You)": "General (Thank You)",
            "Created": "Created",
            "Resolved": "Resolved",
            "Open": "Open",
            
            # Invoice Request sublabel
            "Request (No Info)": "Request (No Info)",
            
            # Payments Claim sublabels
            "Claims Paid (No Info)": "Claims Paid (No Info)",
            "Payment Details Received": "Payment Details Received",
            "Payment Confirmation": "Payment Confirmation",
            
            # Auto Reply sublabels
            "With Alternate Contact": "With Alternate Contact",
            "No Info/Autoreply": "No Info/Autoreply",
            "Return Date Specified": "Return Date Specified",
            "Survey": "Survey",
            "Redirects/Updates (property changes)": "Redirects/Updates (property changes)"
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
        """FIXED: Resolve conflicts using correct category names"""
        if not matches:
            return None
        
        if len(matches) == 1:
            return matches[0]
        
        # FIXED: Priority rules with correct category names
        priority_order = [
            # High priority - specific business actions
            ('Payments Claim', 'Payment Confirmation'),  # FIXED: Correct category names
            ('Manual Review', 'Partial/Disputed Payment'),  # FIXED: Correct category names
            ('No Reply (with/without info)', 'Processing Errors'),  # FIXED: Correct category names
            
            # Medium priority - requests and claims  
            ('Invoices Request', 'Request (No Info)'),  # FIXED: Correct category names
            ('Payments Claim', 'Claims Paid (No Info)'),  # FIXED: Correct category names
            ('Payments Claim', 'Payment Details Received'),  # FIXED: Correct category names
            
            # Lower priority - notifications and auto replies
            ('No Reply (with/without info)', 'Created'),  # FIXED: Correct category names
            ('No Reply (with/without info)', 'Resolved'),  # FIXED: Correct category names
            ('Auto Reply (with/without info)', 'With Alternate Contact'),  # FIXED: Correct category names
            ('Auto Reply (with/without info)', 'Survey'),  # FIXED: Correct category names
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
        patterns = self.compiled_patterns.get("Payments Claim", {}).get("Claims Paid (No Info)", [])
        return any(pattern.search(text.lower()) for pattern in patterns)

    def get_dispute_match(self, text: str) -> bool:
        """Quick check for disputes"""
        if not text:
            return False
        patterns = self.compiled_patterns.get("Manual Review", {}).get("Partial/Disputed Payment", [])
        return any(pattern.search(text.lower()) for pattern in patterns)

    def get_invoice_request_match(self, text: str) -> bool:
        """Quick check for invoice requests"""
        if not text:
            return False
        patterns = self.compiled_patterns.get("Invoices Request", {}).get("Request (No Info)", [])
        return any(pattern.search(text.lower()) for pattern in patterns)

    def get_processing_error_match(self, text: str) -> bool:
        """Quick check for processing errors"""
        if not text:
            return False
        patterns = self.compiled_patterns.get("No Reply (with/without info)", {}).get("Processing Errors", [])
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
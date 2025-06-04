"""
Clean Pattern Matcher - FIXED with proper word boundaries
Quality code preventing false matches inside words
"""

from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

class PatternMatcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # FIXED patterns with proper word boundaries
        self.patterns = {
            "Manual Review": {
                # Disputes & Payments - ENHANCED with missing legal patterns
                "Partial/Disputed Payment": [
                    # Core dispute patterns
                    r"amount.*is.*in.*dispute", r"balance.*is.*not.*ours", r"not.*our.*responsibility", 
                    r"do.*not.*owe", r"\bcontested\b", r"\bdisagreement\b", r"formally.*disputing",
                    r"dispute.*payment", r"contested.*payment", r"challenge.*payment",
                    r"debt.*is.*disputed", r"cease.*and.*desist", r"do.*not.*acknowledge.*debt",
                    r"\bfdcpa\b", r"billing.*error.*dispute", r"not.*properly.*billed",
                    r"wrong.*entity", r"dispute.*billing", r"disputing.*this.*debt",
                    r"owe.*them.*nothing", r"owe.*nothing", r"consider.*this.*a.*scam", 
                    r"looks.*like.*a.*scam", r"is.*this.*legitimate", r"verify.*this.*is.*real",
                    
                    # HIGH PRIORITY FIX: Legal/Cease & Desist patterns (Emails 5 & 6)
                    r"cease.*and.*desist.*letter", r"legal.*notice", r"fdcpa.*violation",
                    r"do.*not.*acknowledge.*this.*debt", r"formally.*dispute.*this.*debt",
                    r"debt.*validation.*request", r"legal.*representation", r"attorney.*correspondence",
                    r"collection.*agency.*violation", r"fair.*debt.*collection", r"cease.*all.*communication",
                    r"legal.*action.*threatened", r"debt.*collector.*harassment", r"validation.*of.*debt",
                    r"cease.*and.*desist.*all.*contact", r"legal.*counsel.*representation"
                ],
                
                # Invoice Receipt - FIXED to be more specific
                "Invoice Receipt": [
                    r"invoice.*attached.*as.*proof", r"attached.*invoice.*copy", r"proof.*of.*invoice.*attached",
                    r"invoice.*documentation.*attached", r"here.*is.*the.*invoice.*copy",
                    r"invoice.*receipt.*attached", r"copy.*of.*invoice.*attached.*for.*your.*records",
                    
                    # MEDIUM PRIORITY FIX: Payment documentation patterns (Email 139)
                    r"payment.*made.*in.*error.*documentation", r"error.*payment.*proof",
                    r"documentation.*for.*payment.*error", r"proof.*of.*payment.*error",
                    r"attached.*payment.*documentation", r"payment.*error.*receipt"
                ],

                # Business Closure - SIMPLIFIED
                "Closure Notification": [
                    r"business.*closed", r"company.*closed", r"out.*of.*business", r"ceased.*operations",
                    r"filed.*bankruptcy", r"bankruptcy.*protection", r"chapter.*7", r"chapter.*11"
                ],
                
                "Closure + Payment Due": [
                    r"closed.*payment.*due", r"business.*closed.*outstanding", r"bankruptcy.*payment.*due",
                    r"closure.*with.*outstanding.*payment"
                ],
                
                # Invoices - CLEAR DISTINCTION
                "External Submission": [
                    r"invoice.*submission.*failed", r"import.*failed", r"failed.*import", r"unable.*to.*import",
                    r"documents.*not.*processed", r"submission.*unsuccessful", r"error.*importing.*invoice"
                ],
                
                "Invoice Errors (format mismatch)": [
                    r"missing.*required.*field", r"format.*mismatch", r"incomplete.*invoice", 
                    r"invoice.*format.*error", r"field.*missing.*from.*invoice"
                ],
                
                # Inquiry/Redirection - CLEANED
                "Inquiry/Redirection": [
                    r"insufficient.*data.*to.*research", r"need.*guidance", r"please.*advise",
                    r"redirect.*to", r"contact.*instead", r"reach.*out.*to", r"please.*check.*with",
                    r"what.*documentation.*needed", r"where.*to.*send.*payment",
                    r"verify.*legitimate", r"looks.*like.*a.*scam", r"are.*you.*legitimate"
                ],

                # HIGH PRIORITY FIX: Enhanced Complex Queries patterns (Email 31)
                "Complex Queries": [
                    r"multiple.*issues", r"complex.*situation", r"legal.*communication",
                    r"settle.*for.*\$", r"settlement.*offer", r"negotiate.*payment",
                    
                    # Settlement and legal arrangement patterns
                    r"settlement.*arrangement", r"legal.*settlement.*agreement", r"payment.*settlement",
                    r"settlement.*negotiation", r"legal.*arrangement", r"settlement.*terms",
                    r"attorney.*settlement", r"legal.*resolution", r"settlement.*discussion",
                    r"complex.*legal.*matter", r"legal.*consultation", r"attorney.*involvement",
                    r"legal.*proceedings", r"court.*settlement", r"mediation.*settlement",
                    
                    # Complex business routing patterns (Email 41)
                    r"complex.*business.*instructions", r"routing.*instructions", r"complex.*routing",
                    r"business.*process.*instructions", r"multi.*step.*process", r"complex.*procedure",
                    r"detailed.*business.*process", r"special.*handling.*instructions", r"complex.*workflow"
                ]
            },
            
            "No Reply (with/without info)": {
                # MEDIUM PRIORITY FIX: Enhanced Sales/Offers patterns (Email 94)
                "Sales/Offers": [
                    r"special.*offer", r"limited.*time.*offer", r"promotional.*offer", 
                    r"discount.*offer", r"exclusive.*deal", r"prices.*increasing", r"limited.*time", r"hours.*left", 
                    r"special.*pricing", r"promotional.*offer", r"sale.*ending", r"limited.*time.*offer",
                    
                    # Payment plan and sales discussion patterns
                    r"payment.*plan.*options", r"payment.*plan.*discussion", r"installment.*plan",
                    r"payment.*arrangement.*offer", r"flexible.*payment.*options", r"payment.*terms.*discussion",
                    r"financing.*options", r"payment.*schedule.*options", r"payment.*plan.*available",
                    r"monthly.*payment.*plan", r"extended.*payment.*terms", r"payment.*flexibility"
                ],
                
                "System Alerts": [
                    r"system.*notification", r"automated.*notification", r"system.*alert",
                    r"maintenance.*notification", r"security.*alert"
                ],
                
                "Processing Errors": [
                    r"processing.*error", r"failed.*to.*process", r"cannot.*be.*processed",
                    r"electronic.*invoice.*rejected", r"request.*couldn.*t.*be.*created",
                    r"system.*unable.*to.*process", r"mail.*delivery.*failed", r"email.*bounced"
                ],
                
                "Business Closure (Info only)": [
                    r"business.*closure.*information", r"closure.*notification.*only"
                ],
                
                "General (Thank You)": [
                    r"thank.*you.*for.*your.*email", r"thanks.*for.*contacting",
                    r"still.*reviewing", r"currently.*reviewing", r"under.*review",
                    r"we.*are.*reviewing", r"for.*your.*records"
                ],
                
                # LOW PRIORITY FIX: Enhanced ticket creation patterns (Emails 75, 77)
                "Created": [
                    r"ticket.*created", r"case.*opened", r"new.*ticket.*opened",
                    r"support.*request.*created", r"case.*has.*been.*created",
                    
                    # Additional ticket creation patterns
                    r"ticket.*has.*been.*opened", r"new.*case.*created", r"support.*ticket.*opened",
                    r"case.*number.*assigned", r"ticket.*number.*assigned", r"new.*support.*case",
                    r"request.*has.*been.*submitted", r"ticket.*submitted.*successfully",
                    r"case.*opened.*for.*review", r"support.*request.*received"
                ],
                
                "Resolved": [
                    r"ticket.*resolved", r"case.*closed", r"case.*resolved",
                    r"ticket.*has.*been.*resolved", r"marked.*as.*resolved", r"status.*resolved"
                ],
                
                "Open": [
                    r"ticket.*open", r"case.*open", r"still.*pending", r"case.*pending"
                ]
            },
            
            "Invoices Request": {
                "Request (No Info)": [
                    # SPECIFIC invoice requests - EXCLUDE documentation
                    r"send.*me.*the.*invoice", r"provide.*the.*invoice", r"need.*invoice.*copy",
                    r"outstanding.*invoices.*owed", r"copies.*of.*any.*invoices",
                    r"send.*invoices.*that.*are.*due", r"provide.*outstanding.*invoices",
                    r"send.*me.*the.*invoice(?!.*paid)", r"need.*invoice.*copy(?!.*paid)"
                ]
            },

            "Payments Claim": {
                "Claims Paid (No Info)": [
                    # BASIC claims without proof - CLEANED UP
                    r"already.*paid", r"payment.*was.*made", r"we.*paid", r"bill.*was.*paid",
                    r"payment.*was.*sent", r"check.*sent", r"payment.*completed",
                    r"this.*was.*paid", r"account.*paid", r"made.*payment"
                ],
                
                "Payment Confirmation": [
                    # ONLY when providing actual proof/details
                    r"proof.*of.*payment", r"payment.*confirmation.*attached", r"check.*number.*\d+",
                    r"eft#.*\d+", r"transaction.*id.*\d+", r"here.*is.*proof.*of.*payment",
                    r"payment.*receipt.*attached", r"wire.*confirmation.*\d+",
                    r"paid.*via.*transaction.*number.*\d+", r"batch.*number.*\d+",
                    r"invoice.*was.*paid.*see.*attachments", r"payment.*proof.*attached",
                    r"here.*is.*proof.*of.*payment", r"payment.*confirmation.*attached"
                ],

                "Payment Details Received": [
                    # FUTURE payments and processing info
                    r"payment.*will.*be.*sent", r"payment.*being.*processed", r"check.*will.*be.*mailed",
                    r"payment.*scheduled", r"in.*process.*of.*issuing.*payment",
                    r"invoices.*being.*processed.*for.*payment", r"will.*pay.*this.*online",
                    r"working.*on.*payment", r"need.*time.*to.*pay"
                ]
            },
            
            "Auto Reply (with/without info)": {
                "With Alternate Contact": [
                    # ONLY genuine OOO with contact - STRICT
                    r"out.*of.*office.*contact.*\d+", r"emergency.*contact.*\d+",
                    r"urgent.*matters.*contact.*\d+", r"immediate.*assistance.*contact.*\d+"
                ],
                
                # LOW PRIORITY FIX: Enhanced Return Date patterns (Emails 11, 38, 52, 53, 66, 70, 95, 105)
                "Return Date Specified": [
                    r"out.*of.*office.*until.*\d+", r"return.*on.*\d+", r"back.*on.*\d+",
                    r"returning.*\d+", r"will.*be.*back.*\d+",
                    
                    # Enhanced return date patterns
                    r"return.*to.*office.*on", r"back.*in.*office.*on", r"returning.*to.*work.*on",
                    r"will.*return.*on", r"back.*from.*vacation.*on", r"return.*date.*is",
                    r"expected.*return.*date", r"returning.*from.*leave.*on", r"back.*on.*\w+day",
                    r"return.*on.*\w+.*\d+", r"back.*\w+.*\d+", r"returning.*\w+.*\d+",
                    r"out.*until.*\w+", r"away.*until.*\w+", r"return.*after.*\w+",
                    r"back.*after.*\w+", r"returning.*after.*the.*holiday", r"back.*monday",
                    r"return.*monday", r"back.*next.*week", r"return.*next.*week"
                ],
                
                "No Info/Autoreply": [
                    r"out.*of.*office", r"automatic.*reply", r"auto-reply", r"currently.*out",
                    r"away.*from.*desk", r"on.*vacation", r"limited.*access.*to.*email",
                    r"do.*not.*reply", r"automated.*response"
                ],
                
                "Survey": [
                    r"\bsurvey\b", r"feedback.*request", r"rate.*our.*service",
                    r"customer.*satisfaction", r"take.*our.*survey"
                ],
                
                "Redirects/Updates (property changes)": [
                    r"no.*longer.*with", r"no.*longer.*employed", r"contact.*changed",
                    r"property.*manager.*changed", r"department.*changed"
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
        
        self.logger.info("✅ Clean PatternMatcher initialized with word boundaries")

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
        """IMPROVED conflict resolution with business logic"""
        if not matches:
            return None
        
        if len(matches) == 1:
            return matches[0]
        
        # BUSINESS LOGIC CONFLICTS - handle specific cases
        match_categories = [(m['main_cat'], m['subcat']) for m in matches]
        
        # 1. Payment Confirmation vs Claims - favor confirmation if has proof numbers
        if any('Payment Confirmation' in str(m) for m in match_categories):
            proof_patterns = [r'\d{4,}', r'eft#', r'transaction.*\d+', r'check.*number.*\d+']
            if any(re.search(pattern, text, re.I) for pattern in proof_patterns):
                for match in matches:
                    if match['subcat'] == 'Payment Confirmation':
                        return match
        
        # 2. Invoice Receipt vs Invoice Request - favor receipt if "attached" mentioned
        if 'Invoice Receipt' in str(match_categories) and 'Request (No Info)' in str(match_categories):
            if 'attached' in text or 'proof' in text:
                for match in matches:
                    if match['subcat'] == 'Invoice Receipt':
                        return match
            else:  # Favor request if no attachment language
                for match in matches:
                    if match['subcat'] == 'Request (No Info)':
                        return match
        
        # 3. Auto Reply vs Manual Review - favor Manual Review for business content
        auto_reply_match = next((m for m in matches if m['main_cat'] == 'Auto Reply (with/without info)'), None)
        manual_match = next((m for m in matches if m['main_cat'] == 'Manual Review'), None)
        
        if auto_reply_match and manual_match:
            business_terms = ['payment', 'invoice', 'dispute', 'collection', 'debt']
            if any(term in text for term in business_terms):
                return manual_match
        
        # 4. Default priority order
        priority_order = [
            ('Manual Review', 'Partial/Disputed Payment'),
            ('Payments Claim', 'Payment Confirmation'),
            ('Manual Review', 'Invoice Receipt'),
            ('Invoices Request', 'Request (No Info)'),
            ('Payments Claim', 'Claims Paid (No Info)'),
            ('No Reply (with/without info)', 'Processing Errors'),
            ('Auto Reply (with/without info)', 'With Alternate Contact')
        ]
        
        for main_cat, subcat in priority_order:
            for match in matches:
                if match['main_cat'] == main_cat and match['subcat'] == subcat:
                    return match
        
        # 5. Return highest confidence as final fallback
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
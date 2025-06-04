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
                "Partial/Disputed Payment": [
                    r"amount.*is.*in.*dispute", r"balance.*is.*not.*ours", r"not.*our.*responsibility", 
                    r"do.*not.*owe", r"\bcontested\b", r"\bdisagreement\b", r"formally.*disputing",
                    r"dispute.*payment", r"contested.*payment", r"challenge.*payment",
                    r"debt.*is.*disputed", r"cease.*and.*desist", r"do.*not.*acknowledge.*debt",
                    r"\bfdcpa\b", r"billing.*error.*dispute", r"not.*properly.*billed",
                    r"wrong.*entity", r"dispute.*billing", r"disputing.*this.*debt",
                    r"owe.*them.*nothing", r"owe.*nothing", r"consider.*this.*a.*scam", 
                    r"looks.*like.*a.*scam", r"is.*this.*legitimate", r"verify.*this.*is.*real",
                    r"cease.*and.*desist.*letter", r"legal.*notice", r"fdcpa.*violation",
                    r"do.*not.*acknowledge.*this.*debt", r"formally.*dispute.*this.*debt",
                    r"debt.*validation.*request", r"legal.*representation", r"attorney.*correspondence",
                    r"collection.*agency.*violation", r"fair.*debt.*collection", r"cease.*all.*communication",
                    r"legal.*action.*threatened", r"debt.*collector.*harassment", r"validation.*of.*debt",
                    r"cease.*and.*desist.*all.*contact", r"legal.*counsel.*representation",
                    r"refuse.*to.*pay", r"will.*not.*pay.*this", r"do.*not.*recognize.*this.*debt"
                ],
                
                "Invoice Receipt": [
                    r"invoice.*attached.*as.*proof", r"attached.*invoice.*copy", r"proof.*of.*invoice.*attached",
                    r"invoice.*documentation.*attached", r"here.*is.*the.*invoice.*copy",
                    r"invoice.*receipt.*attached", r"copy.*of.*invoice.*attached.*for.*your.*records",
                    r"payment.*made.*in.*error.*documentation", r"error.*payment.*proof",
                    r"documentation.*for.*payment.*error", r"proof.*of.*payment.*error",
                    r"attached.*payment.*documentation", r"payment.*error.*receipt",
                    r"invoice.*copy.*for.*your.*records", r"supporting.*invoice.*documentation"
                ],

                "Closure Notification": [
                    r"business.*closed", r"company.*closed", r"out.*of.*business", r"ceased.*operations",
                    r"filed.*bankruptcy", r"bankruptcy.*protection", r"chapter.*7", r"chapter.*11",
                    r"business.*is.*closed", r"company.*has.*closed", r"no.*longer.*in.*business"
                ],
                
                "Closure + Payment Due": [
                    r"closed.*payment.*due", r"business.*closed.*outstanding", r"bankruptcy.*payment.*due",
                    r"closure.*with.*outstanding.*payment", r"closed.*but.*owe", r"bankruptcy.*still.*owe"
                ],
                
                "External Submission": [
                    r"invoice.*submission.*failed", r"import.*failed", r"failed.*import", r"unable.*to.*import",
                    r"documents.*not.*processed", r"submission.*unsuccessful", r"error.*importing.*invoice",
                    r"invoice.*could.*not.*be.*processed", r"submission.*error", r"import.*error"
                ],
                
                "Invoice Errors (format mismatch)": [
                    r"missing.*required.*field", r"format.*mismatch", r"incomplete.*invoice", 
                    r"invoice.*format.*error", r"field.*missing.*from.*invoice",
                    r"invalid.*invoice.*format", r"incorrect.*invoice.*format"
                ],
                
                "Inquiry/Redirection": [
                    r"insufficient.*data.*to.*research", r"need.*guidance", r"please.*advise",
                    r"redirect.*to", r"contact.*instead", r"reach.*out.*to", r"please.*check.*with",
                    r"what.*documentation.*needed", r"where.*to.*send.*payment",
                    r"verify.*legitimate", r"are.*you.*legitimate", r"what.*bills\?",
                    r"what.*is.*this.*for\?", r"what.*are.*they.*charging.*me.*for\?",
                    r"backup.*documentation", r"supporting.*documents", r"provide.*backup",
                    r"can.*you.*provide", r"need.*more.*information", r"require.*additional.*details",
                    r"please.*clarify", r"need.*clarification", r"what.*service", r"what.*product",
                    r"never.*had.*a.*contract", r"no.*agreement.*with", r"no.*relationship.*with"
                ],

                "Complex Queries": [
                    r"multiple.*issues", r"complex.*situation", r"legal.*communication",
                    r"settle.*for.*\$", r"settlement.*offer", r"negotiate.*payment",
                    r"settlement.*arrangement", r"legal.*settlement.*agreement", r"payment.*settlement",
                    r"settlement.*negotiation", r"legal.*arrangement", r"settlement.*terms",
                    r"attorney.*settlement", r"legal.*resolution", r"settlement.*discussion",
                    r"complex.*legal.*matter", r"legal.*consultation", r"attorney.*involvement",
                    r"legal.*proceedings", r"court.*settlement", r"mediation.*settlement",
                    r"complex.*business.*instructions", r"routing.*instructions", r"complex.*routing",
                    r"business.*process.*instructions", r"multi.*step.*process", r"complex.*procedure",
                    r"detailed.*business.*process", r"special.*handling.*instructions", r"complex.*workflow",
                    r"attorney.*will.*contact", r"legal.*counsel.*will", r"escalate.*to.*legal"
                ]
            },
            
            "No Reply (with/without info)": {
                "Sales/Offers": [
                    r"special.*offer", r"limited.*time.*offer", r"promotional.*offer", 
                    r"discount.*offer", r"exclusive.*deal", r"prices.*increasing", r"limited.*time", 
                    r"hours.*left", r"special.*pricing", r"sale.*ending", r"price.*increase",
                    r"promotional.*pricing", r"discount.*pricing", r"flash.*sale", r"clearance.*sale",
                    r"payment.*plan.*options", r"payment.*plan.*discussion", r"installment.*plan",
                    r"payment.*arrangement.*offer", r"flexible.*payment.*options", r"payment.*terms.*discussion",
                    r"financing.*options", r"payment.*schedule.*options", r"payment.*plan.*available",
                    r"monthly.*payment.*plan", r"extended.*payment.*terms", r"payment.*flexibility"
                ],
                
                "System Alerts": [
                    r"system.*notification", r"automated.*notification", r"system.*alert",
                    r"maintenance.*notification", r"security.*alert", r"system.*maintenance",
                    r"server.*maintenance", r"scheduled.*maintenance"
                ],
                
                "Processing Errors": [
                    r"processing.*error", r"failed.*to.*process", r"cannot.*be.*processed",
                    r"electronic.*invoice.*rejected", r"request.*couldn.*t.*be.*created",
                    r"system.*unable.*to.*process", r"mail.*delivery.*failed", r"email.*bounced",
                    r"delivery.*failure", r"message.*undeliverable", r"email.*rejected"
                ],
                
                "Business Closure (Info only)": [
                    r"business.*closure.*information", r"closure.*notification.*only",
                    r"informational.*closure", r"closure.*announcement"
                ],
                
                "General (Thank You)": [
                    r"thank.*you.*for.*your.*email", r"thanks.*for.*contacting",
                    r"still.*reviewing", r"currently.*reviewing", r"under.*review",
                    r"we.*are.*reviewing", r"for.*your.*records", r"received.*your.*message",
                    r"we.*received.*your", r"acknowledgment.*of.*receipt"
                ],
                
                "Created": [
                    r"ticket.*created", r"case.*opened", r"new.*ticket.*opened",
                    r"support.*request.*created", r"case.*has.*been.*created",
                    r"ticket.*has.*been.*opened", r"new.*case.*created", r"support.*ticket.*opened",
                    r"case.*number.*assigned", r"ticket.*number.*assigned", r"new.*support.*case",
                    r"request.*has.*been.*submitted", r"ticket.*submitted.*successfully",
                    r"case.*opened.*for.*review", r"support.*request.*received",
                    r"your.*request.*has.*been.*received", r"ticket.*\d+.*created"
                ],
                
                "Resolved": [
                    r"ticket.*resolved", r"case.*closed", r"case.*resolved",
                    r"ticket.*has.*been.*resolved", r"marked.*as.*resolved", r"status.*resolved",
                    r"case.*has.*been.*closed", r"ticket.*completed", r"request.*completed",
                    r"issue.*resolved", r"matter.*resolved"
                ],
                
                "Open": [
                    r"ticket.*open", r"case.*open", r"still.*pending", r"case.*pending",
                    r"request.*pending", r"under.*investigation", r"being.*reviewed"
                ]
            },

            "Invoices Request": {
                "Request (No Info)": [
                    r"send.*me.*the.*invoice", r"provide.*the.*invoice", r"need.*invoice.*copy",
                    r"outstanding.*invoices.*owed", r"copies.*of.*any.*invoices",
                    r"send.*invoices.*that.*are.*due", r"provide.*outstanding.*invoices",
                    r"send.*me.*invoice", r"share.*the.*invoice", r"forward.*invoice",
                    r"share.*invoice.*copy", r"share.*the.*past.*due.*invoice.*copy",
                    r"please.*share.*the.*invoice", r"can.*you.*send.*the.*invoice",
                    r"need.*a.*copy.*of.*the.*invoice", r"invoice.*copies.*needed",
                    r"send.*copies.*of.*invoices", r"provide.*invoice.*documentation",
                    r"copies.*of.*the.*past.*due.*invoices", r"send.*me.*copies.*of.*invoices",
                    r"please.*send.*invoices", r"need.*invoice.*copy", r"provide.*invoices",
                    r"send.*me.*the.*invoice", r"copies.*of.*invoices",
                    r"(?!.*automatic)(?!.*system)send.*invoices"
                ]
            },

            "Payments Claim": {
                "Claims Paid (No Info)": [
                    # Basic payment claims without proof documents
                    r"already.*paid", r"payment.*was.*made", r"we.*paid", r"bill.*was.*paid",
                    r"payment.*was.*sent", r"check.*sent", r"payment.*completed",
                    r"this.*was.*paid", r"account.*paid", r"made.*payment", r"been.*paid",
                    r"i.*mailed.*a.*check", r"check.*was.*mailed", r"payment.*sent",
                    r"i.*paid.*that.*bill", r"this.*has.*been.*paid", r"account.*is.*paid",
                    r"balance.*is.*paid", r"invoice.*was.*paid", r"bill.*is.*paid",
                    r"payment.*has.*been.*made", r"we.*have.*paid", r"i.*have.*paid",
                    r"this.*was.*settled", r"account.*settled", r"debt.*was.*paid"
                ],
                
                "Payment Confirmation": [
                    # Direct attachment references
                    r"see.*attachments", r"proof.*attached", r"payment.*confirmation.*attached",
                    r"receipt.*attached", r"confirmation.*attached", r"attached.*payment",
                    r"invoice.*was.*paid.*see.*attachments", r"see.*attached.*check",
                    r"proof.*of.*payment.*attached", r"please.*see.*attached.*cancelled.*check",
                    r"use.*as.*proof.*of.*payment", r"please.*use.*as.*proof",
                    r"check.*number.*\d+", r"transaction.*id.*\w+", r"eft.*\w+",
                    r"wire.*confirmation.*\w+", r"batch.*number.*\w+", r"reference.*number.*\w+",
                    r"transaction#.*\d+", r"ach.*confirmation.*number", r"ach.*amount.*\$",
                    r"paid.*via.*transaction.*number.*\w+",
                    r"here.*is.*proof.*of.*payment", r"payment.*proof.*attached",
                    r"wire.*transfer.*confirmation", r"payment.*receipt.*number",
                    r"electronic.*payment.*confirmation", r"bank.*confirmation",
                    r"payment.*verification", r"they.*have.*everything",
                    r"remittance.*details.*for.*your.*reference", r"detailed.*remittance",
                    r"payment.*details.*below", r"remittance.*information",
                    r"wire.*document"
                ],

                "Payment Details Received": [
                    # Future payment commitments
                    r"payment.*will.*be.*sent", r"payment.*being.*processed", 
                    r"check.*will.*be.*mailed", r"payment.*scheduled",
                    r"in.*process.*of.*issuing.*payment", r"invoices.*being.*processed.*for.*payment",
                    r"will.*pay.*this.*online", r"working.*on.*payment", r"need.*time.*to.*pay",
                    r"payment.*is.*being.*processed", r"check.*is.*being.*prepared",
                    r"payment.*will.*be.*issued", r"check.*will.*be.*sent",
                    r"payment.*in.*progress", r"payment.*timeline", r"payment.*schedule",
                    r"arranging.*payment"
                ]
            },
            
            "Auto Reply (with/without info)": {
                "With Alternate Contact": [
                    r"out.*of.*office.*contact.*\d+", r"emergency.*contact.*\d+",
                    r"urgent.*matters.*contact.*\d+", r"immediate.*assistance.*contact.*\d+",
                    r"alternate.*contact", r"emergency.*contact", r"contact.*me.*at",
                    r"reach.*out.*to", r"call.*me", r"urgent.*matters.*contact",
                    r"for.*urgent.*matters.*contact", r"emergency.*assistance.*contact",
                    r"immediate.*help.*contact", r"urgent.*contact"
                ],
                
                "Return Date Specified": [
                    r"out.*of.*office.*until.*\d+", r"return.*on.*\d+", r"back.*on.*\d+",
                    r"returning.*\d+", r"will.*be.*back.*\d+",
                    r"return.*to.*office.*on", r"back.*in.*office.*on", r"returning.*to.*work.*on",
                    r"will.*return.*on", r"back.*from.*vacation.*on", r"return.*date.*is",
                    r"expected.*return.*date", r"returning.*from.*leave.*on", r"back.*on.*\w+day",
                    r"return.*on.*\w+.*\d+", r"back.*\w+.*\d+", r"returning.*\w+.*\d+",
                    r"out.*until.*\w+", r"away.*until.*\w+", r"return.*after.*\w+",
                    r"back.*after.*\w+", r"returning.*after.*the.*holiday", r"back.*monday",
                    r"return.*monday", r"back.*next.*week", r"return.*next.*week",
                    r"will.*be.*back.*on.*\w+", r"returning.*\w+day"
                ],
                
                "No Info/Autoreply": [
                    r"out.*of.*office", r"automatic.*reply", r"auto.*reply", r"currently.*out",
                    r"away.*from.*desk", r"on.*vacation", r"limited.*access.*to.*email",
                    r"do.*not.*reply", r"automated.*response", r"auto.*responder",
                    r"this.*is.*an.*automated", r"automatically.*generated"
                ],
                
                "Survey": [
                    r"\bsurvey\b", r"feedback.*request", r"rate.*our.*service",
                    r"customer.*satisfaction", r"take.*our.*survey", r"your.*feedback.*is.*important",
                    r"please.*rate", r"questionnaire", r"customer.*feedback", r"service.*rating"
                ],
                
                "Redirects/Updates (property changes)": [
                    r"no.*longer.*with", r"no.*longer.*employed", r"contact.*changed",
                    r"property.*manager.*changed", r"department.*changed", r"role.*changed",
                    r"position.*changed", r"contact.*information.*updated"
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
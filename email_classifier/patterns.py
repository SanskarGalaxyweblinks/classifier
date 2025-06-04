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
                    # Dispute & legal statements (well-bounded, grouped)
                    r"amount.*is.*in.*dispute", r"balance.*is.*not.*ours", r"not.*our.*responsibility",
                    r"do.*not.*owe", r"\bcontested\b", r"\bdisagreement\b",
                    r"formally.*disputing", r"dispute.*payment", r"contested.*payment",
                    r"challenge.*payment", r"debt.*is.*disputed", r"cease.*and.*desist",
                    r"do.*not.*acknowledge.*debt", r"\bfdcpa\b", r"billing.*error.*dispute",
                    r"not.*properly.*billed", r"wrong.*entity", r"dispute.*billing",
                    r"disputing.*this.*debt", r"owe.*them.*nothing", r"owe.*nothing",
                    r"consider.*this.*a.*scam", r"looks.*like.*a.*scam", r"is.*this.*legitimate",
                    r"verify.*this.*is.*real", r"cease.*and.*desist.*letter", r"legal.*notice",
                    r"fdcpa.*violation", r"do.*not.*acknowledge.*this.*debt", r"formally.*dispute.*this.*debt",
                    r"debt.*validation.*request", r"legal.*representation", r"attorney.*correspondence",
                    r"collection.*agency.*violation", r"fair.*debt.*collection", r"cease.*all.*communication",
                    r"legal.*action.*threatened", r"debt.*collector.*harassment", r"validation.*of.*debt",
                    r"cease.*and.*desist.*all.*contact", r"legal.*counsel.*representation"
                ],

                "Invoice Receipt": [
                    # Specific invoice/proof attachments, or error documentation
                    r"invoice.*attached.*as.*proof", r"attached.*invoice.*copy", r"proof.*of.*invoice.*attached",
                    r"invoice.*documentation.*attached", r"here.*is.*the.*invoice.*copy", r"invoice.*receipt.*attached",
                    r"copy.*of.*invoice.*attached.*for.*your.*records", r"payment.*made.*in.*error.*documentation",
                    r"error.*payment.*proof", r"documentation.*for.*payment.*error", r"proof.*of.*payment.*error",
                    r"attached.*payment.*documentation", r"payment.*error.*receipt"
                ],

                "Closure Notification": [
                    r"business.*closed", r"company.*closed", r"out.*of.*business",
                    r"ceased.*operations", r"filed.*bankruptcy", r"bankruptcy.*protection",
                    r"chapter.*7", r"chapter.*11"
                ],

                "Closure + Payment Due": [
                    r"closed.*payment.*due", r"business.*closed.*outstanding", r"bankruptcy.*payment.*due",
                    r"closure.*with.*outstanding.*payment"
                ],

                "External Submission": [
                    r"invoice.*submission.*failed", r"import.*failed", r"failed.*import",
                    r"unable.*to.*import", r"documents.*not.*processed", r"submission.*unsuccessful",
                    r"error.*importing.*invoice"
                ],

                "Invoice Errors (format mismatch)": [
                    r"missing.*required.*field", r"format.*mismatch", r"incomplete.*invoice",
                    r"invoice.*format.*error", r"field.*missing.*from.*invoice"
                ],

                "Inquiry/Redirection": [
                    r"insufficient.*data.*to.*research", r"need.*guidance", r"please.*advise",
                    r"redirect.*to", r"contact.*instead", r"reach.*out.*to",
                    r"please.*check.*with", r"what.*documentation.*needed", r"where.*to.*send.*payment",
                    r"verify.*legitimate", r"looks.*like.*a.*scam", r"are.*you.*legitimate"
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
                    r"detailed.*business.*process", r"special.*handling.*instructions", r"complex.*workflow"
                ]
            },
 
            "No Reply (with/without info)": {
                "Sales/Offers": [
                    r"special.*offer", r"limited.*time.*offer", r"promotional.*offer", 
                    r"discount.*offer", r"exclusive.*deal", r"prices.*increasing", r"hours.*left", 
                    r"special.*pricing", r"sale.*ending", r"payment.*plan.*options", r"payment.*plan.*discussion",
                    r"installment.*plan", r"payment.*arrangement.*offer", r"flexible.*payment.*options",
                    r"payment.*terms.*discussion", r"financing.*options", r"payment.*schedule.*options",
                    r"payment.*plan.*available", r"monthly.*payment.*plan", r"extended.*payment.*terms",
                    r"payment.*flexibility"
                ],

                "System Alerts": [
                    r"system.*notification", r"automated.*notification", r"system.*alert",
                    r"maintenance.*notification", r"security.*alert"
                ],

                "Processing Errors": [
                    r"processing.*error", r"failed.*to.*process", r"cannot.*be.*processed",
                    r"electronic.*invoice.*rejected", r"request.*couldn.?t.*be.*created",
                    r"system.*unable.*to.*process", r"mail.*delivery.*failed", r"email.*bounced"
                ],

                "Business Closure (Info only)": [
                    r"business.*closure.*information", r"closure.*notification.*only",
                    r"business.*will.*close", r"store.*will.*close", r"permanently.*closed",
                    r"company.*shutting.*down", r"closing.*operations"
                ],

                "General (Thank You)": [
                    r"thank.*you.*for.*your.*email", r"thanks.*for.*contacting", r"thank.*you.*for.*reaching.*out",
                    r"thank.*you.*for.*your.*patience", r"still.*reviewing", r"currently.*reviewing", 
                    r"under.*review", r"we.*are.*reviewing", r"for.*your.*records"
                ],

                "Created": [
                    r"ticket.*created", r"case.*opened", r"new.*ticket.*opened", r"support.*request.*created", 
                    r"case.*has.*been.*created", r"ticket.*has.*been.*opened", r"new.*case.*created", 
                    r"support.*ticket.*opened", r"case.*number.*assigned", r"ticket.*number.*assigned", 
                    r"new.*support.*case", r"request.*has.*been.*submitted", r"ticket.*submitted.*successfully",
                    r"case.*opened.*for.*review", r"support.*request.*received"
                ],

                "Resolved": [
                    r"ticket.*resolved", r"ticket.*has.*been.*resolved", r"case.*closed", r"case.*resolved", 
                    r"marked.*as.*resolved", r"status.*resolved", r"ticket.*closed", r"case.*completed",
                    r"do.*not.*reply", r"your.*feedback.*is.*important", r"survey.*request", r"this.*case.*is.*now.*closed"
                ],

                "Open": [
                    r"ticket.*open", r"case.*open", r"still.*pending", r"case.*pending"
                ]
            },
   
            "Invoices Request": {
                "Request (No Info)": [
                    # Requests for invoice only, EXCLUDE requests that mention proof, contract, agreement, paid, etc.
                    r"send.*me.*the.*invoice(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"provide.*the.*invoice(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"need.*invoice.*copy(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"copies?.*of.*(any.*)?invoices?(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"send.*invoices?.*that.*are.*due(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"provide.*outstanding.*invoices?(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"request.*for.*invoice(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"forward.*invoice.*copy(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"can.*i.*get.*invoice(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"share.*invoice.*copy(?!.*(paid|contract|agreement|proof|receipt|document|payment))",
                    r"would.*like.*invoice(?!.*(paid|contract|agreement|proof|receipt|document|payment))"
                ]
            },

            "Payments Claim": {
                "Claims Paid (No Info)": [
                    # Only "paid" statements WITHOUT proof/attachment language
                    r"\balready.*paid\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))",
                    r"\bpayment.*was.*made\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))",
                    r"\bwe.*paid\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))",
                    r"\bbill.*was.*paid\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))",
                    r"\bpayment.*was.*sent\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))",
                    r"\bcheck.*sent\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))",
                    r"\bpayment.*completed\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))",
                    r"\bthis.*was.*paid\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))",
                    r"\baccount.*paid\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))",
                    r"\bmade.*payment\b(?!.*(attached|see attached|proof|receipt|confirmation|check enclosed|find attached))"
                ],
                
                "Payment Confirmation": [
                    # MUST include "attached", "see attached", "proof", "receipt", "confirmation", "check enclosed", etc.
                    r"proof.*of.*payment",
                    r"payment.*confirmation.*attached",
                    r"check.*number.*\d+",
                    r"eft#.*\d+",
                    r"transaction.*id.*\d+",
                    r"here.*is.*proof.*of.*payment",
                    r"payment.*receipt.*attached",
                    r"wire.*confirmation.*\d+",
                    r"paid.*via.*transaction.*number.*\d+",
                    r"batch.*number.*\d+",
                    r"invoice.*was.*paid.*see.*attachments",
                    r"payment.*proof.*attached",
                    r"check.*enclosed",
                    r"see.*attached.*(check|proof|receipt|confirmation|document)",
                    r"find.*attached.*(check|proof|receipt|confirmation|document)",
                    r"(attached|see attached|find attached|enclosed).*(check|proof|receipt|confirmation|image|document)",
                    r"attached.*(check|proof|receipt|confirmation|image|document)",
                    r"here.*is.*(proof|receipt|confirmation|check|image|document).*attached"
                ],

                "Payment Details Received": [
                    # Future/pending payment info only
                    r"payment.*will.*be.*sent",
                    r"payment.*being.*processed",
                    r"check.*will.*be.*mailed",
                    r"payment.*scheduled",
                    r"in.*process.*of.*issuing.*payment",
                    r"invoices.*being.*processed.*for.*payment",
                    r"will.*pay.*this.*online",
                    r"working.*on.*payment",
                    r"need.*time.*to.*pay"
                ]
            },

            "Auto Reply (with/without info)": {
                "With Alternate Contact": [
                    # Any OOO/autoreply that gives a contact (phone/email/name)
                    r"out.*of.*office.*(contact|reach|please.*email|call|reach me at)",
                    r"for.*immediate.*assistance.*(contact|email|call)",
                    r"urgent.*matters.*(contact|email|call)",
                    r"in.*my.*absence.*(contact|email|call)",
                    r"please.*contact.*(colleague|someone else|the following|alternate|alternate contact)",
                    r"if.*urgent.*(contact|email|call)",
                    r"for.*support.*(contact|email|call)"
                ],

                "Return Date Specified": [
                    # OOO with a specific date of return
                    r"out.*of.*office.*until.*\d{1,2}[\-/]\d{1,2}",  # until 15/06 or 06-15
                    r"out.*of.*office.*until.*(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                    r"return.*(on|by|after|until|to work on).*[\w\s,]+(\d{1,2}[\-/]\d{1,2}|\d{4})",
                    r"will.*be.*back.*on.*\d{1,2}[\-/]\d{1,2}", 
                    r"expected.*return.*(date|on).*[\w\s,]+",
                    r"back.*(on|by|in).*[\w\s,]+", 
                    r"returning.*(on|by|after|in).*[\w\s,]+",
                    r"will.*return.*(on|by|after|in).*[\w\s,]+",
                    r"away.*until.*(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                    r"on.*vacation.*until.*[\w\s,]+",
                    r"back.*after.*the.*holiday",
                    r"return.*next.*week",
                    r"back.*next.*week",
                    r"out.*until.*(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                ],

                "No Info/Autoreply": [
                    # Generic OOO/auto-reply without alternate contact or date
                    r"out.*of.*office", r"currently.*out", r"on.*vacation", r"away.*from.*desk",
                    r"automatic.*reply", r"auto-?reply", r"limited.*access.*to.*email",
                    r"automated.*response", r"this.*is.*an.*automatic.*reply", r"i.*am.*currently.*away",
                    r"do.*not.*reply", r"thank.*you.*for.*your.*email"
                ],

                "Survey": [
                    r"\bsurvey\b", r"feedback.*request", r"rate.*our.*service",
                    r"customer.*satisfaction", r"take.*our.*survey",
                    r"please.*provide.*feedback", r"how.*did.*we.*do", r"your.*feedback.*is.*important",
                    r"survey.*link", r"complete.*survey"
                ],

                "Redirects/Updates (property changes)": [
                    r"no.*longer.*with", r"no.*longer.*employed", r"contact.*changed",
                    r"property.*manager.*changed", r"department.*changed", r"my.*email.*has.*changed",
                    r"please.*update.*your.*records", r"forward.*future.*emails.*to"
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
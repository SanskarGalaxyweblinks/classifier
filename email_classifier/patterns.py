"""
Simplified Pattern Matcher - Core Business Patterns Only
Focus on essential patterns for maximum accuracy with minimal complexity
"""

from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Configuration
CONFIDENCE_BASE = 0.75
CONFIDENCE_BOOST_PER_MATCH = 0.08
MAX_CONFIDENCE = 0.95
MIN_CONFIDENCE = 0.30

class PatternMatcher:
    """
    Simplified pattern matcher with core business patterns only.
    Reduced complexity for better performance and maintainability.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()
        self._compile_patterns()
        self._initialize_mappings()
        self.logger.info("✅ Simplified Pattern Matcher initialized")

    def _initialize_patterns(self) -> None:
        """Initialize essential patterns with proper word boundaries - core business cases only."""
        
        self.patterns = {
            "Manual Review": {
                "Partial/Disputed Payment": [
                    # Core dispute patterns with word boundaries
                    r"\bdispute\b",
                    r"\bdisputing\b",
                    r"\bowe\b.*\bnothing\b",
                    r"\bowe\b.*\bthem\b.*\bnothing\b",
                    r"\bcontested\b",
                    r"\bscam\b",
                    r"\bfdcpa\b",
                    r"\bcease\b.*\band\b.*\bdesist\b",
                    r"\bdo\b.*\bnot\b.*\backnowledge\b",
                    r"\bdisputing\b.*\bwith\b.*\binsurance\b",
                    r"\bbilling\b.*\bis\b.*\bincorrect\b",
                    r"\bnot\b.*\bour\b.*\bresponsibility\b"
                ],

                "Invoice Receipt": [
                    # Providing invoice proof with word boundaries
                    r"\binvoice\b.*\battached\b",
                    r"\bproof\b.*\bof\b.*\binvoice\b",
                    r"\binvoice\b.*\bcopy\b.*\battached\b",
                    r"\binvoice\b.*\breceipt\b.*\battached\b"
                ],

                "Closure Notification": [
                    # Business closure with word boundaries
                    r"\bbusiness\b.*\bclosed\b",
                    r"\bfiled\b.*\bbankruptcy\b",
                    r"\bout\b.*\bof\b.*\bbusiness\b",
                    r"\bceased\b.*\boperations\b"
                ],

                "External Submission": [
                    # Submission failures with word boundaries
                    r"\bsubmission\b.*\bfailed\b",
                    r"\bimport\b.*\bfailed\b",
                    r"\bprocessing\b.*\bfailed\b",
                    r"\binvoice\b.*\bsubmission\b.*\bfailed\b"
                ],

                "Invoice Errors (format mismatch)": [
                    # Format errors with word boundaries
                    r"\bformat\b.*\berror\b",
                    r"\bmissing\b.*\bfield\b",
                    r"\binvalid\b.*\bformat\b",
                    r"\bformat\b.*\bmismatch\b"
                ],

                "Inquiry/Redirection": [
                    # Redirections and questions with word boundaries
                    r"\bplease\b.*\badvise\b",
                    r"\bneed\b.*\bguidance\b",
                    r"\bcontact\b.*\binstead\b",
                    r"\bwhat\b.*\bvendor\b",
                    r"\breached\b.*\bout\b.*\bto\b.*\bowner\b",
                    r"\bwhat\b.*\bis\b.*\bthe\b.*\bservicing\b.*\baddress\b"
                ],

                "Complex Queries": [
                    # Legal and complex matters with word boundaries
                    r"\bsettlement\b",
                    r"\battorney\b",
                    r"\blegal\b",
                    r"\bminimum\b.*\bsettlement\b.*\bamount\b",
                    r"\bcomplex\b.*\bbusiness\b.*\binstructions\b"
                ]
            },
    
            "No Reply (with/without info)": {
                "Sales/Offers": [
                    # Marketing content with word boundaries
                    r"\bspecial\b.*\boffer\b",
                    r"\blimited\b.*\btime\b",
                    r"\bpromotional\b",
                    r"\bdiscount\b",
                    r"\bsale\b.*\bending\b",
                    r"\bkiller\b.*\bsales\b.*\bsamples\b",
                    r"\bmake\b.*\bsamples\b.*\bthat\b.*\bsell\b",
                    r"\bbusiness\b.*\bguide\b"
                ],

                "System Alerts": [
                    # System notifications with word boundaries
                    r"\bsystem\b.*\bnotification\b",
                    r"\bpassword\b.*\bexpires\b",
                    r"\bmaintenance\b",
                    r"\bpassword\b.*\bfor\b.*\baccount\b.*\bexpires\b"
                ],

                "Processing Errors": [
                    # System errors with word boundaries
                    r"\bprocessing\b.*\berror\b",
                    r"\bfailed\b.*\bto\b.*\bprocess\b",
                    r"\bdelivery\b.*\bfailed\b",
                    r"\binvoice\b.*\brejected\b",
                    r"\binvoices\b.*\bwill\b.*\bnot\b.*\bbe\b.*\bprocessed\b"
                ],

                "General (Thank You)": [
                    # Acknowledgments with word boundaries
                    r"\bthank\b.*\byou\b",
                    r"\backnowledgment\b",
                    r"\breceived\b",
                    r"\bthank\b.*\byou\b.*\bfor\b.*\breaching\b.*\bout\b",
                    r"\bclosing\b.*\bthis\b.*\brequest\b",
                    r"\bno\b.*\blonger\b.*\bmanage\b"
                ],

                "Created": [
                    # Ticket creation with word boundaries
                    r"\bticket\b.*\bcreated\b",
                    r"\bcase\b.*\bopened\b",
                    r"\brequest\b.*\bcreated\b",
                    r"\bquery\b.*\breceived\b.*\bticket\b"
                ],

                "Resolved": [
                    # Case resolution with word boundaries
                    r"\bresolved\b",
                    r"\bclosed\b",
                    r"\bcompleted\b",
                    r"\bcase\b.*\bhas\b.*\bbeen\b.*\bresolved\b",
                    r"\bthis\b.*\bhas\b.*\bbeen\b.*\bresolved\b",
                    r"\baccount\b.*\bwas\b.*\bpaid\b.*\band\b.*\bclosed\b"
                ],

                "Open": [
                    # Open status with word boundaries
                    r"\bpending\b",
                    r"\bin\b.*\bprogress\b",
                    r"\bopen\b"
                ]
            },
    
            "Invoices Request": {
                "Request (No Info)": [
                    # Core invoice requests with word boundaries
                    r"\bprovide\b.*\binvoices?\b.*\bcopies\b",
                    r"\bsend\b.*\bme\b.*\bthe\b.*\binvoices?\b",
                    r"\bneed\b.*\binvoices?\b.*\bcopy\b",
                    r"\bshare\b.*\binvoices?\b",
                    r"\bforward\b.*\binvoices?\b",
                    r"\bprovide\b.*\boutstanding\b.*\binvoices?\b",
                    r"\bshare\b.*\bthe\b.*\bpast\b.*\bdue\b.*\binvoice\b.*\bcopy\b",
                    r"\bsend\b.*\bme\b.*\bthe\b.*\brelevant\b.*\binvoices\b",
                    r"\bsend\b.*\bcopies\b.*\bof\b.*\boutstanding\b.*\binvoices\b",
                    r"\bcan\b.*\byou\b.*\bsed\b.*\bme\b.*\bthe\b.*\binvoices\b",
                    r"\bneed\b.*\ba\b.*\bbreakdown\b.*\bby\b.*\binvoice\b"
                ]
            },

            "Payments Claim": {
                "Claims Paid (No Info)": [
                    # Payment claims without proof with word boundaries
                    r"\balready\b.*\bpaid\b",
                    r"\bpayment\b.*\bwas\b.*\bmade\b",
                    r"\bwe\b.*\bpaid\b",
                    r"\bthis\b.*\bwas\b.*\bpaid\b",
                    r"\bmade\b.*\bthe\b.*\bpayment\b",
                    r"\baccount\b.*\bwas\b.*\bpaid\b",
                    r"\bthis\b.*\baccount\b.*\bwas\b.*\bpaid\b",
                    r"\bhas\b.*\bbeen\b.*\bpaid\b.*\bvia\b.*\bcredit\b.*\bcard\b",
                    r"\bpaid\b.*\bfor\b.*\beverything\b.*\bup\b.*\bfront\b",
                    r"\bhas\b.*\bbeen\b.*\bpaid\b.*\bdirectly\b"
                ],
                
                "Payment Confirmation": [
                    # Payment with proof with word boundaries
                    r"\bproof\b.*\bof\b.*\bpayment\b",
                    r"\bpayment\b.*\battached\b",
                    r"\breceipt\b.*\battached\b",
                    r"\bcheck\b.*\bnumber\b",
                    r"\btransaction\b.*\bid\b",
                    r"\bpaid\b.*\bsee\b.*\battachments\b",
                    r"\bpayment\b.*\breceipt\b.*\bis\b.*\battached\b",
                    r"\bsent\b.*\bproof\b.*\bseveral\b.*\btimes\b",
                    r"\blast\b.*\b4\b.*\bdigits\b.*\bof\b.*\bach\b.*\bpayment\b.*\bid\b",
                    r"\bacopy\b.*\bof\b.*\bthe\b.*\bpayment\b.*\breceipt\b.*\bis\b.*\battached\b"
                ],

                "Payment Details Received": [
                    # Future/pending payments with word boundaries
                    r"\bpayment\b.*\bwill\b.*\bbe\b.*\bsent\b",
                    r"\bpayment\b.*\bbeing\b.*\bprocessed\b",
                    r"\bworking\b.*\bon\b.*\bpayment\b",
                    r"\bpayment\b.*\bis\b.*\bawaiting\b",
                    r"\bpayment\b.*\bis\b.*\bawaiting\b.*\binformation\b"
                ]
            },

            "Auto Reply (with/without info)": {
                "With Alternate Contact": [
                    # OOO with contact info with word boundaries
                    r"\bout\b.*\bof\b.*\boffice\b.*\bcontact\b",
                    r"\balternate\b.*\bcontact\b",
                    r"\bemergency\b.*\bcontact\b",
                    r"\bcontact\b.*\bme\b.*\bat\b"
                ],

                "Return Date Specified": [
                    # OOO with return date with word boundaries
                    r"\breturn\b.*\bon\b",
                    r"\bback\b.*\bon\b",
                    r"\bout\b.*\buntil\b",
                    r"\breturning\b.*\bon\b",
                    r"\bwill\b.*\bbe\b.*\bout\b.*\bof\b.*\bthe\b.*\boffice\b.*\bmonday\b",
                    r"\brespond\b.*\bto\b.*\byour\b.*\bemails\b.*\bupon\b.*\bmy\b.*\breturn\b"
                ],

                "No Info/Autoreply": [
                    # Generic auto-replies with word boundaries
                    r"\bout\b.*\bof\b.*\boffice\b",
                    r"\bautomatic\b.*\breply\b",
                    r"\bauto-?reply\b",
                    r"\baway\b.*\bfrom\b.*\bdesk\b"
                ],

                "Survey": [
                    # Surveys and feedback with word boundaries
                    r"\bsurvey\b",
                    r"\bfeedback\b",
                    r"\brate\b.*\bour\b.*\bservice\b"
                ],

                "Redirects/Updates (property changes)": [
                    # Contact changes with word boundaries
                    r"\bno\b.*\blonger\b.*\bemployed\b",
                    r"\bcontact\b.*\bchanged\b",
                    r"\bquit\b.*\bcontacting\b",
                    r"\bproperty\b.*\bmanager\b.*\bchanged\b",
                    r"\bplease\b.*\bquit\b.*\bcontacting\b.*\bme\b",
                    r"\bdo\b.*\bnot\b.*\bcontact\b.*\bme\b.*\bfurther\b",
                    r"\brefrain\b.*\bfrom\b.*\bcontacting\b"
                ]
            }
        }

    def _compile_patterns(self) -> None:
        """Compile all patterns for optimal performance."""
        self.compiled_patterns = {}
        
        for main_cat, subcats in self.patterns.items():
            self.compiled_patterns[main_cat] = {}
            for subcat, patterns in subcats.items():
                self.compiled_patterns[main_cat][subcat] = [
                    re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                    for pattern in patterns
                ]
        
        pattern_count = sum(len(subcats) for subcats in self.compiled_patterns.values())
        self.logger.info(f"✅ Compiled {pattern_count} simplified pattern groups")

    def _initialize_mappings(self) -> None:
        """Initialize category mappings."""
        
        self.main_categories = {
            "Manual Review": "Manual Review",
            "No Reply (with/without info)": "No Reply (with/without info)",
            "Invoices Request": "Invoices Request", 
            "Payments Claim": "Payments Claim",
            "Auto Reply (with/without info)": "Auto Reply (with/without info)"
        }
        
        # All sublabel mappings
        self.sublabels = {
            # Manual Review
            "Partial/Disputed Payment": "Partial/Disputed Payment",
            "Invoice Receipt": "Invoice Receipt", 
            "Closure Notification": "Closure Notification",
            "External Submission": "External Submission",
            "Invoice Errors (format mismatch)": "Invoice Errors (format mismatch)",
            "Inquiry/Redirection": "Inquiry/Redirection",
            "Complex Queries": "Complex Queries",
            
            # No Reply
            "Sales/Offers": "Sales/Offers",
            "System Alerts": "System Alerts",
            "Processing Errors": "Processing Errors", 
            "General (Thank You)": "General (Thank You)",
            "Created": "Created",
            "Resolved": "Resolved",
            "Open": "Open",
            
            # Invoice Request
            "Request (No Info)": "Request (No Info)",
            
            # Payments Claim
            "Claims Paid (No Info)": "Claims Paid (No Info)",
            "Payment Details Received": "Payment Details Received",
            "Payment Confirmation": "Payment Confirmation",
            
            # Auto Reply
            "With Alternate Contact": "With Alternate Contact",
            "No Info/Autoreply": "No Info/Autoreply",
            "Return Date Specified": "Return Date Specified",
            "Survey": "Survey",
            "Redirects/Updates (property changes)": "Redirects/Updates (property changes)"
        }

    def match_text(self, text: str, exclude_external_proof: bool = False) -> Tuple[Optional[str], Optional[str], float, List[str]]:
        """Main pattern matching with simplified conflict resolution."""
        if not text or len(text.strip()) < 5:
            return None, None, 0.0, []
        
        text_lower = text.lower().strip()
        all_matches = []
        
        # Collect pattern matches
        for main_cat, subcats in self.compiled_patterns.items():
            for subcat, patterns in subcats.items():
                matches = 0
                matched_patterns = []
                
                for pattern in patterns:
                    if pattern.search(text_lower):
                        matches += 1
                        matched_patterns.append(pattern.pattern)
                
                if matches > 0:
                    confidence = min(CONFIDENCE_BASE + (matches * CONFIDENCE_BOOST_PER_MATCH), MAX_CONFIDENCE)
                    all_matches.append({
                        'main_cat': main_cat,
                        'subcat': subcat,
                        'confidence': confidence,
                        'match_count': matches,
                        'patterns': matched_patterns
                    })
        
        if not all_matches:
            return None, None, 0.0, []
        
        # Simplified conflict resolution
        best_match = self._resolve_conflicts(all_matches, text_lower)
        
        if best_match:
            return (
                self.main_categories[best_match['main_cat']],
                self.sublabels[best_match['subcat']],
                best_match['confidence'],
                best_match['patterns'][:3]
            )
        
        return None, None, 0.0, []

    def _resolve_conflicts(self, matches: List[Dict], text: str) -> Optional[Dict]:
        """Simplified conflict resolution with core business logic."""
        if not matches:
            return None
        
        if len(matches) == 1:
            return matches[0]
        
        # Priority resolution rules
        
        # 1. Dispute patterns override everything
        dispute_match = next((m for m in matches if m['subcat'] == 'Partial/Disputed Payment'), None)
        if dispute_match:
            return dispute_match
        
        # 2. Payment with proof vs without proof
        payment_conf = next((m for m in matches if m['subcat'] == 'Payment Confirmation'), None)
        payment_claim = next((m for m in matches if m['subcat'] == 'Claims Paid (No Info)'), None)
        
        if payment_conf and payment_claim:
            # Check for proof indicators
            proof_indicators = ['attached', 'proof', 'receipt', 'number', 'id']
            has_proof = any(indicator in text for indicator in proof_indicators)
            return payment_conf if has_proof else payment_claim
        
        # 3. Invoice request vs payment claim
        invoice_req = next((m for m in matches if m['subcat'] == 'Request (No Info)'), None)
        if invoice_req and payment_claim:
            # Favor invoice request if asking for invoices
            if any(phrase in text for phrase in ['provide invoice', 'send invoice', 'need invoice']):
                return invoice_req
            return payment_claim
        
        # 4. Manual Review takes priority over Auto Reply for business content
        manual = next((m for m in matches if m['main_cat'] == 'Manual Review'), None)
        auto_reply = next((m for m in matches if m['main_cat'] == 'Auto Reply (with/without info)'), None)
        
        if manual and auto_reply:
            business_terms = ['payment', 'invoice', 'dispute', 'collection']
            business_count = sum(1 for term in business_terms if term in text)
            return manual if business_count >= 2 else auto_reply
        
        # 5. Highest confidence wins
        return max(matches, key=lambda x: (x['confidence'], x['match_count']))

    def get_pattern_stats(self) -> Dict[str, int]:
        """Get simplified pattern statistics."""
        stats = {}
        for main_cat, subcats in self.patterns.items():
            total = sum(len(patterns) for patterns in subcats.values())
            stats[main_cat] = total
        
        stats['total_patterns'] = sum(stats.values())
        return stats
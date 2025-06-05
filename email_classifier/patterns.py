"""
Strong Pattern Matcher - Core Business Patterns Only
Removed General (Thank You) and enhanced pattern accuracy
"""

from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Configuration
CONFIDENCE_BASE = 0.80
CONFIDENCE_BOOST_PER_MATCH = 0.10
MAX_CONFIDENCE = 0.95
MIN_CONFIDENCE = 0.40

class PatternMatcher:
    """
    Strong pattern matcher with precise business patterns.
    Enhanced accuracy and reduced misclassification.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()
        self._compile_patterns()
        self._initialize_mappings()
        self.logger.info("✅ Strong Pattern Matcher initialized")

    def _initialize_patterns(self) -> None:
        """Initialize enhanced patterns with minimal conflicts and proper OOO detection."""
        
        self.patterns = {
            "Manual Review": {
                "Partial/Disputed Payment": [
                    # Strong dispute patterns - SPECIFIC to avoid conflicts
                    r"\bformally\s+disputing\b", r"\bdisputing\s+with\s+insurance\b",
                    r"\bmistake\s+was\s+theirs?\b", r"\bsettlement\s+.*\$\d+\b", r"\bsettled?\s+.*\$\d+\b",
                    r"\bdispute\s+this\s+debt\b", r"\bowe\s+them?\s+nothing\b", r"\bconsider\s+this\s+a?\s+scam\b",
                    r"\bdo\s+not\s+acknowledge\b", r"\bbilling\s+is\s+incorrect\b", r"\bnot\s+our\s+responsibility\b",
                    r"\bcease\s+and\s+desist\b", r"\bfdcpa\s+violation\b", r"\bdebt\s+validation\b",
                    r"\bcontested\s+payment\b", r"\brefuse\s+to\s+pay\b", r"\bunauthorized\s+charge\b",
                    r"\bfraudulent\s+charge\b", r"\bincorrect\s+billing\b", r"\bincorrect\s+amount\b",
                    r"\bincorrect\s+payment\b", r"\bincorrect\s+invoice\b", r"\bincorrect\s+statement\b",
                    
                    # ENHANCED: Add specific dispute patterns (no conflicts)
                    r"\bwe\s+do\s+not\s+owe\s+.*amount\b",  # More specific than just "do not owe"
                    r"\bare\s+not\s+responsible\s+for\s+this\b",  # More specific
                    r"\bunaware\s+of\s+this\s+charge\s+and\s+.*researching\b",  # Combined pattern
                    r"\bno\s+record\s+of\s+this\s+.*charge\b",  # More specific
                    r"\bnever\s+received\s+.*invoice\b",  # More specific
                    r"\bwe\s+don'?t\s+owe\s+.*money\b"  # More specific
                ],

                "Invoice Receipt": [
                    # Providing invoice proof
                    r"\binvoice\s+receipt\s+attached\b",
                    r"\bproof\s+of\s+invoice\s+attached\b",
                    r"\binvoice\s+copy\s+attached\b",
                    r"\binvoice\s+documentation\s+attached\b",
                    r"\bhere\s+is\s+the\s+invoice\s+copy\b",
                    r"\berror\s+payment\s+proof\b",
                    r"\bpayment\s+error\s+documentation\b"
                ],

                "Closure Notification": [
                    r"\bbusiness\s+closed\b", r"\bcompany\s+closed\b", r"\bfiled\s+bankruptcy\b",
                    r"\bout\s+of\s+business\b", r"\bceased\s+operations\b", r"\bpermanently\s+closed\b",
                    r"\bchapter\s+7\b", r"\bchapter\s+11\b"
                ],

                "Closure + Payment Due": [
                    r"\bclosed\s+.*outstanding\s+payment\b", r"\bbankruptcy\s+.*payment\s+due\b",
                    r"\bclosure\s+.*payment\s+owed\b"
                ],

                "External Submission": [
                    r"\binvoice\s+submission\s+failed\b", r"\bimport\s+failed\b", r"\bprocessing\s+failed\b",
                    r"\bunable\s+to\s+import\s+invoice\b", r"\bsubmission\s+unsuccessful\b",
                    r"\bdocuments\s+not\s+processed\b"
                ],

                "Invoice Errors (format mismatch)": [
                    r"\bmissing\s+required\s+field\b", r"\bformat\s+mismatch\b", r"\binvalid\s+invoice\s+format\b",
                    r"\bincomplete\s+invoice\b", r"\bformat\s+requirements\s+not\s+met\b",
                    r"\bmandatory\s+fields?\s+missing\b"
                ],

                "Inquiry/Redirection": [
                    r"\bplease\s+advise\b", r"\bneed\s+guidance\b", r"\bcontact\s+.*instead\b",
                    r"\bwhat\s+vendor\b", r"\bwhere\s+to\s+send\s+payment\b",
                    r"\bwhat\s+documentation\s+needed\b", r"\bverify\s+legitimate\b", r"\bguidance\s+required\b"
                ],

                "Complex Queries": [
                    r"\bsettlement\s+arrangement\b", r"\blegal\s+settlement\b", r"\battorney\s+settlement\b",
                    r"\bcomplex\s+business\s+instructions\b", r"\brouting\s+instructions\b",
                    r"\bmulti\s+step\s+process\b", r"\blegal\s+proceedings\b", r"\bmediation\s+settlement\b"
                ]
            },
    
            "No Reply (with/without info)": {
                "Sales/Offers": [
                    r"\bspecial\s+offer\b", r"\blimited\s+time\s+offer\b", r"\bpromotional\s+offer\b",
                    r"\bdiscount\s+offer\b", r"\bexclusive\s+deal\b", r"\bprices?\s+increasing\b",
                    r"\bsale\s+ending\b", r"\bpayment\s+plan\s+options\b", r"\binstallment\s+plan\b",
                    r"\bfinancing\s+options\b"
                ],

                "System Alerts": [
                    r"\bsystem\s+notification\b", r"\bpassword\s+.*expires\b", r"\bmaintenance\s+notification\b",
                    r"\bsecurity\s+alert\b", r"\bserver\s+maintenance\b"
                ],

                "Processing Errors": [
                    r"\bprocessing\s+error\b", r"\bfailed\s+to\s+process\b", r"\bdelivery\s+failed\b",
                    r"\belectronic\s+invoice\s+rejected\b", r"\bmail\s+delivery\s+failed\b",
                    r"\bsystem\s+unable\s+to\s+process\b", r"\bcannot\s+be\s+processed\b"
                ],

                "Business Closure (Info only)": [
                    r"\bbusiness\s+closure\s+information\b", r"\bclosure\s+notification\s+only\b",
                    r"\binformational\s+closure\b", r"\bstore\s+closing\s+notice\b"
                ],

                "Created": [
                    r"\bticket\s+created\b", r"\bcase\s+opened\b", r"\bnew\s+ticket\s+opened\b",
                    r"\bsupport\s+request\s+created\b", r"\bcase\s+number\s+assigned\b",
                    r"\bticket\s+submitted\s+successfully\b"
                ],

                "Resolved": [
                    r"\bticket\s+resolved\b", r"\bcase\s+resolved\b", r"\bcase\s+closed\b",
                    r"\bmarked\s+as\s+resolved\b", r"\bissue\s+resolved\b", r"\brequest\s+completed\b"
                ],

                "Open": [
                    r"\bticket\s+open\b", r"\bcase\s+pending\b", r"\bunder\s+investigation\b",
                    r"\bbeing\s+processed\b", r"\bin\s+progress\b"
                ]
            },
    
            "Invoices Request": {
                "Request (No Info)": [
                    # CONFLICT-FREE: More specific invoice request patterns
                    r"\bsend\s+me\s+the\s+invoices?\b",
                    r"\bprovide\s+.*invoices?\s+copies?\b",
                    r"\bneed\s+invoices?\s+copies?\b",
                    r"\bshare\s+invoices?\s+copies?\b",
                    r"\bforward\s+invoices?\s+copies?\b",
                    r"\bprovide\s+outstanding\s+invoices?\b",
                    r"\bcopies\s+of\s+.*invoices?\b",
                    r"\bneed\s+a\s+breakdown\s+by\s+invoice\b",
                    
                    # ENHANCED: Specific thread patterns (avoid conflicts with payments)
                    r"\bsend\s+a\s+copy\s+of\s+the\s+invoice\s+that\s+is\s+due\b",  # Very specific
                    r"\bprovide\s+an?\s+invoice\s+copy\s+in\s+pdf\s+format\b",  # Very specific
                    r"\brequest.*copies\s+of\s+these\s+invoices\b",  # Specific
                    r"\bcopies\s+of\s+these\s+invoices\s+as\s+we\s+do\s+not\s+have\b"  # Specific context
                ]
            },

            "Payments Claim": {
                "Claims Paid (No Info)": [
                    # CONFLICT-FREE: Specific past payment claims (avoid generic "paid")
                    r"\balready\s+paid\s+this\b",  # More specific
                    r"\bthis\s+was\s+paid\s+on\s+\d+\/\d+\/\d+\b",  # With date
                    r"\bwe\s+paid\s+this\s+.*balance\b",  # More specific
                    r"\baccount\s+was\s+paid\s+.*ago\b",  # More specific
                    r"\bhas\s+been\s+paid\s+to\s+\w+\b",  # More specific
                    r"\bcheck\s+was\s+sent\s+.*ago\b",  # More specific
                    r"\bpayment\s+completed\s+.*ago\b",  # More specific
                    r"\binvoice\s+settled\s+.*ago\b",  # More specific
                    
                    # ENHANCED: Specific thread payment claim patterns
                    r"\bpaid\s+this\s+outstanding\s+balance\s+to\s+\w+\b",  # Very specific
                    r"\bverify\s+.*this\s+has\s+been\s+paid\b",  # Verification request
                    r"\bplease\s+verify\s+.*paid\s+.*ago\b",  # Verification with time
                    r"\bconfirm\s+.*has\s+been\s+paid\s+to\b"  # Confirmation request
                ],
                
                "Payment Confirmation": [
                    # Keep these specific - no conflicts
                    r"\bproof\s+of\s+payment\s+attached\b", r"\bpayment\s+confirmation\s+attached\b",
                    r"\breceipt\s+attached\b", r"\bcheck\s+number\s+\d+\b", r"\btransaction\s+id\s+\w+\b",
                    r"\bach\s+payment\s+id\b", r"\blast\s+4\s+digits\b", r"\breceipt\s+is\s+attached\b",
                    r"\bpayment\s+id\s+are\s+\d+\b", r"\beft#\s+\w+\b", r"\bwire\s+confirmation\b",
                    r"\bbatch\s+number\b", r"\bpaid\s+see\s+attachments\b", r"\bhere\s+is\s+proof\s+of\s+payment\b"
                ],

                "Payment Details Received": [
                    # CONFLICT-FREE: Specific future payment patterns
                    r"\bpayment\s+will\s+be\s+sent\s+.*\b",  # More specific
                    r"\bpayment\s+being\s+processed\s+for\b",  # More specific
                    r"\bworking\s+on\s+payment\s+.*\b",  # More specific
                    r"\bpayment\s+scheduled\s+for\b",  # More specific
                    r"\bwill\s+pay\s+.*online\s+.*\b",  # More specific
                    r"\binvoices?\s+being\s+processed\s+for\s+payment\b",
                    
                    # ENHANCED: Specific future payment patterns (avoid conflicts)
                    r"\bi\s+will\s+pay\s+the\s+remainder\s+after\b",  # Very specific
                    r"\bcan\s+we\s+do\s+the\s+first\s+payment\s+.*monday\b",  # Very specific
                    r"\bissue\s+a\s+payment\s+plan\s+to\s+start\b",  # Very specific
                    r"\bhelp\s+me\s+for\s+payment\s+.*error\b",  # Very specific
                    r"\btried\s+to\s+pay\s+through\s+.*link\b",  # Very specific
                    r"\bpayment\s+error\s+.*information\b"  # Very specific
                ]
            },

            "Auto Reply (with/without info)": {
                "With Alternate Contact": [
                    # FIXED: Proper alternate contact patterns
                    r"\balternate\s+contact\b",
                    r"\bemergency\s+contact\b", 
                    r"\bcontact\s+me\s+at\s+\d+\b",  # With phone number
                    r"\bfor\s+urgent\s+matters\s+contact\b",
                    r"\bimmediate\s+assistance\s+contact\b",
                    r"\breach\s+me\s+at\s+\d+\b",  # With phone number
                    r"\bcall\s+me\s+at\s+\d+\b"  # With phone number
                ],

                "Return Date Specified": [
                    # FIXED: Proper return date patterns
                    r"\breturn\s+on\s+\w+day\b",  # return on Monday
                    r"\bback\s+on\s+\w+day\b",     # back on Friday
                    r"\breturning\s+on\s+\d+\/\d+\b",  # returning on 6/10
                    r"\bout\s+until\s+\d+\/\d+\b",     # out until 6/15
                    r"\baway\s+until\s+\w+day\b",      # away until Monday
                    r"\bexpected\s+return\s+date\s+is\s+\d+\b",
                    r"\bback\s+from\s+vacation\s+on\s+\d+\b",
                    r"\bwill\s+be\s+out\s+of\s+.*office\s+.*monday\b",  # Specific pattern
                    r"\breturn\s+.*monday\b",  # return Monday
                    r"\bback\s+.*monday\b"     # back Monday
                ],

                "No Info/Autoreply": [
                    # FIXED: Generic OOO without specific info
                    r"\bout\s+of\s+office\b",
                    r"\bautomatic\s+reply\b",
                    r"\bauto-?reply\b",
                    r"\baway\s+from\s+desk\b",
                    r"\bcurrently\s+out\b",
                    r"\blimited\s+access\s+to\s+email\b",
                    r"\bdo\s+not\s+reply\s+to\s+this\s+email\b",
                    r"\btemporarily\s+unavailable\b"
                ],

                "Survey": [
                    r"\bsurvey\b", r"\bfeedback\s+request\b", r"\brate\s+our\s+service\b",
                    r"\bcustomer\s+satisfaction\b", r"\btake\s+our\s+survey\b", r"\bservice\s+evaluation\b"
                ],

                "Redirects/Updates (property changes)": [
                    r"\bno\s+longer\s+employed\b", r"\bcontact\s+changed\b", r"\bproperty\s+manager\s+changed\b",
                    r"\bemail\s+address\s+changed\b", r"\bcontact\s+information\s+updated\b",
                    r"\bplease\s+quit\s+contacting\b", r"\bdo\s+not\s+contact\s+me\s+further\b"
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
        self.logger.info(f"✅ Compiled {pattern_count} strong pattern groups")

    def _initialize_mappings(self) -> None:
        """Initialize category mappings."""
        
        self.main_categories = {
            "Manual Review": "Manual Review",
            "No Reply (with/without info)": "No Reply (with/without info)",
            "Invoices Request": "Invoices Request", 
            "Payments Claim": "Payments Claim",
            "Auto Reply (with/without info)": "Auto Reply (with/without info)"
        }
        
        # All sublabel mappings (removed General Thank You)
        self.sublabels = {
            # Manual Review
            "Partial/Disputed Payment": "Partial/Disputed Payment",
            "Invoice Receipt": "Invoice Receipt", 
            "Closure Notification": "Closure Notification",
            "Closure + Payment Due": "Closure + Payment Due",
            "External Submission": "External Submission",
            "Invoice Errors (format mismatch)": "Invoice Errors (format mismatch)",
            "Inquiry/Redirection": "Inquiry/Redirection",
            "Complex Queries": "Complex Queries",
            
            # No Reply (removed General Thank You)
            "Sales/Offers": "Sales/Offers",
            "System Alerts": "System Alerts",
            "Processing Errors": "Processing Errors", 
            "Business Closure (Info only)": "Business Closure (Info only)",
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
        """Main pattern matching with enhanced conflict resolution."""
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
        
        # Enhanced conflict resolution
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
        """Enhanced conflict resolution with strong business logic."""
        if not matches:
            return None
        
        if len(matches) == 1:
            return matches[0]
        
        # Priority resolution rules - Enhanced
        
        # 1. Dispute patterns have highest priority
        dispute_match = next((m for m in matches if m['subcat'] == 'Partial/Disputed Payment'), None)
        if dispute_match:
            return dispute_match
        
        # 2. Payment proof vs claims - Enhanced detection
        payment_conf = next((m for m in matches if m['subcat'] == 'Payment Confirmation'), None)
        payment_claim = next((m for m in matches if m['subcat'] == 'Claims Paid (No Info)'), None)
        
        if payment_conf and payment_claim:
            # Strong proof indicators
            proof_indicators = [
                'attached', 'proof', 'receipt', 'number', 'id', 'confirmation',
                'transaction', 'check number', 'eft#', 'wire', 'batch'
            ]
            has_proof = any(indicator in text for indicator in proof_indicators)
            return payment_conf if has_proof else payment_claim
        
        # 3. Invoice receipt vs request
        invoice_receipt = next((m for m in matches if m['subcat'] == 'Invoice Receipt'), None)
        invoice_request = next((m for m in matches if m['subcat'] == 'Request (No Info)'), None)
        
        if invoice_receipt and invoice_request:
            # Check if providing vs requesting
            providing_indicators = ['attached', 'here is', 'copy attached', 'proof']
            requesting_indicators = ['send me', 'provide', 'need', 'share']
            
            is_providing = any(indicator in text for indicator in providing_indicators)
            is_requesting = any(indicator in text for indicator in requesting_indicators)
            
            if is_providing and not is_requesting:
                return invoice_receipt
            elif is_requesting and not is_providing:
                return invoice_request
        
        # 4. Business content overrides auto-reply
        manual = next((m for m in matches if m['main_cat'] == 'Manual Review'), None)
        auto_reply = next((m for m in matches if m['main_cat'] == 'Auto Reply (with/without info)'), None)
        
        if manual and auto_reply:
            # Strong business terms
            strong_business = ['payment', 'invoice', 'dispute', 'collection', 'debt', 'billing']
            business_count = sum(1 for term in strong_business if term in text)
            
            # Business content takes priority unless clear OOO context
            ooo_context = any(phrase in text for phrase in ['out of office', 'away from desk', 'on vacation'])
            if business_count >= 2 and not ooo_context:
                return manual
            elif ooo_context and business_count < 2:
                return auto_reply
        
        # 5. Survey vs other classifications
        survey_match = next((m for m in matches if m['subcat'] == 'Survey'), None)
        if survey_match:
            # Only choose survey if no strong business context
            business_matches = [m for m in matches if m['main_cat'] in ['Manual Review', 'Payments Claim', 'Invoices Request']]
            if not business_matches:
                return survey_match
        
        # 6. Return highest confidence and match count
        return max(matches, key=lambda x: (x['confidence'], x['match_count']))

    def get_pattern_stats(self) -> Dict[str, int]:
        """Get pattern statistics."""
        stats = {}
        for main_cat, subcats in self.patterns.items():
            total = sum(len(patterns) for patterns in subcats.values())
            stats[main_cat] = total
        
        stats['total_patterns'] = sum(stats.values())
        return stats
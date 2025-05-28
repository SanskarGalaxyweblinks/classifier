"""
Comprehensive pattern matching for ALL email classification sublabels.
"""

from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

class PatternMatcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # COMPREHENSIVE patterns matching ALL sublabels from your hierarchy
        self.patterns = {
            # ===== MANUAL REVIEW =====
            "manual_review": {
                # Disputes & Payments -> Partial/Disputed Payment
                "partial_disputed_payment": [
                    r"partial\s+payment",
                    r"dispute.*payment",
                    r"contested.*payment", 
                    r"disagreement.*payment",
                    r"challenge.*payment",
                    r"question.*payment"
                ],
                
                # Payment/Invoice Updates -> Payment Confirmation (providing proof)
                "payment_confirmation": [
                    r"payment\s+confirmation.*attached",
                    r"proof\s+of\s+payment.*attached",
                    r"payment\s+receipt.*attached",
                    r"confirming.*payment.*proof",
                    r"evidence\s+of\s+payment",
                    r"payment\s+documentation.*attached"
                ],
                
                # Payment/Invoice Updates -> Invoice Receipt (providing proof)
                "invoice_receipt": [
                    r"invoice.*receipt.*attached",
                    r"proof\s+of\s+invoice.*attached",
                    r"invoice\s+copy.*attached",
                    r"invoice\s+documentation.*attached",
                    r"confirming.*invoice.*received"
                ],
                
                # Business Closure -> Closure Notification
                "closure_notification": [
                    r"business.*closed",
                    r"company.*closed",
                    r"closed\s+and\s+dissolved",
                    r"out\s+of\s+business",
                    r"ceased\s+operations",
                    r"no\s+longer\s+operating"
                ],
                
                # Business Closure -> Closure + Payment Due
                "closure_payment_due": [
                    r"closed.*payment.*due",
                    r"business.*closed.*outstanding",
                    r"closure.*payment.*required",
                    r"final.*payment.*closure"
                ],
                
                # Invoices -> External Submission (actionable import failures and issues)
                "external_submission": [
                    r"invoice.*not.*imported",
                    r"failed\s+to\s+import.*invoice",
                    r"invoice.*could\s+not\s+import",
                    r"invoice.*failed.*import",
                    r"not\s+imported.*invoice",
                    r"could\s+not\s+import.*invoice",
                    r"import\s+failed.*invoice",
                    r"import\s+failed",
                    r"import\s+error.*invoice",
                    r"unable\s+to\s+import.*invoice",
                    r"import\s+unsuccessful.*invoice",
                    r"error.*import.*invoice",
                    r"failure.*import.*invoice",
                    r"invoice.*issue",
                    r"problem.*with.*invoice",
                    r"invoice.*error",
                    r"invoice.*concern",
                    r"invoice.*discrepancy"
                ],

                # You may also add generic patterns to "invoice_errors" if you want to catch some format-related import fails:
                "invoice_errors": [
                    r"invoice.*missing.*field",
                    r"invoice.*incomplete",
                    r"format.*mismatch",
                    r"invoice.*format.*issue",
                    r"required.*field.*missing",
                    # Optionally add some import failure patterns here too if you want double coverage
                    r"not\s+imported$",
                    r"was\s+not\s+imported$",
                    r"could\s+not\s+import$",
                    r"failed\s+to\s+import$",
                    r"error.*import",
                    r"failure.*import"
                ],

                # Payment Details Received (manual check needed)
                "payment_details_received": [
                    r"payment\s+details.*attached",
                    r"remittance.*information",
                    r"payment\s+breakdown",
                    r"payment\s+summary.*attached",
                    r"transaction\s+details"
                ],
                
                # Inquiry/Redirection
                "inquiry_redirection": [
                    r"redirect.*to",
                    r"forward.*to",
                    r"contact.*instead",
                    r"please.*reach.*out.*to",
                    r"inquiry.*redirected",
                    r"\bplease\s+review\b",
                    r"\breview\b",
                    r"\bsee\s+below\b",
                    r"\bassist\b",
                    r"\bcheck\b",
                    r"\bfor\s+your\s+review\b"
                ],
                # Complex Queries
                "complex_queries": [
                    r"multiple.*issues",
                    r"several.*questions",
                    r"complex.*situation",
                    r"detailed.*inquiry",
                    r"various.*concerns"
                ]
            },
            
            # ===== NO REPLY =====
            "no_reply": {
            # Notifications -> Sales/Offers
            "sales_offers": [
                r"special\s+offer",
                r"limited\s+time\s+offer",
                r"promotional\s+offer",
                r"sales\s+promotion",
                r"discount\s+offer"
            ],
            # System Alerts -> Processing Errors (not import failures)
            "processing_errors": [
                r"processing\s+error",
                r"failed\s+to\s+process",
                r"processing\s+failed",
                r"unable\s+to\s+process",
                r"error.*processing"
            ],
            # Notifications -> Business Closure (Info only)
            "business_closure_info": [
                r"business.*closed.*information",
                r"closure.*notification.*only",
                r"informing.*closure",
                r"closure.*update.*only"
            ],
            # Tickets/Cases -> Created
            "ticket_created": [
                r"ticket.*created",
                r"case.*opened",
                r"new.*ticket",
                r"support\s+(has\s+)?been\s+created",
    r"assigned\s+#\d+",
    r"request\s+has\s+been\s+created"
                r"ticket.*#\d+",
                r"case.*number.*is",
                r"support.*request.*created"
            ],
            # Tickets/Cases -> Resolved
            "ticket_resolved": [
                r"ticket.*resolved",
                r"case.*closed",
                r"ticket.*completed",
                r"case.*resolved",
                r"support.*request.*completed"
            ],
            # Tickets/Cases -> Open (escalate to Manual Review)
            "ticket_open": [
                r"ticket.*still.*open",
                r"case.*remains.*open",
                r"ticket.*pending",
                r"case.*in.*progress",
                r"support.*request.*open"
            ]
        },
            
            # ===== INVOICES REQUEST =====
            "invoice_request": {
                # Request (No Info) - no details provided
                "request_no_info": [
                    r"send.*invoice",
                    r"need.*invoice",
                    r"please.*send.*invoice",
                    r"provide.*invoice",
                    r"invoice.*request",
                    r"can.*you.*send.*invoice"
                ]
            },
            
            # ===== PAYMENTS CLAIM =====
            "payment_claim": {
                # Claims Paid (No Info) - claiming paid but no proof
                "claims_paid_no_info": [
                    r"payment.*made",
                    r"check.*sent",
                    r"already.*paid",
                    r"payment.*sent",
                    r"check.*is.*being.*overnighted",
                    r"paid.*through",
                    r"payment.*completed"
                ]
            },
            
            # ===== AUTO REPLY =====
            "auto_reply": {
                # Out of Office -> With Alternate Contact
                "out_of_office_alternate": [
                    r"out.*of.*office.*contact",
                    r"away.*contact.*instead",
                    r"unavailable.*please.*contact",
                    r"out.*of.*office.*reach.*out.*to",
                    r"\bunavailable\b",
                    r"\booo\b",
                    r"back\s+in\s+office\s+on",
                    r"on\s+leave"
                ],
                # Out of Office -> No Info/Autoreply
                "out_of_office_general": [
                    r"out\s+of\s+office",
                    r"away\s+from\s+desk",
                    r"not\s+available",
                    r"limited\s+access\s+to\s+email",
                    r"automatic\s+reply",
                    r"\booo\b",
                    r"i'?m\s+on\s+leave",
                    r"will\s+be\s+out",
                    r"auto-?reply"
                ],
                # Out of Office -> Return Date Specified
                "out_of_office_return": [
                    r"return.*on",
                    r"back.*on",
                    r"available.*after",
                    r"returning.*\d+",
                    r"out.*until.*\d+"
                ],
                
                # Confirmations -> Case/Support
                "case_support_confirmation": [
                    r"case.*confirmed",
                    r"support.*request.*confirmed",
                    r"ticket.*confirmed",
                    r"request.*acknowledged"
                ],
                
                # Confirmations -> General (Thank You)
                "general_confirmation": [
                    r"thank\s+you",
                    r"thanks",
                    r"received.*message",
                    r"got.*your.*request",
                    r"we.*received.*your"
                ],
                
                # Miscellaneous -> Survey
                "survey": [
                    r"survey",
                    r"feedback.*request",
                    r"rate.*our.*service",
                    r"customer.*satisfaction",
                    r"please.*rate"
                ],
                
                # Miscellaneous -> Redirects/Updates (property changes)
                "redirects_updates": [
                    r"property.*manager.*changed",
                    r"contact.*information.*updated",
                    r"new.*contact.*person",
                    r"department.*changed",
                    r"forwarding.*to.*new"
                ]
            }
        }
        
        # Compile all patterns
        self.compiled_patterns = {}
        for main_category, subcategories in self.patterns.items():
            self.compiled_patterns[main_category] = {}
            for subcategory, patterns in subcategories.items():
                self.compiled_patterns[main_category][subcategory] = [
                    re.compile(pattern, re.IGNORECASE) for pattern in patterns
                ]
        
        # Map subcategories to proper label names
        self.sublabel_names = {
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
            "sales_offers": "Sales/Offers",
            "processing_errors": "Processing Errors",
            "business_closure_info": "Business Closure (Info only)",
            "ticket_created": "Created",
            "ticket_resolved": "Resolved",
            "ticket_open": "Open",
            "request_no_info": "Request (No Info)",
            "claims_paid_no_info": "Claims Paid (No Info)",
            "out_of_office_alternate": "With Alternate Contact",
            "out_of_office_general": "No Info/Autoreply",
            "out_of_office_return": "Return Date Specified",
            "case_support_confirmation": "Case/Support",
            "general_confirmation": "General (Thank You)",
            "survey": "Survey",
            "redirects_updates": "Redirects/Updates (property changes)"
        }

        
        # Map to main categories
        self.main_category_names = {
            "manual_review": "Manual Review",
            "no_reply": "No Reply (with/without info)",
            "invoice_request": "Invoices Request",
            "payment_claim": "Payments Claim", 
            "auto_reply": "Auto Reply (with/without info)"
        }
        
        self.logger.info("✅ Comprehensive PatternMatcher initialized with ALL sublabels")

    def match_text(self, text: str) -> Tuple[Optional[str], Optional[str], float, List[str]]:
        """
        Match text against all patterns and return best match.
        Returns: (main_category, subcategory, confidence, matched_patterns)
        """
        if not text:
            return None, None, 0.0, []
        
        text = text.lower()
        best_match = None
        best_confidence = 0.0
        best_patterns = []
        
        # Check all categories and subcategories
        for main_cat, subcategories in self.compiled_patterns.items():
            for subcat, patterns in subcategories.items():
                matches = []
                matched_patterns = []
                
                for pattern in patterns:
                    if pattern.search(text):
                        matches.append(pattern.pattern)
                        matched_patterns.append(pattern.pattern)
                
                if matches:
                    # Calculate confidence based on number of matches
                    confidence = min(len(matches) * 0.3, 1.0)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = (main_cat, subcat)
                        best_patterns = matched_patterns
        
        if best_match:
            main_cat, subcat = best_match
            return (
                self.main_category_names[main_cat],
                self.sublabel_names[subcat], 
                best_confidence,
                best_patterns
            )
        
        return None, None, 0.0, []

    def get_all_patterns(self) -> Dict:
        """Return all patterns for debugging."""
        return self.patterns
    
    def get_pattern_count(self) -> Dict[str, int]:
        """Get count of patterns per category."""
        counts = {}
        for main_cat, subcats in self.patterns.items():
            total = sum(len(patterns) for patterns in subcats.values())
            counts[main_cat] = total
        return counts
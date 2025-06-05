"""
Clean, Strong RuleEngine for email classification
Removed General (Thank You) and unnecessary functions
Focus on classify_sublabel and NLP analysis only
"""
import logging
import time
import re
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

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

class RuleEngine:
    """
    Strong RuleEngine with exact hierarchy alignment.
    Two main functions: classify_sublabel and NLP analysis.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pattern_matcher = PatternMatcher()
        self.nlp_processor = NLPProcessor()
        
        # Define exact hierarchy structure for reference
        self._initialize_hierarchy_rules()
        self.logger.info("✅ Strong RuleEngine initialized")

    def _initialize_hierarchy_rules(self) -> None:
        """Initialize exact hierarchy structure for classification rules."""
        
        # EXACT HIERARCHY AS SPECIFIED
        self.hierarchy_structure = {
            "Manual Review": {
                "Disputes & Payments": ["Partial/Disputed Payment"],
                "Invoice Updates": ["Invoice Receipt"],  # providing proof of invoice
                "Business Closure": ["Closure Notification", "Closure + Payment Due"],
                "Invoices": ["External Submission", "Invoice Errors (format mismatch)"],  # invoice issues
                "Direct": ["Inquiry/Redirection", "Complex Queries"]
            },
            "No Reply (with/without info)": {
                "Notifications": ["Sales/Offers", "System Alerts", "Processing Errors", "Business Closure (Info only)"],
                "Tickets/Cases": ["Created", "Resolved", "Open"]
            },
            "Invoices Request": {
                "Direct": ["Request (No Info)"]  # no info in invoice request
            },
            "Payments Claim": {
                "Direct": ["Claims Paid (No Info)", "Payment Details Received", "Payment Confirmation"]
                # Claims Paid (No Info) = claiming paid but no proof
                # Payment Details Received = payment details for manual check  
                # Payment Confirmation = providing proof of payment
            },
            "Auto Reply (with/without info)": {
                "Out of Office": ["With Alternate Contact", "No Info/Autoreply", "Return Date Specified"],
                "Miscellaneous": ["Survey", "Redirects/Updates (property changes)"]
            }
        }
        
        # Default subcategories for each main category
        self.default_subcategories = {
            "Manual Review": "Complex Queries",
            "No Reply (with/without info)": "System Alerts",
            "Invoices Request": "Request (No Info)", 
            "Payments Claim": "Claims Paid (No Info)",
            "Auto Reply (with/without info)": "No Info/Autoreply"
        }

    def classify_sublabel(
        self,
        main_category: str,
        text: str,
        analysis: Optional[TextAnalysis] = None,
        ml_result: Optional[Dict[str, Any]] = None,
        subject: str = ""
    ) -> RuleResult:
        """
        MAIN CLASSIFICATION FUNCTION
        Strong logic based on exact hierarchy structure
        """
        start_time = time.time()
        text_lower = text.lower().strip() if isinstance(text, str) else ""
        subject_lower = subject.lower().strip() if isinstance(subject, str) else ""

        try:
            # Input validation
            if not text_lower and not subject_lower:
                return RuleResult("Uncategorized", "General", 0.1, "Empty input", ["empty_input"])
            
            if not main_category or not isinstance(main_category, str):
                return RuleResult("Uncategorized", "General", 0.1, "Invalid category", ["invalid_category"])

            # STEP 1: HIGH-PRIORITY BUSINESS RULES (Based on Exact Hierarchy)
            
            # 1A: DISPUTES & PAYMENTS → Partial/Disputed Payment
            dispute_phrases = [
                'formally disputing', 'dispute this debt', 'owe nothing', 'owe them nothing',
                'consider this a scam', 'billing is incorrect', 'cease and desist', 'fdcpa',
                'do not acknowledge', 'not our responsibility', 'contested payment', 'refuse payment',
                'disputing with insurance', 'mistake was theirs', 'mistake was there\'s',
                'settlement for $', 'settled for $', 'not our responsibility'
            ]
            if any(phrase in text_lower for phrase in dispute_phrases):
                return RuleResult("Manual Review", "Partial/Disputed Payment", 0.95, "Dispute detected", ["dispute_rule"])

            # 1B: INVOICE UPDATES → Invoice Receipt (providing proof of invoice)
            invoice_proof_phrases = [
                'invoice receipt attached', 'proof of invoice attached', 'invoice copy attached',
                'invoice documentation attached', 'error payment proof', 'payment error documentation'
            ]
            if any(phrase in text_lower for phrase in invoice_proof_phrases):
                return RuleResult("Manual Review", "Invoice Receipt", 0.90, "Invoice proof provided", ["invoice_proof_rule"])

            # 1C: BUSINESS CLOSURE → Closure Notification / Closure + Payment Due
            closure_phrases = ['business closed', 'filed bankruptcy', 'out of business', 'ceased operations']
            if any(phrase in text_lower for phrase in closure_phrases):
                # Check if payment is due
                if any(payment in text_lower for payment in ['outstanding payment', 'payment due', 'amount owed']):
                    return RuleResult("Manual Review", "Closure + Payment Due", 0.90, "Closure with payment due", ["closure_payment_rule"])
                else:
                    return RuleResult("Manual Review", "Closure Notification", 0.90, "Business closure", ["closure_rule"])

            # 1D: INVOICES → External Submission / Invoice Errors (format mismatch)
            submission_errors = ['invoice submission failed', 'import failed', 'documents not processed']
            format_errors = ['missing required field', 'format mismatch', 'invalid invoice format']
            
            if any(phrase in text_lower for phrase in submission_errors):
                return RuleResult("Manual Review", "External Submission", 0.85, "Invoice submission issue", ["submission_rule"])
            elif any(phrase in text_lower for phrase in format_errors):
                return RuleResult("Manual Review", "Invoice Errors (format mismatch)", 0.85, "Invoice format error", ["format_rule"])

            # 1E: PAYMENTS CLAIM → Claims Paid (No Info) / Payment Details Received / Payment Confirmation
            payment_proof_phrases = ['proof of payment', 'payment confirmation attached', 'check number', 'transaction id']
            payment_claim_phrases = ['already paid', 'payment was made', 'check was sent', 'account paid']
            payment_details_phrases = ['payment will be sent', 'payment being processed', 'working on payment']
            
            if any(phrase in text_lower for phrase in payment_proof_phrases):
                return RuleResult("Payments Claim", "Payment Confirmation", 0.90, "Payment proof provided", ["payment_proof_rule"])
            elif any(phrase in text_lower for phrase in payment_details_phrases):
                return RuleResult("Payments Claim", "Payment Details Received", 0.85, "Payment details received", ["payment_details_rule"])
            elif any(phrase in text_lower for phrase in payment_claim_phrases):
                return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.85, "Payment claimed without proof", ["payment_claim_rule"])

            # 1F: INVOICES REQUEST → Request (No Info)
            invoice_request_phrases = ['send me the invoice', 'need invoice copy', 'provide outstanding invoices']
            if any(phrase in text_lower for phrase in invoice_request_phrases):
                # Exclude if providing proof
                if not any(proof in text_lower for proof in ['paid', 'proof', 'attached']):
                    return RuleResult("Invoices Request", "Request (No Info)", 0.85, "Invoice request", ["invoice_request_rule"])

            # 1G: AUTO REPLY → Out of Office / Miscellaneous
            ooo_phrases = ['out of office', 'automatic reply', 'away from desk']
            survey_phrases = ['survey', 'feedback request', 'rate our service']
            redirect_phrases = ['no longer employed', 'contact changed', 'property manager changed']
            
            if any(phrase in text_lower for phrase in survey_phrases):
                # Only survey if no strong business context
                if not any(business in text_lower for business in ['payment', 'invoice', 'dispute']):
                    return RuleResult("Auto Reply (with/without info)", "Survey", 0.85, "Survey detected", ["survey_rule"])
            
            if any(phrase in text_lower for phrase in redirect_phrases):
                return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.85, "Contact change", ["redirect_rule"])
            
            if any(phrase in text_lower for phrase in ooo_phrases):
                # Check for return date
                return_phrases = ['return on', 'back on', 'returning on', 'out until']
                contact_phrases = ['alternate contact', 'emergency contact', 'contact me at']
                
                if any(phrase in text_lower for phrase in return_phrases):
                    return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.85, "OOO with return date", ["ooo_return_rule"])
                elif any(phrase in text_lower for phrase in contact_phrases):
                    return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.85, "OOO with contact", ["ooo_contact_rule"])
                else:
                    return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.80, "Generic OOO", ["ooo_generic_rule"])

            # 1H: NO REPLY → Notifications / Tickets/Cases
            sales_phrases = ['special offer', 'limited time offer', 'price increase', 'payment plan options']
            system_phrases = ['system notification', 'maintenance notification', 'security alert']
            processing_phrases = ['processing error', 'failed to process', 'delivery failed']
            ticket_phrases = ['ticket created', 'case opened', 'support request created']
            resolved_phrases = ['ticket resolved', 'case resolved', 'marked as resolved']
            
            if any(phrase in text_lower for phrase in sales_phrases):
                return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.85, "Sales/marketing", ["sales_rule"])
            elif any(phrase in text_lower for phrase in system_phrases):
                return RuleResult("No Reply (with/without info)", "System Alerts", 0.85, "System notification", ["system_rule"])
            elif any(phrase in text_lower for phrase in processing_phrases):
                return RuleResult("No Reply (with/without info)", "Processing Errors", 0.85, "Processing error", ["processing_rule"])
            elif any(phrase in text_lower for phrase in ticket_phrases):
                return RuleResult("No Reply (with/without info)", "Created", 0.85, "Ticket created", ["ticket_created_rule"])
            elif any(phrase in text_lower for phrase in resolved_phrases):
                return RuleResult("No Reply (with/without info)", "Resolved", 0.85, "Ticket resolved", ["ticket_resolved_rule"])
            
            # 1J: Enhanced dispute with insurance/settlement
            if any(phrase in text_lower for phrase in [
                'disputing with insurance', 'mistake was theirs', 'mistake was there\'s',
                'settlement for $', 'settled for $'
            ]):
                return RuleResult("Manual Review", "Partial/Disputed Payment", 0.90, "Dispute/settlement detected", ["dispute_settlement_rule"])

            # 1K: Payment proof with specific details  
            if any(phrase in text_lower for phrase in [
                'ach payment id', 'last 4 digits', 'receipt is attached', 'payment receipt attached'
            ]):
                return RuleResult("Payments Claim", "Payment Confirmation", 0.90, "Payment proof with details", ["payment_proof_details_rule"])

            # 1L: Contact/management changes
            if any(phrase in text_lower for phrase in [
                'no longer manage', 'new management company', 'please reach out to'
            ]):
                return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.85, "Management change", ["management_change_rule"])

            # STEP 2: PATTERN MATCHER (Secondary Classification)
            if hasattr(self, 'pattern_matcher'):
                main_cat, subcat, confidence, patterns = self.pattern_matcher.match_text(text_lower)
                
                if main_cat and confidence >= 0.50:
                    # Validate against hierarchy
                    if self._validate_hierarchy_match(main_cat, subcat):
                        return RuleResult(main_cat, subcat, confidence, f"Pattern: {subcat}", patterns)

            # STEP 3: NLP ANALYSIS (if available)
            if analysis and analysis.topics:
                nlp_result = self._classify_with_nlp_analysis(text_lower, analysis)
                if nlp_result:
                    return nlp_result

            # STEP 4: BUSINESS FALLBACK (Conservative routing)
            business_terms = ['payment', 'invoice', 'dispute', 'collection', 'debt', 'billing']
            business_count = sum(1 for term in business_terms if term in text_lower)
            
            if business_count >= 2:
                return RuleResult("Manual Review", "Complex Queries", 0.60, "Multiple business terms", ["business_fallback"])
            elif business_count == 1:
                if 'payment' in text_lower:
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.55, "Payment term", ["payment_fallback"])
                elif 'invoice' in text_lower:
                    return RuleResult("Invoices Request", "Request (No Info)", 0.55, "Invoice term", ["invoice_fallback"])
                else:
                    return RuleResult("Manual Review", "Inquiry/Redirection", 0.55, "Business term", ["business_term_fallback"])
            else:
                # No business terms - system notification
                return RuleResult("No Reply (with/without info)", "System Alerts", 0.50, "General notification", ["general_fallback"])

        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return RuleResult("Manual Review", "Complex Queries", 0.30, f"Error: {e}", ["error_fallback"])

    def _classify_with_nlp_analysis(self, text: str, analysis: TextAnalysis) -> Optional[RuleResult]:
        """
        NLP ANALYSIS FUNCTION
        Uses NLP topics to classify based on exact hierarchy
        """
        try:
            for topic in analysis.topics:
                
                # MANUAL REVIEW TOPICS
                if topic == 'Partial/Disputed Payment':
                    return RuleResult("Manual Review", "Partial/Disputed Payment", 0.80, "NLP: Dispute", ["nlp_dispute"])
                elif topic == 'Invoice Receipt':
                    return RuleResult("Manual Review", "Invoice Receipt", 0.80, "NLP: Invoice proof", ["nlp_invoice_proof"])
                elif topic == 'Closure Notification':
                    return RuleResult("Manual Review", "Closure Notification", 0.80, "NLP: Closure", ["nlp_closure"])
                elif topic == 'Closure + Payment Due':
                    return RuleResult("Manual Review", "Closure + Payment Due", 0.80, "NLP: Closure+Payment", ["nlp_closure_payment"])
                elif topic == 'External Submission':
                    return RuleResult("Manual Review", "External Submission", 0.80, "NLP: Submission issue", ["nlp_submission"])
                elif topic == 'Invoice Errors (format mismatch)':
                    return RuleResult("Manual Review", "Invoice Errors (format mismatch)", 0.80, "NLP: Format error", ["nlp_format"])
                elif topic == 'Inquiry/Redirection':
                    return RuleResult("Manual Review", "Inquiry/Redirection", 0.80, "NLP: Inquiry", ["nlp_inquiry"])
                elif topic == 'Complex Queries':
                    return RuleResult("Manual Review", "Complex Queries", 0.80, "NLP: Complex", ["nlp_complex"])
                
                # NO REPLY TOPICS
                elif topic == 'Sales/Offers':
                    return RuleResult("No Reply (with/without info)", "Sales/Offers", 0.80, "NLP: Sales", ["nlp_sales"])
                elif topic == 'System Alerts':
                    return RuleResult("No Reply (with/without info)", "System Alerts", 0.80, "NLP: System", ["nlp_system"])
                elif topic == 'Processing Errors':
                    return RuleResult("No Reply (with/without info)", "Processing Errors", 0.80, "NLP: Processing", ["nlp_processing"])
                elif topic == 'Business Closure (Info only)':
                    return RuleResult("No Reply (with/without info)", "Business Closure (Info only)", 0.80, "NLP: Closure info", ["nlp_closure_info"])
                elif topic == 'Created':
                    return RuleResult("No Reply (with/without info)", "Created", 0.80, "NLP: Ticket created", ["nlp_created"])
                elif topic == 'Resolved':
                    return RuleResult("No Reply (with/without info)", "Resolved", 0.80, "NLP: Resolved", ["nlp_resolved"])
                elif topic == 'Open':
                    return RuleResult("No Reply (with/without info)", "Open", 0.80, "NLP: Open", ["nlp_open"])
                
                # PAYMENTS CLAIM TOPICS
                elif topic == 'Claims Paid (No Info)':
                    return RuleResult("Payments Claim", "Claims Paid (No Info)", 0.80, "NLP: Payment claim", ["nlp_payment_claim"])
                elif topic == 'Payment Details Received':
                    return RuleResult("Payments Claim", "Payment Details Received", 0.80, "NLP: Payment details", ["nlp_payment_details"])
                elif topic == 'Payment Confirmation':
                    return RuleResult("Payments Claim", "Payment Confirmation", 0.80, "NLP: Payment proof", ["nlp_payment_proof"])
                
                # INVOICES REQUEST TOPICS
                elif topic == 'Request (No Info)':
                    return RuleResult("Invoices Request", "Request (No Info)", 0.80, "NLP: Invoice request", ["nlp_invoice_request"])
                
                # AUTO REPLY TOPICS  
                elif topic == 'With Alternate Contact':
                    return RuleResult("Auto Reply (with/without info)", "With Alternate Contact", 0.80, "NLP: OOO contact", ["nlp_ooo_contact"])
                elif topic == 'No Info/Autoreply':
                    return RuleResult("Auto Reply (with/without info)", "No Info/Autoreply", 0.80, "NLP: Auto reply", ["nlp_auto_reply"])
                elif topic == 'Return Date Specified':
                    return RuleResult("Auto Reply (with/without info)", "Return Date Specified", 0.80, "NLP: Return date", ["nlp_return_date"])
                elif topic == 'Survey':
                    return RuleResult("Auto Reply (with/without info)", "Survey", 0.80, "NLP: Survey", ["nlp_survey"])
                elif topic == 'Redirects/Updates (property changes)':
                    return RuleResult("Auto Reply (with/without info)", "Redirects/Updates (property changes)", 0.80, "NLP: Redirect", ["nlp_redirect"])

            # High urgency/complexity -> Manual Review
            if hasattr(analysis, 'urgency_score') and analysis.urgency_score > 0.7:
                return RuleResult("Manual Review", "Complex Queries", 0.75, f"High urgency: {analysis.urgency_score:.2f}", ["nlp_urgency"])
            
            if hasattr(analysis, 'complexity_score') and analysis.complexity_score > 0.7:
                return RuleResult("Manual Review", "Complex Queries", 0.75, f"High complexity: {analysis.complexity_score:.2f}", ["nlp_complexity"])

            return None

        except Exception as e:
            self.logger.error(f"NLP analysis error: {e}")
            return None

    def _validate_hierarchy_match(self, main_cat: str, subcat: str) -> bool:
        """Validate that subcategory belongs to main category in hierarchy."""
        if main_cat not in self.hierarchy_structure:
            return False
        
        # Check all subcategory groups under main category
        for group_name, subcategories in self.hierarchy_structure[main_cat].items():
            if subcat in subcategories:
                return True
        
        return False
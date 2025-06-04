"""
Clean Email Classifier with Simple Label Mapping
"""

import logging
import time
import re
from typing import Dict, Any, Optional

from email_classifier.preprocessor import EmailPreprocessor
from email_classifier.nlp_utils import NLPProcessor, TextAnalysis
from email_classifier.ml_classifier import MLClassifier
from email_classifier.rule_engine import RuleEngine, RuleResult

logger = logging.getLogger(__name__)

class EmailClassifier:
    """Clean Email Classifier with ALLOWED_LABELS mapping"""
    
    ALLOWED_LABELS = [
        "no_reply_no_info", "no_reply_with_info", 
        "auto_reply_no_info", "auto_reply_with_info",
        "invoice_request_no_info", "claims_paid_no_proof", 
        "claims_paid_with_proof", "manual_review", "Uncategorized"
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.preprocessor = EmailPreprocessor()
        self.nlp_processor = NLPProcessor()
        self.ml_classifier = MLClassifier()
        self.rule_engine = RuleEngine()
        
        # Core detection patterns
        self.phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\(\d{3}\)\s*\d{3}[-.]?\d{4}'
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.ticket_pattern = r'(?:ticket|case|#)\s*[:\s]*[A-Z0-9-]+'
        
        self.logger.info("✅ EmailClassifier initialized")

    def classify_email(self, subject: str, body: str, email_id: Optional[int] = None) -> Dict[str, Any]:
        """Main classification with mapping to ALLOWED_LABELS"""
        start_time = time.time()
        
        try:
            processed = self.preprocessor.preprocess_email(subject, body)
            if not processed.cleaned_text:
                return self._fallback_result("Empty content", start_time)
            
            # Get classifications with error handling
            try:
                analysis = self.nlp_processor.analyze_text(processed.cleaned_text)
            except Exception as e:
                self.logger.warning(f"NLP analysis failed: {e}")
                analysis = None
            
            try:
                ml_result = self.ml_classifier.classify_email(processed.cleaned_text, has_thread=processed.has_thread)
            except Exception as e:
                self.logger.warning(f"ML classification failed: {e}")
                ml_result = {
                    'category': 'Manual Review',
                    'subcategory': 'Complex Queries', 
                    'confidence': 0.5,
                    'method_used': 'ml_fallback',
                    'reason': f'ML error: {e}'
                }
            
            try:
                rule_result = self.rule_engine.classify_sublabel(
                    ml_result['category'], processed.cleaned_text, 
                    analysis=analysis, ml_result=ml_result, has_thread=processed.has_thread,
                    subject=processed.cleaned_subject
                )
            except Exception as e:
                self.logger.warning(f"Rule engine failed: {e}")
                rule_result = RuleResult(
                    category='Manual Review',
                    subcategory='Complex Queries',
                    confidence=0.5,
                    reason=f'Rule error: {e}',
                    matched_rules=['rule_fallback']
                )
            
            self.logger.debug(f"Email {email_id}: ML={ml_result['category']}/{ml_result.get('subcategory', 'N/A')}, "
                            f"Rule={rule_result.category}/{rule_result.subcategory}")
            
            detailed_result = self._get_best_classification(ml_result, rule_result, processed, analysis, start_time)
            final_label = self._map_to_final_label(detailed_result, processed.cleaned_text + " " + processed.cleaned_subject)
            
            result = {**detailed_result, 'final_label': final_label}
            
            self.logger.info(f"Email {email_id}: {detailed_result['category']}/{detailed_result['subcategory']} → {final_label}")
            return result
            
        except Exception as e:
            self.logger.error(f"Classification error for email {email_id}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return self._fallback_result(f"Critical error: {e}", start_time)

    def debug_classification(self, subject: str, body: str) -> Dict[str, Any]:
        """Debug method to see classification step-by-step"""
        print(f"=== DEBUG CLASSIFICATION ===")
        print(f"Subject: {subject[:50]}...")
        print(f"Body length: {len(body)}")
        
        try:
            processed = self.preprocessor.preprocess_email(subject, body)
            print(f"Processed text length: {len(processed.cleaned_text)}")
            print(f"Has thread: {processed.has_thread}")
            
            ml_result = self.ml_classifier.classify_email(processed.cleaned_text, has_thread=processed.has_thread)
            print(f"ML Result: {ml_result['category']}/{ml_result.get('subcategory', 'N/A')} (conf: {ml_result['confidence']:.2f})")
            
            rule_result = self.rule_engine.classify_sublabel(
                ml_result['category'], processed.cleaned_text, 
                has_thread=processed.has_thread, subject=processed.cleaned_subject
            )
            print(f"Rule Result: {rule_result.category}/{rule_result.subcategory} (conf: {rule_result.confidence:.2f})")
            
            return {'ml': ml_result, 'rule': rule_result}
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            print(traceback.format_exc())
            return {'error': str(e)}

    def _get_best_classification(self, ml_result, rule_result, processed, analysis, start_time):
        """Get best classification from ML and Rule results"""
        thread_context = {
            'has_thread': processed.has_thread,
            'thread_count': 0,
            'current_reply': 0
        }
        
        base_result = {
            'thread_context': thread_context,
            'processing_time': time.time() - start_time,
            'timestamp': time.time()
        }
        
        if rule_result.confidence >= 0.8:
            return {
                **base_result,
                'category': rule_result.category,
                'subcategory': rule_result.subcategory,
                'confidence': rule_result.confidence,
                'method_used': 'rule_high_confidence',
                'reason': rule_result.reason,
                'matched_patterns': rule_result.matched_rules
            }
        
        if processed.has_thread:
            return {
                **base_result,
                'category': rule_result.category,
                'subcategory': rule_result.subcategory,
                'confidence': min(rule_result.confidence + 0.1, 0.9),
                'method_used': 'thread_priority',
                'reason': f"Thread: {rule_result.reason}",
                'matched_patterns': rule_result.matched_rules
            }
        
        if ml_result['confidence'] >= 0.6 and rule_result.confidence >= 0.4:
            return {
                **base_result,
                'category': rule_result.category,
                'subcategory': rule_result.subcategory,
                'confidence': round((ml_result['confidence'] * 0.6) + (rule_result.confidence * 0.4), 2),
                'method_used': 'ml_rule_combined',
                'reason': f"Combined: {rule_result.reason}",
                'matched_patterns': rule_result.matched_rules
            }
        
        return {
            **base_result,
            'category': rule_result.category,
            'subcategory': rule_result.subcategory,
            'confidence': rule_result.confidence,
            'method_used': 'rule_fallback',
            'reason': rule_result.reason,
            'matched_patterns': rule_result.matched_rules
        }

    def _map_to_final_label(self, result: Dict[str, Any], full_text: str) -> str:
        """Map detailed result to ALLOWED_LABELS"""
        category = result['category']
        subcategory = result['subcategory']
        
        if category == "Manual Review":
            return "manual_review"
        
        elif category == "No Reply (with/without info)":
            return "no_reply_with_info" if self._has_useful_info(full_text) else "no_reply_no_info"
        
        elif category == "Invoices Request":
            return "invoice_request_no_info"
        
        elif category == "Payments Claim":
            if subcategory in ["Claims Paid (No Info)", "Payment Details Received"]:
                return "claims_paid_with_proof" if self._has_payment_proof(full_text) else "claims_paid_no_proof"
            elif subcategory == "Payment Confirmation":
                return "claims_paid_with_proof" if self._has_payment_proof(full_text) else "claims_paid_no_proof"
            else:
                return "claims_paid_no_proof"
        
        elif category == "Auto Reply (with/without info)":
            return "auto_reply_with_info" if self._has_contact_info(full_text) else "auto_reply_no_info"
        
        elif category == "Uncategorized":
            return "Uncategorized"
        
        else:
            return "manual_review"

    def _has_payment_proof(self, text: str) -> bool:
        """FIXED: Enhanced payment proof detection"""
        text_lower = text.lower()
        
        # Strong proof indicators (specific attachments and transaction details)
        strong_proof = [
            'see attached', 'attached cancelled check', 'proof attached',
            'payment confirmation attached', 'receipt attached', 'wire confirmation',
            'here is proof of payment', 'use as proof of payment', 'proof of payment'
        ]
        
        # Transaction details with numbers/IDs
        transaction_patterns = [
            r'check number\s*[#:]?\s*\d+', r'transaction id\s*[#:]?\s*\w+',
            r'eft#\s*\w+', r'confirmation number\s*[#:]?\s*\w+',
            r'transaction#\s*\d+', r'batch number\s*[#:]?\s*\w+',
            r'wire confirmation\s*[#:]?\s*\w+', r'ach amount\s*\$[\d,]+'
        ]
        
        # Structured payment data
        structured_proof = [
            'remittance details for your reference', 'payment details below',
            'transaction# ', 'vendor:', 'invoice# ', 'po# '
        ]
        
        # Check strong proof indicators
        if any(phrase in text_lower for phrase in strong_proof):
            return True
        
        # Check transaction patterns
        for pattern in transaction_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check structured data
        if any(phrase in text_lower for phrase in structured_proof):
            return True
        
        # Exclude future payments
        future_payment_phrases = [
            'will pay', 'going to pay', 'payment will be sent', 'check will be mailed',
            'payment being processed', 'working on payment', 'need time to pay'
        ]
        
        if any(phrase in text_lower for phrase in future_payment_phrases):
            return False
        
        return False

    def _has_useful_info(self, text: str) -> bool:
        """FIXED: Check if No Reply email has useful information"""
        text_lower = text.lower()
        
        # Ticket/case information
        if (re.search(self.ticket_pattern, text, re.IGNORECASE) or
            any(word in text_lower for word in ['case number', 'ticket number', 'support id', 'request number'])):
            return True
        
        # Contact information
        if (re.search(self.email_pattern, text) or 
            re.search(self.phone_pattern, text)):
            return True
        
        # Actionable links or references
        actionable_info = [
            'click here', 'visit', 'portal', 'link below', 'reference number',
            'http', 'www.', 'online', 'website', 'survey', 'feedback'
        ]
        if any(info in text_lower for info in actionable_info):
            return True
        
        # Status updates with useful info
        status_info = [
            'resolved', 'completed', 'processed', 'approved', 'closed',
            'status:', 'update:', 'notification'
        ]
        if any(info in text_lower for info in status_info):
            return True
        
        return False

    def _has_contact_info(self, text: str) -> bool:
        """FIXED: Check if Auto Reply has contact information"""
        text_lower = text.lower()
        
        # Direct contact info (phone/email)
        if (re.search(self.phone_pattern, text) or 
            re.search(self.email_pattern, text)):
            return True
        
        # Specific contact instructions with actual details
        specific_contact = [
            'contact me at', 'call me at', 'reach me at', 'emergency contact',
            'urgent matters contact', 'immediate assistance contact',
            'alternate contact', 'contact information'
        ]
        if any(phrase in text_lower for phrase in specific_contact):
            return True
        
        # Return date WITH contact instructions
        has_return_date = any(phrase in text_lower for phrase in [
            'return on', 'back on', 'returning', 'will be back', 'out until'
        ])
        has_contact_instruction = any(word in text_lower for word in [
            'contact', 'call', 'reach', 'assistance', 'urgent'
        ])
        if has_return_date and has_contact_instruction:
            return True
        
        # Survey or feedback with actionable links
        survey_with_action = [
            'survey web site', 'click here', 'visit the survey', 'take our survey',
            'complete the online survey', 'feedback link', 'rate our service'
        ]
        if any(phrase in text_lower for phrase in survey_with_action):
            return True
        
        # Actionable business information
        actionable_content = [
            'portal', 'link below', 'website', 'online', 'reference number',
            'ticket number', 'case number', 'customer service', 'helpdesk'
        ]
        if any(content in text_lower for content in actionable_content):
            return True
        
        return False

    def _fallback_result(self, reason: str, start_time: float) -> Dict[str, Any]:
        """Create a fallback result when classification fails"""
        return {
            'category': 'Manual Review',
            'subcategory': 'Error Handling',
            'confidence': 0.5,
            'method_used': 'fallback',
            'reason': reason,
            'matched_patterns': [],
            'thread_context': {
                'has_thread': False,
                'thread_count': 0,
                'current_reply': 0
            },
            'processing_time': time.time() - start_time,
            'timestamp': time.time(),
            'final_label': 'manual_review'
        }
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
from email_classifier.rule_engine import RuleEngine

logger = logging.getLogger(__name__)

class EmailClassifier:
    """Clean Email Classifier with ALLOWED_LABELS mapping"""
    
    ALLOWED_LABELS = [
        "no_reply_no_info", "no_reply_with_info", 
        "auto_reply_no_info", "auto_reply_with_info",
        "invoice_request_no_info", "claims_paid_no_proof", 
        "claims_paid_with_proof", "manual_review", "Uncategerised"
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.preprocessor = EmailPreprocessor()
        self.nlp_processor = NLPProcessor()
        self.ml_classifier = MLClassifier()
        self.rule_engine = RuleEngine()
        
        # Simple info detection patterns
        self.phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\(\d{3}\)\s*\d{3}[-.]?\d{4}'
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.ticket_pattern = r'(?:ticket|case|#)\s*[:\s]*[A-Z0-9-]+'
        
        self.logger.info("✅ EmailClassifier initialized")

    def classify_email(self, subject: str, body: str, email_id: Optional[int] = None) -> Dict[str, Any]:
        """Main classification with mapping to ALLOWED_LABELS"""
        start_time = time.time()
        
        try:
            # Process email
            processed = self.preprocessor.preprocess_email(subject, body)
            if not processed.cleaned_text:
                return self._fallback_result("Empty content", start_time)
            
            # Get classifications with individual error handling
            try:
                analysis = self.nlp_processor.analyze_text(processed.cleaned_text)
            except Exception as e:
                self.logger.warning(f"NLP analysis failed: {e}")
                analysis = None
            
            try:
                ml_result = self.ml_classifier.classify_email(processed.cleaned_text, has_thread=processed.has_thread)
            except Exception as e:
                self.logger.warning(f"ML classification failed: {e}")
                # Create fallback ML result
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
                # Create fallback rule result
                from rule_engine import RuleResult  # Adjust import as needed
                rule_result = RuleResult(
                    category='Manual Review',
                    subcategory='Complex Queries',
                    confidence=0.5,
                    reason=f'Rule error: {e}',
                    matched_rules=['rule_fallback']
                )
            
            # Debug logging
            self.logger.debug(f"Email {email_id}: ML={ml_result['category']}/{ml_result.get('subcategory', 'N/A')}, "
                            f"Rule={rule_result.category}/{rule_result.subcategory}")
            
            # Create detailed result
            detailed_result = self._get_best_classification(ml_result, rule_result, processed, analysis, start_time)
            
            # Map to final label
            final_label = self._map_to_final_label(detailed_result, processed.cleaned_text + " " + processed.cleaned_subject)
            
            # Return result with final label
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
        
        # High confidence rule
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
        
        # Thread priority
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
        
        # Combined ML + Rule
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
        
        # Rule fallback
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
        
        # Manual Review
        if category == "Manual Review":
            return "manual_review"
        
        # No Reply - check for info
        elif category == "No Reply (with/without info)":
            return "no_reply_with_info" if self._has_info(full_text) else "no_reply_no_info"
        
        # Invoice Request
        elif category == "Invoices Request":
            return "invoice_request_no_info"
        
        # Payments Claim - based on subcategory
        elif category == "Payments Claim":
            if subcategory == "Claims Paid (No Info)":
                return "claims_paid_no_proof"
            else:  # Payment Details Received or Payment Confirmation
                return "claims_paid_with_proof"
        
        # Auto Reply - check for contact info
        elif category == "Auto Reply (with/without info)":
            return "auto_reply_with_info" if self._has_contact_info(full_text) else "auto_reply_no_info"
        
        # Uncategorized
        elif category == "Uncategorized":
            return "Uncategerised"
        
        # Default fallback
        else:
            return "manual_review"

    def _has_info(self, text: str) -> bool:
        """Check if No Reply email has useful info (tickets, emails, phones)"""
        return (re.search(self.ticket_pattern, text, re.IGNORECASE) or 
                re.search(self.email_pattern, text) or 
                re.search(self.phone_pattern, text) or
                any(word in text.lower() for word in ['case number', 'ticket number', 'support id']))

    def _has_contact_info(self, text: str) -> bool:
        """Check if Auto Reply has contact information"""
        text_lower = text.lower()
        
        # Check for phone/email
        if re.search(self.phone_pattern, text) or re.search(self.email_pattern, text):
            return True
        
        # Check for contact phrases
        contact_phrases = ['contact me at', 'reach out to', 'call me', 'alternate contact', 'emergency contact']
        if any(phrase in text_lower for phrase in contact_phrases):
            return True
        
        # Check for return date + contact combo
        if any(word in text_lower for word in ['return', 'back on']) and \
           any(word in text_lower for word in ['contact', 'call', 'reach']):
            return True
        
        return False

    def _fallback_result(self, reason: str, start_time: float) -> Dict[str, Any]:
        """Simple fallback result"""
        return {
            'category': 'Manual Review',
            'subcategory': 'Complex Queries',
            'confidence': 0.3,
            'method_used': 'fallback',
            'reason': reason,
            'matched_patterns': [],
            'thread_context': {'has_thread': False, 'thread_count': 0, 'current_reply': 0},
            'processing_time': time.time() - start_time,
            'timestamp': time.time(),
            'final_label': 'manual_review'
        }
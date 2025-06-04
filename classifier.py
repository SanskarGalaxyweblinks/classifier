"""
Clean Email Classifier - Aligned with New Preprocessor Architecture
Focused, quality code without unnecessary complexity
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
    """Clean Email Classifier aligned with enhanced preprocessor"""
    
    ALLOWED_LABELS = [
        "no_reply_no_info", "no_reply_with_info", 
        "auto_reply_no_info", "auto_reply_with_info",
        "invoice_request_no_info", "claims_paid_no_proof", 
        "claims_paid_with_proof", "manual_review", "uncategorized"
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.preprocessor = EmailPreprocessor()
        self.nlp_processor = NLPProcessor()
        self.ml_classifier = MLClassifier()
        self.rule_engine = RuleEngine()
        self.logger.info("✅ EmailClassifier initialized")

    def classify_email(self, subject: str, body: str, email_id: Optional[int] = None) -> Dict[str, Any]:
        """Main classification method"""
        start_time = time.time()
        
        try:
            # Step 1: Preprocess
            processed = self.preprocessor.preprocess_email(subject or "", body)
            if not processed.cleaned_text:
                return self._fallback_result("Empty content", start_time)
            
            # Step 2: NLP Analysis
            try:
                analysis = self.nlp_processor.analyze_text(processed.cleaned_text)
            except Exception as e:
                self.logger.warning(f"NLP failed: {e}")
                analysis = None
            
            # Step 3: ML Classification
            try:
                ml_result = self.ml_classifier.classify_email(processed.cleaned_text)
            except Exception as e:
                self.logger.warning(f"ML failed: {e}")
                ml_result = {
                    'category': 'Manual Review',
                    'subcategory': 'Complex Queries',
                    'confidence': 0.5,
                    'method_used': 'ml_fallback',
                    'reason': f'ML error: {e}'
                }
            
            # Step 4: Rule Classification
            try:
                rule_result = self.rule_engine.classify_sublabel(
                    ml_result['category'], processed.cleaned_text, 
                    analysis=analysis, ml_result=ml_result,
                    subject=processed.cleaned_subject
                )
            except Exception as e:
                self.logger.warning(f"Rule failed: {e}")
                rule_result = RuleResult(
                    category='Manual Review',
                    subcategory='Complex Queries',
                    confidence=0.5,
                    reason=f'Rule error: {e}',
                    matched_rules=['rule_fallback']
                )
            
            # Step 5: Get best classification
            best_result = self._get_best_classification(ml_result, rule_result, start_time)
            
            # Step 6: Map to final label using NLP entities
            final_label = self._map_to_final_label(best_result, processed, analysis)
            
            result = {**best_result, 'final_label': final_label}
            
            self.logger.info(f"Email {email_id}: {best_result['category']}/{best_result['subcategory']} → {final_label}")
            return result
            
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return self._fallback_result(f"Error: {e}", start_time)

    def _get_best_classification(self, ml_result, rule_result, start_time):
        """Simple confidence-based classification selection"""
        base_result = {
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
        
        # Combined ML + Rule
        if ml_result['confidence'] >= 0.6 and rule_result.confidence >= 0.4:
            combined_confidence = (ml_result['confidence'] * 0.6) + (rule_result.confidence * 0.4)
            return {
                **base_result,
                'category': rule_result.category,
                'subcategory': rule_result.subcategory,
                'confidence': round(combined_confidence, 2),
                'method_used': 'ml_rule_combined',
                'reason': rule_result.reason,
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

    def _map_to_final_label(self, result: Dict[str, Any], processed, analysis: Optional[TextAnalysis]) -> str:
        """Map to final labels using NLP entities instead of regex patterns"""
        category = result['category']
        subcategory = result['subcategory']
        
        # Manual Review
        if category == "Manual Review":
            return "manual_review"
        
        # No Reply - check for info using NLP entities
        elif category == "No Reply (with/without info)":
            has_info = self._has_info_from_nlp(analysis)
            return "no_reply_with_info" if has_info else "no_reply_no_info"
        
        # Invoice Request
        elif category == "Invoices Request":
            return "invoice_request_no_info"
        
        # Payments Claim - based on subcategory
        elif category == "Payments Claim":
            if subcategory == "Claims Paid (No Info)":
                return "claims_paid_no_proof"
            else:  # Payment Details Received or Payment Confirmation
                return "claims_paid_with_proof"
        
        # Auto Reply - check for contact info using NLP entities
        elif category == "Auto Reply (with/without info)":
            has_contact = self._has_contact_from_nlp(analysis)
            return "auto_reply_with_info" if has_contact else "auto_reply_no_info"
        
        # Uncategorized
        elif category == "Uncategorized":
            return "uncategorized"
        
        else:
            return "manual_review"

    def _has_info_from_nlp(self, analysis: Optional[TextAnalysis]) -> bool:
        """Check for useful info using NLP entities instead of regex"""
        if not analysis or not analysis.entities:
            return False
        
        # Check entity types that indicate useful information
        useful_entity_types = ['ACCOUNT', 'CASE_TICKET', 'INVOICE', 'TRANSACTION', 'REFERENCE', 'EMAIL', 'PHONE']
        
        for entity in analysis.entities:
            if entity.get('label', '').upper() in useful_entity_types:
                return True
        
        return False

    def _has_contact_from_nlp(self, analysis: Optional[TextAnalysis]) -> bool:
        """Check for contact info using NLP entities instead of regex"""
        if not analysis or not analysis.entities:
            return False
        
        # Check for contact-related entities
        contact_entity_types = ['EMAIL', 'PHONE']
        
        for entity in analysis.entities:
            if entity.get('label', '').upper() in contact_entity_types:
                return True
        
        # Check key phrases for contact information
        if analysis.key_phrases:
            contact_phrases = ['contact me at', 'reach out to', 'alternate contact', 'emergency contact']
            for phrase in analysis.key_phrases:
                if any(contact in phrase.lower() for contact in contact_phrases):
                    return True
        
        return False

    def _fallback_result(self, reason: str, start_time: float) -> Dict[str, Any]:
        """Simple fallback result"""
        return {
            'category': 'Manual Review',
            'subcategory': 'Error Handling',
            'confidence': 0.5,
            'method_used': 'fallback',
            'reason': reason,
            'matched_patterns': [],
            'processing_time': time.time() - start_time,
            'timestamp': time.time(),
            'final_label': 'manual_review'
        }

    def debug_classification(self, subject: str, body: str) -> Dict[str, Any]:
        """Simple debug method"""
        print(f"=== DEBUG CLASSIFICATION ===")
        print(f"Subject: {subject[:50]}...")
        print(f"Body length: {len(body)}")
        
        try:
            processed = self.preprocessor.preprocess_email(subject, body)
            print(f"Cleaned text length: {len(processed.cleaned_text)}")
            print(f"Has thread: {processed.has_thread}")
            
            ml_result = self.ml_classifier.classify_email(processed.cleaned_text)
            print(f"ML: {ml_result['category']}/{ml_result.get('subcategory', 'N/A')} (conf: {ml_result['confidence']:.2f})")
            
            rule_result = self.rule_engine.classify_sublabel(
                ml_result['category'], processed.cleaned_text, 
                subject=processed.cleaned_subject
            )
            print(f"Rule: {rule_result.category}/{rule_result.subcategory} (conf: {rule_result.confidence:.2f})")
            
            final_result = self.classify_email(subject, body)
            print(f"Final: {final_result['final_label']}")
            
            return {'ml': ml_result, 'rule': rule_result.__dict__, 'final': final_result}
            
        except Exception as e:
            print(f"ERROR: {e}")
            return {'error': str(e)}
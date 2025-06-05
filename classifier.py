"""
Clean Email Classifier - Aligned with Updated Hierarchy
Properly integrated with all updated components
Removed General (Thank You) and aligned with exact hierarchy
"""

import logging
import time
from typing import Dict, Any, Optional

from email_classifier.preprocessor import EmailPreprocessor
from email_classifier.nlp_utils import NLPProcessor, TextAnalysis
from email_classifier.ml_classifier import MLClassifier
from email_classifier.rule_engine import RuleEngine, RuleResult

logger = logging.getLogger(__name__)

class EmailClassifier:
    """
    Clean Email Classifier aligned with exact hierarchy structure.
    Hybrid approach: Preprocessor → NLP → ML → Rule Engine → Final Classification
    """
    
    # Updated final labels aligned with exact hierarchy
    ALLOWED_LABELS = [
        "manual_review",           # All Manual Review cases
        "no_reply_no_info",        # No Reply without useful info
        "no_reply_with_info",      # No Reply with useful info (entities/references)
        "invoice_request_no_info",         # Invoice Request cases
        "payment_claim_no_proof",  # Payment claims without proof
        "payment_claim_with_proof", # Payment claims with proof/details
        "auto_reply_no_info",      # Auto Reply without contact info
        "auto_reply_with_info",    # Auto Reply with contact info
        "uncategorized"            # Fallback cases
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.preprocessor = EmailPreprocessor()
        self.nlp_processor = NLPProcessor()
        self.ml_classifier = MLClassifier()
        self.rule_engine = RuleEngine()
        self.logger.info("✅ Clean EmailClassifier initialized")

    def classify_email(self, subject: str, body: str, email_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Main classification method - clean hybrid approach.
        Flow: Preprocess → NLP → ML → Rules → Final Label
        """
        start_time = time.time()
        
        try:
            # Step 1: Preprocessing
            processed = self.preprocessor.preprocess_email(subject or "", body)
            if not processed.cleaned_text:
                return self._create_fallback_result("Empty content after preprocessing", start_time)
            
            # Step 2: NLP Analysis
            analysis = None
            try:
                analysis = self.nlp_processor.analyze_text(processed.cleaned_text)
                self.logger.debug(f"NLP extracted {len(analysis.entities)} entities, {len(analysis.topics)} topics")
            except Exception as e:
                self.logger.warning(f"NLP analysis failed: {e}")
            
            # Step 3: ML Classification (lightweight first pass)
            ml_result = None
            try:
                ml_result = self.ml_classifier.classify_email(processed.cleaned_text)
                self.logger.debug(f"ML classified as: {ml_result['category']}/{ml_result['subcategory']}")
            except Exception as e:
                self.logger.warning(f"ML classification failed: {e}")
                ml_result = {
                    'category': 'Manual Review',
                    'subcategory': 'Complex Queries',
                    'confidence': 0.5,
                    'reason': f'ML error: {str(e)}'
                }
            
            # Step 4: Rule Engine Classification (final decision)
            try:
                rule_result = self.rule_engine.classify_sublabel(
                    main_category=ml_result['category'],
                    text=processed.cleaned_text,
                    analysis=analysis,
                    ml_result=ml_result,
                    subject=processed.cleaned_subject
                )
                self.logger.debug(f"Rules classified as: {rule_result.category}/{rule_result.subcategory}")
            except Exception as e:
                self.logger.error(f"Rule engine failed: {e}")
                rule_result = RuleResult(
                    category='Manual Review',
                    subcategory='Complex Queries',
                    confidence=0.4,
                    reason=f'Rule engine error: {str(e)}',
                    matched_rules=['error_fallback']
                )
            
            # Step 5: Create final result
            final_result = self._create_final_result(
                rule_result=rule_result,
                ml_result=ml_result,
                analysis=analysis,
                processed=processed,
                start_time=start_time
            )
            
            # Step 6: Map to standardized final label
            final_label = self._map_to_final_label(rule_result, analysis)
            final_result['final_label'] = final_label
            
            self.logger.info(f"Email {email_id}: {rule_result.category}/{rule_result.subcategory} → {final_label}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Classification pipeline error: {e}")
            return self._create_fallback_result(f"Pipeline error: {str(e)}", start_time)

    def _create_final_result(self, rule_result: RuleResult, ml_result: Dict[str, Any], 
                           analysis: Optional[TextAnalysis], processed, start_time: float) -> Dict[str, Any]:
        """Create comprehensive final result."""
        
        # Determine confidence and method
        if rule_result.confidence >= 0.80:
            method = 'rule_high_confidence'
            confidence = rule_result.confidence
        elif rule_result.confidence >= 0.60 and ml_result.get('confidence', 0) >= 0.50:
            method = 'hybrid_ml_rule'
            confidence = (rule_result.confidence * 0.7) + (ml_result.get('confidence', 0) * 0.3)
        else:
            method = 'rule_based'
            confidence = rule_result.confidence
        
        return {
            # Core classification
            'category': rule_result.category,
            'subcategory': rule_result.subcategory,
            'confidence': round(confidence, 3),
            'method_used': method,
            'reason': rule_result.reason,
            
            # Pattern/rule information
            'matched_patterns': rule_result.matched_rules,
            
            # NLP insights
            'entities': analysis.entities if analysis else [],
            'key_phrases': analysis.key_phrases if analysis else [],
            'topics': analysis.topics if analysis else [],
            'urgency_score': analysis.urgency_score if analysis else 0.0,
            'complexity_score': analysis.complexity_score if analysis else 0.0,
            'action_required': analysis.action_required if analysis else False,
            
            # Processing metadata
            'processing_time': round(time.time() - start_time, 3),
            'timestamp': time.time(),
            'has_thread': processed.has_thread,
            'thread_count': processed.thread_count
        }

    def _map_to_final_label(self, rule_result: RuleResult, analysis: Optional[TextAnalysis]) -> str:
        """
        Map to final standardized labels based on exact hierarchy.
        Updated to match new hierarchy without General (Thank You).
        """
        category = rule_result.category
        subcategory = rule_result.subcategory
        
        # MANUAL REVIEW - All subcategories go to manual_review
        if category == "Manual Review":
            return "manual_review"
        
        # NO REPLY - Check for useful information using entities
        elif category == "No Reply (with/without info)":
            has_useful_info = self._has_useful_info(analysis)
            return "no_reply_with_info" if has_useful_info else "no_reply_no_info"
        
        # INVOICES REQUEST - All go to invoice_request
        elif category == "Invoices Request":
            return "invoice_request_no_info"
        
        # PAYMENTS CLAIM - Based on proof/details
        elif category == "Payments Claim":
            if subcategory == "Claims Paid (No Info)":
                return "payment_claim_no_proof"
            else:  # Payment Details Received or Payment Confirmation
                return "payment_claim_with_proof"
        
        # AUTO REPLY - Check for contact information
        elif category == "Auto Reply (with/without info)":
            has_contact_info = self._has_contact_info(analysis)
            return "auto_reply_with_info" if has_contact_info else "auto_reply_no_info"
        
        # UNCATEGORIZED
        elif category == "Uncategorized":
            return "uncategorized"
        
        # FALLBACK
        else:
            return "manual_review"

    def _has_useful_info(self, analysis: Optional[TextAnalysis]) -> bool:
        """Check if No Reply email contains useful information (entities/references)."""
        if not analysis:
            return False
        
        # Check for business entities
        if analysis.entities:
            useful_entity_types = ['ACCOUNT', 'INVOICE', 'TRANSACTION', 'REFERENCE', 'EMAIL', 'PHONE', 'AMOUNT', 'DATE']
            for entity in analysis.entities:
                if entity.get('label', '').upper() in useful_entity_types:
                    return True
        
        # Check for reference numbers or IDs in key phrases
        if analysis.key_phrases:
            reference_indicators = ['number', 'id', 'reference', 'ticket', 'case', 'account']
            for phrase in analysis.key_phrases:
                if any(indicator in phrase.lower() for indicator in reference_indicators):
                    return True
        
        return False

    def _has_contact_info(self, analysis: Optional[TextAnalysis]) -> bool:
        """Check if Auto Reply contains contact information."""
        if not analysis:
            return False
        
        # Check for contact entities
        if analysis.entities:
            contact_entity_types = ['EMAIL', 'PHONE']
            for entity in analysis.entities:
                if entity.get('label', '').upper() in contact_entity_types:
                    return True
        
        # Check for contact phrases
        if analysis.key_phrases:
            contact_indicators = ['contact me at', 'reach me at', 'alternate contact', 'emergency contact', 'call me']
            for phrase in analysis.key_phrases:
                if any(indicator in phrase.lower() for indicator in contact_indicators):
                    return True
        
        return False

    def _create_fallback_result(self, reason: str, start_time: float) -> Dict[str, Any]:
        """Create fallback result for errors."""
        return {
            'category': 'Manual Review',
            'subcategory': 'Complex Queries',
            'confidence': 0.3,
            'method_used': 'fallback',
            'reason': reason,
            'matched_patterns': ['fallback'],
            'entities': [],
            'key_phrases': [],
            'topics': [],
            'urgency_score': 0.0,
            'complexity_score': 0.0,
            'action_required': False,
            'processing_time': round(time.time() - start_time, 3),
            'timestamp': time.time(),
            'has_thread': False,
            'thread_count': 0,
            'final_label': 'manual_review'
        }

    def debug_classification(self, subject: str, body: str) -> Dict[str, Any]:
        """Debug method to trace classification pipeline."""
        print("=" * 60)
        print("DEBUG EMAIL CLASSIFICATION")
        print("=" * 60)
        print(f"Subject: {subject[:50]}...")
        print(f"Body length: {len(body)} characters")
        
        try:
            # Step 1: Preprocessing
            processed = self.preprocessor.preprocess_email(subject, body)
            print(f"\n1. PREPROCESSING:")
            print(f"   Cleaned text length: {len(processed.cleaned_text)}")
            print(f"   Has thread: {processed.has_thread}")
            print(f"   Thread count: {processed.thread_count}")
            
            # Step 2: NLP Analysis
            analysis = self.nlp_processor.analyze_text(processed.cleaned_text)
            print(f"\n2. NLP ANALYSIS:")
            print(f"   Entities: {len(analysis.entities)}")
            print(f"   Topics: {analysis.topics[:3]}")  # Show first 3 topics
            print(f"   Key phrases: {len(analysis.key_phrases)}")
            print(f"   Urgency: {analysis.urgency_score:.2f}")
            print(f"   Complexity: {analysis.complexity_score:.2f}")
            
            # Step 3: ML Classification
            ml_result = self.ml_classifier.classify_email(processed.cleaned_text)
            print(f"\n3. ML CLASSIFICATION:")
            print(f"   Category: {ml_result['category']}")
            print(f"   Subcategory: {ml_result.get('subcategory', 'N/A')}")
            print(f"   Confidence: {ml_result['confidence']:.2f}")
            
            # Step 4: Rule Engine
            rule_result = self.rule_engine.classify_sublabel(
                ml_result['category'], processed.cleaned_text, 
                analysis=analysis, subject=processed.cleaned_subject
            )
            print(f"\n4. RULE ENGINE:")
            print(f"   Category: {rule_result.category}")
            print(f"   Subcategory: {rule_result.subcategory}")
            print(f"   Confidence: {rule_result.confidence:.2f}")
            print(f"   Reason: {rule_result.reason}")
            
            # Step 5: Final Classification
            final_result = self.classify_email(subject, body)
            print(f"\n5. FINAL RESULT:")
            print(f"   Final label: {final_result['final_label']}")
            print(f"   Method: {final_result['method_used']}")
            print(f"   Processing time: {final_result['processing_time']:.3f}s")
            
            return {
                'preprocessing': {
                    'cleaned_length': len(processed.cleaned_text),
                    'has_thread': processed.has_thread
                },
                'nlp': {
                    'entities': analysis.entities,
                    'topics': analysis.topics,
                    'urgency': analysis.urgency_score,
                    'complexity': analysis.complexity_score
                },
                'ml': ml_result,
                'rules': rule_result.__dict__,
                'final': final_result
            }
            
        except Exception as e:
            print(f"\nERROR: {e}")
            return {'error': str(e)}

    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classifier configuration and stats."""
        return {
            'allowed_labels': self.ALLOWED_LABELS,
            'components': {
                'preprocessor': 'EmailPreprocessor',
                'nlp': 'NLPProcessor', 
                'ml': 'MLClassifier',
                'rules': 'RuleEngine'
            },
            'hierarchy_aligned': True,
            'general_thank_you_removed': True
        }
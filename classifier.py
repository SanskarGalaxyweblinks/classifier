"""
High-Quality Email Classifier - Main Orchestrator
Implements your exact business flow with clean architecture.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import all your components
from email_classifier.preprocessor import EmailPreprocessor
from email_classifier.nlp_utils import NLPProcessor, TextAnalysis
from email_classifier.ml_classifier import MLClassifier
from email_classifier.rule_engine import RuleEngine
from email_classifier.labels import LabelHierarchy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    """Clean result structure for your business logic."""
    category: str
    subcategory: str
    confidence: float
    method_used: str
    reason: str
    matched_patterns: List[str]
    thread_context: Dict[str, Any]
    processing_time: float

class EmailClassifier:
    """
    Main Email Classifier - Orchestrates your entire business flow.
    
    Business Flow:
    Email Input → Preprocessor → NLP Analysis → ML Classification → Rule Engine → Final Result
    """
    
    def __init__(self):
        """Initialize all components - Quality over quantity."""
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize components in order
            self.preprocessor = EmailPreprocessor()
            self.nlp_processor = NLPProcessor()
            self.ml_classifier = MLClassifier()
            self.rule_engine = RuleEngine()
            self.label_hierarchy = LabelHierarchy()
            
            self.logger.info("✅ EmailClassifier initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize EmailClassifier: {e}")
            raise RuntimeError(f"Classifier initialization failed: {e}")

    def classify_email(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Main classification method - implements your exact business logic.
        
        Args:
            subject: Email subject line
            body: Email body content
            
        Returns:
            Complete classification result with all business context
        """
        start_time = time.time()
        
        try:
            # STEP 1: Preprocess (clean text + thread detection)
            self.logger.info("🧹 Starting email preprocessing...")
            processed = self.preprocessor.preprocess_email(subject, body)
            
            if not processed.cleaned_text:
                return self._create_fallback_result("Empty content after preprocessing")
            
            # STEP 2: NLP Analysis (extract business intelligence)
            self.logger.info("🧠 Performing NLP analysis...")
            analysis = self.nlp_processor.analyze_text(processed.cleaned_text)
            
            # STEP 3: ML Classification (get main category + confidence)
            self.logger.info("🤖 Running ML classification...")
            ml_result = self.ml_classifier.classify_email(
                processed.cleaned_text,
                has_thread=processed.has_thread
            )
            
            # STEP 4: Rule Engine (final sublabel assignment)
            self.logger.info("⚡ Applying business rules...")
            rule_result = self.rule_engine.classify_sublabel(
                ml_result['category'],
                processed.cleaned_text,
                analysis=analysis,
                ml_result=ml_result,
                has_thread=processed.has_thread
            )
            
            # STEP 5: Validate and finalize
            final_result = self._finalize_classification(
                ml_result,
                rule_result,
                processed,
                analysis,
                time.time() - start_time
            )
            
            # STEP 6: Update statistics
            self._update_statistics(final_result)
            
            self.logger.info(
                f"✅ Classification complete: {final_result.category}/{final_result.subcategory} "
                f"(confidence: {final_result.confidence:.2f}, time: {final_result.processing_time:.2f}s)"
            )
            
            return self._result_to_dict(final_result)
            
        except Exception as e:
            self.logger.error(f"❌ Classification error: {e}")
            return self._create_fallback_result(f"Error: {e}")

    def _finalize_classification(
        self, 
        ml_result: Dict[str, Any],
        rule_result: Any,
        processed: Any,
        analysis: TextAnalysis,
        processing_time: float
    ) -> ClassificationResult:
        """
        Quality decision logic - combines all inputs intelligently.
        """
        
        # Create thread context
        thread_context = {
            'has_thread': processed.has_thread,
            'thread_count': processed.thread_count,
            'current_reply': len(processed.current_reply) if processed.current_reply else 0
        }
        
        # HIGH QUALITY DECISION LOGIC
        
        # 1. High-confidence rule result (trust it completely)
        if rule_result.confidence >= 0.8:
            return ClassificationResult(
                category=rule_result.category,
                subcategory=rule_result.subcategory,
                confidence=rule_result.confidence,
                method_used="rule_engine_high_confidence",
                reason=f"High-confidence rule match: {rule_result.reason}",
                matched_patterns=rule_result.matched_rules,
                thread_context=thread_context,
                processing_time=processing_time
            )
        
        # 2. Thread emails with ML support
        if processed.has_thread and ml_result['confidence'] >= 0.6:
            combined_confidence = min(
                (ml_result['confidence'] * 0.7) + (rule_result.confidence * 0.3),
                0.95
            )
            return ClassificationResult(
                category=rule_result.category,
                subcategory=rule_result.subcategory,
                confidence=combined_confidence,
                method_used="thread_ml_rule_hybrid",
                reason=f"Thread email with ML+Rule support: {rule_result.reason}",
                matched_patterns=rule_result.matched_rules,
                thread_context=thread_context,
                processing_time=processing_time
            )
        
        # 3. High ML confidence with medium rules
        if ml_result['confidence'] >= 0.7 and rule_result.confidence >= 0.4:
            combined_confidence = (ml_result['confidence'] * 0.6) + (rule_result.confidence * 0.4)
            return ClassificationResult(
                category=rule_result.category,
                subcategory=rule_result.subcategory,
                confidence=combined_confidence,
                method_used="ml_rule_combined",
                reason=f"ML+Rule classification: {rule_result.reason}",
                matched_patterns=rule_result.matched_rules,
                thread_context=thread_context,
                processing_time=processing_time
            )
        
        # 4. Complex/urgent emails go to Manual Review
        if analysis.complexity_score >= 0.7 or analysis.urgency_score >= 0.8:
            return ClassificationResult(
                category="Manual Review",
                subcategory="Complex Queries",
                confidence=0.75,
                method_used="complexity_urgency_escalation",
                reason=f"High complexity ({analysis.complexity_score:.2f}) or urgency ({analysis.urgency_score:.2f})",
                matched_patterns=[],
                thread_context=thread_context,
                processing_time=processing_time
            )
        
        # 5. Medium confidence - use rule result with validation
        if rule_result.confidence >= 0.4:
            # Validate with hierarchy
            if self.label_hierarchy.validate_classification(rule_result.category, rule_result.subcategory):
                return ClassificationResult(
                    category=rule_result.category,
                    subcategory=rule_result.subcategory,
                    confidence=min(rule_result.confidence + 0.1, 0.8),
                    method_used="rule_with_validation",
                    reason=f"Validated rule classification: {rule_result.reason}",
                    matched_patterns=rule_result.matched_rules,
                    thread_context=thread_context,
                    processing_time=processing_time
                )
        
        # 6. Fallback - Manual Review
        return ClassificationResult(
            category="Manual Review",
            subcategory="Complex Queries",
            confidence=0.4,
            method_used="low_confidence_fallback",
            reason="Low confidence across all methods - manual review required",
            matched_patterns=[],
            thread_context=thread_context,
            processing_time=processing_time
        )

    def _update_statistics(self, result: ClassificationResult) -> None:
        """Update classification statistics for monitoring."""
        try:
            self.label_hierarchy.update_usage_statistics(
                result.subcategory,
                result.confidence,
                result.processing_time
            )
        except Exception as e:
            self.logger.error(f"❌ Statistics update failed: {e}")

    def _result_to_dict(self, result: ClassificationResult) -> Dict[str, Any]:
        """Convert result to dictionary for API/external use."""
        return {
            'category': result.category,
            'subcategory': result.subcategory,
            'confidence': result.confidence,
            'method_used': result.method_used,
            'reason': result.reason,
            'matched_patterns': result.matched_patterns,
            'thread_context': result.thread_context,
            'processing_time': result.processing_time,
            'timestamp': time.time()
        }

    def _create_fallback_result(self, reason: str) -> Dict[str, Any]:
        """Create fallback result for errors."""
        fallback_result = ClassificationResult(
            category="Manual Review",
            subcategory="Complex Queries",
            confidence=0.3,
            method_used="error_fallback",
            reason=f"Fallback: {reason}",
            matched_patterns=[],
            thread_context={'has_thread': False, 'thread_count': 0},
            processing_time=0.0
        )
        return self._result_to_dict(fallback_result)

    def classify_batch(self, emails: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        High-quality batch processing for multiple emails.
        
        Args:
            emails: List of {'subject': str, 'body': str} dictionaries
            
        Returns:
            List of classification results
        """
        results = []
        total_emails = len(emails)
        
        self.logger.info(f"📧 Starting batch classification of {total_emails} emails")
        
        for i, email in enumerate(emails, 1):
            try:
                self.logger.info(f"Processing email {i}/{total_emails}")
                
                result = self.classify_email(
                    email.get('subject', ''),
                    email.get('body', '')
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"❌ Error processing email {i}: {e}")
                results.append(self._create_fallback_result(f"Batch processing error: {e}"))
        
        self.logger.info(f"✅ Batch classification complete: {len(results)} results")
        return results

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance and usage statistics."""
        try:
            return {
                'classifier_stats': {
                    'total_classifications': getattr(self.label_hierarchy, 'total_processed', 0),
                    'success_rate': getattr(self.label_hierarchy, 'success_rate', 0.0),
                    'avg_processing_time': getattr(self.label_hierarchy, 'avg_processing_time', 0.0)
                },
                'label_distribution': self.label_hierarchy.get_label_statistics(),
                'hierarchy_validation': self.label_hierarchy.get_hierarchy_stats()
            }
        except Exception as e:
            self.logger.error(f"❌ Failed to get performance stats: {e}")
            return {'error': str(e)}

# Example usage
if __name__ == "__main__":
    # Initialize classifier
    classifier = EmailClassifier()
    
    # Example classification
    sample_email = {
        'subject': 'Payment Confirmation Required',
        'body': 'We need confirmation that payment was received for invoice #12345.'
    }
    
    result = classifier.classify_email(
        sample_email['subject'], 
        sample_email['body']
    )
    
    print(f"Classification Result:")
    print(f"Category: {result['category']}")
    print(f"Subcategory: {result['subcategory']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Method: {result['method_used']}")
    print(f"Reason: {result['reason']}")
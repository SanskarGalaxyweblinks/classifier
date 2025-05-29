"""
High-Quality Email Classifier - Main Orchestrator
MAINTAINS EXACT ORIGINAL OUTPUT FORMAT
"""

import logging
import time
from typing import Dict, List, Optional, Any

# Import all your components
from email_classifier.preprocessor import EmailPreprocessor
from email_classifier.nlp_utils import NLPProcessor, TextAnalysis
from email_classifier.ml_classifier import MLClassifier
from email_classifier.rule_engine import RuleEngine

logger = logging.getLogger(__name__)

class EmailClassifier:
    """
    Main Email Classifier - Orchestrates your entire business flow.
    MAINTAINS EXACT ORIGINAL OUTPUT FORMAT
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
            
            # Performance tracking
            self.stats = {
                'total_processed': 0,
                'successful_classifications': 0,
                'errors': 0,
                'avg_processing_time': 0.0
            }
            
            self.logger.info("✅ EmailClassifier initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize EmailClassifier: {e}")
            raise RuntimeError(f"Classifier initialization failed: {e}")

    def classify_email(self, subject: str, body: str, email_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Main classification method - EXACT ORIGINAL FORMAT OUTPUT
        
        Returns the EXACT format your existing code expects:
        {
            'category': str,
            'subcategory': str, 
            'confidence': float,
            'method_used': str,
            'reason': str,
            'matched_patterns': list,
            'thread_context': dict,
            'processing_time': float,
            'timestamp': float
        }
        """
        start_time = time.time()
        
        try:
            self.stats['total_processed'] += 1
            
            # STEP 1: Preprocess (clean text + thread detection)
            processed = self.preprocessor.preprocess_email(subject, body)
            
            if not processed.cleaned_text:
                return self._create_fallback_result("Empty content after preprocessing", start_time)
            
            # STEP 2: NLP Analysis (extract business intelligence)
            analysis = self.nlp_processor.analyze_text(processed.cleaned_text)
            
            # STEP 3: ML Classification (get main category + confidence)
            ml_result = self.ml_classifier.classify_email(
                processed.cleaned_text,
                has_thread=processed.has_thread
            )
            
            # STEP 4: Rule Engine (final sublabel assignment)
            rule_result = self.rule_engine.classify_sublabel(
                ml_result['category'],
                processed.cleaned_text,
                analysis=analysis,
                ml_result=ml_result,
                has_thread=processed.has_thread
            )
            
            # STEP 5: Create final result in EXACT original format
            final_result = self._create_final_result(
                ml_result,
                rule_result,
                processed,
                analysis,
                time.time() - start_time
            )
            
            # STEP 6: Update statistics
            self._update_statistics(final_result)
            
            self.logger.info(
                f"✅ Email {email_id or 'N/A'}: {final_result['category']}/{final_result['subcategory']} "
                f"(conf: {final_result['confidence']:.2f}, time: {final_result['processing_time']:.3f}s)"
            )
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"❌ Classification error for email {email_id}: {e}")
            self.stats['errors'] += 1
            return self._create_fallback_result(f"Error: {e}", start_time)

    def _create_final_result(
        self, 
        ml_result: Dict[str, Any],
        rule_result: Any,
        processed: Any,
        analysis: TextAnalysis,
        processing_time: float
    ) -> Dict[str, Any]:
        """
        Create final result in EXACT original format your code expects
        """
        
        # Create thread context in exact original format
        thread_context = {
            'has_thread': processed.has_thread,
            'thread_count': getattr(processed, 'thread_count', 0),
            'current_reply': len(processed.current_reply) if hasattr(processed, 'current_reply') and processed.current_reply else 0
        }
        
        timestamp = time.time()
        
        # INTELLIGENT DECISION LOGIC - but output in original format
        
        # 1. High-confidence rule result (trust it completely)
        if rule_result.confidence >= 0.85:
            self.stats['successful_classifications'] += 1
            return {
                'category': rule_result.category,
                'subcategory': rule_result.subcategory,
                'confidence': rule_result.confidence,
                'method_used': "rule_engine_high_confidence",
                'reason': f"High-confidence rule match: {rule_result.reason}",
                'matched_patterns': rule_result.matched_rules,
                'thread_context': thread_context,
                'processing_time': processing_time,
                'timestamp': timestamp
            }
        
        # 2. Thread emails with rule engine priority
        if processed.has_thread:
            final_confidence = min(rule_result.confidence + 0.1, 0.95)
            self.stats['successful_classifications'] += 1
            return {
                'category': rule_result.category,
                'subcategory': rule_result.subcategory,
                'confidence': final_confidence,
                'method_used': "thread_rule_priority",
                'reason': f"Thread email with rule engine priority: {rule_result.reason}",
                'matched_patterns': rule_result.matched_rules,
                'thread_context': thread_context,
                'processing_time': processing_time,
                'timestamp': timestamp
            }
        
        # 3. High ML confidence with rule validation
        if ml_result['confidence'] >= 0.7 and rule_result.confidence >= 0.5:
            combined_confidence = round((ml_result['confidence'] * 0.6) + (rule_result.confidence * 0.4), 2)
            self.stats['successful_classifications'] += 1
            return {
                'category': rule_result.category,
                'subcategory': rule_result.subcategory,
                'confidence': combined_confidence,
                'method_used': "ml_rule_combined",
                'reason': f"ML+Rule classification: {rule_result.reason}",
                'matched_patterns': rule_result.matched_rules,
                'thread_context': thread_context,
                'processing_time': processing_time,
                'timestamp': timestamp
            }
        
        # 4. Complex/urgent emails go to Manual Review
        if analysis.complexity_score >= 0.7 or analysis.urgency_score >= 0.8:
            self.stats['successful_classifications'] += 1
            return {
                'category': "Manual Review",
                'subcategory': "Complex Queries",
                'confidence': 0.75,
                'method_used': "complexity_urgency_escalation",
                'reason': f"High complexity ({analysis.complexity_score:.2f}) or urgency ({analysis.urgency_score:.2f})",
                'matched_patterns': [],
                'thread_context': thread_context,
                'processing_time': processing_time,
                'timestamp': timestamp
            }
        
        # 5. Medium confidence rule result
        if rule_result.confidence >= 0.4:
            final_confidence = min(rule_result.confidence + 0.1, 0.8)
            self.stats['successful_classifications'] += 1
            return {
                'category': rule_result.category,
                'subcategory': rule_result.subcategory,
                'confidence': final_confidence,
                'method_used': "rule_with_validation",
                'reason': f"Validated rule classification: {rule_result.reason}",
                'matched_patterns': rule_result.matched_rules,
                'thread_context': thread_context,
                'processing_time': processing_time,
                'timestamp': timestamp
            }
        
        # 6. ML fallback for edge cases
        if ml_result['confidence'] >= 0.5:
            self.stats['successful_classifications'] += 1
            return {
                'category': ml_result['category'],
                'subcategory': ml_result['subcategory'],
                'confidence': ml_result['confidence'],
                'method_used': "ml_fallback",
                'reason': f"ML fallback classification: {ml_result.get('reason', 'ML classified')}",
                'matched_patterns': ml_result.get('matched_patterns', []),
                'thread_context': thread_context,
                'processing_time': processing_time,
                'timestamp': timestamp
            }
        
        # 7. Final fallback - Manual Review
        return {
            'category': "Manual Review",
            'subcategory': "Complex Queries",
            'confidence': 0.5,
            'method_used': "final_fallback",
            'reason': "Low confidence across all methods - manual review required",
            'matched_patterns': [],
            'thread_context': thread_context,
            'processing_time': processing_time,
            'timestamp': timestamp
        }

    def _update_statistics(self, result: Dict[str, Any]) -> None:
        """Update classification statistics for monitoring."""
        try:
            # Update average processing time
            if self.stats['total_processed'] > 0:
                current_avg = self.stats['avg_processing_time']
                new_avg = ((current_avg * (self.stats['total_processed'] - 1)) + result['processing_time']) / self.stats['total_processed']
                self.stats['avg_processing_time'] = round(new_avg, 4)
        except Exception as e:
            self.logger.error(f"❌ Statistics update failed: {e}")

    def _create_fallback_result(self, reason: str, start_time: float) -> Dict[str, Any]:
        """Create fallback result in EXACT original format."""
        processing_time = time.time() - start_time
        timestamp = time.time()
        
        return {
            'category': "Manual Review",
            'subcategory': "Complex Queries",
            'confidence': 0.3,
            'method_used': "error_fallback",
            'reason': f"Fallback: {reason}",
            'matched_patterns': [],
            'thread_context': {'has_thread': False, 'thread_count': 0, 'current_reply': 0},
            'processing_time': processing_time,
            'timestamp': timestamp
        }

    def classify_batch(self, emails: List[Dict[str, Any]], batch_size: int = 50) -> List[Dict[str, Any]]:
        """
        Batch processing that maintains EXACT original format
        """
        results = []
        total_emails = len(emails)
        
        self.logger.info(f"📧 Starting batch classification of {total_emails} emails")
        
        # Process in batches for better memory management
        for batch_start in range(0, total_emails, batch_size):
            batch_end = min(batch_start + batch_size, total_emails)
            batch = emails[batch_start:batch_end]
            
            self.logger.info(f"Processing batch {(batch_start//batch_size)+1}: emails {batch_start+1}-{batch_end}")
            
            for email in batch:
                try:
                    email_id = email.get('email_id')
                    subject = email.get('subject', '')
                    body = email.get('body', '') or email.get('cleaned_text', '')
                    
                    result = self.classify_email(subject, body, email_id)
                    results.append(result)
                    
                except Exception as e:
                    email_id = email.get('email_id', 'unknown')
                    self.logger.error(f"❌ Error processing email {email_id}: {e}")
                    results.append(self._create_fallback_result(f"Batch processing error: {e}", time.time()))
        
        success_rate = (self.stats['successful_classifications'] / max(self.stats['total_processed'], 1)) * 100
        self.logger.info(f"✅ Batch classification complete: {len(results)} results (success rate: {success_rate:.1f}%)")
        
        return results

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance and usage statistics."""
        try:
            success_rate = (self.stats['successful_classifications'] / max(self.stats['total_processed'], 1)) * 100
            
            base_stats = {
                'classifier_stats': {
                    'total_processed': self.stats['total_processed'],
                    'successful_classifications': self.stats['successful_classifications'],
                    'errors': self.stats['errors'],
                    'success_rate_percent': round(success_rate, 2),
                    'avg_processing_time_ms': round(self.stats['avg_processing_time'] * 1000, 2)
                }
            }
            
            # Add rule engine performance if available
            try:
                base_stats['rule_engine_stats'] = self.rule_engine.get_performance_metrics()
            except:
                pass
            
            return base_stats
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get performance stats: {e}")
            return {
                'error': str(e),
                'basic_stats': self.stats
            }

    def reset_statistics(self) -> None:
        """Reset performance statistics."""
        self.stats = {
            'total_processed': 0,
            'successful_classifications': 0,
            'errors': 0,
            'avg_processing_time': 0.0
        }
        self.logger.info("📊 Statistics reset")

# Example usage and testing
if __name__ == "__main__":
    # Initialize classifier
    classifier = EmailClassifier()
    
    # Example single email classification
    result = classifier.classify_email(
        'Payment Confirmation Required',
        'We need confirmation that payment was received for invoice #12345.',
        email_id=1
    )
    
    print("=== Single Email Classification ===")
    print(f"Category: {result['category']}")
    print(f"Subcategory: {result['subcategory']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Method: {result['method_used']}")
    print(f"Reason: {result['reason']}")
    
    # Example batch processing
    sample_batch = [
        {'email_id': 1, 'subject': 'Payment Made', 'body': 'We have already paid this invoice.'},
        {'email_id': 2, 'subject': 'Invoice Request', 'body': 'Please send us the invoice copy.'},
        {'email_id': 3, 'subject': 'Out of Office', 'body': 'I am out of office until Monday.'}
    ]
    
    batch_results = classifier.classify_batch(sample_batch)
    
    print("\n=== Batch Classification Results ===")
    for result in batch_results:
        print(f"Category: {result['category']}, Subcategory: {result['subcategory']}")
    
    # Performance stats
    stats = classifier.get_performance_stats()
    print(f"\n=== Performance Stats ===")
    print(f"Total Processed: {stats['classifier_stats']['total_processed']}")
    print(f"Success Rate: {stats['classifier_stats']['success_rate_percent']}%")
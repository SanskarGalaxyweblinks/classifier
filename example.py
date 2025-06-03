"""
Clean CSV Email Processor - With Debugging and Error Handling
Works with the simplified EmailClassifier
"""

import csv
import logging
import json
import time
import traceback
from typing import Dict, List, Any
from classifier import EmailClassifier

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CSVEmailProcessor:
    """Clean CSV processor that uses the simplified classifier."""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.classifier = EmailClassifier()
        
        # Set CSV field size limit
        csv.field_size_limit(2147483647)
    
    def debug_single_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Debug a single email to see what's happening"""
        print(f"\n{'='*80}")
        print(f"🔍 DEBUGGING SINGLE EMAIL")
        print(f"{'='*80}")
        print(f"Subject: {subject[:100]}...")
        print(f"Body length: {len(body)} characters")
        print(f"Body preview: {body[:200]}...")
        print(f"{'='*80}")
        
        try:
            # Test each component individually
            print("1️⃣ Testing Preprocessor...")
            processed = self.classifier.preprocessor.preprocess_email(subject, body)
            print(f"   ✅ Cleaned text length: {len(processed.cleaned_text)}")
            print(f"   ✅ Has thread: {processed.has_thread}")
            print(f"   ✅ Thread count: {processed.thread_count}")
            
            print("\n2️⃣ Testing ML Classifier...")
            ml_result = self.classifier.ml_classifier.classify_email(
                processed.cleaned_text, 
                has_thread=processed.has_thread
            )
            print(f"   ✅ ML Result: {ml_result['category']}/{ml_result.get('subcategory', 'N/A')}")
            print(f"   ✅ ML Confidence: {ml_result['confidence']:.2f}")
            
            print("\n3️⃣ Testing NLP Processor...")
            analysis = self.classifier.nlp_processor.analyze_text(processed.cleaned_text)
            print(f"   ✅ NLP Topics: {getattr(analysis, 'topics', [])[:5]}")
            print(f"   ✅ Complexity: {getattr(analysis, 'complexity_score', 0):.2f}")
            
            print("\n4️⃣ Testing Rule Engine...")
            rule_result = self.classifier.rule_engine.classify_sublabel(
                ml_result['category'], 
                processed.cleaned_text,
                analysis=analysis,
                ml_result=ml_result,
                has_thread=processed.has_thread,
                subject=processed.cleaned_subject
            )
            print(f"   ✅ Rule Result: {rule_result.category}/{rule_result.subcategory}")
            print(f"   ✅ Rule Confidence: {rule_result.confidence:.2f}")
            print(f"   ✅ Rule Reason: {rule_result.reason}")
            
            print("\n5️⃣ Testing Full Classification...")
            full_result = self.classifier.classify_email(subject, body, email_id=999)
            print(f"   ✅ Final Category: {full_result['category']}")
            print(f"   ✅ Final Subcategory: {full_result['subcategory']}")
            print(f"   ✅ Final Label: {full_result.get('final_label', 'N/A')}")
            print(f"   ✅ Final Confidence: {full_result['confidence']:.2f}")
            
            print(f"\n{'='*80}")
            print("🎉 DEBUG COMPLETED SUCCESSFULLY!")
            print(f"{'='*80}")
            
            return {
                'success': True,
                'processed': processed,
                'ml_result': ml_result,
                'analysis': analysis,
                'rule_result': rule_result,
                'full_result': full_result
            }
            
        except Exception as e:
            print(f"\n❌ ERROR DURING DEBUG: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}
    
    def process_emails(self) -> List[Dict[str, Any]]:
        """
        Process emails from CSV file using the classifier.
        
        Returns:
            List of classification results
        """
        results = []
        start_time = time.time()
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                # Count total emails for progress tracking
                total_emails = sum(1 for _ in csv_reader)
                file.seek(0)
                next(csv_reader)  # Skip header again
                
                logger.info(f"📧 Starting processing of {total_emails} emails")
                
                for row_num, row in enumerate(csv_reader, 1):
                    try:
                        # Extract email data
                        subject = row.get('subject', '').strip()
                        body = row.get('body', '').strip()
                        
                        if not subject and not body:
                            logger.warning(f"⚠️ Email #{row_num}: Empty subject and body, skipping")
                            continue
                        
                        # Print progress every 10 emails
                        if row_num % 10 == 0 or row_num == 1:
                            logger.info(f"Processing email {row_num}/{total_emails}")
                        
                        # Classify the email with individual error handling
                        try:
                            classification_result = self.classifier.classify_email(
                                subject=subject,
                                body=body,
                                email_id=row_num
                            )
                        except Exception as classify_error:
                            logger.error(f"❌ Classification error for email #{row_num}: {classify_error}")
                            # Create fallback classification result
                            classification_result = {
                                'category': 'Manual Review',
                                'subcategory': 'Complex Queries',
                                'confidence': 0.3,
                                'method_used': 'error_fallback',
                                'reason': f'Classification error: {classify_error}',
                                'matched_patterns': [],
                                'thread_context': {'has_thread': False, 'thread_count': 0, 'current_reply': 0},
                                'processing_time': 0.0,
                                'timestamp': time.time(),
                                'final_label': 'manual_review'
                            }
                        
                        # Get preprocessing info for JSON
                        try:
                            processed_email = self.classifier.preprocessor.preprocess_email(subject, body)
                        except Exception as preprocess_error:
                            logger.error(f"❌ Preprocessing error for email #{row_num}: {preprocess_error}")
                            # Create fallback preprocessing info
                            class FallbackProcessed:
                                def __init__(self):
                                    self.cleaned_text = body[:500] if body else subject
                                    self.has_thread = False
                                    self.thread_count = 0
                                    self.current_reply = ""
                            processed_email = FallbackProcessed()
                        
                        # Store result with enhanced structure
                        results.append({
                            'email_id': row_num,
                            'subject': subject,
                            'cleaned_text': processed_email.cleaned_text,
                            'classification': classification_result,
                            'final_label': classification_result.get('final_label', 'manual_review'),
                            'preprocessing_info': {
                                'has_thread': processed_email.has_thread,
                                'thread_count': getattr(processed_email, 'thread_count', 0),
                                'current_reply_length': len(getattr(processed_email, 'current_reply', ''))
                            }
                        })
                        
                        # Print detailed results for first 5 emails
                        if row_num <= 5:
                            self._print_detailed_result(row_num, subject, classification_result)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing email #{row_num}: {str(e)}")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        results.append({
                            'email_id': row_num,
                            'subject': row.get('subject', ''),
                            'cleaned_text': '',
                            'error': str(e),
                            'classification': {
                                'category': 'Manual Review',
                                'subcategory': 'Complex Queries',
                                'confidence': 0.1,
                                'method_used': 'critical_error',
                                'reason': f'Critical error: {e}',
                                'final_label': 'manual_review'
                            },
                            'final_label': 'manual_review',
                            'preprocessing_info': {
                                'has_thread': False,
                                'thread_count': 0,
                                'current_reply_length': 0
                            }
                        })
                
                # Calculate performance metrics
                total_time = time.time() - start_time
                self._print_summary(results, total_time)
                
                # Save results
                self._save_results(results)
                
                return results
                
        except FileNotFoundError:
            logger.error(f"❌ Could not find CSV file: {self.csv_file_path}")
            return []
        except Exception as e:
            logger.error(f"❌ Error reading CSV file: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _print_detailed_result(self, email_id: int, subject: str, result: Dict[str, Any]) -> None:
        """Print detailed results for debugging."""
        print(f"\n{'='*60}")
        print(f"📧 Email #{email_id}")
        print(f"Subject: {subject[:50]}...")
        print(f"Category: {result['category']}")
        print(f"Subcategory: {result['subcategory']}")
        print(f"Final Label: {result.get('final_label', 'N/A')}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Method: {result['method_used']}")
        print(f"Reason: {result.get('reason', 'N/A')}")
        print(f"Time: {result.get('processing_time', 0):.3f}s")
        
        # Show thread info if present
        if result.get('thread_context', {}).get('has_thread'):
            print(f"Thread: Yes ({result['thread_context']['thread_count']} messages)")
        
        print(f"{'='*60}")
    
    def _print_summary(self, results: List[Dict[str, Any]], total_time: float) -> None:
        """Print processing summary with label distribution."""
        successful = [r for r in results if 'error' not in r]
        errors = len(results) - len(successful)
        
        if successful:
            avg_time = sum(r['classification']['processing_time'] for r in successful) / len(successful)
            avg_confidence = sum(r['classification']['confidence'] for r in successful) / len(successful)
            
            # Calculate label distribution
            label_counts = {}
            for result in successful:
                label = result.get('final_label', 'unknown')
                label_counts[label] = label_counts.get(label, 0) + 1
        else:
            avg_time = avg_confidence = 0
            label_counts = {}
        
        print(f"\n{'='*60}")
        print(f"📊 PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Total Emails: {len(results)}")
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Errors: {errors}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"⏱️  Avg Time/Email: {avg_time:.3f}s")
        print(f"🎯 Avg Confidence: {avg_confidence:.2f}")
        
        if label_counts:
            print(f"\n📋 LABEL DISTRIBUTION:")
            for label, count in sorted(label_counts.items()):
                percentage = (count / len(successful)) * 100
                print(f"   {label}: {count} ({percentage:.1f}%)")
        
        print(f"{'='*60}")
    
    def _save_results(self, results: List[Dict[str, Any]]) -> None:
        """Save results to JSON file with enhanced structure."""
        try:
            # Use timestamp in filename for uniqueness
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_filename = f'classification_results_{timestamp}.json'
            
            # Enhanced structure with summary
            label_summary = {}
            for result in results:
                if 'error' not in result:
                    label = result.get('final_label', 'unknown')
                    label_summary[label] = label_summary.get(label, 0) + 1
            
            output_data = {
                'total_emails': len(results),
                'successful_classifications': len([r for r in results if 'error' not in r]),
                'errors': len([r for r in results if 'error' in r]),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'label_summary': label_summary,
                'results': results
            }
            
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Results saved to: {output_filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")

def main():
    """Main function to run the classifier."""
    csv_file_path = "inbox_emails_20250530_160726.csv"
    
    # Initialize processor
    processor = CSVEmailProcessor(csv_file_path)
    
    # DEBUG: Test first email before processing all
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            first_row = next(csv_reader)
            
            print("🔍 DEBUGGING FIRST EMAIL BEFORE BATCH PROCESSING...")
            debug_result = processor.debug_single_email(
                first_row.get('subject', ''), 
                first_row.get('body', '')
            )
            
            if not debug_result.get('success', False):
                print("❌ Debug failed! Check your classifier configuration.")
                return
            else:
                print("✅ Debug successful! Proceeding with batch processing...")
                
    except Exception as e:
        logger.error(f"❌ Error during debug: {e}")
        print("⚠️ Debug failed, but proceeding with batch processing...")
    
    # Run normal processing
    results = processor.process_emails()
    
    if results:
        logger.info(f"🎉 Processing complete! Classified {len(results)} emails.")
    else:
        logger.error("❌ No emails were processed.")

if __name__ == '__main__':
    main()
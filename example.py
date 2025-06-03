"""
Clean CSV Email Processor - Simplified and Efficient
Works with the simplified EmailClassifier
"""

import csv
import logging
import json
import time
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
                        
                        # Classify the email (this is all you need!)
                        classification_result = self.classifier.classify_email(
                            subject=subject,
                            body=body,
                            email_id=row_num
                        )
                        
                        # Get preprocessing info for JSON (same as your original)
                        processed_email = self.classifier.preprocessor.preprocess_email(subject, body)
                        
                        # Store result with EXACT same structure as your original
                        results.append({
                            'email_id': row_num,
                            'subject': subject,
                            'cleaned_text': processed_email.cleaned_text,
                            'classification': classification_result,
                            'final_label': classification_result.get('final_label', 'manual_review'),  # ← ADD THIS
                            'preprocessing_info': {
                                'has_thread': processed_email.has_thread,
                                'thread_count': processed_email.thread_count,
                                'current_reply_length': len(processed_email.current_reply) if processed_email.current_reply else 0
                            }
                        })
                        
                        # Print detailed results for first 5 emails
                        if row_num <= 5:
                            self._print_detailed_result(row_num, subject, classification_result)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing email #{row_num}: {str(e)}")
                        results.append({
                            'email_id': row_num,
                            'subject': row.get('subject', ''),
                            'cleaned_text': '',
                            'error': str(e),
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
            return []
    
    def _print_detailed_result(self, email_id: int, subject: str, result: Dict[str, Any]) -> None:
        """Print detailed results for debugging."""
        print(f"\n{'='*60}")
        print(f"📧 Email #{email_id}")
        print(f"Subject: {subject[:50]}...")
        print(f"Category: {result['category']}")
        print(f"Subcategory: {result['subcategory']}")
        print(f"Final Label: {result.get('final_label', 'N/A')}")  # ← ADD THIS
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Method: {result['method_used']}")
        print(f"Time: {result['processing_time']:.3f}s")
        
        # Show thread info if present
        if result.get('thread_context', {}).get('has_thread'):
            print(f"Thread: Yes ({result['thread_context']['thread_count']} messages)")
        
        print(f"{'='*60}")
    
    def _print_summary(self, results: List[Dict[str, Any]], total_time: float) -> None:
        """Print processing summary."""
        successful = [r for r in results if 'error' not in r]
        errors = len(results) - len(successful)
        
        if successful:
            avg_time = sum(r['classification']['processing_time'] for r in successful) / len(successful)
            avg_confidence = sum(r['classification']['confidence'] for r in successful) / len(successful)
        else:
            avg_time = avg_confidence = 0
        
        print(f"\n{'='*60}")
        print(f"📊 PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Total Emails: {len(results)}")
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Errors: {errors}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"⏱️  Avg Time/Email: {avg_time:.3f}s")
        print(f"🎯 Avg Confidence: {avg_confidence:.2f}")
        print(f"{'='*60}")
    
    def _save_results(self, results: List[Dict[str, Any]]) -> None:
        """Save results to JSON file with EXACT same structure as original."""
        try:
            # Use same filename format as your original
            output_filename = 'classification_results.json'
            
            # Same structure as your original JSON
            output_data = {
                'total_emails': len(results),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
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
    
    # Initialize processor and run
    processor = CSVEmailProcessor(csv_file_path)
    results = processor.process_emails()
    
    if results:
        logger.info(f"🎉 Processing complete! Classified {len(results)} emails.")
    else:
        logger.error("❌ No emails were processed.")

if __name__ == '__main__':
    main()
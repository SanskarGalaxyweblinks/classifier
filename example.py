"""
Enhanced CSV Email Processor - Supports Thread Logic and New Client Data Structure
Handles: subject,sender,body,received_date,has_attachments,message_id,body_length,data_source,had_threads
"""

import csv
import logging
import json
import time
import os
from typing import Dict, List, Any, Optional
from email_classifier.classifier import EmailClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedCSVEmailProcessor:
    """Enhanced CSV processor supporting thread logic and new client data structure"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.classifier = EmailClassifier()
        csv.field_size_limit(2147483647)
        
        # Validate file exists
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        logger.info(f"✅ Initialized processor for: {csv_file_path}")
    
    def process_emails(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process emails from CSV file with enhanced thread logic support
        
        Args:
            limit: Optional limit on number of emails to process (for testing)
        """
        results = []
        processed_count = 0
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                # Validate required columns
                required_columns = ['subject', 'body']
                optional_columns = ['sender', 'has_attachments', 'had_threads', 'message_id']
                
                available_columns = csv_reader.fieldnames or []
                missing_required = [col for col in required_columns if col not in available_columns]
                
                if missing_required:
                    raise ValueError(f"Missing required columns: {missing_required}")
                
                # Check which optional columns are available
                has_enhanced_data = all(col in available_columns for col in optional_columns)
                logger.info(f"Enhanced data available: {has_enhanced_data}")
                logger.info(f"Available columns: {available_columns}")
                
                for row_num, row in enumerate(csv_reader, 1):
                    if limit and processed_count >= limit:
                        logger.info(f"Reached processing limit: {limit}")
                        break
                    
                    # Extract basic fields
                    subject = row.get('subject', '').strip()
                    body = row.get('body', '').strip()
                    
                    # Skip empty emails
                    if not subject and not body:
                        logger.debug(f"Skipping empty email {row_num}")
                        continue
                    
                    # Extract enhanced fields (with fallbacks)
                    sender = row.get('sender', '').strip()
                    has_attachments = self._parse_boolean(row.get('has_attachments', 'false'))
                    had_threads = self._parse_boolean(row.get('had_threads', 'false'))
                    message_id = row.get('message_id', '').strip()
                    
                    # Process email with enhanced classification
                    try:
                        result = self._classify_enhanced_email(
                            subject=subject,
                            body=body,
                            sender=sender,
                            has_attachments=has_attachments,
                            had_threads=had_threads,
                            email_id=row_num
                        )
                        
                        # Add metadata
                        result.update({
                            'email_id': row_num,
                            'message_id': message_id,
                            'sender': sender,
                            'has_attachments': has_attachments,
                            'had_threads': had_threads,
                            'enhanced_processing': has_enhanced_data
                        })
                        
                        results.append(result)
                        processed_count += 1
                        
                        # Progress logging
                        if processed_count % 50 == 0:
                            logger.info(f"Processed {processed_count} emails")
                            
                    except Exception as e:
                        logger.error(f"Error processing email {row_num}: {e}")
                        results.append(self._create_error_result(row_num, subject, body, str(e)))
                
                # Save results
                self._save_results(results, has_enhanced_data)
                logger.info(f"✅ Successfully processed {len(results)} emails")
                
        except Exception as e:
            logger.error(f"❌ Error reading CSV: {e}")
            raise
        
        return results
    
    def _classify_enhanced_email(self, subject: str, body: str, sender: str, 
                                has_attachments: bool, had_threads: bool, email_id: int) -> Dict[str, Any]:
        """Classify email using enhanced rule engine with thread logic"""
        
        # Get cleaned text from preprocessor
        try:
            processed = self.classifier.preprocessor.preprocess_email(subject, body)
            cleaned_text = processed.cleaned_text
        except Exception as e:
            logger.warning(f"Preprocessing failed for email {email_id}: {e}")
            cleaned_text = body  # Fallback
        
        # Get NLP analysis
        try:
            analysis = self.classifier.nlp_processor.analyze_text(cleaned_text)
        except Exception as e:
            logger.warning(f"NLP analysis failed for email {email_id}: {e}")
            analysis = None
        
        # Get ML classification
        try:
            ml_result = self.classifier.ml_classifier.classify_email(cleaned_text)
        except Exception as e:
            logger.warning(f"ML classification failed for email {email_id}: {e}")
            ml_result = {
                'category': 'Manual Review',
                'subcategory': 'Complex Queries',
                'confidence': 0.5
            }
        
        # Enhanced rule classification with thread logic
        try:
            rule_result = self.classifier.rule_engine.classify_sublabel(
                main_category=ml_result['category'],
                text=cleaned_text,
                analysis=analysis,
                ml_result=ml_result,
                subject=processed.cleaned_subject if 'processed' in locals() else subject,
                had_threads=had_threads,
                has_attachments=has_attachments,
                sender=sender
            )
        except Exception as e:
            logger.error(f"Rule engine failed for email {email_id}: {e}")
            # Fallback rule result
            from email_classifier.rule_engine import RuleResult
            rule_result = RuleResult(
                category='Manual Review',
                subcategory='Complex Queries',
                confidence=0.3,
                reason=f'Rule engine error: {str(e)}',
                matched_rules=['error_fallback']
            )
        
        # Map to final label
        final_label = self.classifier._map_to_final_label(rule_result, analysis)
        
        return {
            'subject': subject,
            'cleaned_text': cleaned_text,
            'final_label': final_label,
            'category': rule_result.category,
            'subcategory': rule_result.subcategory,
            'confidence': rule_result.confidence,
            'method_used': 'enhanced_rule_engine',
            'reason': rule_result.reason,
            'matched_patterns': rule_result.matched_rules,
            'entities': analysis.entities if analysis else [],
            'topics': analysis.topics if analysis else [],
            'urgency_score': analysis.urgency_score if analysis else 0.0,
            'complexity_score': analysis.complexity_score if analysis else 0.0,
            'thread_logic_applied': had_threads,
            'attachment_logic_applied': has_attachments
        }
    
    def _parse_boolean(self, value: str) -> bool:
        """Parse boolean values from CSV (handles various formats)"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value = value.lower().strip()
            return value in ['true', '1', 'yes', 't', 'y']
        
        return False
    
    def _create_error_result(self, email_id: int, subject: str, body: str, error: str) -> Dict[str, Any]:
        """Create error result for failed processing"""
        return {
            'email_id': email_id,
            'subject': subject,
            'cleaned_text': body,
            'final_label': 'manual_review',
            'category': 'Manual Review',
            'subcategory': 'Error Handling',
            'confidence': 0.3,
            'method_used': 'error_fallback',
            'reason': f'Processing error: {error}',
            'matched_patterns': ['error'],
            'entities': [],
            'topics': [],
            'urgency_score': 0.0,
            'complexity_score': 0.0,
            'thread_logic_applied': False,
            'attachment_logic_applied': False,
            'error': error
        }
    
    def _save_results(self, results: List[Dict[str, Any]], has_enhanced_data: bool) -> None:
        """Save results to JSON file with metadata"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'enhanced_results_{timestamp}.json'
        
        # Calculate statistics
        stats = self._calculate_statistics(results)
        
        output_data = {
            'metadata': {
                'timestamp': timestamp,
                'total_emails': len(results),
                'enhanced_data_available': has_enhanced_data,
                'csv_file': os.path.basename(self.csv_file_path),
                'processing_stats': stats
            },
            'results': results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 Results saved to {filename}")
        
        # Print summary
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        print(f"Total emails processed: {len(results)}")
        print(f"Enhanced data available: {has_enhanced_data}")
        for label, count in stats['label_distribution'].items():
            print(f"{label}: {count}")
        print("="*60)
    
    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate processing statistics"""
        label_counts = {}
        thread_counts = {'with_threads': 0, 'without_threads': 0}
        attachment_counts = {'with_attachments': 0, 'without_attachments': 0}
        confidence_sum = 0
        
        for result in results:
            # Label distribution
            label = result.get('final_label', 'unknown')
            label_counts[label] = label_counts.get(label, 0) + 1
            
            # Thread statistics
            if result.get('thread_logic_applied', False):
                thread_counts['with_threads'] += 1
            else:
                thread_counts['without_threads'] += 1
            
            # Attachment statistics
            if result.get('attachment_logic_applied', False):
                attachment_counts['with_attachments'] += 1
            else:
                attachment_counts['without_attachments'] += 1
            
            # Confidence
            confidence_sum += result.get('confidence', 0)
        
        return {
            'label_distribution': label_counts,
            'thread_distribution': thread_counts,
            'attachment_distribution': attachment_counts,
            'average_confidence': round(confidence_sum / len(results), 3) if results else 0
        }
    
    def process_sample(self, n: int = 10) -> List[Dict[str, Any]]:
        """Process a small sample for testing"""
        logger.info(f"🧪 Processing sample of {n} emails for testing")
        return self.process_emails(limit=n)
    
    def debug_email(self, email_id: int) -> Dict[str, Any]:
        """Debug a specific email by ID"""
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row_num, row in enumerate(csv_reader, 1):
                    if row_num == email_id:
                        subject = row.get('subject', '').strip()
                        body = row.get('body', '').strip()
                        
                        print(f"\n🔍 DEBUGGING EMAIL {email_id}")
                        print("="*50)
                        print(f"Subject: {subject[:100]}...")
                        print(f"Body length: {len(body)}")
                        print(f"Has attachments: {row.get('has_attachments', 'N/A')}")
                        print(f"Had threads: {row.get('had_threads', 'N/A')}")
                        print(f"Sender: {row.get('sender', 'N/A')[:50]}...")
                        
                        # Process with debug
                        return self.classifier.debug_classification(subject, body)
                
                raise ValueError(f"Email {email_id} not found")
                
        except Exception as e:
            logger.error(f"Debug failed: {e}")
            return {'error': str(e)}

def main():
    """Main function with enhanced processing"""
    # Update this path to your CSV file
    csv_file = "/Users/gwl/Desktop/new_project/TESTING/new_start/clean_emails_20250604_185156.csv"
    
    try:
        processor = EnhancedCSVEmailProcessor(csv_file)
        
        # Test with sample first
        print("🧪 Testing with sample emails...")
        sample_results = processor.process_sample(5)
        
        if sample_results:
            print("✅ Sample processing successful!")
            
            # Ask user if they want to process all
            user_input = input("\nProcess all emails? (y/n): ").strip().lower()
            if user_input in ['y', 'yes']:
                print("🚀 Processing all emails...")
                all_results = processor.process_emails()
                print(f"✅ Processed {len(all_results)} emails total")
            else:
                print("👍 Sample processing complete")
        else:
            print("❌ Sample processing failed")
            
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")

if __name__ == '__main__':
    main()
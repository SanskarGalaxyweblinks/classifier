"""
Clean CSV Email Processor - Simple and focused
"""

import csv
import logging
import json
import time
from typing import Dict, List, Any
from classifier import EmailClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSVEmailProcessor:
    """Simple CSV processor for email classification"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.classifier = EmailClassifier()
        csv.field_size_limit(2147483647)
    
    def process_emails(self) -> List[Dict[str, Any]]:
        """Process emails from CSV file"""
        results = []
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row_num, row in enumerate(csv_reader, 1):
                    subject = row.get('subject', '').strip()
                    body = row.get('body', '').strip()
                    
                    if not subject and not body:
                        continue
                    
                    # Get cleaned text from preprocessor
                    try:
                        processed = self.classifier.preprocessor.preprocess_email(subject, body)
                        cleaned_text = processed.cleaned_text
                    except Exception as e:
                        logger.warning(f"Preprocessing failed for email {row_num}: {e}")
                        cleaned_text = body  # Fallback to original body
                    
                    # Classify email
                    try:
                        result = self.classifier.classify_email(subject, body, row_num)
                        results.append({
                            'email_id': row_num,
                            'subject': subject,
                            'cleaned_text': cleaned_text,
                            'final_label': result['final_label'],
                            'category': result['category'],
                            'subcategory': result['subcategory'],
                            'confidence': result['confidence']
                        })
                        
                        if row_num % 50 == 0:
                            logger.info(f"Processed {row_num} emails")
                            
                    except Exception as e:
                        logger.error(f"Error processing email {row_num}: {e}")
                        results.append({
                            'email_id': row_num,
                            'subject': subject,
                            'cleaned_text': body,  # Use original as fallback
                            'final_label': 'manual_review',
                            'category': 'Manual Review',
                            'subcategory': 'Error Handling',
                            'confidence': 0.3
                        })
                
                # Save results
                self._save_results(results)
                logger.info(f"Processed {len(results)} emails")
                
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
        
        return results
    
    def _save_results(self, results: List[Dict[str, Any]]) -> None:
        """Save results to JSON file"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'results_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Results saved to {filename}")

def main():
    """Main function"""
    csv_file = "/Users/gwl/Desktop/new_project/TESTING/new_start/clean_emails_20250604_185156.csv"
    processor = CSVEmailProcessor(csv_file)
    results = processor.process_emails()

if __name__ == '__main__':
    main()
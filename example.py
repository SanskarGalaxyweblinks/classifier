"""
Example script to demonstrate the email classification system using real data from CSV.
"""

import csv
import logging
import json
import time
from typing import Dict, List, Any
from classifier import EmailClassifier

# Increase CSV field size limit
csv.field_size_limit(2147483647)  # Set to maximum value

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_csv_emails(csv_file_path: str) -> List[Dict[str, Any]]:
    """
    Process emails from a CSV file using the classifier and save results.
    
    Args:
        csv_file_path: Path to the CSV file containing emails
        
    Returns:
        List of classification results
    """
    classifier = EmailClassifier()
    results = []
    total_time = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            total_emails = sum(1 for _ in csv_reader)  # Count total emails
            file.seek(0)  # Reset file pointer
            next(csv_reader)  # Skip header
            
            for row_num, row in enumerate(csv_reader, 1):
                print(f"\n{'='*80}")
                print(f"Processing Email #{row_num}/{total_emails}")
                print(f"{'='*80}")
                print(f"Subject: {row['subject']}")
                
                try:
                    start_time = time.time()
                    
                    # Get cleaned text from preprocessor
                    processed_email = classifier.preprocessor.preprocess_email(row['subject'], row['body'])
                    cleaned_text = processed_email.cleaned_text
                    
                    # Classify the email using the updated classifier pipeline
                    result = classifier.classify_email(row['subject'], row['body'])
                    
                    # Calculate processing time
                    processing_time = time.time() - start_time
                    total_time += processing_time
                    
                    # Add processing time to result
                    result['processing_time'] = processing_time
                    
                    # Print results
                    print_results(result)
    
                    # Save result with cleaned text
                    results.append({
                        'email_id': row_num,
                        'subject': row['subject'],
                        'cleaned_text': cleaned_text,
                        'classification': result,
                        'preprocessing_info': {
                            'has_thread': processed_email.has_thread,
                            'thread_count': processed_email.thread_count,
                            'current_reply_length': len(processed_email.current_reply) if processed_email.current_reply else 0
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing email #{row_num}: {str(e)}")
                    results.append({
                        'email_id': row_num,
                        'subject': row['subject'],
                        'error': str(e)
                    })
                    continue
        
        # Calculate and print performance metrics
        successful_results = [r for r in results if 'error' not in r]
        avg_time = total_time / len(successful_results) if successful_results else 0
        logger.info(f"\nPerformance Metrics:")
        logger.info(f"Total Emails Processed: {len(results)}")
        logger.info(f"Successful Classifications: {len(successful_results)}")
        logger.info(f"Total Processing Time: {total_time:.2f}s")
        logger.info(f"Average Processing Time: {avg_time:.2f}s")
        
        # Save all results to JSON file
        save_results(results)
        
        return results
        
    except FileNotFoundError:
        logger.error(f"Error: Could not find the CSV file at {csv_file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        return []

def print_results(result: Dict[str, Any]) -> None:
    """
    Print classification results in a formatted way.
    
    Args:
        result: Classification result dictionary
    """
    print("\nClassification Results:")
    print(f"Category: {result['category']}")
    print(f"Subcategory: {result['subcategory']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Method Used: {result['method_used']}")
    print(f"Reason: {result['reason']}")
    print(f"Processing Time: {result.get('processing_time', 0):.2f}s")
    
    if result.get('matched_patterns'):
        print(f"\nMatched Patterns: {', '.join(result['matched_patterns'][:3])}")
    
    if result.get('thread_context'):
        print("\nThread Context:")
        thread = result['thread_context']
        print(f"Has Thread: {thread.get('has_thread', False)}")
        print(f"Thread Count: {thread.get('thread_count', 0)}")
        print(f"Current Reply Length: {thread.get('current_reply', 0)}")

def save_results(results: List[Dict[str, Any]]) -> None:
    """
    Save classification results to JSON file.
    
    Args:
        results: List of classification results
    """
    try:
        with open('classification_results.json', 'w', encoding='utf-8') as out_json:
            json.dump({
                'total_emails': len(results),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'results': results
            }, out_json, ensure_ascii=False, indent=2)
        logger.info(f"\nSaved classification results for {len(results)} emails to classification_results.json")
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")

def main():
    """Main function to run the classifier test."""
    csv_file_path = "new.csv"
    process_csv_emails(csv_file_path)

if __name__ == '__main__':
    main() 
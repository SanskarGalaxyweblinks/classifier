# Advanced Email Classification System

A robust email classification system that combines pattern matching and machine learning approaches to accurately categorize emails.

## Project Structure

```
email_classifier/
├── __init__.py
├── preprocessor.py      # Email preprocessing and cleaning
├── nlp_utils.py        # NLP analysis utilities
├── ml_classifier.py    # ML-based classification
├── rule_engine.py      # Rule-based classification
├── patterns.py         # Pattern matching definitions
└── labels.py          # Label hierarchy management

classifier.py          # Main orchestrator (outside email_classifier folder)
example.py            # Example usage script
requirements.txt      # Project dependencies
```

## Features

- **Advanced Email Preprocessing**
  - HTML parsing and cleaning
  - Text extraction and normalization
  - Thread detection and handling
  - Noise removal and text cleaning

- **Pattern Matching Engine**
  - Comprehensive regex patterns
  - Hierarchical classification
  - Confidence scoring
  - Subcategory support

- **Machine Learning Classification**
  - BART model for zero-shot classification
  - Keyword-based fallback system
  - Confidence threshold handling
  - Multi-label support

- **Rule Engine**
  - Business rule validation
  - Pattern matching integration
  - Thread context analysis
  - Performance metrics tracking

- **Label Hierarchy**
  - Structured category system
  - Validation rules
  - Usage statistics
  - Business rule enforcement

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd email-classifier
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Classification

```python
from classifier import EmailClassifier

# Initialize classifier
classifier = EmailClassifier()

# Classify an email
result = classifier.classify_email(
    subject="Payment Confirmation Required",
    body="We need confirmation that payment was received for invoice #12345."
)

# Access results
print(f"Category: {result['category']}")
print(f"Subcategory: {result['subcategory']}")
print(f"Confidence: {result['confidence']}")
print(f"Method: {result['method_used']}")
```

### Processing CSV Files

```python
from example import process_csv_emails

# Process emails from CSV file
results = process_csv_emails("test.csv")

# Results are automatically saved to classification_results.json
```

## Classification Flow

1. **Preprocessing** (`preprocessor.py`)
   - Cleans HTML and extracts text
   - Detects email threads
   - Removes noise and standardizes format

2. **NLP Analysis** (`nlp_utils.py`)
   - Analyzes text sentiment
   - Extracts entities and key phrases
   - Identifies topics and urgency

3. **ML Classification** (`ml_classifier.py`)
   - Uses BART model for initial classification
   - Falls back to keyword-based classification
   - Provides confidence scores

4. **Rule Engine** (`rule_engine.py`)
   - Applies business rules
   - Validates classifications
   - Handles special cases

5. **Label Hierarchy** (`labels.py`)
   - Validates category assignments
   - Enforces business rules
   - Tracks usage statistics

## Main Categories

- **Manual Review**
  - Payment Confirmation
  - Partial/Disputed Payment
  - Business Closure
  - Complex Queries

- **No Reply**
  - System Notifications
  - Sales Offers
  - Processing Errors
  - Import Failures

- **Invoices Request**
  - Invoice Copies
  - Documentation
  - Information Requests

- **Payments Claim**
  - Claims Paid (No Info)
  - Payment Confirmation
  - Payment Details

- **Auto Reply**
  - Out of Office
  - Thank You Messages
  - Surveys
  - System Generated

## Performance

The system achieves high accuracy through:
- Pattern matching for rule-based cases
- ML classification for complex cases
- Combined approach for improved confidence
- Fallback to manual review for uncertain cases

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
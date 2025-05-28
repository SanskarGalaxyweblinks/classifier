from email_classifier.preprocessor import EmailPreprocessor

def test_preprocessor():
    preprocessor = EmailPreprocessor()
    
    test_cases = [
        # Test 1: Single email with noise
        {
            'input': 'his e-mail originates from outside the organization. Good morning Please send invoices.',
            'expected': 'Good morning Please send invoices.',
            'is_thread': False
        },
        # Test 2: Thread email with invoice request
        {
            'input': '''
From: sender@example.com
Sent: 2024-05-21 09:25 AM
To: recipient@example.com
Subject: Collection Notice

Original Message:
Account# D591167
Amount Due: $7713.00

From: recipient@example.com
Sent: 2024-05-21 10:30 AM
To: sender@example.com
Subject: Re: Collection Notice

Could you please provide invoice copies which are yet to be paid.
''',
            'expected': 'Could you please provide invoice copies which are yet to be paid.',
            'is_thread': True,
            'classification': 'INVOICE_REQUEST'
        },
        # Test 3: Thread email with payment confirmation
        {
            'input': '''
From: sender@example.com
Sent: 2024-05-21 09:25 AM
To: recipient@example.com
Subject: Collection Notice

Original Message:
Account# D591167
Amount Due: $7713.00

From: recipient@example.com
Sent: 2024-05-21 10:30 AM
To: sender@example.com
Subject: Re: Collection Notice

Payment has been sent. Check number 12345.
''',
            'expected': 'Payment has been sent. Check number 12345.',
            'is_thread': True,
            'classification': 'CLAIM_PAID'
        },
        # Test 4: Thread email with dispute
        {
            'input': '''
From: sender@example.com
Sent: 2024-05-21 09:25 AM
To: recipient@example.com
Subject: Collection Notice

Original Message:
Account# D591167
Amount Due: $7713.00

From: recipient@example.com
Sent: 2024-05-21 10:30 AM
To: sender@example.com
Subject: Re: Collection Notice

I dispute this amount. Please provide proof of debt.
''',
            'expected': 'I dispute this amount. Please provide proof of debt.',
            'is_thread': True,
            'classification': 'MANUAL_REVIEW'
        },
        # Test 5: Complex HTML with noise
        {
            'input': '''
            <div>his e-mail originates from outside the organization.</div>
            <p>Please send invoice copies.</p>
            <blockquote>Previous message</blockquote>
            ''',
            'expected': 'Please send invoice copies.',
            'is_thread': False
        },
        # Test 6: Collection Notice
        {
            'input': '''
            <div>Quarantined Email Report</div>
            <p>Account# D591167</p>
            <p>File# 2943185</p>
            <p>Amount Due: $7713.00</p>
            <p>Client: Culligan Quench</p>
            <p>Phone: 555-123-4567</p>
            <p>Email: contact@example.com</p>
            ''',
            'expected': 'Account# D591167 File# 2943185 Amount Due: $7713.00 Client: Culligan Quench Phone: 555-123-4567 Email: contact@example.com'
        },
        # Test 7: Business Correspondence
        {
            'input': '''
            <div>his e-mail originates from outside the organization.</div>
            <p>Dear Vendor,</p>
            <p>Please process the following invoice:</p>
            <p>Invoice #: INV-2024-001</p>
            <p>Amount: $1,234.56</p>
            <p>Due Date: 05/21/2024</p>
            ''',
            'expected': 'Dear Vendor, Please process the following invoice: Invoice #: INV-2024-001 Amount: $1,234.56 Due Date: 05/21/2024'
        }
    ]
    
    print("\nTesting Preprocessor Changes:")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        result = preprocessor.preprocess_email("Test Subject", test['input'])
        print(f"\nTest {i}:")
        print(f"Input: {repr(test['input'])}")
        print(f"Output: {repr(result['current_reply'])}")
        print(f"Expected: {repr(test['expected'])}")
        print(f"Is Thread: {result['is_thread']} (Expected: {test.get('is_thread', False)})")
        if result['is_thread']:
            print(f"Classification: {result['classification']} (Expected: {test.get('classification', 'MANUAL_REVIEW')})")
        print(f"Pass: {result['current_reply'].strip() == test['expected'].strip()}")
        if result.get('collection_info'):
            print(f"Collection Info: {result['collection_info']}")
        print("-" * 50)

if __name__ == "__main__":
    test_preprocessor() 
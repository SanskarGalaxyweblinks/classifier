"""
Clean NLP processor for email classification - aligned with correct hierarchy structure.
"""

import logging
import re
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class TextAnalysis:
    """Main TextAnalysis class used by rule engine."""
    sentiment: float  # -1 to 1
    entities: List[Dict[str, str]]  # List of named entities
    key_phrases: List[str]  # Important phrases
    topics: List[str]  # Main topics aligned with hierarchy
    urgency_score: float  # 0 to 1
    financial_terms: List[str]  # Financial-related terms
    action_required: bool  # Whether action is needed
    complexity_score: float  # 0 to 1

class NLPProcessor:
    """
    Quality NLP processor aligned with exact hierarchy structure.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_hierarchy_patterns()
        self.logger.info("✅ NLP Processor initialized with correct hierarchy")
    
    def _initialize_hierarchy_patterns(self):
        """Initialize patterns aligned with EXACT hierarchy structure - UPDATED with missed patterns."""
        
        # UPDATED: Use EXACT sublabel names from hierarchy + missing patterns from analysis
        self.hierarchy_indicators = {
            # Manual Review sublabels - EXACT NAMES + ENHANCED PATTERNS
            'Partial/Disputed Payment': [
                'partial', 'dispute', 'contested', 'disagreement', 'refuse payment', 'billing error',
                'owe nothing', 'owe them nothing', 'consider this a scam', 'looks like a scam',
                'is this legitimate', 'verify this debt', 'do not acknowledge', 'formally disputing',
                'dispute this debt', 'billing is incorrect', 'not our responsibility', 'cease and desist',
                'fdcpa', 'not properly billed', 'wrong entity', 'debt is disputed',
                'cease and desist letter', 'legal notice', 'fdcpa violation', 'debt validation request',
                'collection agency violation', 'fair debt collection', 'attorney correspondence',
                'legal representation', 'debt collector harassment', 'validation of debt',
                'cease all communication', 'legal action threatened', 'legal counsel representation'
            ],
            'Invoice Receipt': [
                'invoice attached', 'proof of invoice', 'invoice copy attached', 'invoice documentation attached',
                'invoice receipt attached', 'copy of invoice attached for your records',
                'attached invoice as proof', 'here is the invoice copy',
                'payment made in error documentation', 'error payment proof', 'documentation for payment error',
                'proof of payment error', 'attached payment documentation', 'payment error receipt'
            ],
            'Closure Notification': [
                'business closed', 'company closed', 'out of business', 'ceased operations', 'bankruptcy',
                'filed bankruptcy', 'bankruptcy protection', 'chapter 7', 'chapter 11'
            ],
            'Closure + Payment Due': [
                'closure payment due', 'bankruptcy payment', 'closed outstanding payment',
                'business closed outstanding', 'closure with outstanding payment'
            ],
            'External Submission': [
                'invoice issue', 'submission failed', 'import failed', 'unable to import',
                'documents not processed', 'submission unsuccessful', 'error importing invoice',
                'invoice submission failed'
            ],
            'Invoice Errors (format mismatch)': [
                'missing field', 'format mismatch', 'incomplete invoice', 'format error',
                'missing required field', 'invoice format error', 'field missing from invoice'
            ],
            'Inquiry/Redirection': [
                'redirect', 'forward', 'contact instead', 'guidance needed', 'verify legitimate',
                'reach out to', 'please check with', 'insufficient data to research',
                'need guidance', 'please advise', 'what documentation needed',
                'where to send payment', 'what bills', 'what is this for',
                'what are they charging me for', 'backup documentation', 'supporting documents'
            ],
            'Complex Queries': [
                'multiple issues', 'complex situation', 'legal communication', 'settlement',
                'settle for', 'settlement offer', 'negotiate payment', 'attorney',
                'law firm', 'legal counsel', 'legal action',
                'settlement arrangement', 'legal settlement agreement', 'payment settlement',
                'settlement negotiation', 'legal arrangement', 'settlement terms',
                'attorney settlement', 'legal resolution', 'settlement discussion',
                'complex legal matter', 'legal consultation', 'attorney involvement',
                'legal proceedings', 'court settlement', 'mediation settlement',
                'complex business instructions', 'routing instructions', 'complex routing',
                'business process instructions', 'multi step process', 'complex procedure',
                'detailed business process', 'special handling instructions', 'complex workflow'
            ],
            
            # No Reply - EXACT NAMES + ENHANCED PATTERNS
            'Sales/Offers': [
                'sales offer', 'promotion', 'discount', 'special offer',
                'prices increasing', 'price increase', 'limited time offer', 'hours left',
                'sale ending', 'special pricing', 'promotional offer', 'exclusive deal',
                'limited time', 'promotional pricing', 'discount offer',
                'payment plan options', 'payment plan discussion', 'installment plan',
                'payment arrangement offer', 'flexible payment options', 'payment terms discussion',
                'financing options', 'payment schedule options', 'payment plan available',
                'monthly payment plan', 'extended payment terms', 'payment flexibility'
            ],
            'System Alerts': [
                'system alert', 'notification', 'maintenance',
                'system notification', 'automated notification', 'security alert',
                'maintenance notification'
            ],
            'Processing Errors': [
                'processing error', 'failed to process', 'delivery failed',
                'cannot be processed', 'electronic invoice rejected', 'request couldn\'t be created',
                'system unable to process', 'mail delivery failed', 'email bounced'
            ],
            'Business Closure (Info only)': [
                'closure information', 'business closure info',
                'closure notification only'
            ],
            'General (Thank You)': [
                'thank you', 'received your message', 'acknowledgment',
                'thank you for your email', 'thanks for contacting', 'still reviewing',
                'currently reviewing', 'under review', 'we are reviewing', 'for your records'
            ],
            'Created': [
                'ticket created', 'case created', 'new ticket', 'case opened',
                'new ticket opened', 'support request created', 'case has been created',
                'ticket has been opened', 'new case created', 'support ticket opened',
                'case number assigned', 'ticket number assigned', 'new support case',
                'request has been submitted', 'ticket submitted successfully',
                'case opened for review', 'support request received'
            ],
            'Resolved': [
                'ticket resolved', 'case resolved', 'case closed', 'completed',
                'ticket has been resolved', 'marked as resolved', 'status resolved'
            ],
            'Open': [
                'ticket open', 'case open', 'pending',
                'still pending', 'case pending'
            ],
            
            # Invoices Request - EXACT NAME + ENHANCED PATTERNS
            'Request (No Info)': [
                'invoice request', 'need invoice', 'send invoice', 'provide invoice',
                'send me the invoice', 'provide the invoice', 'need invoice copy',
                'outstanding invoices owed', 'copies of any invoices',
                'send invoices that are due', 'provide outstanding invoices'
            ],
            
            # Payments Claim - EXACT NAMES + ENHANCED PATTERNS
            'Claims Paid (No Info)': [
                'already paid', 'payment made', 'check sent', 'we paid',
                'payment was made', 'bill was paid', 'payment was sent', 'payment completed',
                'this was paid', 'account paid', 'made payment', 'been paid',
                'i mailed a check', 'check was mailed'
            ],
            'Payment Confirmation': [
                'see attachments', 'proof attached', 'payment confirmation attached',
                'receipt attached', 'confirmation attached', 'attached payment',
                'invoice was paid see attachments', 'here is proof of payment',
                'payment receipt number', 'wire transfer confirmation',
                'check number', 'transaction id', 'wire confirmation', 'batch number',
                'paid via transaction number', 'ach confirmation number'
            ],
            'Payment Details Received': [
                'payment details', 'payment scheduled', 'payment timeline',
                'payment will be sent', 'payment being processed', 'check will be mailed',
                'in process of issuing payment', 'invoices being processed for payment',
                'will pay this online', 'working on payment', 'need time to pay'
            ],
            
            # Auto Reply - EXACT NAMES + ENHANCED PATTERNS
            'With Alternate Contact': [
                'alternate contact', 'emergency contact', 'contact me at',
                'out of office contact', 'emergency contact number', 'urgent matters contact',
                'immediate assistance contact'
            ],
            'No Info/Autoreply': [
                'out of office', 'automatic reply', 'auto-reply',
                'currently out', 'away from desk', 'on vacation', 'limited access to email',
                'do not reply', 'automated response'
            ],
            'Return Date Specified': [
                'return date', 'back on', 'returning', 'until',
                'out of office until', 'will be back', 'returning on',
                'return to office on', 'back in office on', 'returning to work on',
                'will return on', 'back from vacation on', 'return date is',
                'expected return date', 'returning from leave on', 'back on monday',
                'return on monday', 'back monday', 'return monday', 'back next week',
                'return next week', 'out until friday', 'away until monday',
                'return after holiday', 'back after holiday', 'returning after the holiday'
            ],
            'Survey': [
                'survey', 'feedback', 'questionnaire', 'rate',
                'feedback request', 'rate our service', 'customer satisfaction',
                'take our survey', 'your feedback is important', 'please rate'
            ],
            'Redirects/Updates (property changes)': [
                'property manager', 'contact changed', 'no longer with',
                'no longer employed', 'department changed', 'property manager changed'
            ]
        }

        # Enhanced financial keywords
        self.financial_keywords = {
            'payment_terms': [
                'payment', 'pay', 'paid', 'remittance', 'check', 'wire', 'transfer',
                'settlement', 'eft', 'ach', 'electronic payment', 'credit card payment'
            ],
            'invoice_terms': [
                'invoice', 'bill', 'statement', 'receipt',
                'billing', 'charge', 'fee'
            ],
            'amount_terms': [
                'amount', 'total', 'sum', 'balance', 'due',
                'cost', 'price', 'fee', 'charge'
            ],
            'dispute_terms': [
                'dispute', 'disagreement', 'contested', 'challenge',
                'owe nothing', 'scam', 'not legitimate', 'not our debt', 'refuse payment',
                'cease and desist', 'fdcpa', 'legal action', 'attorney', 'debt validation'
            ],
            'closure_terms': [
                'closed', 'closure', 'terminated', 'ceased', 'dissolved',
                'bankruptcy', 'out of business', 'liquidated'
            ],
            'sales_terms': [
                'price', 'pricing', 'offer', 'deal', 'promotion', 'discount',
                'sale', 'special', 'limited time', 'exclusive', 'payment plan', 'financing'
            ],
            'legal_terms': [
                'attorney', 'lawyer', 'legal counsel', 'law firm', 'settlement',
                'legal action', 'cease and desist', 'fdcpa', 'legal notice', 'court'
            ],
            'error_terms': [
                'error', 'mistake', 'incorrect', 'wrong', 'failed', 'issue', 'problem'
            ],
            'customer_question_terms': [
                'what bills', 'what is this for', 'what are they charging me for',
                'did you receive', 'have you received', 'is there paperwork',
                'what do i owe', 'what am i being charged for'
            ]
        }

        # Customer question indicators (NEW - critical for fixing misclassifications)
        self.customer_question_indicators = {
            'direct_questions': [
                'what bills?', 'what is this for?', 'what are they charging me for?',
                'did you receive my check?', 'have you received payment?',
                'is there any type of paperwork?', 'what do i owe?'
            ],
            'payment_inquiries': [
                'did you receive my check', 'have you received payment',
                'check was mailed', 'i mailed a check', 'payment was sent'
            ],
            'general_inquiries': [
                'what documentation needed', 'where to send payment',
                'backup documentation', 'supporting documents'
            ]
        }

        # Enhanced proof validation indicators
        self.proof_indicators = {
            'providing_proof': [
                'see attachments', 'attached', 'proof attached', 'here is proof', 
                'confirmation attached', 'documentation attached', 'receipt attached',
                'was paid see attachments', 'payment confirmation attached',
                'check number', 'transaction id', 'wire confirmation', 'batch number'
            ],
            'requesting_proof': [
                'send me', 'provide', 'need copy', 'share', 'forward', 'need invoice',
                'provide invoice', 'send invoice', 'copies of invoices'
            ],
            'future_payment_indicators': [
                'will pay', 'going to pay', 'payment will be sent', 'check will be mailed',
                'payment being processed', 'working on payment', 'need time to pay'
            ]
        }

        # Auto-reply subject indicators (NEW - critical for subject-based detection)
        self.auto_reply_subject_indicators = [
            'automatic reply:', 'auto-reply:', 'automatic reply', 'auto reply',
            'out of office:', 'ooo:', 'away message'
        ]

        # Enhanced sentiment indicators
        self.positive_words = [
            'thank', 'good', 'great', 'appreciate', 'excellent', 'pleased', 'satisfied',
            'wonderful', 'fantastic', 'amazing', 'perfect', 'outstanding'
        ]

        self.negative_words = [
            'error', 'issue', 'problem', 'wrong', 'failed', 'dispute', 'concern',
            'scam', 'fraud', 'illegitimate', 'incorrect', 'unacceptable', 'terrible'
        ]

        # Enhanced urgency indicators
        self.urgency_keywords = [
            'urgent', 'immediate', 'asap', 'critical', 'deadline', 'today', 'now', 'quickly',
            'emergency', 'rush', 'priority', 'time sensitive', 'expires'
        ]

        # Enhanced action indicators
        self.action_keywords = [
            'please', 'kindly', 'request', 'need', 'send', 'provide', 'confirm', 'verify',
            'submit', 'forward', 'respond', 'reply', 'contact', 'call', 'email'
        ]

        # Enhanced complexity indicators
        self.complexity_keywords = [
            'multiple', 'various', 'complex', 'detailed', 'several', 'numerous',
            'complicated', 'intricate', 'extensive', 'comprehensive', 'elaborate',
            'settlement', 'legal', 'attorney', 'routing instructions', 'business process'
        ]
    
    def analyze_text(self, text: str) -> TextAnalysis:
        """
        Main analysis method - returns TextAnalysis for rule engine.
        """
        try:
            if not text or not isinstance(text, str):
                return self._get_empty_analysis()
            
            text_lower = text.lower()
            
            # Perform analysis
            sentiment = self._calculate_sentiment(text_lower)
            entities = self._extract_entities(text)
            key_phrases = self._extract_key_phrases(text_lower)
            topics = self._identify_hierarchy_topics(text_lower)
            urgency_score = self._calculate_urgency(text_lower)
            financial_terms = self._extract_financial_terms(text_lower)
            action_required = self._check_action_required(text_lower)
            complexity_score = self._calculate_complexity(text_lower, text)
            
            return TextAnalysis(
                sentiment=sentiment,
                entities=entities,
                key_phrases=key_phrases,
                topics=topics,
                urgency_score=urgency_score,
                financial_terms=financial_terms,
                action_required=action_required,
                complexity_score=complexity_score
            )
            
        except Exception as e:
            self.logger.error(f"NLP analysis error: {e}")
            return self._get_empty_analysis()
    
    def _identify_hierarchy_topics(self, text: str) -> List[str]:
        """Identify topics aligned with EXACT hierarchy structure."""
        topics = []
        
        # Check hierarchy indicators with EXACT sublabel names
        for exact_sublabel, keywords in self.hierarchy_indicators.items():
            if any(keyword in text for keyword in keywords):
                topics.append(exact_sublabel)  # Use exact sublabel name
        
        # Add financial categories (keep these as separate indicators)
        for category, keywords in self.financial_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.append(category)
        
        return list(set(topics))  # Remove duplicates
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score."""
        positive_count = sum(1 for word in self.positive_words if word in text)
        negative_count = sum(1 for word in self.negative_words if word in text)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        return (positive_count - negative_count) / total
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract entities relevant to email classification."""
        entities = []
        
        # Email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({
                'text': email, 
                'label': 'EMAIL', 
                'start': text.find(email), 
                'end': text.find(email) + len(email)
            })
        
        # Account numbers
        accounts = re.findall(r'(?:account|acct)#?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        for account in accounts:
            entities.append({
                'text': account, 
                'label': 'ACCOUNT', 
                'start': text.find(account), 
                'end': text.find(account) + len(account)
            })
        
        # Case/Ticket numbers
        cases = re.findall(r'(?:case|ticket)#?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        for case in cases:
            entities.append({
                'text': case, 
                'label': 'CASE_NUMBER', 
                'start': text.find(case), 
                'end': text.find(case) + len(case)
            })
        
        # Invoice numbers
        invoices = re.findall(r'(?:invoice|inv)#?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        for invoice in invoices:
            entities.append({
                'text': invoice, 
                'label': 'INVOICE_NUMBER', 
                'start': text.find(invoice), 
                'end': text.find(invoice) + len(invoice)
            })
        
        # Transaction numbers
        transactions = re.findall(r'(?:transaction|trans)#?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        for transaction in transactions:
            entities.append({
                'text': transaction,
                'label': 'TRANSACTION_NUMBER',
                'start': text.find(transaction),
                'end': text.find(transaction) + len(transaction)
            })
        
        return entities
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases relevant to classification."""
        key_phrases = []
        
        # Add hierarchy-specific phrases (using exact sublabel names)
        for exact_sublabel, keywords in self.hierarchy_indicators.items():
            for keyword in keywords:
                if keyword in text:
                    key_phrases.append(keyword)
        
        # Add financial terms
        for category, keywords in self.financial_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    key_phrases.append(keyword)
        
        return list(set(key_phrases))[:10]  # Limit to top 10


    def _calculate_urgency(self, text: str) -> float:
        """Calculate urgency score based on keywords."""
        urgency_count = sum(1 for keyword in self.urgency_keywords if keyword in text)
        return min(urgency_count * 0.25, 1.0)
    
    def _extract_financial_terms(self, text: str) -> List[str]:
        """Extract financial terms."""
        financial_terms = []
        
        for category, keywords in self.financial_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    financial_terms.append(keyword)
        
        return list(set(financial_terms))
    
    def _check_action_required(self, text: str) -> bool:
        """Check if action is required based on keywords."""
        return any(keyword in text for keyword in self.action_keywords)
    
    def _calculate_complexity(self, text_lower: str, original_text: str) -> float:
        """Enhanced complexity calculation."""
        complexity_score = 0.0
        
        # Complexity keywords
        complexity_count = sum(1 for keyword in self.complexity_keywords if keyword in text_lower)
        complexity_score += min(complexity_count * 0.15, 0.3)
        
        # Sentence count
        sentences = [s.strip() for s in original_text.split('.') if s.strip()]
        if len(sentences) > 5:
            complexity_score += 0.2
        
        # Word count
        word_count = len(original_text.split())
        if word_count > 200:
            complexity_score += 0.2
        
        # Multiple financial terms
        financial_count = len(self._extract_financial_terms(text_lower))
        if financial_count > 3:
            complexity_score += 0.15
        
        # Multiple hierarchy topics (using exact names)
        hierarchy_topics = [topic for topic in self._identify_hierarchy_topics(text_lower) 
                        if topic in self.hierarchy_indicators]
        if len(hierarchy_topics) > 2:
            complexity_score += 0.15
        
        return min(complexity_score, 1.0)

    def _get_empty_analysis(self) -> TextAnalysis:
        """Return empty analysis for errors or empty input."""
        return TextAnalysis(
            sentiment=0.0,
            entities=[],
            key_phrases=[],
            topics=[],
            urgency_score=0.0,
            financial_terms=[],
            action_required=False,
            complexity_score=0.0
        )

    def get_hierarchy_topics_info(self) -> Dict[str, List[str]]:
        """Get information about available hierarchy topics with EXACT names."""
        return {
            'manual_review_topics': [
                'Partial/Disputed Payment', 'Invoice Receipt', 'Closure Notification',
                'Closure + Payment Due', 'External Submission', 'Invoice Errors (format mismatch)',
                'Inquiry/Redirection', 'Complex Queries'
            ],
            'no_reply_topics': [
                'Sales/Offers', 'System Alerts', 'Processing Errors', 
                'Business Closure (Info only)', 'General (Thank You)',
                'Created', 'Resolved', 'Open'
            ],
            'invoices_request_topics': ['Request (No Info)'],
            'payments_claim_topics': [
                'Claims Paid (No Info)', 'Payment Confirmation', 'Payment Details Received'
            ],
            'auto_reply_topics': [
                'With Alternate Contact', 'No Info/Autoreply', 'Return Date Specified',
                'Survey', 'Redirects/Updates (property changes)'
            ]
        }



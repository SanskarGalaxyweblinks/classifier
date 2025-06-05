"""
Clean NLP Processor for email classification
Lightweight, focused, and efficient for hybrid approach
Removed General (Thank You) and simplified patterns
"""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import unicodedata

logger = logging.getLogger(__name__)

@dataclass
class TextAnalysis:
    """Simple text analysis result for email classification."""
    entities: List[Dict[str, str]]  # Named entities
    key_phrases: List[str]  # Important phrases
    topics: List[str]  # Detected topics
    urgency_score: float  # 0 to 1
    financial_terms: List[str]  # Business terms
    action_required: bool  # Needs action
    complexity_score: float  # 0 to 1

class NLPProcessor:
    """
    Clean NLP processor for hybrid email classification.
    Focused on essential features only.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()
        self._initialize_entities()
        self.logger.info("✅ Clean NLP Processor initialized")

    def _initialize_patterns(self) -> None:
        """Initialize essential patterns aligned with hierarchy - ENHANCED VERSION."""
        
        # Key hierarchy indicators (removed General Thank You)
        self.hierarchy_indicators = {
            
            # === MANUAL REVIEW SUBLABELS ===
            'Partial/Disputed Payment': [
                # Legal dispute patterns
                'formally disputing', 'dispute this debt', 'do not acknowledge', 'owe nothing',
                'owe them nothing', 'consider this a scam', 'looks like a scam', 'billing is incorrect',
                'not our responsibility', 'cease and desist', 'fdcpa violation', 'debt validation',
                'collection agency violation', 'attorney correspondence', 'legal representation',
                'fair debt collection', 'legal action threatened', 'debt collector harassment',
                
                # Dispute intensity patterns
                'contested payment', 'refuse payment', 'challenge payment', 'billing error dispute',
                'not properly billed', 'wrong entity', 'debt is disputed', 'verify this debt',
                
                # ENHANCED: Missing dispute patterns from misclassified emails
                'no record of any charge', 'havent done business with', 'haven\'t done business with',
                'error on your end', 'write off this amount', 'charge is bogus', 'bogus charge',
                'this is an error', 'this is a error', 'dont have record', 'don\'t have record',
                'no knowledge of', 'unaware of this charge', 'researching this charge',
                'never received invoice', 'never received statement', 'no record of',
                'dont owe', 'don\'t owe', 'are not responsible', 'not liable for this',
                'incorrect charge', 'wrong amount', 'billing mistake', 'charge in error',
                
                # CRITICAL ADDITIONS from thread analysis:
                'i don\'t know anything about owing', 'don\'t know anything about owing',
                'i was disputing', 'was disputing', 'disputing with', 'disputing over',
                'minimum settlement amount', 'settlement amount', 'clear the account'
            ],
            
            'Invoice Receipt': [
                # Providing invoice proof patterns
                'invoice receipt attached', 'proof of invoice attached', 'copy of invoice attached',
                'invoice documentation attached', 'here is the invoice copy', 'attached invoice as proof',
                'invoice receipt for your records', 'documentation for payment error',
                'payment made in error documentation', 'error payment proof', 'payment error receipt'
            ],
            
            'Closure Notification': [
                'business closed', 'company closed', 'out of business', 'ceased operations',
                'filed bankruptcy', 'bankruptcy protection', 'chapter 7', 'chapter 11',
                'business shutting down', 'permanently closed', 'company liquidated',
                # ENHANCED: Additional closure patterns
                'filing for bankruptcy', 'going out of business', 'business dissolution',
                'company dissolved', 'operations terminated', 'business terminated'
            ],
            
            'Closure + Payment Due': [
                'business closed outstanding payment', 'closure with outstanding payment',
                'bankruptcy payment due', 'closed but payment owed', 'closure payment required'
            ],
            
            'External Submission': [
                'invoice submission failed', 'import failed', 'unable to import invoice',
                'documents not processed', 'submission unsuccessful', 'error importing invoice',
                'invoice processing failed', 'upload failed', 'system rejected submission'
            ],
            
            'Invoice Errors (format mismatch)': [
                'missing required field', 'format mismatch', 'incomplete invoice', 'invoice format error',
                'field missing from invoice', 'invalid invoice format', 'format requirements not met',
                'invoice template error', 'missing mandatory fields'
            ],
            
            'Inquiry/Redirection': [
                'insufficient data to research', 'need guidance', 'please advise', 'redirect to',
                'contact instead', 'reach out to', 'please check with', 'what documentation needed',
                'where to send payment', 'verify legitimate', 'guidance required', 'need clarification',
                
                # CRITICAL ADDITIONS from thread analysis:
                'i don\'t have an account with', 'what is the servicing address'
            ],
            
            'Complex Queries': [
                'settlement arrangement', 'legal settlement agreement', 'payment settlement',
                'settlement negotiation', 'attorney settlement', 'legal resolution', 'court settlement',
                'complex business instructions', 'routing instructions', 'multi step process',
                'detailed business process', 'special handling instructions', 'complex workflow',
                'attorney involvement', 'legal proceedings', 'mediation settlement'
            ],

            # === NO REPLY SUBLABELS ===
            'Sales/Offers': [
                'special offer', 'limited time offer', 'promotional offer', 'discount offer',
                'exclusive deal', 'prices increasing', 'price increase', 'sale ending', 'hours left',
                'payment plan options', 'payment plan discussion', 'installment plan', 'financing options',
                'flexible payment options', 'payment arrangement offer', 'monthly payment plan'
            ],
            
            'System Alerts': [
                'system notification', 'automated notification', 'system alert', 'maintenance notification',
                'security alert', 'server maintenance', 'system upgrade', 'service disruption'
            ],
            
            'Processing Errors': [
                'processing error', 'failed to process', 'cannot be processed', 'electronic invoice rejected',
                'request couldn\'t be created', 'system unable to process', 'mail delivery failed',
                'email bounced', 'delivery failure', 'system malfunction', 'processing failure'
            ],
            
            'Business Closure (Info only)': [
                'business closure information', 'closure notification only', 'informational closure',
                'closure announcement', 'business will close', 'store closing notice'
            ],
            
            # NOTE: Removed 'General (Thank You)' as requested in hierarchy update
            
            'Created': [
                'ticket created', 'case opened', 'new ticket opened', 'support request created',
                'case has been created', 'ticket submitted successfully', 'case number assigned',
                'support ticket opened', 'request has been submitted', 'case opened for review',
                # ENHANCED: Additional ticket creation patterns
                'case logged', 'ticket logged', 'new case created', 'support case opened'
            ],
            
            'Resolved': [
                'ticket resolved', 'case resolved', 'case closed', 'ticket has been resolved',
                'marked as resolved', 'status resolved', 'case completed', 'issue resolved',
                'request completed', 'ticket closed successfully',
                # ENHANCED: Additional resolution patterns
                'case completed successfully', 'ticket marked complete', 'issue closed'
            ],
            
            'Open': [
                'ticket open', 'case open', 'still pending', 'case pending', 'under investigation',
                'being processed', 'in progress', 'awaiting response',
                # ENHANCED: Additional open status patterns
                'under review', 'being reviewed', 'awaiting information', 'pending review'
            ],

            # === INVOICES REQUEST SUBLABEL ===
            'Request (No Info)': [
                'send me the invoice', 'provide the invoice', 'need invoice copy', 'invoice request',
                'copies of invoices', 'send invoices that are due', 'provide outstanding invoices',
                'forward invoice copy', 'share invoice copy', 'need invoice documentation',
                # ENHANCED: Additional invoice request patterns
                'send invoice copy', 'invoice copy needed', 'need copy of invoice',
                'please send invoice', 'provide invoice copy', 'invoice documentation needed'
            ],

            # === PAYMENTS CLAIM SUBLABELS ===
            'Claims Paid (No Info)': [
                'already paid', 'payment was made', 'we paid', 'bill was paid', 'payment was sent',
                'check was sent', 'payment completed', 'this was paid', 'account paid', 'made payment',
                'been paid', 'payment processed', 'invoice settled',
                # ENHANCED: Additional past payment patterns
                'account was paid', 'invoice was paid', 'bill has been paid', 'we have paid',
                'payment was completed', 'check mailed', 'payment sent', 'balance paid',
                
                # CRITICAL ADDITIONS from thread analysis:
                'i have paid all these bills', 'have paid all', 'paid all these'
            ],
            
            'Payment Details Received': [
                'payment will be sent', 'payment being processed', 'check will be mailed',
                'payment scheduled', 'in process of issuing payment', 'invoices being processed for payment',
                'will pay this online', 'working on payment', 'need time to pay', 'payment in progress',
                
                # ENHANCED: Missing future payment patterns from misclassified emails
                'will make payment from next week', 'can we do the first payment this upcoming',
                'payment this upcoming monday', 'make payment from next', 'going to pay',
                'plan to pay', 'will pay next week', 'payment next week', 'when can we pay',
                'payment is awaiting information', 'payment awaiting information', 'will issue payment',
                'payment will be issued', 'arranging payment', 'scheduling payment',
                'payment arrangement', 'will send payment', 'planning to pay', 'intend to pay',
                
                # Payment issues/help patterns
                'help me for payment', 'payment help', 'payment issue', 'tried to pay',
                'payment error', 'trouble paying', 'cannot pay', 'unable to pay',
                'payment link error', 'error when paying', 'payment not working'
            ],
            
            'Payment Confirmation': [
                'payment confirmation attached', 'proof of payment', 'check number', 'transaction id',
                'eft#', 'wire confirmation', 'batch number', 'here is proof of payment',
                'payment receipt attached', 'invoice was paid see attachments', 'payment verified',
                'paid via transaction number',
                # ENHANCED: Additional proof patterns
                'receipt attached', 'confirmation attached', 'payment receipt', 'bank confirmation',
                'transfer confirmation', 'payment verification', 'proof attached',
                
                # CRITICAL ADDITIONS from thread analysis:
                'sent proof several times', 'sent proof', 'have paid.*and sent proof'
            ],

            # === AUTO REPLY SUBLABELS ===
            'With Alternate Contact': [
                'alternate contact', 'emergency contact number', 'urgent matters contact',
                'immediate assistance contact', 'contact me at', 'reach me at', 'call for urgent',
                'emergency contact information',
                # ENHANCED: Better contact detection patterns
                'please contact', 'please email', 'call me at', 'reach out to',
                'for urgent assistance', 'emergency phone', 'alternate phone',
                'backup contact', 'direct contact', 'personal contact'
            ],
            
            'No Info/Autoreply': [
                'out of office', 'automatic reply', 'auto-reply', 'currently out', 'away from desk',
                'on vacation', 'limited access to email', 'do not reply', 'automated response',
                'currently unavailable',
                # ENHANCED: Missing OOO patterns from misclassified emails
                'attending meetings', 'attending company meetings', 'currently attending',
                'offsite conference', 'away conference', 'out meetings', 'limited email access',
                'no access to email', 'temporarily away', 'away from office',
                'out of the office', 'will be out', 'currently offsite'
            ],
            
            'Return Date Specified': [
                'return on', 'back on', 'returning on', 'will be back on', 'return date is',
                'expected return date', 'back monday', 'return monday', 'back next week',
                'return next week', 'out until', 'away until', 'return after holiday',
                'returning from leave on', 'back from vacation on',
                # ENHANCED: Better return date detection from misclassified emails
                'out from to', 'away from to', 'back on friday', 'return friday',
                'out until monday', 'away until friday', 'back after weekend',
                'return after', 'will be back', 'expected back', 'returning after',
                
                # CRITICAL ADDITIONS from thread analysis:
                'i will be in touch.*next week', 'out of the country', 'away from work'
            ],
            
            'Survey': [
                'survey', 'feedback request', 'rate our service', 'customer satisfaction',
                'take our survey', 'your feedback is important', 'please rate', 'questionnaire',
                'service evaluation', 'feedback form'
            ],
            
            'Redirects/Updates (property changes)': [
                'property manager changed', 'no longer employed', 'contact changed',
                'department changed', 'no longer with company', 'position changed',
                'email address changed', 'contact information updated',
                # ENHANCED: Additional contact change patterns
                'no longer affiliated', 'please remove me', 'unsubscribe me',
                'quit contacting', 'do not contact further', 'contact details changed',
                'management changed', 'new contact person'
            ]
        }
        
        # ENHANCED: Business terms with additional keywords
        self.financial_keywords = {
            'payment': ['payment', 'paid', 'check', 'wire', 'eft', 'transaction', 'transfer', 'remittance'],
            'invoice': ['invoice', 'bill', 'statement', 'billing', 'charges', 'fees'],
            'dispute': ['dispute', 'contested', 'scam', 'fdcpa', 'challenge', 'refuse', 'bogus'],
            'legal': ['attorney', 'lawyer', 'legal', 'settlement', 'court', 'litigation'],
            'closure': ['closed', 'bankruptcy', 'ceased operations', 'liquidated', 'dissolved']
        }
        
        # ENHANCED: Action indicators with additional words
        self.urgency_words = ['urgent', 'immediate', 'asap', 'critical', 'deadline', 'emergency', 'priority']
        self.action_words = ['please', 'need', 'send', 'provide', 'confirm', 'verify', 'forward', 'share']

    def _initialize_entities(self) -> None:
        """Initialize entity patterns."""
        self.entity_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            'account': r'(?:account|acct)#?\s*([A-Z0-9-]{4,})',
            'invoice': r'(?:invoice|inv)#?\s*([A-Z0-9-]{3,})',
            'amount': r'\$[\d,]+\.?\d{0,2}',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'payment_proof': r'(?:receipt|proof).*(?:attached|included)',
            'payment_id': r'(?:payment|ach|transaction)\s+id[:\s]*([A-Z0-9]+)',
            'digits': r'last\s+4\s+digits.*?(\d{4})'
        }

    def analyze_text(self, text: str) -> TextAnalysis:
        """
        Main analysis method - focused and efficient.
        
        Args:
            text: Email content to analyze
            
        Returns:
            TextAnalysis with essential features
        """
        if not text or len(text.strip()) < 5:
            return self._get_empty_analysis()
        
        try:
            text_clean = self._clean_text(text)
            text_lower = text_clean.lower()
            
            # Extract features
            entities = self._extract_entities(text_clean)
            key_phrases = self._extract_key_phrases(text_lower)
            topics = self._identify_topics(text_lower)
            urgency_score = self._calculate_urgency(text_lower)
            financial_terms = self._extract_financial_terms(text_lower)
            action_required = self._check_action_required(text_lower)
            complexity_score = self._calculate_complexity(text_lower)
            
            return TextAnalysis(
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

    def _clean_text(self, text: str) -> str:
        """Simple text cleaning."""
        text = unicodedata.normalize('NFKC', text)
        text = re.sub(r'\s+', ' ', text.strip())
        return text

    def _identify_topics(self, text: str) -> List[str]:
        """Identify topics using hierarchy patterns."""
        topics = []
        
        for topic_name, patterns in self.hierarchy_indicators.items():
            if any(pattern in text for pattern in patterns):
                topics.append(topic_name)
        
        return topics

    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract basic entities."""
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(0),
                    'label': entity_type.upper(),
                    'start': match.start(),
                    'end': match.end()
                })
                if len(entities) >= 10:  # Limit entities
                    break
        
        return entities

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract important phrases."""
        key_phrases = []
        
        # Get hierarchy phrases
        for patterns in self.hierarchy_indicators.values():
            for pattern in patterns:
                if pattern in text:
                    key_phrases.append(pattern)
        
        # Get financial phrases
        for keywords in self.financial_keywords.values():
            for keyword in keywords:
                if keyword in text:
                    key_phrases.append(keyword)
        
        return key_phrases[:10]  # Limit phrases

    def _calculate_urgency(self, text: str) -> float:
        """Calculate urgency score."""
        urgency_count = sum(1 for word in self.urgency_words if word in text)
        return min(urgency_count * 0.3, 1.0)

    def _extract_financial_terms(self, text: str) -> List[str]:
        """Extract financial terms."""
        financial_terms = []
        
        for category, keywords in self.financial_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    financial_terms.append(keyword)
        
        return financial_terms

    def _check_action_required(self, text: str) -> bool:
        """Check if action is required."""
        action_count = sum(1 for word in self.action_words if word in text)
        return action_count >= 2

    def _calculate_complexity(self, text: str) -> float:
        """Calculate complexity score."""
        complexity = 0.0
        
        # Word count factor
        word_count = len(text.split())
        if word_count > 200:
            complexity += 0.3
        elif word_count > 100:
            complexity += 0.2
        
        # Multiple topics
        topics = self._identify_topics(text)
        if len(topics) > 2:
            complexity += 0.3
        
        # Legal terms
        legal_terms = self.financial_keywords['legal']
        if any(term in text for term in legal_terms):
            complexity += 0.2
        
        return min(complexity, 1.0)

    def _get_empty_analysis(self) -> TextAnalysis:
        """Return empty analysis."""
        return TextAnalysis(
            entities=[],
            key_phrases=[],
            topics=[],
            urgency_score=0.0,
            financial_terms=[],
            action_required=False,
            complexity_score=0.0
        )
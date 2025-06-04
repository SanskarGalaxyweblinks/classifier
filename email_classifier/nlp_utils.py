"""
High-Quality NLP Processor for email classification - Exact hierarchy alignment, No thread logic
Focus on accuracy and performance, smart entity extraction and topic identification
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import unicodedata

logger = logging.getLogger(__name__)

# Configuration
MAX_KEY_PHRASES = 15
MAX_ENTITIES = 20
COMPLEXITY_THRESHOLDS = {
    'high': 0.8,
    'medium': 0.6,
    'low': 0.4
}

@dataclass
class TextAnalysis:
    """Comprehensive text analysis result for email classification."""
    sentiment: float  # -1 to 1
    entities: List[Dict[str, str]]  # Named entities with positions
    key_phrases: List[str]  # Important phrases for classification
    topics: List[str]  # Hierarchy-aligned topics
    urgency_score: float  # 0 to 1
    financial_terms: List[str]  # Financial/business terms
    action_required: bool  # Whether action is needed
    complexity_score: float  # 0 to 1

class NLPProcessor:
    """
    Production-grade NLP processor optimized for email classification.
    Exact hierarchy alignment with smart pattern recognition.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_hierarchy_patterns()
        self._initialize_business_indicators()
        self._initialize_entity_patterns()
        self.logger.info("✅ NLP Processor initialized - No thread logic")

    def _initialize_hierarchy_patterns(self) -> None:
        """Initialize patterns perfectly aligned with exact hierarchy structure."""
        
        # EXACT sublabel names with optimized patterns
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
                'not properly billed', 'wrong entity', 'debt is disputed', 'verify this debt'
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
                'business shutting down', 'permanently closed', 'company liquidated'
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
                'where to send payment', 'verify legitimate', 'guidance required', 'need clarification'
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
            
            'General (Thank You)': [
                'thank you for your email', 'thanks for contacting', 'thank you for reaching out',
                'still reviewing', 'currently reviewing', 'under review', 'we are reviewing',
                'for your records', 'acknowledgment received', 'message received'
            ],
            
            'Created': [
                'ticket created', 'case opened', 'new ticket opened', 'support request created',
                'case has been created', 'ticket submitted successfully', 'case number assigned',
                'support ticket opened', 'request has been submitted', 'case opened for review'
            ],
            
            'Resolved': [
                'ticket resolved', 'case resolved', 'case closed', 'ticket has been resolved',
                'marked as resolved', 'status resolved', 'case completed', 'issue resolved',
                'request completed', 'ticket closed successfully'
            ],
            
            'Open': [
                'ticket open', 'case open', 'still pending', 'case pending', 'under investigation',
                'being processed', 'in progress', 'awaiting response'
            ],

            # === INVOICES REQUEST SUBLABEL ===
            'Request (No Info)': [
                'send me the invoice', 'provide the invoice', 'need invoice copy', 'invoice request',
                'copies of invoices', 'send invoices that are due', 'provide outstanding invoices',
                'forward invoice copy', 'share invoice copy', 'need invoice documentation'
            ],

            # === PAYMENTS CLAIM SUBLABELS ===
            'Claims Paid (No Info)': [
                'already paid', 'payment was made', 'we paid', 'bill was paid', 'payment was sent',
                'check was sent', 'payment completed', 'this was paid', 'account paid', 'made payment',
                'been paid', 'payment processed', 'invoice settled'
            ],
            
            'Payment Details Received': [
                'payment will be sent', 'payment being processed', 'check will be mailed',
                'payment scheduled', 'in process of issuing payment', 'invoices being processed for payment',
                'will pay this online', 'working on payment', 'need time to pay', 'payment in progress'
            ],
            
            'Payment Confirmation': [
                'payment confirmation attached', 'proof of payment', 'check number', 'transaction id',
                'eft#', 'wire confirmation', 'batch number', 'here is proof of payment',
                'payment receipt attached', 'invoice was paid see attachments', 'payment verified',
                'paid via transaction number'
            ],

            # === AUTO REPLY SUBLABELS ===
            'With Alternate Contact': [
                'alternate contact', 'emergency contact number', 'urgent matters contact',
                'immediate assistance contact', 'contact me at', 'reach me at', 'call for urgent',
                'emergency contact information'
            ],
            
            'No Info/Autoreply': [
                'out of office', 'automatic reply', 'auto-reply', 'currently out', 'away from desk',
                'on vacation', 'limited access to email', 'do not reply', 'automated response',
                'currently unavailable'
            ],
            
            'Return Date Specified': [
                'return on', 'back on', 'returning on', 'will be back on', 'return date is',
                'expected return date', 'back monday', 'return monday', 'back next week',
                'return next week', 'out until', 'away until', 'return after holiday',
                'returning from leave on', 'back from vacation on'
            ],
            
            'Survey': [
                'survey', 'feedback request', 'rate our service', 'customer satisfaction',
                'take our survey', 'your feedback is important', 'please rate', 'questionnaire',
                'service evaluation', 'feedback form'
            ],
            
            'Redirects/Updates (property changes)': [
                'property manager changed', 'no longer employed', 'contact changed',
                'department changed', 'no longer with company', 'position changed',
                'email address changed', 'contact information updated'
            ]
        }

    def _initialize_business_indicators(self) -> None:
        """Initialize comprehensive business and financial indicators."""
        
        self.financial_keywords = {
            'payment_terms': [
                'payment', 'remittance', 'settlement', 'eft', 'ach', 'wire transfer',
                'electronic payment', 'credit card payment', 'check payment', 'cash payment'
            ],
            'invoice_terms': [
                'invoice', 'bill', 'statement', 'receipt', 'billing', 'charge', 'fee',
                'invoice number', 'billing statement', 'account statement'
            ],
            'amount_terms': [
                'amount', 'total', 'sum', 'balance', 'due', 'cost', 'price', 'fee',
                'charge', 'outstanding', 'owed', 'debt'
            ],
            'dispute_terms': [
                'dispute', 'disagreement', 'contested', 'challenge', 'owe nothing', 'scam',
                'not legitimate', 'refuse payment', 'cease and desist', 'fdcpa', 'legal action',
                'attorney', 'debt validation', 'collection violation'
            ],
            'closure_terms': [
                'closed', 'closure', 'terminated', 'ceased', 'dissolved', 'bankruptcy',
                'out of business', 'liquidated', 'shut down', 'ceased operations'
            ],
            'legal_terms': [
                'attorney', 'lawyer', 'legal counsel', 'law firm', 'settlement', 'legal action',
                'cease and desist', 'fdcpa', 'legal notice', 'court', 'litigation', 'lawsuit'
            ]
        }
        
        # Enhanced sentiment indicators
        self.sentiment_indicators = {
            'positive': [
                'thank', 'appreciate', 'excellent', 'pleased', 'satisfied', 'wonderful',
                'fantastic', 'great', 'good', 'perfect', 'outstanding', 'helpful'
            ],
            'negative': [
                'error', 'issue', 'problem', 'wrong', 'failed', 'dispute', 'concern',
                'scam', 'fraud', 'illegitimate', 'incorrect', 'unacceptable', 'terrible',
                'disappointed', 'frustrated', 'angry'
            ]
        }
        
        # Action and urgency indicators
        self.action_indicators = {
            'urgency': [
                'urgent', 'immediate', 'asap', 'critical', 'deadline', 'today', 'now',
                'quickly', 'emergency', 'rush', 'priority', 'time sensitive', 'expires'
            ],
            'action_required': [
                'please', 'kindly', 'request', 'need', 'send', 'provide', 'confirm',
                'verify', 'submit', 'forward', 'respond', 'reply', 'contact', 'call'
            ],
            'complexity': [
                'multiple', 'various', 'complex', 'detailed', 'several', 'numerous',
                'complicated', 'intricate', 'extensive', 'comprehensive', 'elaborate',
                'settlement', 'legal', 'attorney', 'routing instructions'
            ]
        }

    def _initialize_entity_patterns(self) -> None:
        """Initialize entity extraction patterns."""
        
        self.entity_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            'account': r'(?:account|acct)#?\s*([A-Z0-9-]{4,})',
            'case_ticket': r'(?:case|ticket)#?\s*([A-Z0-9-]{3,})',
            'invoice': r'(?:invoice|inv)#?\s*([A-Z0-9-]{3,})',
            'transaction': r'(?:transaction|trans|eft)#?\s*([A-Z0-9-]{4,})',
            'amount': r'\$[\d,]+\.?\d{0,2}',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'reference': r'(?:ref|reference)#?\s*([A-Z0-9-]{3,})'
        }

    def analyze_text(self, text: str) -> TextAnalysis:
        """
        Main analysis method - comprehensive text analysis for classification.
        
        Args:
            text: Email content to analyze
            
        Returns:
            TextAnalysis object with all extracted features
        """
        if not text or not isinstance(text, str) or len(text.strip()) < 5:
            return self._get_empty_analysis()
        
        try:
            text_normalized = self._normalize_text(text)
            text_lower = text_normalized.lower()
            
            # Core analysis components
            sentiment = self._calculate_sentiment(text_lower)
            entities = self._extract_entities(text_normalized)
            key_phrases = self._extract_key_phrases(text_lower)
            topics = self._identify_hierarchy_topics(text_lower)
            urgency_score = self._calculate_urgency(text_lower)
            financial_terms = self._extract_financial_terms(text_lower)
            action_required = self._check_action_required(text_lower)
            complexity_score = self._calculate_complexity(text_lower, text_normalized)
            
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

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent processing."""
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Replace non-breaking spaces and other whitespace
        text = text.replace('\xa0', ' ')
        text = re.sub(r'[\u200b-\u200f]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()

    def _identify_hierarchy_topics(self, text: str) -> List[str]:
        """Identify topics using exact hierarchy sublabel names."""
        topics = set()
        
        # Primary: Hierarchy indicators (exact sublabel names)
        for exact_sublabel, patterns in self.hierarchy_indicators.items():
            if any(pattern in text for pattern in patterns):
                topics.add(exact_sublabel)
        
        # Secondary: Financial categories
        for category, keywords in self.financial_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.add(category)
        
        return list(topics)

    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score with enhanced accuracy."""
        positive_count = sum(1 for word in self.sentiment_indicators['positive'] if word in text)
        negative_count = sum(1 for word in self.sentiment_indicators['negative'] if word in text)
        
        # Weight by word importance
        positive_weight = positive_count * 1.0
        negative_weight = negative_count * 1.2  # Negative words carry more weight
        
        total_weight = positive_weight + negative_weight
        if total_weight == 0:
            return 0.0
        
        sentiment = (positive_weight - negative_weight) / total_weight
        return max(-1.0, min(1.0, sentiment))

    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract business-relevant entities with position information."""
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = {
                    'text': match.group(0 if entity_type in ['email', 'phone', 'amount', 'date'] else 1),
                    'label': entity_type.upper(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9
                }
                entities.append(entity)
                
                if len(entities) >= MAX_ENTITIES:
                    break
            
            if len(entities) >= MAX_ENTITIES:
                break
        
        return entities

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases relevant to email classification."""
        key_phrases = set()
        
        # Hierarchy-specific phrases (using exact sublabel names)
        for sublabel, patterns in self.hierarchy_indicators.items():
            for pattern in patterns:
                if pattern in text:
                    key_phrases.add(pattern)
        
        # Financial and business phrases
        for category, keywords in self.financial_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    key_phrases.add(keyword)
        
        # Important action phrases
        for category, keywords in self.action_indicators.items():
            for keyword in keywords:
                if keyword in text:
                    key_phrases.add(keyword)
        
        return list(key_phrases)[:MAX_KEY_PHRASES]

    def _calculate_urgency(self, text: str) -> float:
        """Calculate urgency score based on keywords and context."""
        urgency_matches = sum(1 for keyword in self.action_indicators['urgency'] if keyword in text)
        
        # Context boosters
        if 'immediate' in text and any(word in text for word in ['payment', 'response', 'action']):
            urgency_matches += 1
        
        if 'deadline' in text or 'expires' in text:
            urgency_matches += 1
        
        return min(urgency_matches * 0.25, 1.0)

    def _extract_financial_terms(self, text: str) -> List[str]:
        """Extract financial and business terms."""
        financial_terms = set()
        
        for category, keywords in self.financial_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    financial_terms.add(keyword)
        
        return list(financial_terms)

    def _check_action_required(self, text: str) -> bool:
        """Determine if the email requires action based on language patterns."""
        action_count = sum(1 for keyword in self.action_indicators['action_required'] if keyword in text)
        
        # Strong action indicators
        strong_actions = ['please provide', 'need you to', 'must respond', 'require immediate']
        has_strong_action = any(phrase in text for phrase in strong_actions)
        
        return action_count >= 2 or has_strong_action

    def _calculate_complexity(self, text_lower: str, original_text: str) -> float:
        """Enhanced complexity calculation with multiple factors."""
        complexity_score = 0.0
        
        # Complexity keywords
        complexity_keywords = self.action_indicators['complexity']
        complexity_count = sum(1 for keyword in complexity_keywords if keyword in text_lower)
        complexity_score += min(complexity_count * 0.15, 0.35)
        
        # Text length factor
        word_count = len(original_text.split())
        if word_count > 300:
            complexity_score += 0.25
        elif word_count > 150:
            complexity_score += 0.15
        
        # Sentence complexity
        sentences = [s.strip() for s in original_text.split('.') if s.strip()]
        if len(sentences) > 8:
            complexity_score += 0.20
        
        # Multiple financial terms
        financial_count = len(self._extract_financial_terms(text_lower))
        if financial_count > 5:
            complexity_score += 0.20
        
        # Multiple hierarchy topics
        hierarchy_topics = [topic for topic in self._identify_hierarchy_topics(text_lower) 
                          if topic in self.hierarchy_indicators]
        if len(hierarchy_topics) > 3:
            complexity_score += 0.15
        
        # Legal/settlement complexity
        legal_terms = self.financial_keywords['legal_terms']
        legal_count = sum(1 for term in legal_terms if term in text_lower)
        if legal_count > 0:
            complexity_score += 0.10
        
        return min(complexity_score, 1.0)

    def _get_empty_analysis(self) -> TextAnalysis:
        """Return empty analysis for errors or invalid input."""
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

    def get_hierarchy_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of main categories to their sublabels."""
        return {
            'Manual Review': [
                'Partial/Disputed Payment', 'Invoice Receipt', 'Closure Notification',
                'Closure + Payment Due', 'External Submission', 'Invoice Errors (format mismatch)',
                'Inquiry/Redirection', 'Complex Queries'
            ],
            'No Reply (with/without info)': [
                'Sales/Offers', 'System Alerts', 'Processing Errors', 
                'Business Closure (Info only)', 'General (Thank You)',
                'Created', 'Resolved', 'Open'
            ],
            'Invoices Request': ['Request (No Info)'],
            'Payments Claim': [
                'Claims Paid (No Info)', 'Payment Details Received', 'Payment Confirmation'
            ],
            'Auto Reply (with/without info)': [
                'With Alternate Contact', 'No Info/Autoreply', 'Return Date Specified',
                'Survey', 'Redirects/Updates (property changes)'
            ]
        }

    def validate_patterns(self) -> Dict[str, Any]:
        """Validate pattern coverage and consistency."""
        return {
            'total_hierarchy_patterns': len(self.hierarchy_indicators),
            'total_financial_terms': sum(len(terms) for terms in self.financial_keywords.values()),
            'entity_patterns': len(self.entity_patterns),
            'sentiment_indicators': {
                'positive': len(self.sentiment_indicators['positive']),
                'negative': len(self.sentiment_indicators['negative'])
            },
            'action_indicators': {
                category: len(indicators) 
                for category, indicators in self.action_indicators.items()
            }
        }

    def analyze_pattern_coverage(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze how well patterns cover a set of texts."""
        coverage_stats = {
            'total_texts': len(texts),
            'texts_with_topics': 0,
            'texts_with_entities': 0,
            'texts_with_financial_terms': 0,
            'avg_topics_per_text': 0,
            'topic_distribution': {}
        }
        
        all_topics = []
        
        for text in texts:
            analysis = self.analyze_text(text)
            
            if analysis.topics:
                coverage_stats['texts_with_topics'] += 1
                all_topics.extend(analysis.topics)
            
            if analysis.entities:
                coverage_stats['texts_with_entities'] += 1
            
            if analysis.financial_terms:
                coverage_stats['texts_with_financial_terms'] += 1
        
        if texts:
            coverage_stats['avg_topics_per_text'] = len(all_topics) / len(texts)
        
        # Topic distribution
        from collections import Counter
        topic_counts = Counter(all_topics)
        coverage_stats['topic_distribution'] = dict(topic_counts.most_common(10))
        
        return coverage_stats
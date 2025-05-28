"""
Clean NLP utilities for email classification - designed for rule engine integration.
"""

import logging
import re
from typing import Dict, List
from dataclasses import dataclass
from collections import Counter

@dataclass
class TextAnalysis:
    """Main TextAnalysis class used by rule engine."""
    sentiment: float  # -1 to 1
    entities: List[Dict[str, str]]  # List of named entities
    key_phrases: List[str]  # Important phrases
    topics: List[str]  # Main topics aligned with sublabels
    urgency_score: float  # 0 to 1
    financial_terms: List[str]  # Financial-related terms
    action_required: bool  # Whether action is needed
    complexity_score: float  # 0 to 1

class NLPProcessor:
    """
    Quality NLP processor - no external dependencies, uses existing patterns.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_sublabel_patterns()
        self.logger.info("✅ NLP Processor initialized for rule engine")
    
    def _initialize_sublabel_patterns(self):
        """Initialize patterns aligned with your sublabel structure."""
        
        # Sublabel-specific keywords for topic identification
        self.sublabel_indicators = {
            # Manual Review sublabels
            'partial_disputed_payment': ['partial', 'dispute', 'contested', 'disagreement'],
            'payment_confirmation': ['payment confirmation', 'proof of payment', 'payment receipt', 'payment evidence'],
            'invoice_receipt': ['invoice receipt', 'proof of invoice', 'invoice copy', 'invoice attached'],
            'closure_notification': ['business closed', 'company closed', 'out of business', 'ceased operations'],
            'closure_payment_due': ['closed', 'payment due', 'outstanding', 'final payment'],
            'external_submission': ['invoice issue', 'invoice problem', 'invoice concern'],
            'invoice_errors': ['missing field', 'format mismatch', 'incomplete', 'required field'],
            'payment_details_received': ['payment details', 'remittance info', 'payment breakdown'],
            'inquiry_redirection': ['redirect', 'forward', 'contact instead', 'reach out to'],
            'complex_queries': ['multiple', 'various', 'several', 'complex'],
            
            # No Reply sublabels  
            'sales_offers': ['offer', 'promotion', 'discount', 'sale'],
            'processing_errors': ['processing error', 'failed to process', 'processing failed'],
            'import_failures': ['import failed', 'import error', 'failed import'],
            'business_closure_info': ['closure information', 'informing closure'],
            'ticket_created': ['ticket created', 'case opened', 'new ticket', 'case number'],
            'ticket_resolved': ['ticket resolved', 'case closed', 'resolved', 'completed'],
            'ticket_open': ['ticket open', 'case pending', 'still open'],
            
            # Auto Reply sublabels
            'out_of_office': ['out of office', 'away from desk', 'automatic reply'],
            'with_alternate_contact': ['contact', 'reach out', 'alternative'],
            'return_date_specified': ['return', 'back on', 'until'],
            'case_support_confirmation': ['case confirmed', 'support request', 'ticket confirmed'],
            'general_thank_you': ['thank you', 'thanks', 'received your message'],
            'survey': ['survey', 'feedback', 'rate'],
            'redirects_updates': ['property manager', 'contact changed', 'forwarding']
        }
        
        # Financial terms
        self.financial_keywords = {
            'payment': ['payment', 'pay', 'paid', 'remittance', 'check', 'wire'],
            'invoice': ['invoice', 'bill', 'statement', 'receipt'],
            'amount': ['amount', 'total', 'sum', 'balance', 'due'],
            'dispute': ['dispute', 'disagreement', 'contested'],
            'closure': ['closed', 'closure', 'terminated', 'dissolved']
        }
        
        # Sentiment words
        self.positive_words = ['thank', 'good', 'great', 'appreciate', 'excellent', 'pleased']
        self.negative_words = ['error', 'issue', 'problem', 'wrong', 'failed', 'dispute']
        
        # Urgency indicators
        self.urgency_keywords = ['urgent', 'immediate', 'asap', 'critical', 'deadline', 'today', 'now']
        
        # Action indicators
        self.action_keywords = ['please', 'kindly', 'request', 'need', 'send', 'provide']
        
        # Complexity indicators
        self.complexity_keywords = ['multiple', 'various', 'complex', 'detailed', 'if', 'unless']
    
    def analyze_text(self, text: str) -> TextAnalysis:
        """
        Main analysis method - returns TextAnalysis for rule engine.
        """
        try:
            if not text or not isinstance(text, str):
                return self._get_empty_analysis()
            
            text_lower = text.lower()
            
            # Perform all analysis
            sentiment = self._calculate_sentiment(text_lower)
            entities = self._extract_entities(text)
            key_phrases = self._extract_key_phrases(text_lower)
            topics = self._identify_sublabel_topics(text_lower)
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
            self.logger.error(f"❌ NLP analysis error: {e}")
            return self._get_empty_analysis()
    
    def _identify_sublabel_topics(self, text: str) -> List[str]:
        """Identify topics aligned with your sublabel structure."""
        topics = []
        
        # Check sublabel indicators
        for sublabel, keywords in self.sublabel_indicators.items():
            for keyword in keywords:
                if keyword in text:
                    topics.append(sublabel)
                    break  # Only add once per sublabel
        
        # Check financial categories
        for category, keywords in self.financial_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    topics.append(category)
                    break
        
        return list(set(topics))  # Remove duplicates
    
    def _calculate_sentiment(self, text: str) -> float:
        """Simple sentiment calculation."""
        positive_count = sum(1 for word in self.positive_words if word in text)
        negative_count = sum(1 for word in self.negative_words if word in text)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        return (positive_count - negative_count) / total
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract basic entities without external dependencies."""
        entities = []
        
        # Email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({'text': email, 'label': 'EMAIL', 'start': text.find(email), 'end': text.find(email) + len(email)})
        
        # Account numbers
        accounts = re.findall(r'Account#?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        for account in accounts:
            entities.append({'text': account, 'label': 'ACCOUNT', 'start': text.find(account), 'end': text.find(account) + len(account)})
        
        # Case/Ticket numbers
        cases = re.findall(r'(case|ticket).*?#?([A-Z0-9]+)', text, re.IGNORECASE)
        for case_type, case_num in cases:
            entities.append({'text': case_num, 'label': 'CASE_NUMBER', 'start': text.find(case_num), 'end': text.find(case_num) + len(case_num)})
        
        return entities
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases relevant to classification."""
        key_phrases = []
        
        # Add sublabel-specific phrases
        for sublabel, keywords in self.sublabel_indicators.items():
            for keyword in keywords:
                if keyword in text:
                    key_phrases.append(keyword)
        
        # Add financial terms
        for category, keywords in self.financial_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    key_phrases.append(keyword)
        
        return list(set(key_phrases))
    
    def _calculate_urgency(self, text: str) -> float:
        """Calculate urgency score."""
        urgency_score = 0.0
        
        for keyword in self.urgency_keywords:
            if keyword in text:
                urgency_score += 0.2
        
        return min(urgency_score, 1.0)
    
    def _extract_financial_terms(self, text: str) -> List[str]:
        """Extract financial terms as simple list."""
        financial_terms = []
        
        for category, keywords in self.financial_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    financial_terms.append(keyword)
        
        return list(set(financial_terms))
    
    def _check_action_required(self, text: str) -> bool:
        """Check if action is required."""
        return any(keyword in text for keyword in self.action_keywords)
    
    def _calculate_complexity(self, text_lower: str, original_text: str) -> float:
        """Calculate complexity score."""
        complexity_score = 0.0
        
        # Check complexity keywords
        complexity_count = sum(1 for keyword in self.complexity_keywords if keyword in text_lower)
        complexity_score += min(complexity_count * 0.1, 0.3)
        
        # Sentence length
        sentences = original_text.split('.')
        if sentences:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_length > 15:
                complexity_score += 0.2
        
        # Multiple financial terms
        financial_count = len(self._extract_financial_terms(text_lower))
        if financial_count > 2:
            complexity_score += 0.2
        
        # Multiple topics
        topic_count = len(self._identify_sublabel_topics(text_lower))
        if topic_count > 2:
            complexity_score += 0.2
        
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
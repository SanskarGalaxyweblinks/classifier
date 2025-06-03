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
        """Initialize patterns aligned with EXACT hierarchy structure."""
        
        # Hierarchy-aligned topic indicators - CORRECTED
        self.hierarchy_indicators = {
            # Manual Review sublabels
            'partial_disputed_payment': ['partial', 'dispute', 'contested', 'disagreement', 'refuse payment'],
            'invoice_receipt': ['invoice receipt', 'proof of invoice', 'invoice copy', 'invoice documentation'],
            'closure_notification': ['closure notification', 'business closed', 'company closed', 'out of business'],
            'closure_payment_due': ['closure', 'payment due', 'outstanding payment', 'final payment'],
            'external_submission': ['invoice issue', 'invoice error', 'invoice problem', 'submission failed'],
            'invoice_errors_format': ['missing field', 'format mismatch', 'incomplete invoice', 'format error'],
            'inquiry_redirection': ['redirect', 'forward', 'contact instead', 'reach out to'],
            'complex_queries': ['multiple issues', 'various topics', 'complex query'],
            
            # No Reply - Notifications sublabels
            'sales_offers': ['sales offer', 'promotion', 'discount', 'special offer'],
            'system_alerts': ['system alert', 'alert notification', 'system notification'],
            'processing_errors': ['processing error', 'failed to process', 'processing failed'],
            'business_closure_info': ['closure information', 'business closure info', 'closure notice'],
            'general_thank_you': ['thank you', 'thanks', 'received your message', 'acknowledgment'],
            
            # No Reply - Tickets/Cases sublabels  
            'tickets_created': ['ticket created', 'case created', 'new ticket', 'case opened'],
            'tickets_resolved': ['ticket resolved', 'case resolved', 'ticket closed', 'case closed'],
            'tickets_open': ['ticket open', 'case open', 'still pending', 'in progress'],
            
            # Invoices Request sublabel
            'invoice_request_no_info': ['invoice request', 'need invoice', 'send invoice', 'invoice copy'],
                        
            # Payments Claim sublabels - CORRECTED
            'claims_paid_no_info': ['payment made', 'already paid', 'check sent', 'payment completed'],
            'payment_confirmation': ['payment confirmation', 'proof of payment', 'payment receipt', 'payment evidence'],
            'payment_details_received': ['payment details', 'remittance info', 'payment breakdown'],

            # Auto Reply - Out of Office sublabels
            'ooo_alternate_contact': ['alternate contact', 'contact instead', 'reach out to'],
            'ooo_no_info': ['out of office', 'away from desk', 'automatic reply'],
            'ooo_return_date': ['return date', 'back on', 'return', 'until'],
            
            # Auto Reply - Miscellaneous sublabels
            'survey': ['survey', 'feedback', 'questionnaire', 'rate'],
            'redirects_updates': ['property manager', 'contact changed', 'forwarding', 'property changes']
        }
        
        # Financial terms
        self.financial_keywords = {
            'payment': ['payment', 'pay', 'paid', 'remittance', 'check', 'wire', 'transfer'],
            'invoice': ['invoice', 'bill', 'statement', 'receipt'],
            'amount': ['amount', 'total', 'sum', 'balance', 'due'],
            'dispute': ['dispute', 'disagreement', 'contested', 'challenge'],
            'closure': ['closed', 'closure', 'terminated', 'ceased', 'dissolved']
        }
        
        # Sentiment indicators
        self.positive_words = ['thank', 'good', 'great', 'appreciate', 'excellent', 'pleased', 'satisfied']
        self.negative_words = ['error', 'issue', 'problem', 'wrong', 'failed', 'dispute', 'concern']
        
        # Urgency indicators
        self.urgency_keywords = ['urgent', 'immediate', 'asap', 'critical', 'deadline', 'today', 'now', 'quickly']
        
        # Action indicators
        self.action_keywords = ['please', 'kindly', 'request', 'need', 'send', 'provide', 'confirm', 'verify']
        
        # Complexity indicators
        self.complexity_keywords = ['multiple', 'various', 'complex', 'detailed', 'several', 'numerous']
    
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
        """Identify topics aligned with hierarchy structure."""
        topics = []
        
        # Check hierarchy indicators
        for topic, keywords in self.hierarchy_indicators.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)
        
        # Check financial categories
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
        
        # Add hierarchy-specific phrases
        for topic, keywords in self.hierarchy_indicators.items():
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
        """Calculate complexity score."""
        complexity_score = 0.0
        
        # Check complexity keywords
        complexity_count = sum(1 for keyword in self.complexity_keywords if keyword in text_lower)
        complexity_score += min(complexity_count * 0.15, 0.3)
        
        # Check sentence count and length
        sentences = [s.strip() for s in original_text.split('.') if s.strip()]
        if len(sentences) > 5:
            complexity_score += 0.2
        
        # Check word count
        word_count = len(original_text.split())
        if word_count > 200:
            complexity_score += 0.2
        
        # Check multiple financial terms
        financial_count = len(self._extract_financial_terms(text_lower))
        if financial_count > 3:
            complexity_score += 0.2
        
        # Check multiple topics
        topic_count = len(self._identify_hierarchy_topics(text_lower))
        if topic_count > 2:
            complexity_score += 0.1
        
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
        """Get information about available hierarchy topics."""
        return {
            'manual_review_topics': [
                'partial_disputed_payment', 'invoice_receipt', 'closure_notification',
                'closure_payment_due', 'external_submission', 'invoice_errors_format',
                'inquiry_redirection', 'complex_queries'
            ],
            'no_reply_notifications_topics': [
                'sales_offers', 'system_alerts', 'processing_errors', 
                'business_closure_info', 'general_thank_you'
            ],
            'no_reply_tickets_topics': [
                'tickets_created', 'tickets_resolved', 'tickets_open'
            ],
            'invoices_request_topics': ['request_no_info'],
            'payments_claim_topics': [
                'claims_paid_no_info', 'payment_confirmation', 'payment_details_received'
            ],
            'auto_reply_ooo_topics': [
                'with_alternate_contact', 'no_info_autoreply', 'return_date_specified'
            ],
            'auto_reply_misc_topics': ['survey', 'redirects_updates']
        }


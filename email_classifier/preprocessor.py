import re
import logging
import unicodedata
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import html2text
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

# Add multi-line Outlook/Gmail thread block regex
OUTLOOK_THREAD_BLOCK = re.compile(
    r"(^From: .+\n^Sent: .+\n^To: .+\n(^Cc: .+\n)?^Subject: .+$)",
    re.MULTILINE | re.IGNORECASE
)

@dataclass
class ProcessedEmail:
    current_reply: str  # The current reply text (before thread markers)
    has_thread: bool   # Whether the email contains a thread
    thread_count: int  # Number of thread markers found
    cleaned_text: str  # The cleaned text for classification
    cleaned_subject: str  # The cleaned subject line
    original_body: str # The original email body
    processing_time: float = 0.0
    compression_ratio: float = 0.0
    redaction_count: int = 0

class EmailPreprocessor:
    # ====== MINIMAL NOISE PATTERNS (only obvious noise) ======
    NOISE_PATTERNS = [
        r'EXTERNAL:\s*This e-mail originates from outside the organization\.',
        r'Learn why this is important',
        r'\[Learn why this is important\]',
        r'https://aka\.ms/LearnAboutSenderIdentification',

        # Microsoft banner patterns - COMPLETE REMOVAL
        r'This is the first time you received an email from this sender \([^)]+\)\.',
        r'Exercise caution when clicking links, opening attachments or taking further action, before validating its authenticity\.',
        r'Some people who received this message don\'t often get email from [^.]+\.',
        
        # Only remove standalone email headers (not content)
        r'^From:\s*[^\n]*$',
        r'^To:\s*[^\n]*$',
        r'^Sent:\s*[^\n]*$', 
        r'^Date:\s*[^\n]*$',
        r'^Subject:\s*[^\n]*$',
        
        # Reference tracking
        r'Ref:MSG[A-Za-z0-9]+',

        # [OPTIONAL] Legal disclaimers
        # r'The information transmitted \(including attachments\) is covered by the Electronic Communications Privacy Act.*',
        # r'Confidentiality Notice:.*',
        # r'If you received this in error, please contact the sender.*'
    ]

    # ====== STRONG THREAD SEPARATORS (for cutting threads) ======
    THREAD_SEPARATORS = [
        r'From:\s*ABCCollectionsTeamD@abc-amega\.com',
        r'-----Original Message-----',
        r'Dear Accounts Payable:\s*Your Company has been referred to us',
        r'-{5,}\s*Forwarded message\s*-{5,}',
        r'From:\s*[^\n]+@[^\n]+\s*Sent:\s*[^\n]+\s*To:\s*[^\n]+\s*Subject:',
        r'Od:\s*[^\n]+@[^\n]+\s*Wysłano:\s*[^\n]+\s*Do:\s*[^\n]+\s*Temat:',
        r'From:\s*[^\n]+\s*Sent:\s*\w+,\s+\w+\s+\d{1,2},\s+\d{4}',
        r'External email\.\s*Think before clicking',
        r'Think before clicking links or opening attachments',
    ]

    # ====== THREAD INDICATORS (for detection only) ======
    THREAD_INDICATORS = [
        r'From:.*?Sent:.*?To:',
        r'From:.*ABCCollectionsTeamD',
        r'On\s+\w+.*?wrote:',
        r'Dear.*?Your Company has been referred to us',
        r'External email\.\s*Think before clicking',
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.ignore_tables = True
        
        # Compile patterns for performance
        self.compiled_noise_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE) 
            for p in self.NOISE_PATTERNS
        ]
        
        self.compiled_thread_separators = [
            re.compile(p, re.IGNORECASE | re.MULTILINE) 
            for p in self.THREAD_SEPARATORS
        ]
        
        logger.info("Initialized EmailPreprocessor")

    def preprocess_email(self, subject: str, body: str) -> ProcessedEmail:
        """Preprocess email by cleaning and extracting actionable text."""
        start_time = time.time()
        original_length = len(body)
        
        try:
            original_body = body
            
            # Convert HTML to text if needed
            if self._is_html(body):
                body = self._convert_html_to_text(body)
                logger.info("Converted HTML to text")
            
            # Clean subject
            cleaned_subject = self._clean_subject(subject)
            logger.info(f"Cleaned subject: {cleaned_subject}")
            
            # Extract current reply (for thread detection and current_reply field)
            current_reply = self._extract_current_reply(body)
            logger.info(f"Extracted current reply (length: {len(current_reply)})")
            
            # MAIN CHANGE: Clean the FULL BODY, not just current reply
            # This preserves complete email content for classification and DB updates
            cleaned_text = self._clean_full_body(body)
            
            # SAFETY CHECK: Ensure we have substantial content
            if len(cleaned_text.strip()) < 50:
                logger.warning("Cleaned text too short, using minimal cleaning")
                cleaned_text = self._minimal_clean(body)
            
            logger.info(f"Final cleaned text (length: {len(cleaned_text)}):\n{cleaned_text[:500]}...")
            
            # Detect thread
            has_thread, thread_count = self._detect_thread(body)
            logger.info(f"Thread detection: has_thread={has_thread}, count={thread_count}")
            
            # Calculate metrics
            processing_time = time.time() - start_time
            compression_ratio = len(cleaned_text) / original_length if original_length > 0 else 0
            
            return ProcessedEmail(
                current_reply=current_reply,
                has_thread=has_thread,
                thread_count=thread_count,
                cleaned_text=cleaned_text,  # This is the FULL BODY now
                cleaned_subject=cleaned_subject,
                original_body=original_body,
                processing_time=processing_time,
                compression_ratio=compression_ratio,
                redaction_count=0  # No redaction for DB purposes
            )
            
        except Exception as e:
            logger.error(f"Error preprocessing email: {str(e)}")
            return ProcessedEmail(
                current_reply="",
                has_thread=False,
                thread_count=0,
                cleaned_text="",
                cleaned_subject=subject,
                original_body=body,
                processing_time=time.time() - start_time,
                compression_ratio=0.0,
                redaction_count=0
            )

    def _convert_html_to_text(self, html: str) -> str:
        """Convert HTML to plain text - CONTENT PRESERVING VERSION."""
        try:
            logger.info(f"Original HTML length: {len(html)}")
            
            soup = BeautifulSoup(html, 'html.parser')
            logger.info(f"After BeautifulSoup parsing: {len(str(soup))}")
            
            # ONLY remove truly unwanted elements
            for element in soup(["script", "style"]):
                element.decompose()
            
            # Remove 1x1 tracking pixels only
            for img in soup.find_all('img'):
                width = img.get('width')
                height = img.get('height')
                if width == '1' and height == '1':
                    img.decompose()
            
            logger.info(f"After removing unwanted elements: {len(str(soup))}")
            
            # Get text content - PRESERVE EVERYTHING
            text = soup.get_text(separator='\n', strip=True)
            logger.info(f"After get_text: {len(text)}")
            
            # Minimal normalization
            text = self._normalize_text(text)
            
            # Remove only obvious HTML artifacts
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'&[a-zA-Z]+;', ' ', text)
            text = re.sub(r'&#\d+;', ' ', text)
            
            logger.info(f"Final converted text length: {len(text)}")
            return text
            
        except Exception as e:
            logger.error(f"Error converting HTML to text: {str(e)}")
            # FALLBACK: Just strip HTML tags
            fallback = re.sub(r'<[^>]+>', ' ', html)
            return re.sub(r'\s+', ' ', fallback).strip()

    def _normalize_text(self, text: str) -> str:
        """Normalize text by handling special characters and whitespace."""
        text = text.replace('\xa0', ' ')
        text = re.sub(r'[\u200b-\u200f]', '', text)
        text = unicodedata.normalize('NFKC', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()

    def _detect_thread(self, text: str) -> Tuple[bool, int]:
        """Conservative thread detection."""
        all_indicators = self.THREAD_SEPARATORS + self.THREAD_INDICATORS
        
        count = 0
        for indicator in all_indicators:
            if re.search(indicator, text, re.IGNORECASE | re.DOTALL):
                count += 1
                logger.info(f"Found thread indicator: {indicator[:50]}...")
        
        return count > 0, count

    def _extract_current_reply(self, text: str) -> str:
        """Extract current message for current_reply field."""
        logger.info(f"Starting current reply extraction. Text length: {len(text)}")
        
        # Priority: Outlook/Gmail block, then other patterns
        match = OUTLOOK_THREAD_BLOCK.search(text)
        if match:
            content_before = text[:match.start()].strip()
            if len(content_before) >= 50:
                logger.info(f"Found Outlook thread block, extracted current reply")
                return content_before
            else:
                logger.info(f"Outlook thread block found but content too short, keeping full text")
        
        for pattern in self.compiled_thread_separators:
            match = pattern.search(text)
            if match:
                content_before = text[:match.start()].strip()
                if len(content_before) >= 50:
                    logger.info(f"Found thread marker, extracted current reply")
                    return content_before
        
        # If no thread found, return full text
        logger.info("No thread marker found, using full text")
        return text

    def _clean_subject(self, subject: str) -> str:
        """Clean subject line by removing prefixes."""
        subject = ' '.join(subject.split())
        
        # Remove common prefixes
        prefixes = [r'^Re:\s*', r'^Fwd:\s*', r'^FW:\s*', r'^\[EXTERNAL\]\s*', r'^ODP:\s*']
        for prefix in prefixes:
            subject = re.sub(prefix, '', subject, flags=re.IGNORECASE)
        
        return subject.strip()

    def _clean_full_body(self, text: str) -> str:
        """Clean FULL EMAIL BODY - remove threads but preserve business content."""
        logger.info(f"Starting full body cleaning. Original length: {len(text)}")
        
        # STEP 1: Remove thread content first (Outlook/Gmail then patterns)
        text = self._remove_thread_content(text)
        logger.info(f"After thread removal: {len(text)}")
        
        # STEP 2: Normalize text
        text = self._normalize_text(text)
        
        # STEP 3: Remove ONLY minimal noise patterns
        for pattern in self.compiled_noise_patterns:
            before_text = text
            text = pattern.sub(' ', text)
            if text != before_text:
                logger.info(f"Removed noise pattern")
        
        # STEP 4: Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        text = text.strip()
        
        # STEP 5: Remove basic markdown artifacts only
        text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)  # Links
        text = re.sub(r'[*_~`]{2,}', '', text)  # Formatting
        
        logger.info(f"Final full body length: {len(text)}")
        return text

    def _minimal_clean(self, text: str) -> str:
        """Minimal cleaning - preserve everything."""
        logger.info("Applying minimal cleaning")
        
        # Just normalize
        text = self._normalize_text(text)
        
        # Remove only the most obvious noise
        text = re.sub(r'EXTERNAL:\s*This e-mail originates from outside the organization\.', '', text)
        text = re.sub(r'Learn why this is important', '', text)
        
        return text.strip()

    def _remove_thread_content(self, text: str) -> str:
        """Remove thread content but keep current business message."""
        logger.info("Starting thread content removal")
        
        # Priority: Outlook/Gmail block, then other patterns
        match = OUTLOOK_THREAD_BLOCK.search(text)
        if match:
            content_before = text[:match.start()].strip()
            if len(content_before) >= 30:
                logger.info(f"Found Outlook thread block, keeping content before it (length: {len(content_before)})")
                return content_before
            else:
                logger.info(f"Outlook thread block found but content too short, keeping full text")
        
        for pattern in self.compiled_thread_separators:
            match = pattern.search(text)
            if match:
                content_before = text[:match.start()].strip()
                if len(content_before) >= 30:
                    logger.info(f"Found thread marker, keeping content before it (length: {len(content_before)})")
                    return content_before
                else:
                    logger.info(f"Thread marker found but content too short, keeping full text")
        
        # If no thread found, return original text
        logger.info("No thread markers found, keeping full text")
        return text

    def _count_redactions(self, text: str) -> int:
        """Count redacted items - should be 0 for full body."""
        return 0  # No redaction for full body

    def _is_html(self, text: str) -> bool:
        """Check if text contains HTML."""
        return bool(re.search(r'<[^>]+>', text))

    
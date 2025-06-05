import re
# import logging
# import unicodedata
# from typing import Dict, List, Optional, Tuple
# from dataclasses import dataclass
# import time

# logger = logging.getLogger(__name__)

# # Add multi-line Outlook/Gmail thread block regex
# OUTLOOK_THREAD_BLOCK = re.compile(
#     r"(^From: .+\n^Sent: .+\n^To: .+\n(^Cc: .+\n)?^Subject: .+$)",
#     re.MULTILINE | re.IGNORECASE
# )

# @dataclass
# class ProcessedEmail:
#     current_reply: str  # The current reply text (before thread markers)
#     has_thread: bool   # Whether the email contains a thread
#     thread_count: int  # Number of thread markers found
#     cleaned_text: str  # The cleaned text for classification
#     cleaned_subject: str  # The cleaned subject line
#     original_body: str # The original email body
#     processing_time: float = 0.0
#     compression_ratio: float = 0.0
#     redaction_count: int = 0

# class EmailPreprocessor:
#     # ====== CUSTOM FAREWELL PHRASES ======
#     FAREWELL_PHRASES = [
#         "thanks", "thank you", "thanky you", "regards", "best regards", "many thanks", "cheers",
#         "have a good day", "have a nice day", "have a great day", "have a wonderful day", "have a pleasant day",
#         "kind regards", "warm regards", "may regards", "sincerely", "yours sincerely", "yours truly",
#         "yours faithfully", "take care", "stay safe", "with regards", "with best wishes", "respectfully"
#     ]
    
#     # ====== SAFETY WARNING KEYWORDS ======
#     SAFETY_WARNING_KEYWORDS = [
#         "this is the first time you received an email from",
#         "some people who received this message don't often get email from",
#         "learn why this is important",
#         "exercise caution when clicking links",
#         "before validating its authenticity"
#     ]

#     # ====== ENHANCED NOISE PATTERNS (more flexible matching) ======
#     NOISE_PATTERNS = [
#         r'EXTERNAL:\s*This e-mail originates from outside the organization\.',
#         r'Learn why this is important',
#         r'\[Learn why this is important\]',
#         r'https://aka\.ms/LearnAboutSenderIdentification',

#         # Microsoft banner patterns - ENHANCED with more flexible matching
#         r'This is the first time you received an email from this sender\s*\([^)]+\)\.?\s*Exercise caution when clicking links[^.]*\.',
#         r'This is the first time you received an email from this sender\s*\([^)]+\)\.?',
#         r'Exercise caution when clicking links, opening attachments or taking further action, before validating its authenticity\.?',
#         r'Some people who received this message don\'t often get email from\s+[^\s.]+\.?\s*Learn why this is important',
#         r'Some people who received this message don\'t often get email from\s+[^\s.]+\.?',
        
#         # More general patterns for safety warnings
#         r'This is the first time.*?received an email from.*?sender.*?\([^)]+\)',
#         r'Exercise caution when clicking.*?before validating.*?authenticity',
#         r'Some people.*?don\'t often get email from.*?[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        
#         # Multi-line safety warning block (the entire warning as one block)
#         r'This is the first time you received an email from this sender.*?Exercise caution.*?authenticity\.?\s*Some people.*?don\'t often get email from.*?Learn why this is important',
        
#         # Only remove standalone email headers (not content)
#         r'^From:\s*[^\n]*$',
#         r'^To:\s*[^\n]*$',
#         r'^Sent:\s*[^\n]*$', 
#         r'^Date:\s*[^\n]*$',
#         r'^Subject:\s*[^\n]*$',
        
#         # Reference tracking
#         r'Ref:MSG[A-Za-z0-9]+',
#     ]

#     # ====== STRONG THREAD SEPARATORS (for cutting threads) ======
#     THREAD_SEPARATORS = [
#         r'From:\s*ABCCollectionsTeamD@abc-amega\.com',
#         r'-----Original Message-----',
#         r'Dear Accounts Payable:\s*Your Company has been referred to us',
#         r'-{5,}\s*Forwarded message\s*-{5,}',
#         r'From:\s*[^\n]+@[^\n]+\s*Sent:\s*[^\n]+\s*To:\s*[^\n]+\s*Subject:',
#         r'Od:\s*[^\n]+@[^\n]+\s*Wysłano:\s*[^\n]+\s*Do:\s*[^\n]+\s*Temat:',
#         r'From:\s*[^\n]+\s*Sent:\s*\w+,\s+\w+\s+\d{1,2},\s+\d{4}',
#         r'External email\.\s*Think before clicking',
#         r'Think before clicking links or opening attachments',
#     ]

#     # ====== THREAD INDICATORS (for detection only) ======
#     THREAD_INDICATORS = [
#         r'From:.*?Sent:.*?To:',
#         r'From:.*ABCCollectionsTeamD',
#         r'On\s+\w+.*?wrote:',
#         r'Dear.*?Your Company has been referred to us',
#         r'External email\.\s*Think before clicking',
#     ]

#     def __init__(self):
#         self.logger = logging.getLogger(__name__)
        
#         # Compile patterns for performance
#         self.compiled_noise_patterns = [
#             re.compile(p, re.IGNORECASE | re.MULTILINE | re.DOTALL) 
#             for p in self.NOISE_PATTERNS
#         ]
        
#         self.compiled_thread_separators = [
#             re.compile(p, re.IGNORECASE | re.MULTILINE) 
#             for p in self.THREAD_SEPARATORS
#         ]
        
#         # Compile custom patterns
#         self.farewell_pattern = re.compile(
#             r"^\s*(?:" + "|".join(re.escape(p) for p in self.FAREWELL_PHRASES) + r")[\s\.,!]*$", 
#             re.IGNORECASE
#         )
        
#         self.reply_line_pattern = re.compile(
#             r"^On\s+\w+\s+\d{1,2},\s+\d{4},\s+at\s+[\d:]+.*wrote:", 
#             re.IGNORECASE
#         )
        
#         self.sender_warning_pattern = re.compile(
#             r"^\[.*learn why this is important.*\]$", 
#             re.IGNORECASE
#         )
        
#         # Enhanced safety warning pattern for line-by-line cleaning
#         self.enhanced_safety_pattern = re.compile(
#             r"(this is the first time.*?sender|exercise caution when clicking|some people.*?don't often get email|learn why this is important)", 
#             re.IGNORECASE
#         )
        
#         logger.info("Initialized EmailPreprocessor with enhanced cleaning patterns")

#     def preprocess_email(self, subject: str, body: str) -> ProcessedEmail:
#         """Preprocess email by cleaning and extracting actionable text."""
#         start_time = time.time()
#         original_length = len(body)
        
#         try:
#             original_body = body
            
#             # Clean subject (keep existing logic)
#             cleaned_subject = self._clean_subject(subject)
#             logger.info(f"Cleaned subject: {cleaned_subject}")
            
#             # Extract current reply (for thread detection and current_reply field)
#             current_reply = self._extract_current_reply(body)
#             logger.info(f"Extracted current reply (length: {len(current_reply)})")
            
#             # Apply custom body cleaning followed by existing cleaning
#             cleaned_text = self._clean_full_body_enhanced(body)
            
#             # SAFETY CHECK: Ensure we have substantial content
#             if len(cleaned_text.strip()) < 50:
#                 logger.warning("Cleaned text too short, using minimal cleaning")
#                 cleaned_text = self._minimal_clean(body)
            
#             logger.info(f"Final cleaned text (length: {len(cleaned_text)}):\n{cleaned_text[:500]}...")
            
#             # Detect thread
#             has_thread, thread_count = self._detect_thread(body)
#             logger.info(f"Thread detection: has_thread={has_thread}, count={thread_count}")
            
#             # Calculate metrics
#             processing_time = time.time() - start_time
#             compression_ratio = len(cleaned_text) / original_length if original_length > 0 else 0
            
#             return ProcessedEmail(
#                 current_reply=current_reply,
#                 has_thread=has_thread,
#                 thread_count=thread_count,
#                 cleaned_text=cleaned_text,
#                 cleaned_subject=cleaned_subject,
#                 original_body=original_body,
#                 processing_time=processing_time,
#                 compression_ratio=compression_ratio,
#                 redaction_count=0
#             )
            
#         except Exception as e:
#             logger.error(f"Error preprocessing email: {str(e)}")
#             return ProcessedEmail(
#                 current_reply="",
#                 has_thread=False,
#                 thread_count=0,
#                 cleaned_text="",
#                 cleaned_subject=subject,
#                 original_body=body,
#                 processing_time=time.time() - start_time,
#                 compression_ratio=0.0,
#                 redaction_count=0
#             )

#     def _normalize_text(self, text: str) -> str:
#         """Normalize text by handling special characters and whitespace."""
#         text = text.replace('\xa0', ' ')
#         text = re.sub(r'[\u200b-\u200f]', '', text)
#         text = unicodedata.normalize('NFKC', text)
#         text = re.sub(r'\s+', ' ', text)
#         text = re.sub(r'\n\s*\n', '\n', text)
#         return text.strip()

#     def _detect_thread(self, text: str) -> Tuple[bool, int]:
#         """Conservative thread detection."""
#         all_indicators = self.THREAD_SEPARATORS + self.THREAD_INDICATORS
        
#         count = 0
#         for indicator in all_indicators:
#             if re.search(indicator, text, re.IGNORECASE | re.DOTALL):
#                 count += 1
#                 logger.info(f"Found thread indicator: {indicator[:50]}...")
        
#         return count > 0, count

#     def _extract_current_reply(self, text: str) -> str:
#         """Extract current message for current_reply field."""
#         logger.info(f"Starting current reply extraction. Text length: {len(text)}")
        
#         # Priority: Outlook/Gmail block, then other patterns
#         match = OUTLOOK_THREAD_BLOCK.search(text)
#         if match:
#             content_before = text[:match.start()].strip()
#             if len(content_before) >= 50:
#                 logger.info(f"Found Outlook thread block, extracted current reply")
#                 return content_before
#             else:
#                 logger.info(f"Outlook thread block found but content too short, keeping full text")
        
#         for pattern in self.compiled_thread_separators:
#             match = pattern.search(text)
#             if match:
#                 content_before = text[:match.start()].strip()
#                 if len(content_before) >= 50:
#                     logger.info(f"Found thread marker, extracted current reply")
#                     return content_before
        
#         logger.info("No thread marker found, using full text")
#         return text

#     def _clean_subject(self, subject: str) -> str:
#         """Clean subject line by removing prefixes."""
#         subject = ' '.join(subject.split())
        
#         # Remove common prefixes
#         prefixes = [r'^Re:\s*', r'^Fwd:\s*', r'^FW:\s*', r'^\[EXTERNAL\]\s*', r'^ODP:\s*']
#         for prefix in prefixes:
#             subject = re.sub(prefix, '', subject, flags=re.IGNORECASE)
        
#         return subject.strip()

#     def _clean_full_body_enhanced(self, text: str) -> str:
#         """Enhanced full body cleaning: Custom cleaning first, then existing patterns."""
#         logger.info(f"Starting enhanced full body cleaning. Original length: {len(text)}")
        
#         # STEP 1: Apply custom line-by-line cleaning (your logic)
#         text = self._apply_custom_cleaning(text)
#         logger.info(f"After custom cleaning: {len(text)}")
        
#         # STEP 2: Remove thread content (existing logic)
#         text = self._remove_thread_content(text)
#         logger.info(f"After thread removal: {len(text)}")
        
#         # STEP 3: Normalize text
#         text = self._normalize_text(text)
        
#         # STEP 4: Remove noise patterns (existing logic) - Enhanced patterns
#         for pattern in self.compiled_noise_patterns:
#             before_text = text
#             text = pattern.sub(' ', text)
#             if text != before_text:
#                 logger.info(f"Removed noise pattern")
        
#         # STEP 5: Clean up whitespace and markdown
#         text = re.sub(r'\s+', ' ', text)
#         text = re.sub(r'\n\s*\n', '\n', text)
#         text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)  # Links
#         text = re.sub(r'[*_~`]{2,}', '', text)  # Formatting
#         text = text.strip()
        
#         logger.info(f"Final enhanced body length: {len(text)}")
#         return text

#     def _apply_custom_cleaning(self, text: str) -> str:
#         """Apply your custom line-by-line cleaning logic with enhanced safety warning detection."""
#         logger.info("Applying custom line-by-line cleaning")
        
#         lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
#         output_lines = []
        
#         for line in lines:
#             lower_line = line.lower()
            
#             # Remove everything after reply chain
#             if self.reply_line_pattern.match(line):
#                 logger.info("Found reply line pattern, stopping processing")
#                 break
            
#             # Remove everything after farewell
#             if self.farewell_pattern.match(line):
#                 logger.info("Found farewell pattern, stopping processing")
#                 break
            
#             # Enhanced safety warning detection
#             if self.enhanced_safety_pattern.search(line):
#                 logger.info(f"Skipped safety warning line: {line[:50]}...")
#                 continue
            
#             # Skip known warning lines
#             if lower_line.startswith("caution :"):
#                 logger.info("Skipped caution line")
#                 continue
                
#             if lower_line == "external: this e-mail originates from outside the organization.":
#                 logger.info("Skipped external email warning")
#                 continue
                
#             if self.sender_warning_pattern.match(line):
#                 logger.info("Skipped sender warning pattern")
#                 continue
                
#             if any(keyword in lower_line for keyword in self.SAFETY_WARNING_KEYWORDS):
#                 logger.info("Skipped safety warning keyword line")
#                 continue
            
#             output_lines.append(line)
        
#         result = '\n'.join(output_lines)
#         logger.info(f"Custom cleaning completed. Lines processed: {len(lines)}, Lines kept: {len(output_lines)}")
#         return result

#     def _minimal_clean(self, text: str) -> str:
#         """Minimal cleaning - preserve everything."""
#         logger.info("Applying minimal cleaning")
        
#         # Just normalize
#         text = self._normalize_text(text)
        
#         # Remove only the most obvious noise including safety warnings
#         text = re.sub(r'EXTERNAL:\s*This e-mail originates from outside the organization\.', '', text)
#         text = re.sub(r'Learn why this is important', '', text)
#         text = re.sub(r'This is the first time.*?sender.*?\([^)]+\)', '', text, flags=re.IGNORECASE)
#         text = re.sub(r'Exercise caution when clicking.*?authenticity', '', text, flags=re.IGNORECASE)
#         text = re.sub(r'Some people.*?don\'t often get email from.*?@[^\s.]+', '', text, flags=re.IGNORECASE)
        
#         return text.strip()

#     def _remove_thread_content(self, text: str) -> str:
#         """Remove thread content but keep current business message."""
#         logger.info("Starting thread content removal")
        
#         # Priority: Outlook/Gmail block, then other patterns
#         match = OUTLOOK_THREAD_BLOCK.search(text)
#         if match:
#             content_before = text[:match.start()].strip()
#             if len(content_before) >= 30:
#                 logger.info(f"Found Outlook thread block, keeping content before it (length: {len(content_before)})")
#                 return content_before
#             else:
#                 logger.info(f"Outlook thread block found but content too short, keeping full text")
        
#         for pattern in self.compiled_thread_separators:
#             match = pattern.search(text)
#             if match:
#                 content_before = text[:match.start()].strip()
#                 if len(content_before) >= 30:
#                     logger.info(f"Found thread marker, keeping content before it (length: {len(content_before)})")
#                     return content_before
#                 else:
#                     logger.info(f"Thread marker found but content too short, keeping full text")
        
#         logger.info("No thread markers found, keeping full text")
#         return text



import re
import logging
import unicodedata
from typing import Dict, List, Optional, Tuple
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
    # ====== CUSTOM FAREWELL PHRASES ======
    FAREWELL_PHRASES = [
        "thanks", "thank you", "thanky you", "regards", "best regards", "many thanks", "cheers",
        "have a good day", "have a nice day", "have a great day", "have a wonderful day", "have a pleasant day",
        "kind regards", "warm regards", "may regards", "sincerely", "yours sincerely", "yours truly",
        "yours faithfully", "take care", "stay safe", "with regards", "with best wishes", "respectfully"
    ]
    
    # ====== SAFETY WARNING KEYWORDS ======
    SAFETY_WARNING_KEYWORDS = [
        "this is the first time you received an email from",
        "some people who received this message don't often get email from",
        "learn why this is important",
        "exercise caution when clicking links",
        "before validating its authenticity"
    ]

    # ====== ENHANCED NOISE PATTERNS (more flexible matching) ======
    NOISE_PATTERNS = [
        r'EXTERNAL:\s*This e-mail originates from outside the organization\.',
        r'Learn why this is important',
        r'\[Learn why this is important\]',
        r'https://aka\.ms/LearnAboutSenderIdentification',

        # Microsoft banner patterns - ENHANCED with more flexible matching
        r'This is the first time you received an email from this sender\s*\([^)]+\)\.?\s*Exercise caution when clicking links[^.]*\.',
        r'This is the first time you received an email from this sender\s*\([^)]+\)\.?',
        r'Exercise caution when clicking links, opening attachments or taking further action, before validating its authenticity\.?',
        r'Some people who received this message don\'t often get email from\s+[^\s.]+\.?\s*Learn why this is important',
        r'Some people who received this message don\'t often get email from\s+[^\s.]+\.?',
        
        # More general patterns for safety warnings
        r'This is the first time.*?received an email from.*?sender.*?\([^)]+\)',
        r'Exercise caution when clicking.*?before validating.*?authenticity',
        r'Some people.*?don\'t often get email from.*?[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        
        # Multi-line safety warning block (the entire warning as one block)
        r'This is the first time you received an email from this sender.*?Exercise caution.*?authenticity\.?\s*Some people.*?don\'t often get email from.*?Learn why this is important',
        
        # Only remove standalone email headers (not content)
        r'^From:\s*[^\n]*$',
        r'^To:\s*[^\n]*$',
        r'^Sent:\s*[^\n]*$', 
        r'^Date:\s*[^\n]*$',
        r'^Subject:\s*[^\n]*$',
        
        # Reference tracking
        r'Ref:MSG[A-Za-z0-9]+',
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
        
        # Compile patterns for performance
        self.compiled_noise_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE | re.DOTALL) 
            for p in self.NOISE_PATTERNS
        ]
        
        self.compiled_thread_separators = [
            re.compile(p, re.IGNORECASE | re.MULTILINE) 
            for p in self.THREAD_SEPARATORS
        ]
        
        # Compile custom patterns
        self.farewell_pattern = re.compile(
            r"^\s*(?:" + "|".join(re.escape(p) for p in self.FAREWELL_PHRASES) + r")[\s\.,!]*$", 
            re.IGNORECASE
        )
        
        self.reply_line_pattern = re.compile(
            r"^On\s+\w+\s+\d{1,2},\s+\d{4},\s+at\s+[\d:]+.*wrote:", 
            re.IGNORECASE
        )
        
        self.sender_warning_pattern = re.compile(
            r"^\[.*learn why this is important.*\]$", 
            re.IGNORECASE
        )
        
        # Enhanced safety warning pattern for line-by-line cleaning
        self.enhanced_safety_pattern = re.compile(
            r"(this is the first time.*?sender|exercise caution when clicking|some people.*?don't often get email|learn why this is important)", 
            re.IGNORECASE
        )
        
        # NEW: Pattern for "Sent from my" detection
        self.sent_from_pattern = re.compile(
            r"sent from my", 
            re.IGNORECASE
        )
        
        logger.info("Initialized EmailPreprocessor with enhanced cleaning patterns")

    def preprocess_email(self, subject: str, body: str) -> ProcessedEmail:
        """Preprocess email by cleaning and extracting actionable text."""
        start_time = time.time()
        original_length = len(body)
        
        try:
            original_body = body
            
            # Clean subject (keep existing logic)
            cleaned_subject = self._clean_subject(subject)
            logger.info(f"Cleaned subject: {cleaned_subject}")
            
            # Extract current reply (for thread detection and current_reply field)
            current_reply = self._extract_current_reply(body)
            logger.info(f"Extracted current reply (length: {len(current_reply)})")
            
            # Apply custom body cleaning followed by existing cleaning
            cleaned_text = self._clean_full_body_enhanced(body)
            
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
                cleaned_text=cleaned_text,
                cleaned_subject=cleaned_subject,
                original_body=original_body,
                processing_time=processing_time,
                compression_ratio=compression_ratio,
                redaction_count=0
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

    def _clean_full_body_enhanced(self, text: str) -> str:
        """Enhanced full body cleaning: Custom cleaning first, then existing patterns."""
        logger.info(f"Starting enhanced full body cleaning. Original length: {len(text)}")
        
        # STEP 1: Apply custom line-by-line cleaning (your logic)
        text = self._apply_custom_cleaning(text)
        logger.info(f"After custom cleaning: {len(text)}")
        
        # STEP 2: Remove thread content (existing logic)
        text = self._remove_thread_content(text)
        logger.info(f"After thread removal: {len(text)}")
        
        # STEP 3: Normalize text
        text = self._normalize_text(text)
        
        # STEP 4: Remove noise patterns (existing logic) - Enhanced patterns
        for pattern in self.compiled_noise_patterns:
            before_text = text
            text = pattern.sub(' ', text)
            if text != before_text:
                logger.info(f"Removed noise pattern")
        
        # STEP 5: Clean up whitespace and markdown
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)  # Links
        text = re.sub(r'[*_~`]{2,}', '', text)  # Formatting
        text = text.strip()
        
        logger.info(f"Final enhanced body length: {len(text)}")
        return text

    def _check_last_three_words_for_farewell(self, line: str) -> Tuple[bool, str]:
        """
        Check if any of the last three words match farewell keywords.
        Returns (found_farewell, cleaned_line_without_farewell_and_after)
        """
        words = line.split()
        if len(words) == 0:
            return False, line
        
        # Check last 1, 2, or 3 words
        for i in range(min(3, len(words))):
            # Get the last (i+1) words
            last_words = words[-(i+1):]
            phrase_to_check = ' '.join(last_words).lower()
            
            # Remove punctuation for comparison
            phrase_clean = re.sub(r'[^\w\s]', '', phrase_to_check)
            
            # Check if this phrase matches any farewell
            for farewell in self.FAREWELL_PHRASES:
                if phrase_clean == farewell.lower():
                    # Found a match - return the line up to this point
                    if len(words) > (i+1):
                        cleaned_line = ' '.join(words[:-(i+1)]).strip()
                        logger.info(f"Found farewell '{farewell}' in last words, truncating line")
                        return True, cleaned_line
                    else:
                        # The entire line is just the farewell
                        logger.info(f"Line is just farewell '{farewell}', removing entirely")
                        return True, ""
        
        return False, line

    def _clean_sent_from_line(self, line: str) -> str:
        """
        Remove 'Sent from my' and everything after it in the line.
        Keep the line but truncate it at 'Sent from my'.
        """
        match = self.sent_from_pattern.search(line)
        if match:
            # Keep everything before 'Sent from my'
            cleaned_line = line[:match.start()].strip()
            logger.info(f"Found 'Sent from my', truncating line to: '{cleaned_line}'")
            return cleaned_line
        return line

    def _apply_custom_cleaning(self, text: str) -> str:
        """Apply your custom line-by-line cleaning logic with enhanced safety warning detection."""
        logger.info("Applying custom line-by-line cleaning")
        
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        output_lines = []
        
        for line in lines:
            lower_line = line.lower()
            
            # Remove everything after reply chain
            if self.reply_line_pattern.match(line):
                logger.info("Found reply line pattern, stopping processing")
                break
            
            # Remove everything after farewell (existing logic)
            if self.farewell_pattern.match(line):
                logger.info("Found farewell pattern, stopping processing")
                break
            
            # NEW CASE 1: Check if last 3 words contain farewell keywords
            found_farewell, cleaned_line = self._check_last_three_words_for_farewell(line)
            if found_farewell:
                if cleaned_line.strip():  # If there's content before the farewell
                    output_lines.append(cleaned_line)
                # Stop processing after this line regardless
                logger.info("Found farewell in last words, stopping processing")
                break
            
            # Update line to the cleaned version (in case "Sent from my" was removed)
            line = cleaned_line if found_farewell else line
            
            # NEW CASE 2: Clean 'Sent from my' phrases
            line = self._clean_sent_from_line(line)
            
            # Enhanced safety warning detection
            if self.enhanced_safety_pattern.search(line):
                logger.info(f"Skipped safety warning line: {line[:50]}...")
                continue
            
            # Skip known warning lines
            if lower_line.startswith("caution :"):
                logger.info("Skipped caution line")
                continue
                
            if lower_line == "external: this e-mail originates from outside the organization.":
                logger.info("Skipped external email warning")
                continue
                
            if self.sender_warning_pattern.match(line):
                logger.info("Skipped sender warning pattern")
                continue
                
            if any(keyword in lower_line for keyword in self.SAFETY_WARNING_KEYWORDS):
                logger.info("Skipped safety warning keyword line")
                continue
            
            # Only add non-empty lines
            if line.strip():
                output_lines.append(line)
        
        result = '\n'.join(output_lines)
        logger.info(f"Custom cleaning completed. Lines processed: {len(lines)}, Lines kept: {len(output_lines)}")
        return result

    def _minimal_clean(self, text: str) -> str:
        """Minimal cleaning - preserve everything."""
        logger.info("Applying minimal cleaning")
        
        # Just normalize
        text = self._normalize_text(text)
        
        # Remove only the most obvious noise including safety warnings
        text = re.sub(r'EXTERNAL:\s*This e-mail originates from outside the organization\.', '', text)
        text = re.sub(r'Learn why this is important', '', text)
        text = re.sub(r'This is the first time.*?sender.*?\([^)]+\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Exercise caution when clicking.*?authenticity', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Some people.*?don\'t often get email from.*?@[^\s.]+', '', text, flags=re.IGNORECASE)
        
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
        
        logger.info("No thread markers found, keeping full text")
        return text
"""
High-Quality Pattern Matcher - Complete word boundary protection
Prevents false matches inside words (e.g., "inside" -> "in" + "side")
Every pattern uses proper \b word boundaries for precision
"""

from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Configuration
CONFIDENCE_BASE = 0.75
CONFIDENCE_BOOST_PER_MATCH = 0.05
MAX_CONFIDENCE = 0.95
MIN_CONFIDENCE = 0.30

class PatternMatcher:
    """
    Production-grade pattern matcher with complete word boundary protection.
    Every pattern uses \b to prevent substring matches within words.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()
        self._compile_patterns()
        self._initialize_mappings()
        self.logger.info("✅ Pattern Matcher initialized with complete word boundaries")

    def _initialize_patterns(self) -> None:
        """Initialize patterns with comprehensive word boundary protection."""
        
        self.patterns = {
            "Manual Review": {
                "Partial/Disputed Payment": [
                    # Legal dispute statements - all with word boundaries
                    r"\bamount\b.*\bis\b.*\bin\b.*\bdispute\b",
                    r"\bbalance\b.*\bis\b.*\bnot\b.*\bours\b",
                    r"\bnot\b.*\bout\b.*\bresponsibility\b",
                    r"\bdo\b.*\bnot\b.*\bowe\b",
                    r"\bcontested\b", r"\bdisagreement\b", r"\bdispute\b",
                    r"\bformally\b.*\bdisputing\b",
                    r"\bdispute\b.*\bpayment\b",
                    r"\bcontested\b.*\bpayment\b",
                    r"\bchallenge\b.*\bpayment\b",
                    r"\bdebt\b.*\bis\b.*\bdisputed\b",
                    r"\bcease\b.*\band\b.*\bdesist\b",
                    r"\bdo\b.*\bnot\b.*\backnowledge\b.*\bdebt\b",
                    r"\bfdcpa\b", r"\bbilling\b.*\berror\b.*\bdispute\b",
                    r"\bnot\b.*\bproperly\b.*\bbilled\b",
                    r"\bwrong\b.*\bentity\b",
                    r"\bdispute\b.*\bbilling\b",
                    r"\bdisputing\b.*\bthis\b.*\bdebt\b",
                    r"\bowe\b.*\bthem\b.*\bnothing\b",
                    r"\bowe\b.*\bnothing\b",
                    r"\bconsider\b.*\bthis\b.*\ba\b.*\bscam\b",
                    r"\blooks\b.*\blike\b.*\ba\b.*\bscam\b",
                    r"\bis\b.*\bthis\b.*\blegitimate\b",
                    r"\bverify\b.*\bthis\b.*\bis\b.*\breal\b",
                    r"\bcease\b.*\band\b.*\bdesist\b.*\bletter\b",
                    r"\blegal\b.*\bnotice\b",
                    r"\bfdcpa\b.*\bviolation\b",
                    r"\bdo\b.*\bnot\b.*\backnowledge\b.*\bthis\b.*\bdebt\b",
                    r"\bformally\b.*\bdispute\b.*\bthis\b.*\bdebt\b",
                    r"\bdebt\b.*\bvalidation\b.*\brequest\b",
                    r"\blegal\b.*\brepresentation\b",
                    r"\battorney\b.*\bcorrespondence\b",
                    r"\bcollection\b.*\bagency\b.*\bviolation\b",
                    r"\bfair\b.*\bdebt\b.*\bcollection\b",
                    r"\bcease\b.*\ball\b.*\bcommunication\b",
                    r"\blegal\b.*\baction\b.*\bthreatened\b",
                    r"\bdebt\b.*\bcollector\b.*\bharassment\b",
                    r"\bvalidation\b.*\bof\b.*\bdebt\b",
                    r"\bcease\b.*\band\b.*\bdesist\b.*\ball\b.*\bcontact\b",
                    r"\blegal\b.*\bcounsel\b.*\brepresentation\b"
                ],

                "Invoice Receipt": [
                    # Specific invoice/proof attachments with word boundaries
                    r"\binvoice\b.*\battached\b.*\bas\b.*\bproof\b",
                    r"\battached\b.*\binvoice\b.*\bcopy\b",
                    r"\bproof\b.*\bof\b.*\binvoice\b.*\battached\b",
                    r"\binvoice\b.*\bdocumentation\b.*\battached\b",
                    r"\bhere\b.*\bis\b.*\bthe\b.*\binvoice\b.*\bcopy\b",
                    r"\binvoice\b.*\breceipt\b.*\battached\b",
                    r"\bcopy\b.*\bof\b.*\binvoice\b.*\battached\b.*\bfor\b.*\byour\b.*\brecords\b",
                    r"\bpayment\b.*\bmade\b.*\bin\b.*\berror\b.*\bdocumentation\b",
                    r"\berror\b.*\bpayment\b.*\bproof\b",
                    r"\bdocumentation\b.*\bfor\b.*\bpayment\b.*\berror\b",
                    r"\bproof\b.*\bof\b.*\bpayment\b.*\berror\b",
                    r"\battached\b.*\bpayment\b.*\bdocumentation\b",
                    r"\bpayment\b.*\berror\b.*\breceipt\b"
                ],

                "Closure Notification": [
                    # Business closure patterns with word boundaries
                    r"\bbusiness\b.*\bclosed\b",
                    r"\bcompany\b.*\bclosed\b",
                    r"\bout\b.*\bof\b.*\bbusiness\b",
                    r"\bceased\b.*\boperations\b",
                    r"\bfiled\b.*\bbankruptcy\b",
                    r"\bbankruptcy\b.*\bprotection\b",
                    r"\bchapter\b.*\b7\b",
                    r"\bchapter\b.*\b11\b",
                    r"\bbusiness\b.*\bshutting\b.*\bdown\b",
                    r"\bpermanently\b.*\bclosed\b",
                    r"\bcompany\b.*\bliquidated\b"
                ],

                "Closure + Payment Due": [
                    # Closure with outstanding payment with word boundaries
                    r"\bclosed\b.*\bpayment\b.*\bdue\b",
                    r"\bbusiness\b.*\bclosed\b.*\boutstanding\b",
                    r"\bbankruptcy\b.*\bpayment\b.*\bdue\b",
                    r"\bclosure\b.*\bwith\b.*\boutstanding\b.*\bpayment\b",
                    r"\bclosed\b.*\bbut\b.*\bpayment\b.*\bowed\b",
                    r"\bclosure\b.*\bpayment\b.*\brequired\b"
                ],

                "External Submission": [
                    # Invoice submission issues with word boundaries
                    r"\binvoice\b.*\bsubmission\b.*\bfailed\b",
                    r"\bimport\b.*\bfailed\b",
                    r"\bfailed\b.*\bimport\b",
                    r"\bunable\b.*\bto\b.*\bimport\b",
                    r"\bdocuments\b.*\bnot\b.*\bprocessed\b",
                    r"\bsubmission\b.*\bunsuccessful\b",
                    r"\berror\b.*\bimporting\b.*\binvoice\b",
                    r"\binvoice\b.*\bprocessing\b.*\bfailed\b",
                    r"\bupload\b.*\bfailed\b",
                    r"\bsystem\b.*\brejected\b.*\bsubmission\b"
                ],

                "Invoice Errors (format mismatch)": [
                    # Format and field errors with word boundaries
                    r"\bmissing\b.*\brequired\b.*\bfield\b",
                    r"\bformat\b.*\bmismatch\b",
                    r"\bincomplete\b.*\binvoice\b",
                    r"\binvoice\b.*\bformat\b.*\berror\b",
                    r"\bfield\b.*\bmissing\b.*\bfrom\b.*\binvoice\b",
                    r"\binvalid\b.*\binvoice\b.*\bformat\b",
                    r"\bformat\b.*\brequirements\b.*\bnot\b.*\bmet\b",
                    r"\binvoice\b.*\btemplate\b.*\berror\b",
                    r"\bmissing\b.*\bmandatory\b.*\bfields\b"
                ],

                "Inquiry/Redirection": [
                    # Inquiry and redirection patterns with word boundaries
                    r"\binsufficient\b.*\bdata\b.*\bto\b.*\bresearch\b",
                    r"\bneed\b.*\bguidance\b",
                    r"\bplease\b.*\badvise\b",
                    r"\bredirect\b.*\bto\b",
                    r"\bcontact\b.*\binstead\b",
                    r"\breach\b.*\bout\b.*\bto\b",
                    r"\bplease\b.*\bcheck\b.*\bwith\b",
                    r"\bwhat\b.*\bdocumentation\b.*\bneeded\b",
                    r"\bwhere\b.*\bto\b.*\bsend\b.*\bpayment\b",
                    r"\bverify\b.*\blegitimate\b",
                    r"\blooks\b.*\blike\b.*\ba\b.*\bscam\b",
                    r"\bare\b.*\byou\b.*\blegitimate\b",
                    r"\bguidance\b.*\brequired\b",
                    r"\bneed\b.*\bclarification\b"
                ],

                "Complex Queries": [
                    # Complex business and legal patterns with word boundaries
                    r"\bmultiple\b.*\bissues\b",
                    r"\bcomplex\b.*\bsituation\b",
                    r"\blegal\b.*\bcommunication\b",
                    r"\bsettle\b.*\bfor\b.*\$",
                    r"\bsettlement\b.*\boffer\b",
                    r"\bnegotiate\b.*\bpayment\b",
                    r"\bsettlement\b.*\barrangement\b",
                    r"\blegal\b.*\bsettlement\b.*\bagreement\b",
                    r"\bpayment\b.*\bsettlement\b",
                    r"\bsettlement\b.*\bnegotiation\b",
                    r"\blegal\b.*\barrangement\b",
                    r"\bsettlement\b.*\bterms\b",
                    r"\battorney\b.*\bsettlement\b",
                    r"\blegal\b.*\bresolution\b",
                    r"\bsettlement\b.*\bdiscussion\b",
                    r"\bcomplex\b.*\blegal\b.*\bmatter\b",
                    r"\blegal\b.*\bconsultation\b",
                    r"\battorney\b.*\binvolvement\b",
                    r"\blegal\b.*\bproceedings\b",
                    r"\bcourt\b.*\bsettlement\b",
                    r"\bmediation\b.*\bsettlement\b",
                    r"\bcomplex\b.*\bbusiness\b.*\binstructions\b",
                    r"\brouting\b.*\binstructions\b",
                    r"\bcomplex\b.*\brouting\b",
                    r"\bbusiness\b.*\bprocess\b.*\binstructions\b",
                    r"\bmulti\b.*\bstep\b.*\bprocess\b",
                    r"\bcomplex\b.*\bprocedure\b",
                    r"\bdetailed\b.*\bbusiness\b.*\bprocess\b",
                    r"\bspecial\b.*\bhandling\b.*\binstructions\b",
                    r"\bcomplex\b.*\bworkflow\b"
                ]
            },
 
            "No Reply (with/without info)": {
                "Sales/Offers": [
                    # Sales and promotional content with word boundaries
                    r"\bspecial\b.*\boffer\b",
                    r"\blimited\b.*\btime\b.*\boffer\b",
                    r"\bpromotional\b.*\boffer\b", 
                    r"\bdiscount\b.*\boffer\b",
                    r"\bexclusive\b.*\bdeal\b",
                    r"\bprices\b.*\bincreasing\b",
                    r"\bhours\b.*\bleft\b", 
                    r"\bspecial\b.*\bpricing\b",
                    r"\bsale\b.*\bending\b",
                    r"\bpayment\b.*\bplan\b.*\boptions\b",
                    r"\bpayment\b.*\bplan\b.*\bdiscussion\b",
                    r"\binstallment\b.*\bplan\b",
                    r"\bpayment\b.*\barrangement\b.*\boffer\b",
                    r"\bflexible\b.*\bpayment\b.*\boptions\b",
                    r"\bpayment\b.*\bterms\b.*\bdiscussion\b",
                    r"\bfinancing\b.*\boptions\b",
                    r"\bpayment\b.*\bschedule\b.*\boptions\b",
                    r"\bpayment\b.*\bplan\b.*\bavailable\b",
                    r"\bmonthly\b.*\bpayment\b.*\bplan\b",
                    r"\bextended\b.*\bpayment\b.*\bterms\b",
                    r"\bpayment\b.*\bflexibility\b",
                    r"\bprice\b.*\bincrease\b"
                ],

                "System Alerts": [
                    # System notifications with word boundaries
                    r"\bsystem\b.*\bnotification\b",
                    r"\bautomated\b.*\bnotification\b",
                    r"\bsystem\b.*\balert\b",
                    r"\bmaintenance\b.*\bnotification\b",
                    r"\bsecurity\b.*\balert\b",
                    r"\bserver\b.*\bmaintenance\b",
                    r"\bsystem\b.*\bupgrade\b",
                    r"\bservice\b.*\bdisruption\b"
                ],

                "Processing Errors": [
                    # Processing and delivery errors with word boundaries
                    r"\bprocessing\b.*\berror\b",
                    r"\bfailed\b.*\bto\b.*\bprocess\b",
                    r"\bcannot\b.*\bbe\b.*\bprocessed\b",
                    r"\belectronic\b.*\binvoice\b.*\brejected\b",
                    r"\brequest\b.*\bcouldn.?t\b.*\bbe\b.*\bcreated\b",
                    r"\bsystem\b.*\bunable\b.*\bto\b.*\bprocess\b",
                    r"\bmail\b.*\bdelivery\b.*\bfailed\b",
                    r"\bemail\b.*\bbounced\b",
                    r"\bdelivery\b.*\bfailure\b",
                    r"\bsystem\b.*\bmalfunction\b",
                    r"\bprocessing\b.*\bfailure\b"
                ],

                "Business Closure (Info only)": [
                    # Informational closure notices with word boundaries
                    r"\bbusiness\b.*\bclosure\b.*\binformation\b",
                    r"\bclosure\b.*\bnotification\b.*\bonly\b",
                    r"\bbusiness\b.*\bwill\b.*\bclose\b",
                    r"\bstore\b.*\bwill\b.*\bclose\b",
                    r"\bpermanently\b.*\bclosed\b",
                    r"\bcompany\b.*\bshutting\b.*\bdown\b",
                    r"\bclosing\b.*\boperations\b",
                    r"\binformational\b.*\bclosure\b",
                    r"\bclosure\b.*\bannouncement\b",
                    r"\bstore\b.*\bclosing\b.*\bnotice\b"
                ],

                "General (Thank You)": [
                    # Thank you and acknowledgment messages with word boundaries
                    r"\bthank\b.*\byou\b.*\bfor\b.*\byour\b.*\bemail\b",
                    r"\bthanks\b.*\bfor\b.*\bcontacting\b",
                    r"\bthank\b.*\byou\b.*\bfor\b.*\breaching\b.*\bout\b",
                    r"\bthank\b.*\byou\b.*\bfor\b.*\byour\b.*\bpatience\b",
                    r"\bstill\b.*\breviewing\b",
                    r"\bcurrently\b.*\breviewing\b", 
                    r"\bunder\b.*\breview\b",
                    r"\bwe\b.*\bare\b.*\breviewing\b",
                    r"\bfor\b.*\byour\b.*\brecords\b",
                    r"\backnowledgment\b.*\breceived\b",
                    r"\bmessage\b.*\breceived\b"
                ],

                "Created": [
                    # Ticket and case creation with word boundaries
                    r"\bticket\b.*\bcreated\b",
                    r"\bcase\b.*\bopened\b",
                    r"\bnew\b.*\bticket\b.*\bopened\b",
                    r"\bsupport\b.*\brequest\b.*\bcreated\b", 
                    r"\bcase\b.*\bhas\b.*\bbeen\b.*\bcreated\b",
                    r"\bticket\b.*\bhas\b.*\bbeen\b.*\bopened\b",
                    r"\bnew\b.*\bcase\b.*\bcreated\b", 
                    r"\bsupport\b.*\bticket\b.*\bopened\b",
                    r"\bcase\b.*\bnumber\b.*\bassigned\b",
                    r"\bticket\b.*\bnumber\b.*\bassigned\b", 
                    r"\bnew\b.*\bsupport\b.*\bcase\b",
                    r"\brequest\b.*\bhas\b.*\bbeen\b.*\bsubmitted\b",
                    r"\bticket\b.*\bsubmitted\b.*\bsuccessfully\b",
                    r"\bcase\b.*\bopened\b.*\bfor\b.*\breview\b",
                    r"\bsupport\b.*\brequest\b.*\breceived\b"
                ],

                "Resolved": [
                    # Resolution and completion with word boundaries
                    r"\bticket\b.*\bresolved\b",
                    r"\bticket\b.*\bhas\b.*\bbeen\b.*\bresolved\b",
                    r"\bcase\b.*\bclosed\b",
                    r"\bcase\b.*\bresolved\b", 
                    r"\bmarked\b.*\bas\b.*\bresolved\b",
                    r"\bstatus\b.*\bresolved\b",
                    r"\bticket\b.*\bclosed\b",
                    r"\bcase\b.*\bcompleted\b",
                    r"\bdo\b.*\bnot\b.*\breply\b",
                    r"\byour\b.*\bfeedback\b.*\bis\b.*\bimportant\b",
                    r"\bsurvey\b.*\brequest\b",
                    r"\bthis\b.*\bcase\b.*\bis\b.*\bnow\b.*\bclosed\b",
                    r"\bissue\b.*\bresolved\b",
                    r"\brequest\b.*\bcompleted\b",
                    r"\bticket\b.*\bclosed\b.*\bsuccessfully\b"
                ],

                "Open": [
                    # Open status indicators with word boundaries
                    r"\bticket\b.*\bopen\b",
                    r"\bcase\b.*\bopen\b",
                    r"\bstill\b.*\bpending\b",
                    r"\bcase\b.*\bpending\b",
                    r"\bunder\b.*\binvestigation\b",
                    r"\bbeing\b.*\bprocessed\b",
                    r"\bin\b.*\bprogress\b",
                    r"\bawaiting\b.*\bresponse\b"
                ]
            },
   
            "Invoices Request": {
                "Request (No Info)": [
                    # Invoice requests excluding proof scenarios with word boundaries
                    r"\bsend\b.*\bme\b.*\bthe\b.*\binvoice\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\bprovide\b.*\bthe\b.*\binvoice\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\bneed\b.*\binvoice\b.*\bcopy\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\bcopies?\b.*\bof\b.*(?:\bany\b.*)?binvoices?\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\bsend\b.*\binvoices?\b.*\bthat\b.*\bare\b.*\bdue\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\bprovide\b.*\boutstanding\b.*\binvoices?\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\brequest\b.*\bfor\b.*\binvoice\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\bforward\b.*\binvoice\b.*\bcopy\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\bcan\b.*\bi\b.*\bget\b.*\binvoice\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\bshare\b.*\binvoice\b.*\bcopy\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))",
                    r"\bwould\b.*\blike\b.*\binvoice\b(?!.*(?:\bpaid\b|\bcontract\b|\bagreement\b|\bproof\b|\breceipt\b|\bdocument\b|\bpayment\b))"
                ]
            },

            "Payments Claim": {
                "Claims Paid (No Info)": [
                    # Payment claims WITHOUT proof/attachment language with word boundaries
                    r"\balready\b.*\bpaid\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))",
                    r"\bpayment\b.*\bwas\b.*\bmade\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))",
                    r"\bwe\b.*\bpaid\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))",
                    r"\bbill\b.*\bwas\b.*\bpaid\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))",
                    r"\bpayment\b.*\bwas\b.*\bsent\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))",
                    r"\bcheck\b.*\bsent\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))",
                    r"\bpayment\b.*\bcompleted\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))",
                    r"\bthis\b.*\bwas\b.*\bpaid\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))",
                    r"\baccount\b.*\bpaid\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))",
                    r"\bmade\b.*\bpayment\b(?!.*(?:\battached\b|\bsee\b.*\battached\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b.*\benclosed\b|\bfind\b.*\battached\b))"
                ],
                
                "Payment Confirmation": [
                    # MUST include attachment/proof language with word boundaries
                    r"\bproof\b.*\bof\b.*\bpayment\b",
                    r"\bpayment\b.*\bconfirmation\b.*\battached\b",
                    r"\bcheck\b.*\bnumber\b.*\d+",
                    r"\beft#\b.*\d+",
                    r"\btransaction\b.*\bid\b.*\d+",
                    r"\bhere\b.*\bis\b.*\bproof\b.*\bof\b.*\bpayment\b",
                    r"\bpayment\b.*\breceipt\b.*\battached\b",
                    r"\bwire\b.*\bconfirmation\b.*\d+",
                    r"\bpaid\b.*\bvia\b.*\btransaction\b.*\bnumber\b.*\d+",
                    r"\bbatch\b.*\bnumber\b.*\d+",
                    r"\binvoice\b.*\bwas\b.*\bpaid\b.*\bsee\b.*\battachments\b",
                    r"\bpayment\b.*\bproof\b.*\battached\b",
                    r"\bcheck\b.*\benclosed\b",
                    r"\bsee\b.*\battached\b.*(?:\bcheck\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bdocument\b)",
                    r"\bfind\b.*\battached\b.*(?:\bcheck\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bdocument\b)",
                    r"(?:\battached\b|\bsee\b.*\battached\b|\bfind\b.*\battached\b|\benclosed\b).*(?:\bcheck\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bimage\b|\bdocument\b)",
                    r"\battached\b.*(?:\bcheck\b|\bproof\b|\breceipt\b|\bconfirmation\b|\bimage\b|\bdocument\b)",
                    r"\bhere\b.*\bis\b.*(?:\bproof\b|\breceipt\b|\bconfirmation\b|\bcheck\b|\bimage\b|\bdocument\b).*\battached\b"
                ],

                "Payment Details Received": [
                    # Future/pending payment info only with word boundaries
                    r"\bpayment\b.*\bwill\b.*\bbe\b.*\bsent\b",
                    r"\bpayment\b.*\bbeing\b.*\bprocessed\b",
                    r"\bcheck\b.*\bwill\b.*\bbe\b.*\bmailed\b",
                    r"\bpayment\b.*\bscheduled\b",
                    r"\bin\b.*\bprocess\b.*\bof\b.*\bissuing\b.*\bpayment\b",
                    r"\binvoices\b.*\bbeing\b.*\bprocessed\b.*\bfor\b.*\bpayment\b",
                    r"\bwill\b.*\bpay\b.*\bthis\b.*\bonline\b",
                    r"\bworking\b.*\bon\b.*\bpayment\b",
                    r"\bneed\b.*\btime\b.*\bto\b.*\bpay\b",
                    r"\bpayment\b.*\bin\b.*\bprogress\b"
                ]
            },

            "Auto Reply (with/without info)": {
                "With Alternate Contact": [
                    # OOO/autoreply with contact information with word boundaries
                    r"\bout\b.*\bof\b.*\boffice\b.*(?:\bcontact\b|\breach\b|\bplease\b.*\bemail\b|\bcall\b|\breach\b.*\bme\b.*\bat\b)",
                    r"\bfor\b.*\bimmediate\b.*\bassistance\b.*(?:\bcontact\b|\bemail\b|\bcall\b)",
                    r"\burgent\b.*\bmatters\b.*(?:\bcontact\b|\bemail\b|\bcall\b)",
                    r"\bin\b.*\bmy\b.*\babsence\b.*(?:\bcontact\b|\bemail\b|\bcall\b)",
                    r"\bplease\b.*\bcontact\b.*(?:\bcolleague\b|\bsomeone\b.*\belse\b|\bthe\b.*\bfollowing\b|\balternate\b|\balternate\b.*\bcontact\b)",
                    r"\bif\b.*\burgent\b.*(?:\bcontact\b|\bemail\b|\bcall\b)",
                    r"\bfor\b.*\bsupport\b.*(?:\bcontact\b|\bemail\b|\bcall\b)",
                    r"\balternate\b.*\bcontact\b",
                    r"\bemergency\b.*\bcontact\b.*\bnumber\b",
                    r"\burgent\b.*\bmatters\b.*\bcontact\b",
                    r"\bimmediate\b.*\bassistance\b.*\bcontact\b",
                    r"\bcontact\b.*\bme\b.*\bat\b",
                    r"\breach\b.*\bme\b.*\bat\b",
                    r"\bcall\b.*\bfor\b.*\burgent\b",
                    r"\bemergency\b.*\bcontact\b.*\binformation\b"
                ],

                "Return Date Specified": [
                    # OOO with specific return date with word boundaries
                    r"\bout\b.*\bof\b.*\boffice\b.*\buntil\b.*\d{1,2}[\-/]\d{1,2}",
                    r"\bout\b.*\bof\b.*\boffice\b.*\buntil\b.*(?:\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b|\bfriday\b|\bsaturday\b|\bsunday\b)",
                    r"\breturn\b.*(?:\bon\b|\bby\b|\bafter\b|\buntil\b|\bto\b.*\bwork\b.*\bon\b).*[\w\s,]+(?:\d{1,2}[\-/]\d{1,2}|\d{4})",
                    r"\bwill\b.*\bbe\b.*\bback\b.*\bon\b.*\d{1,2}[\-/]\d{1,2}", 
                    r"\bexpected\b.*\breturn\b.*(?:\bdate\b|\bon\b).*[\w\s,]+",
                    r"\bback\b.*(?:\bon\b|\bby\b|\bin\b).*[\w\s,]+", 
                    r"\breturning\b.*(?:\bon\b|\bby\b|\bafter\b|\bin\b).*[\w\s,]+",
                    r"\bwill\b.*\breturn\b.*(?:\bon\b|\bby\b|\bafter\b|\bin\b).*[\w\s,]+",
                    r"\baway\b.*\buntil\b.*(?:\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b|\bfriday\b|\bsaturday\b|\bsunday\b)",
                    r"\bon\b.*\bvacation\b.*\buntil\b.*[\w\s,]+",
                    r"\bback\b.*\bafter\b.*\bthe\b.*\bholiday\b",
                    r"\breturn\b.*\bnext\b.*\bweek\b",
                    r"\bback\b.*\bnext\b.*\bweek\b",
                    r"\bout\b.*\buntil\b.*(?:\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b|\bfriday\b|\bsaturday\b|\bsunday\b)",
                    r"\breturn\b.*\bon\b.*(?:\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b|\bfriday\b|\bsaturday\b|\bsunday\b)",
                    r"\bback\b.*\bon\b.*(?:\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b|\bfriday\b|\bsaturday\b|\bsunday\b)",
                    r"\breturn\b.*(?:\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b|\bfriday\b|\bsaturday\b|\bsunday\b)",
                    r"\bback\b.*(?:\bmonday\b|\btuesday\b|\bwednesday\b|\bthursday\b|\bfriday\b|\bsaturday\b|\bsunday\b)",
                    r"\breturn\b.*\bafter\b.*\bholiday\b",
                    r"\bback\b.*\bafter\b.*\bholiday\b",
                    r"\breturning\b.*\bafter\b.*\bthe\b.*\bholiday\b",
                    r"\breturn\b.*\bto\b.*\boffice\b.*\bon\b",
                    r"\bback\b.*\bin\b.*\boffice\b.*\bon\b",
                    r"\breturning\b.*\bto\b.*\bwork\b.*\bon\b",
                    r"\bwill\b.*\breturn\b.*\bon\b",
                    r"\bback\b.*\bfrom\b.*\bvacation\b.*\bon\b",
                    r"\breturn\b.*\bdate\b.*\bis\b",
                    r"\bexpected\b.*\breturn\b.*\bdate\b",
                    r"\breturning\b.*\bfrom\b.*\bleave\b.*\bon\b"
                ],

                "No Info/Autoreply": [
                    # Generic OOO/auto-reply without contact or date with word boundaries
                    r"\bout\b.*\bof\b.*\boffice\b",
                    r"\bcurrently\b.*\bout\b",
                    r"\bon\b.*\bvacation\b",
                    r"\baway\b.*\bfrom\b.*\bdesk\b",
                    r"\bautomatic\b.*\breply\b",
                    r"\bauto-?reply\b",
                    r"\blimited\b.*\baccess\b.*\bto\b.*\bemail\b",
                    r"\bautomated\b.*\bresponse\b",
                    r"\bthis\b.*\bis\b.*\ban\b.*\bautomatic\b.*\breply\b",
                    r"\bi\b.*\bam\b.*\bcurrently\b.*\baway\b",
                    r"\bdo\b.*\bnot\b.*\breply\b",
                    r"\bthank\b.*\byou\b.*\bfor\b.*\byour\b.*\bemail\b",
                    r"\bcurrently\b.*\bunavailable\b"
                ],

                "Survey": [
                    # Survey and feedback requests with word boundaries
                    r"\bsurvey\b",
                    r"\bfeedback\b.*\brequest\b",
                    r"\brate\b.*\bout\b.*\bservice\b",
                    r"\bcustomer\b.*\bsatisfaction\b",
                    r"\btake\b.*\bout\b.*\bsurvey\b",
                    r"\bplease\b.*\bprovide\b.*\bfeedback\b",
                    r"\bhow\b.*\bdid\b.*\bwe\b.*\bdo\b",
                    r"\byour\b.*\bfeedback\b.*\bis\b.*\bimportant\b",
                    r"\bsurvey\b.*\blink\b",
                    r"\bcomplete\b.*\bsurvey\b",
                    r"\bservice\b.*\bevaluation\b",
                    r"\bfeedback\b.*\bform\b",
                    r"\bquestionnaire\b",
                    r"\bplease\b.*\brate\b"
                ],

                "Redirects/Updates (property changes)": [
                    # Contact changes and redirects with word boundaries
                    r"\bno\b.*\blonger\b.*\bwith\b",
                    r"\bno\b.*\blonger\b.*\bemployed\b",
                    r"\bcontact\b.*\bchanged\b",
                    r"\bproperty\b.*\bmanager\b.*\bchanged\b",
                    r"\bdepartment\b.*\bchanged\b",
                    r"\bmy\b.*\bemail\b.*\bhas\b.*\bchanged\b",
                    r"\bplease\b.*\bupdate\b.*\byour\b.*\brecords\b",
                    r"\bforward\b.*\bfuture\b.*\bemails\b.*\bto\b",
                    r"\bno\b.*\blonger\b.*\bwith\b.*\bcompany\b",
                    r"\bposition\b.*\bchanged\b",
                    r"\bemail\b.*\baddress\b.*\bchanged\b",
                    r"\bcontact\b.*\binformation\b.*\bupdated\b"
                ]
            }
        }

    def _compile_patterns(self) -> None:
        """Compile all patterns for optimal performance."""
        self.compiled_patterns = {}
        
        for main_cat, subcats in self.patterns.items():
            self.compiled_patterns[main_cat] = {}
            for subcat, patterns in subcats.items():
                self.compiled_patterns[main_cat][subcat] = [
                    re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                    for pattern in patterns
                ]
        
        self.logger.info(f"✅ Compiled {sum(len(subcats) for subcats in self.compiled_patterns.values())} pattern groups")

    def _initialize_mappings(self) -> None:
        """Initialize category and sublabel mappings."""
        
        # Main category mappings
        self.main_categories = {
            "Manual Review": "Manual Review",
            "No Reply (with/without info)": "No Reply (with/without info)",
            "Invoices Request": "Invoices Request", 
            "Payments Claim": "Payments Claim",
            "Auto Reply (with/without info)": "Auto Reply (with/without info)"
        }
        
        # Sublabel mappings - exact hierarchy names
        self.sublabels = {
            # Manual Review sublabels
            "Partial/Disputed Payment": "Partial/Disputed Payment",
            "Invoice Receipt": "Invoice Receipt", 
            "Closure Notification": "Closure Notification",
            "Closure + Payment Due": "Closure + Payment Due",
            "External Submission": "External Submission",
            "Invoice Errors (format mismatch)": "Invoice Errors (format mismatch)",
            "Inquiry/Redirection": "Inquiry/Redirection",
            "Complex Queries": "Complex Queries",
            
            # No Reply sublabels
            "Sales/Offers": "Sales/Offers",
            "System Alerts": "System Alerts",
            "Processing Errors": "Processing Errors", 
            "Business Closure (Info only)": "Business Closure (Info only)",
            "General (Thank You)": "General (Thank You)",
            "Created": "Created",
            "Resolved": "Resolved",
            "Open": "Open",
            
            # Invoice Request sublabel
            "Request (No Info)": "Request (No Info)",
            
            # Payments Claim sublabels
            "Claims Paid (No Info)": "Claims Paid (No Info)",
            "Payment Details Received": "Payment Details Received",
            "Payment Confirmation": "Payment Confirmation",
            
            # Auto Reply sublabels
            "With Alternate Contact": "With Alternate Contact",
            "No Info/Autoreply": "No Info/Autoreply",
            "Return Date Specified": "Return Date Specified",
            "Survey": "Survey",
            "Redirects/Updates (property changes)": "Redirects/Updates (property changes)"
        }

    def match_text(self, text: str, exclude_external_proof: bool = False) -> Tuple[Optional[str], Optional[str], float, List[str]]:
        """Main pattern matching with smart conflict resolution."""
        if not text or len(text.strip()) < 5:
            return None, None, 0.0, []
        
        text_lower = text.lower().strip()
        
        # External proof exclusion check
        if exclude_external_proof and self._has_external_proof_reference(text_lower):
            return None, None, 0.0, []
        
        all_matches = []
        
        # Collect pattern matches
        for main_cat, subcats in self.compiled_patterns.items():
            for subcat, patterns in subcats.items():
                matches = 0
                matched_patterns = []
                
                for pattern in patterns:
                    if pattern.search(text_lower):
                        matches += 1
                        matched_patterns.append(pattern.pattern)
                
                if matches > 0:
                    confidence = min(CONFIDENCE_BASE + (matches * CONFIDENCE_BOOST_PER_MATCH), MAX_CONFIDENCE)
                    all_matches.append({
                        'main_cat': main_cat,
                        'subcat': subcat,
                        'confidence': confidence,
                        'match_count': matches,
                        'patterns': matched_patterns
                    })
        
        if not all_matches:
            return None, None, 0.0, []
        
        # Smart conflict resolution
        best_match = self._resolve_conflicts(all_matches, text_lower)
        
        if best_match:
            return (
                self.main_categories[best_match['main_cat']],
                self.sublabels[best_match['subcat']],
                best_match['confidence'],
                best_match['patterns'][:3]
            )
        
        return None, None, 0.0, []

    def _resolve_conflicts(self, matches: List[Dict], text: str) -> Optional[Dict]:
        """Smart conflict resolution with essential business logic."""
        if not matches:
            return None
        
        if len(matches) == 1:
            return matches[0]
        
        # 1. Payment Confirmation vs Claims - check for proof numbers
        payment_conf = next((m for m in matches if m['subcat'] == 'Payment Confirmation'), None)
        payment_claim = next((m for m in matches if m['subcat'] == 'Claims Paid (No Info)'), None)
        
        if payment_conf and payment_claim:
            has_proof = any(re.search(pattern, text, re.I) for pattern in [
                r'\d{4,}', r'\beft#\b', r'\btransaction\b.*\d+', r'\bcheck\b.*\bnumber\b'
            ])
            return payment_conf if has_proof else payment_claim
        
        # 2. Invoice Receipt vs Request - check for attachment language
        invoice_receipt = next((m for m in matches if m['subcat'] == 'Invoice Receipt'), None)
        invoice_request = next((m for m in matches if m['subcat'] == 'Request (No Info)'), None)
        
        if invoice_receipt and invoice_request:
            has_attachment = any(word in text for word in ['attached', 'proof', 'enclosed'])
            return invoice_receipt if has_attachment else invoice_request
        
        # 3. Auto Reply vs Manual Review - favor Manual for business content
        auto_reply = next((m for m in matches if m['main_cat'] == 'Auto Reply (with/without info)'), None)
        manual = next((m for m in matches if m['main_cat'] == 'Manual Review'), None)
        
        if auto_reply and manual:
            business_count = sum(1 for term in ['payment', 'invoice', 'dispute'] if term in text)
            return manual if business_count >= 2 else auto_reply
        
        # 4. Survey vs Dispute - favor dispute for strong dispute language
        survey = next((m for m in matches if m['subcat'] == 'Survey'), None)
        dispute = next((m for m in matches if m['subcat'] == 'Partial/Disputed Payment'), None)
        
        if survey and dispute:
            strong_dispute = any(phrase in text for phrase in ['owe nothing', 'scam', 'fdcpa'])
            return dispute if strong_dispute else survey
        
        # 5. Priority order for remaining conflicts
        priority_order = [
            ('Manual Review', 'Partial/Disputed Payment'),
            ('Payments Claim', 'Payment Confirmation'),
            ('Manual Review', 'Invoice Receipt'),
            ('Invoices Request', 'Request (No Info)'),
            ('Payments Claim', 'Claims Paid (No Info)')
        ]
        
        for main_cat, subcat in priority_order:
            for match in matches:
                if match['main_cat'] == main_cat and match['subcat'] == subcat:
                    return match
        
        # Final fallback - highest confidence
        return max(matches, key=lambda x: (x['confidence'], x['match_count']))

    def _has_external_proof_reference(self, text: str) -> bool:
        """Check if text refers to external proof rather than providing proof."""
        external_phrases = [
            'if you look at your own email', 'you will see it was settled',
            'you sent an email confirming', 'please consult your client',
            'check with your client', 'you have the confirmation'
        ]
        return any(phrase in text for phrase in external_phrases)
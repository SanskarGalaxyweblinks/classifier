"""
Clean and simple email classification label hierarchy.
Removed General (Thank You) and optimized structure.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class Label:
    name: str
    description: str
    sublabels: Optional[List['Label']] = None

class LabelHierarchy:
    """Simple, efficient label hierarchy for email classification."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.root = self._create_hierarchy()
        self._label_cache = self._build_cache()
        self.logger.info("✅ Label hierarchy initialized")

    def _create_hierarchy(self) -> Label:
        """Create the hierarchy structure - Updated without General (Thank You)."""
        return Label(
            name="Root (Inbox)",
            description="Entry point for all emails",
            sublabels=[
                Label(
                    name="Manual Review",
                    description="Cases requiring human attention",
                    sublabels=[
                        Label(
                            name="Disputes & Payments",
                            description="Payment disputes and partial payment cases",
                            sublabels=[
                                Label(name="Partial/Disputed Payment", description="Payment disputes and contested charges")
                            ]
                        ),
                        Label(
                            name="Invoice Updates",
                            description="Updates related to invoices", 
                            sublabels=[
                                Label(name="Invoice Receipt", description="Providing proof of invoice received")
                            ]
                        ),
                        Label(
                            name="Business Closure",
                            description="Business closure related notifications",
                            sublabels=[
                                Label(name="Closure Notification", description="General business closure notices"),
                                Label(name="Closure + Payment Due", description="Business closure with outstanding payments")
                            ]
                        ),
                        Label(
                            name="Invoices",
                            description="Invoice related issues and submissions",
                            sublabels=[
                                Label(name="External Submission", description="Third-party invoice submission issues"),
                                Label(name="Invoice Errors (format mismatch)", description="Missing fields or invalid invoice formats")
                            ]
                        ),
                        Label(name="Inquiry/Redirection", description="Questions and contact redirections"),
                        Label(name="Complex Queries", description="Multiple topics requiring manual review")
                    ]
                ),
                Label(
                    name="No Reply (with/without info)",
                    description="System-generated, marketing, and informational emails",
                    sublabels=[
                        Label(
                            name="Notifications",
                            description="System and business notifications",
                            sublabels=[
                                Label(name="Sales/Offers", description="Promotions and marketing content"),
                                Label(name="System Alerts", description="System notifications and alerts"),
                                Label(name="Processing Errors", description="System failure and processing error notifications"),
                                Label(name="Business Closure (Info only)", description="Informational closure announcements")
                            ]
                        ),
                        Label(
                            name="Tickets/Cases",
                            description="Support ticket and case related notifications",
                            sublabels=[
                                Label(name="Created", description="New ticket creation notifications"),
                                Label(name="Resolved", description="Ticket resolution notifications"),
                                Label(name="Open", description="Open ticket status updates")
                            ]
                        )
                    ]
                ),
                Label(
                    name="Invoices Request",
                    description="Requests for invoice information",
                    sublabels=[
                        Label(name="Request (No Info)", description="Invoice requests without sufficient information")
                    ]
                ),
                Label(
                    name="Payments Claim",
                    description="Claims related to payments", 
                    sublabels=[
                        Label(name="Claims Paid (No Info)", description="Payment claims without supporting proof"),
                        Label(name="Payment Details Received", description="Payment details requiring manual verification"),
                        Label(name="Payment Confirmation", description="Payment claims with supporting proof")
                    ]
                ),
                Label(
                    name="Auto Reply (with/without info)",
                    description="Automated responses and out-of-office messages",
                    sublabels=[
                        Label(
                            name="Out of Office",
                            description="Out of office notifications",
                            sublabels=[
                                Label(name="With Alternate Contact", description="OOO with alternative contact information"),
                                Label(name="No Info/Autoreply", description="Generic OOO and auto-reply messages"),
                                Label(name="Return Date Specified", description="OOO with specific return date")
                            ]
                        ),
                        Label(
                            name="Miscellaneous",
                            description="Other automated responses",
                            sublabels=[
                                Label(name="Survey", description="Feedback requests and surveys"),
                                Label(name="Redirects/Updates (property changes)", description="Contact changes and redirections")
                            ]
                        )
                    ]
                ),
                Label(name="Uncategorized", description="Emails requiring review and retraining")
            ]
        )

    def _build_cache(self) -> Dict[str, Dict]:
        """Build cache for fast label lookups."""
        cache = {}
        
        def _cache_labels(label: Label, path: List[str] = []):
            current_path = path + [label.name]
            cache[label.name] = {
                'label': label,
                'path': current_path,
                'parent': path[-1] if path else None
            }
            
            if label.sublabels:
                for sublabel in label.sublabels:
                    _cache_labels(sublabel, current_path)
        
        _cache_labels(self.root)
        return cache

    def get_all_labels(self) -> List[str]:
        """Get all label names."""
        return list(self._label_cache.keys())

    def get_label_path(self, label_name: str) -> List[str]:
        """Get path to a label."""
        return self._label_cache.get(label_name, {}).get('path', [])

    def get_sublabels(self, label_name: str) -> List[str]:
        """Get direct sublabels."""
        if label_name in self._label_cache:
            label = self._label_cache[label_name]['label']
            if label.sublabels:
                return [sublabel.name for sublabel in label.sublabels]
        return []

    def get_parent(self, label_name: str) -> Optional[str]:
        """Get parent label."""
        return self._label_cache.get(label_name, {}).get('parent')

    def is_valid_label(self, label_name: str) -> bool:
        """Check if label exists."""
        return label_name in self._label_cache

    def get_main_categories(self) -> List[str]:
        """Get main categories."""
        return [label.name for label in self.root.sublabels] if self.root.sublabels else []

    def get_final_sublabels(self) -> List[str]:
        """Get leaf labels (no children)."""
        return [
            name for name, info in self._label_cache.items()
            if not info['label'].sublabels and name != "Root (Inbox)"
        ]

    def validate_classification(self, category: str, subcategory: str = None) -> bool:
        """Validate category/subcategory combination."""
        if not self.is_valid_label(category):
            return False
        
        if subcategory:
            if not self.is_valid_label(subcategory):
                return False
            path = self.get_label_path(subcategory)
            return category in path
        
        return True

    def search_labels(self, search_term: str) -> List[str]:
        """Search labels by name or description."""
        search_term = search_term.lower()
        return [
            name for name, info in self._label_cache.items()
            if search_term in name.lower() or 
               (info['label'].description and search_term in info['label'].description.lower())
        ]

    def get_hierarchy_info(self) -> Dict[str, int]:
        """Get basic hierarchy statistics."""
        return {
            'total_labels': len(self._label_cache),
            'main_categories': len(self.get_main_categories()),
            'final_sublabels': len(self.get_final_sublabels())
        }

    def export_structure(self) -> Dict:
        """Export hierarchy as dictionary."""
        def _export_label(label: Label) -> Dict:
            result = {'name': label.name, 'description': label.description}
            if label.sublabels:
                result['sublabels'] = [_export_label(sub) for sub in label.sublabels]
            return result
        
        return _export_label(self.root)
"""
Quality label hierarchy for email classification system.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

@dataclass
class Label:
    name: str
    description: str
    sublabels: Optional[List['Label']] = None
    rules: Optional[List[str]] = None

class LabelHierarchy:
    """Clean, efficient label hierarchy matching your exact structure."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.root = self._create_hierarchy()
        self._label_cache = {}  # Cache for fast lookups
        self._stats = {'usage': {}, 'failures': {}}  # Simple stats
        self._build_cache()
        self._initialize_statistics()
        self.logger.info("✅ Quality label hierarchy initialized")

    def _create_hierarchy(self) -> Label:
        """Create the exact hierarchy structure you specified."""
        return Label(
            name="Root (Inbox)",
            description="Entry point for all incoming emails",
            sublabels=[
                Label(
                    name="Manual Review",
                    description="Cases requiring human attention due to complexity, ambiguity, exceptions, or business risk",
                    sublabels=[
                        Label(
                            name="Disputes & Payments",
                            description="Payment disputes and partial payment cases",
                            sublabels=[
                                Label(name="Partial/Disputed Payment", description="Partial or disputed payment cases")
                            ]
                        ),
                        Label(
                            name="Payment/Invoice Updates", 
                            description="Updates related to payments and invoices",
                            sublabels=[
                                Label(name="Payment Confirmation", description="Payment proof requiring manual review"),
                                Label(name="Invoice Receipt", description="Invoice proof requiring manual logging")
                            ]
                        ),
                        Label(
                            name="Business Closure",
                            description="Business closure related notifications",
                            sublabels=[
                                Label(name="Closure Notification", description="General closure notices"),
                                Label(name="Closure + Payment Due", description="Closure notifications with outstanding dues")
                            ]
                        ),
                        Label(
                            name="Invoices",
                            description="Invoice related issues and submissions",
                            sublabels=[
                                Label(name="External Submission", description="Invoice issues from third parties"),
                                Label(name="Invoice Errors (format mismatch)", description="Invoices with missing fields or invalid formats")
                            ]
                        ),
                        Label(name="Payment Details Received", description="Payment remittance details requiring manual check"),
                        Label(name="Inquiry/Redirection", description="Redirections and alternate contact requests"),
                        Label(name="Complex Queries", description="Multiple topics requiring human review")
                    ]
                ),
                Label(
                    name="No Reply (with/without info)",
                    description="System-generated, marketing, informational, or alert mail",
                    sublabels=[
                        Label(
                            name="Notifications",
                            description="System and business notifications",
                            sublabels=[
                                Label(name="Sales/Offers", description="Promotions and marketing messages"),
                                Label(
                                    name="System Alerts",
                                    description="System generated alerts and notifications",
                                    sublabels=[
                                        Label(name="Processing Errors", description="Failure notifications from automated systems"),
                                        Label(name="Import Failures", description="Data import or sync issues")
                                    ]
                                ),
                                Label(name="Business Closure (Info only)", description="Closure announcements with no payment due")
                            ]
                        ),
                        Label(
                            name="Tickets/Cases",
                            description="Support ticket and case related notifications",
                            sublabels=[
                                Label(name="Created", description="Notification of new tickets or support cases"),
                                Label(name="Resolved", description="Emails notifying that a ticket or case has been closed"),
                                Label(name="Open", description="Updates that a case or ticket is still open - escalate to Manual Review")
                            ]
                        )
                    ]
                ),
                Label(
                    name="Invoices Request",
                    description="Requests for invoice information",
                    sublabels=[
                        Label(name="Request (No Info)", description="Invoice request missing key information")
                    ]
                ),
                Label(
                    name="Payments Claim", 
                    description="Claims related to payments",
                    sublabels=[
                        Label(name="Claims Paid (No Info)", description="Claims payment made but no proof attached")
                    ]
                ),
                Label(
                    name="Auto Reply (with/without info)",
                    description="Automated responses and acknowledgments",
                    sublabels=[
                        Label(
                            name="Out of Office",
                            description="Out of office notifications",
                            sublabels=[
                                Label(name="With Alternate Contact", description="OOO with alternative contact information"),
                                Label(name="No Info/Autoreply", description="Generic OOO messages"),
                                Label(name="Return Date Specified", description="OOO with return date")
                            ]
                        ),
                        Label(
                            name="Confirmations",
                            description="Confirmation messages and acknowledgments",
                            sublabels=[
                                Label(name="Case/Support", description="Support ticket confirmations"),
                                Label(name="General (Thank You)", description="General acknowledgments and thank you messages")
                            ]
                        ),
                        Label(
                            name="Miscellaneous",
                            description="Other automated responses",
                            sublabels=[
                                Label(name="Survey", description="Customer feedback requests and surveys"),
                                Label(name="Redirects/Updates (property changes)", description="Changes in property manager or contact info")
                            ]
                        )
                    ]
                ),
                Label(name="Uncategorized", description="Unrecognized emails needing manual review for retraining")
            ]
        )

    def _build_cache(self) -> None:
        """Build cache for fast label lookups."""
        def _cache_labels(label: Label, path: List[str] = []):
            current_path = path + [label.name]
            self._label_cache[label.name] = {
                'label': label,
                'path': current_path.copy(),
                'parent': path[-1] if path else None
            }
            
            if label.sublabels:
                for sublabel in label.sublabels:
                    _cache_labels(sublabel, current_path)
        
        _cache_labels(self.root)

    def get_all_labels(self) -> List[str]:
        """Get flat list of all label names."""
        return list(self._label_cache.keys())

    def get_label_path(self, label_name: str) -> List[str]:
        """Get full path to a label."""
        if label_name in self._label_cache:
            return self._label_cache[label_name]['path']
        
        self.logger.warning(f"Label '{label_name}' not found")
        return []

    def get_sublabels(self, label_name: str) -> List[str]:
        """Get direct sublabels for a given label."""
        if label_name in self._label_cache:
            label = self._label_cache[label_name]['label']
            if label.sublabels:
                return [sublabel.name for sublabel in label.sublabels]
        return []

    def get_all_sublabels(self, label_name: str) -> List[str]:
        """Get all sublabels (recursive) for a given label."""
        sublabels = []
        
        def _collect_sublabels(label: Label):
            if label.sublabels:
                for sublabel in label.sublabels:
                    sublabels.append(sublabel.name)
                    _collect_sublabels(sublabel)
        
        if label_name in self._label_cache:
            label = self._label_cache[label_name]['label']
            _collect_sublabels(label)
        
        return sublabels

    def get_parent(self, label_name: str) -> Optional[str]:
        """Get parent label name."""
        if label_name in self._label_cache:
            return self._label_cache[label_name]['parent']
        return None

    def is_valid_label(self, label_name: str) -> bool:
        """Check if label exists in hierarchy."""
        return label_name in self._label_cache

    def get_main_categories(self) -> List[str]:
        """Get all main category names."""
        if self.root.sublabels:
            return [label.name for label in self.root.sublabels]
        return []

    def get_final_sublabels(self) -> List[str]:
        """Get all final (leaf) sublabels that have no children."""
        final_sublabels = []
        
        for label_name, info in self._label_cache.items():
            label = info['label']
            if not label.sublabels and label_name != "Root (Inbox)":
                final_sublabels.append(label_name)
        
        return final_sublabels

    def validate_classification(self, category: str, subcategory: str) -> bool:
        """Validate if category/subcategory combination is valid."""
        # Check if category exists
        if not self.is_valid_label(category):
            return False
        
        # Check if subcategory exists and belongs to category
        if subcategory:
            if not self.is_valid_label(subcategory):
                return False
            
            # Check if subcategory is under category
            path = self.get_label_path(subcategory)
            return category in path
        
        return True

    def get_label_info(self, label_name: str) -> Dict[str, any]:
        """Get comprehensive information about a label."""
        if label_name not in self._label_cache:
            return {}
        
        info = self._label_cache[label_name]
        label = info['label']
        
        return {
            'name': label.name,
            'description': label.description,
            'path': info['path'],
            'parent': info['parent'],
            'sublabels': self.get_sublabels(label_name),
            'is_final': not bool(label.sublabels),
            'depth': len(info['path']) - 1
        }

    def get_hierarchy_stats(self) -> Dict[str, int]:
        """Get statistics about the hierarchy."""
        total_labels = len(self._label_cache)
        main_categories = len(self.get_main_categories())
        final_sublabels = len(self.get_final_sublabels())
        
        # Calculate depth distribution
        depths = {}
        for info in self._label_cache.values():
            depth = len(info['path']) - 1
            depths[depth] = depths.get(depth, 0) + 1
        
        return {
            'total_labels': total_labels,
            'main_categories': main_categories,
            'final_sublabels': final_sublabels,
            'max_depth': max(depths.keys()) if depths else 0,
            'depth_distribution': depths
        }

    def search_labels(self, search_term: str) -> List[str]:
        """Search for labels containing the search term."""
        search_term = search_term.lower()
        matching_labels = []
        
        for label_name, info in self._label_cache.items():
            label = info['label']
            if (search_term in label_name.lower() or 
                (label.description and search_term in label.description.lower())):
                matching_labels.append(label_name)
        
        return matching_labels

    def _initialize_validation_rules(self) -> None:
        """Initialize validation rules for each label."""
        self._validation_rules = {
            # Manual Review validation rules
            "Manual Review": {
                "required_keywords": ["manual", "review", "human", "attention"],
                "confidence_threshold": 0.6,
                "escalation_rules": ["high_complexity", "dispute", "closure"]
            },
            
            "Partial/Disputed Payment": {
                "required_keywords": ["partial", "dispute", "contested", "disagreement"],
                "forbidden_keywords": ["full payment", "complete payment"],
                "confidence_threshold": 0.7
            },
            
            "Payment Confirmation": {
                "required_keywords": ["proof", "confirmation", "evidence", "receipt"],
                "attachment_required": True,
                "confidence_threshold": 0.8
            },
            
            "Invoice Receipt": {
                "required_keywords": ["invoice", "receipt", "copy", "attached"],
                "attachment_required": True,
                "confidence_threshold": 0.8
            },
            
            "Closure Notification": {
                "required_keywords": ["closed", "closure", "terminated", "ceased"],
                "forbidden_keywords": ["payment due", "outstanding"],
                "confidence_threshold": 0.7
            },
            
            "Closure + Payment Due": {
                "required_keywords": ["closed", "payment due", "outstanding", "final payment"],
                "confidence_threshold": 0.8
            },
            
            "External Submission": {
                "required_keywords": ["invoice issue", "invoice problem", "invoice error"],
                "confidence_threshold": 0.7
            },
            
            "Invoice Errors (format mismatch)": {
                "required_keywords": ["missing field", "format", "incomplete", "error"],
                "confidence_threshold": 0.7
            },
            
            "Payment Details Received": {
                "required_keywords": ["payment details", "remittance", "breakdown"],
                "manual_review_required": True,
                "confidence_threshold": 0.8
            },
            
            # No Reply validation rules
            "No Reply (with/without info)": {
                "automated_response": True,
                "response_required": False,
                "confidence_threshold": 0.6
            },
            
            "Sales/Offers": {
                "required_keywords": ["offer", "promotion", "discount", "sale"],
                "response_required": False,
                "confidence_threshold": 0.7
            },
            
            "Processing Errors": {
                "required_keywords": ["processing error", "failed", "error"],
                "system_alert": True,
                "confidence_threshold": 0.8
            },
            
            "Import Failures": {
                "required_keywords": ["import failed", "import error", "sync error"],
                "system_alert": True,
                "confidence_threshold": 0.8
            },
            
            "Created": {
                "required_keywords": ["ticket created", "case opened", "new ticket"],
                "response_required": False,
                "confidence_threshold": 0.8
            },
            
            "Resolved": {
                "required_keywords": ["resolved", "closed", "completed"],
                "response_required": False,
                "confidence_threshold": 0.8
            },
            
            "Open": {
                "required_keywords": ["open", "pending", "in progress"],
                "escalation_rule": "Manual Review",
                "confidence_threshold": 0.7
            },
            
            # Auto Reply validation rules
            "Auto Reply (with/without info)": {
                "automated_response": True,
                "confidence_threshold": 0.6
            },
            
            "With Alternate Contact": {
                "required_keywords": ["contact", "reach out", "alternative"],
                "contact_info_required": True,
                "confidence_threshold": 0.8
            },
            
            "No Info/Autoreply": {
                "required_keywords": ["out of office", "away", "automatic"],
                "confidence_threshold": 0.8
            },
            
            "Return Date Specified": {
                "required_keywords": ["return", "back on", "until"],
                "date_required": True,
                "confidence_threshold": 0.8
            },
            
            "General (Thank You)": {
                "required_keywords": ["thank", "thanks", "received"],
                "confidence_threshold": 0.7
            },
            
            # Simple category rules
            "Invoices Request": {
                "required_keywords": ["invoice", "send", "request"],
                "confidence_threshold": 0.7
            },
            
            "Payments Claim": {
                "required_keywords": ["payment", "paid", "check sent"],
                "proof_required": False,
                "confidence_threshold": 0.7
            },
            
            "Uncategorized": {
                "fallback_category": True,
                "confidence_threshold": 0.3
            }
        }

    def _initialize_statistics(self) -> None:
        """Initialize statistics tracking for labels."""
        self._statistics = {
            'usage_count': {},
            'confidence_scores': {},
            'validation_failures': {},
            'escalation_count': {},
            'processing_time': {},
            'accuracy_metrics': {}
        }
        
        # Initialize counters for all labels
        for label_name in self._label_cache.keys():
            self._statistics['usage_count'][label_name] = 0
            self._statistics['confidence_scores'][label_name] = []
            self._statistics['validation_failures'][label_name] = 0
            self._statistics['escalation_count'][label_name] = 0
            self._statistics['processing_time'][label_name] = []

    def validate_label_assignment(self, label_name: str, text: str, confidence: float, 
                                 has_attachments: bool = False, contact_info: str = None) -> Dict[str, any]:
        """Comprehensive label validation with business rules."""
        
        if label_name not in self._validation_rules:
            return {
                'valid': False,
                'reason': f'No validation rules defined for {label_name}',
                'suggested_action': 'review_rules'
            }
        
        rules = self._validation_rules[label_name]
        validation_result = {
            'valid': True,
            'confidence_valid': True,
            'keyword_valid': True,
            'business_rule_valid': True,
            'issues': [],
            'suggested_action': None
        }
        
        # Check confidence threshold
        min_confidence = rules.get('confidence_threshold', 0.5)
        if confidence < min_confidence:
            validation_result['confidence_valid'] = False
            validation_result['issues'].append(f'Confidence {confidence:.2f} below threshold {min_confidence}')
        
        # Check required keywords
        if 'required_keywords' in rules:
            text_lower = text.lower()
            required_found = any(keyword in text_lower for keyword in rules['required_keywords'])
            if not required_found:
                validation_result['keyword_valid'] = False
                validation_result['issues'].append(f'Missing required keywords: {rules["required_keywords"]}')
        
        # Check forbidden keywords
        if 'forbidden_keywords' in rules:
            text_lower = text.lower()
            forbidden_found = any(keyword in text_lower for keyword in rules['forbidden_keywords'])
            if forbidden_found:
                validation_result['keyword_valid'] = False
                validation_result['issues'].append(f'Contains forbidden keywords')
        
        # Check business-specific rules
        if rules.get('attachment_required', False) and not has_attachments:
            validation_result['business_rule_valid'] = False
            validation_result['issues'].append('Attachment required but not provided')
        
        if rules.get('contact_info_required', False) and not contact_info:
            validation_result['business_rule_valid'] = False
            validation_result['issues'].append('Contact information required but not provided')
        
        if rules.get('date_required', False):
            # Simple date pattern check
            import re
            date_patterns = [r'\d{1,2}/\d{1,2}/\d{4}', r'\d{4}-\d{2}-\d{2}', r'(january|february|march|april|may|june|july|august|september|october|november|december)']
            has_date = any(re.search(pattern, text.lower()) for pattern in date_patterns)
            if not has_date:
                validation_result['business_rule_valid'] = False
                validation_result['issues'].append('Date information required but not found')
        
        # Check for escalation rules
        if 'escalation_rule' in rules:
            validation_result['suggested_action'] = f'escalate_to_{rules["escalation_rule"].replace(" ", "_").lower()}'
        
        # Overall validation
        validation_result['valid'] = (validation_result['confidence_valid'] and 
                                    validation_result['keyword_valid'] and 
                                    validation_result['business_rule_valid'])
        
        # Update statistics
        self._update_validation_statistics(label_name, validation_result['valid'])
        
        return validation_result

    def get_label_statistics(self, label_name: str = None) -> Dict[str, any]:
        """Get comprehensive statistics for labels."""
        
        if label_name:
            # Statistics for specific label
            if label_name not in self._statistics['usage_count']:
                return {'error': f'No statistics available for {label_name}'}
            
            confidence_scores = self._statistics['confidence_scores'][label_name]
            processing_times = self._statistics['processing_time'][label_name]
            
            return {
                'label_name': label_name,
                'usage_count': self._statistics['usage_count'][label_name],
                'avg_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                'min_confidence': min(confidence_scores) if confidence_scores else 0,
                'max_confidence': max(confidence_scores) if confidence_scores else 0,
                'validation_failures': self._statistics['validation_failures'][label_name],
                'escalation_count': self._statistics['escalation_count'][label_name],
                'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'success_rate': self._calculate_success_rate(label_name)
            }
        
        else:
            # Overall statistics
            total_usage = sum(self._statistics['usage_count'].values())
            total_failures = sum(self._statistics['validation_failures'].values())
            
            # Top used labels
            sorted_usage = sorted(self._statistics['usage_count'].items(), key=lambda x: x[1], reverse=True)
            top_labels = dict(sorted_usage[:10])
            
            # Labels with most failures
            sorted_failures = sorted(self._statistics['validation_failures'].items(), key=lambda x: x[1], reverse=True)
            problem_labels = dict(sorted_failures[:5])
            
            return {
                'total_classifications': total_usage,
                'total_validation_failures': total_failures,
                'overall_success_rate': ((total_usage - total_failures) / max(total_usage, 1)) * 100,
                'top_used_labels': top_labels,
                'problem_labels': problem_labels,
                'label_distribution': self._get_label_distribution(),
                'performance_metrics': self._get_performance_metrics()
            }

    def _update_validation_statistics(self, label_name: str, is_valid: bool) -> None:
        """Update validation statistics for a label."""
        if not is_valid:
            self._statistics['validation_failures'][label_name] += 1

    def update_usage_statistics(self, label_name: str, confidence: float, processing_time: float = 0) -> None:
        """Update usage statistics for a label."""
        if label_name in self._statistics['usage_count']:
            self._statistics['usage_count'][label_name] += 1
            self._statistics['confidence_scores'][label_name].append(confidence)
            if processing_time > 0:
                self._statistics['processing_time'][label_name].append(processing_time)

    def _calculate_success_rate(self, label_name: str) -> float:
        """Calculate success rate for a specific label."""
        usage = self._statistics['usage_count'][label_name]
        failures = self._statistics['validation_failures'][label_name]
        return ((usage - failures) / max(usage, 1)) * 100

    def _get_label_distribution(self) -> Dict[str, float]:
        """Get distribution of label usage as percentages."""
        total = sum(self._statistics['usage_count'].values())
        if total == 0:
            return {}
        
        return {
            label: (count / total) * 100 
            for label, count in self._statistics['usage_count'].items() 
            if count > 0
        }

    def _get_performance_metrics(self) -> Dict[str, any]:
        """Get overall performance metrics."""
        all_confidences = []
        all_times = []
        
        for confidences in self._statistics['confidence_scores'].values():
            all_confidences.extend(confidences)
        
        for times in self._statistics['processing_time'].values():
            all_times.extend(times)
        
        return {
            'avg_confidence_global': sum(all_confidences) / len(all_confidences) if all_confidences else 0,
            'avg_processing_time_global': sum(all_times) / len(all_times) if all_times else 0,
            'total_processed': len(all_confidences)
        }

    def get_validation_rules(self, label_name: str) -> Dict[str, any]:
        """Get validation rules for a specific label."""
        return self._validation_rules.get(label_name, {})

    def reset_statistics(self) -> None:
        """Reset all statistics (useful for testing or new periods)."""
        self._initialize_statistics()
        self.logger.info("📊 Label statistics reset")

    def export_structure(self) -> Dict:
        """Export hierarchy structure for external use."""
        def _export_label(label: Label) -> Dict:
            result = {
                'name': label.name,
                'description': label.description
            }
            if label.sublabels:
                result['sublabels'] = [_export_label(sublabel) for sublabel in label.sublabels]
            return result
        
        return _export_label(self.root)
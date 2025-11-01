"""
Data access and filtering service.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class DataService:
    """Service for accessing annotation data."""

    def __init__(self):
        """Initialize data service."""
        self.base_dir = Path(__file__).parent.parent.parent
        self.domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]

    def get_annotations(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get paginated list of annotations with filters."""
        all_records = []

        annotator_ids = filters.get("annotator_ids", [1, 2, 3, 4, 5])
        domains = filters.get("domains", self.domains)
        malformed_only = filters.get("malformed_only", False)
        completed_only = filters.get("completed_only", False)
        search_text = filters.get("search_text")
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 50)

        # Read annotations from selected workers
        for annotator_id in annotator_ids:
            for domain in domains:
                annotations_path = self.base_dir / "data" / "annotations" / f"annotator_{annotator_id}" / domain / "annotations.jsonl"
                
                if not annotations_path.exists():
                    continue

                # Read JSONL file
                with open(annotations_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                            record["annotator_id"] = annotator_id
                            record["domain"] = domain

                            # Apply filters
                            if malformed_only and not record.get("malformed", False):
                                continue
                            if completed_only and record.get("malformed", False):
                                continue
                            if search_text:
                                text = record.get("text", "").lower()
                                if search_text.lower() not in text:
                                    continue
                            if date_from:
                                record_time = datetime.fromisoformat(record.get("timestamp", ""))
                                if record_time < date_from:
                                    continue
                            if date_to:
                                record_time = datetime.fromisoformat(record.get("timestamp", ""))
                                if record_time > date_to:
                                    continue

                            all_records.append(record)
                        except json.JSONDecodeError:
                            continue

        # Sort by timestamp (newest first)
        all_records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Paginate
        total = len(all_records)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = all_records[start_idx:end_idx]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

    def get_worker_annotations(self, annotator_id: int, domain: str, limit: int = 100) -> Dict[str, Any]:
        """Get all annotations for a specific worker."""
        annotations_path = self.base_dir / "data" / "annotations" / f"annotator_{annotator_id}" / domain / "annotations.jsonl"

        annotations = []

        if not annotations_path.exists():
            # Return empty list if no annotations yet
            return {
                "annotator_id": annotator_id,
                "domain": domain,
                "annotations": [],
                "total": 0
            }

        # Read all annotations (up to limit)
        with open(annotations_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    annotations.append(record)

                    if len(annotations) >= limit:
                        break
                except json.JSONDecodeError:
                    continue

        # Return newest first
        annotations.reverse()

        return {
            "annotator_id": annotator_id,
            "domain": domain,
            "annotations": annotations,
            "total": len(annotations)
        }

    def get_annotation(self, annotator_id: int, domain: str, sample_id: str) -> Dict[str, Any]:
        """Get specific annotation detail."""
        annotations_path = self.base_dir / "data" / "annotations" / f"annotator_{annotator_id}" / domain / "annotations.jsonl"

        if not annotations_path.exists():
            raise FileNotFoundError(f"Annotations not found for annotator {annotator_id}, domain {domain}")

        # Search for the annotation
        with open(annotations_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if record.get("id") == sample_id:
                        record["annotator_id"] = annotator_id
                        record["domain"] = domain
                        return record
                except json.JSONDecodeError:
                    continue

        raise FileNotFoundError(f"Annotation not found: {sample_id}")

    def get_statistics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get aggregated statistics."""
        if not filters:
            filters = {}

        annotator_ids = filters.get("annotator_ids", [1, 2, 3, 4, 5])
        domains = filters.get("domains", self.domains)

        total_annotations = 0
        malformed_count = 0
        by_domain = {}
        by_annotator = {}
        label_distribution = {}

        for annotator_id in annotator_ids:
            by_annotator[str(annotator_id)] = {"total": 0, "malformed": 0}

            for domain in domains:
                if domain not in by_domain:
                    by_domain[domain] = {"total": 0, "malformed": 0}
                if domain not in label_distribution:
                    label_distribution[domain] = {}

                annotations_path = self.base_dir / "data" / "annotations" / f"annotator_{annotator_id}" / domain / "annotations.jsonl"
                
                if not annotations_path.exists():
                    continue

                with open(annotations_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                            total_annotations += 1
                            by_domain[domain]["total"] += 1
                            by_annotator[str(annotator_id)]["total"] += 1

                            if record.get("malformed", False):
                                malformed_count += 1
                                by_domain[domain]["malformed"] += 1
                                by_annotator[str(annotator_id)]["malformed"] += 1
                            else:
                                # Count label
                                label = record.get("label", "UNKNOWN")
                                if label not in label_distribution[domain]:
                                    label_distribution[domain][label] = 0
                                label_distribution[domain][label] += 1

                        except json.JSONDecodeError:
                            continue

        malformed_percentage = (malformed_count / total_annotations * 100) if total_annotations > 0 else 0.0

        return {
            "total_annotations": total_annotations,
            "malformed_count": malformed_count,
            "malformed_percentage": round(malformed_percentage, 2),
            "by_domain": by_domain,
            "by_annotator": by_annotator,
            "label_distribution": label_distribution
        }

"""
Progress tracking and reporting utilities
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ProcessingStats:
    """Statistics for processing operations"""

    total: int = 0
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    errors: List[str] = field(default_factory=list)

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.total == 0:
            return 0.0
        return (self.processed / self.total) * 100

    @property
    def items_per_second(self) -> float:
        """Get processing rate"""
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0
        return self.processed / elapsed

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total": self.total,
            "processed": self.processed,
            "failed": self.failed,
            "skipped": self.skipped,
            "elapsed_time": self.elapsed_time,
            "success_rate": self.success_rate,
            "items_per_second": self.items_per_second,
            "start_time": (
                datetime.fromtimestamp(self.start_time).isoformat()
                if self.start_time
                else None
            ),
            "end_time": (
                datetime.fromtimestamp(self.end_time).isoformat()
                if self.end_time
                else None
            ),
            "error_count": len(self.errors),
        }


class ProgressTracker:
    """Track progress of pipeline operations"""

    def __init__(self, operation_name: str, report_file: Optional[Path] = None):
        self.operation_name = operation_name
        self.report_file = report_file
        self.stats = ProcessingStats()
        self.stats.start_time = time.time()

    def start(self, total: int):
        """Start tracking"""
        self.stats.total = total
        self.stats.start_time = time.time()

    def mark_processed(self):
        """Mark an item as processed"""
        self.stats.processed += 1

    def mark_failed(self, error: Optional[str] = None):
        """Mark an item as failed"""
        self.stats.failed += 1
        if error:
            self.stats.errors.append(error)

    def mark_skipped(self):
        """Mark an item as skipped"""
        self.stats.skipped += 1

    def finish(self):
        """Finish tracking"""
        self.stats.end_time = time.time()
        if self.report_file:
            self.save_report()

    def print_summary(self):
        """Print progress summary"""
        elapsed = self.stats.elapsed_time
        rate = self.stats.items_per_second

        print(f"\n{'='*80}")
        print(f"{self.operation_name.upper()} - SUMMARY")
        print(f"{'='*80}")
        print(f"Total:        {self.stats.total}")
        print(f"Processed:    {self.stats.processed} ({self.stats.success_rate:.1f}%)")
        print(f"Failed:       {self.stats.failed}")
        print(f"Skipped:      {self.stats.skipped}")
        print(f"Elapsed:      {elapsed:.1f} seconds")
        print(f"Rate:         {rate:.2f} items/second")
        if self.stats.errors:
            print(f"\nErrors ({len(self.stats.errors)}):")
            for error in self.stats.errors[:10]:  # Show first 10
                print(f"  - {error}")
            if len(self.stats.errors) > 10:
                print(f"  ... and {len(self.stats.errors) - 10} more")
        print(f"{'='*80}\n")

    def save_report(self):
        """Save progress report to file"""
        if not self.report_file:
            return

        self.report_file.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "operation": self.operation_name,
            "stats": self.stats.to_dict(),
            "timestamp": datetime.now().isoformat(),
        }

        with open(self.report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    def get_progress_string(self) -> str:
        """Get current progress as string"""
        if self.stats.total == 0:
            return f"{self.operation_name}: Starting..."

        percentage = (self.stats.processed / self.stats.total) * 100
        return f"{self.operation_name}: {self.stats.processed}/{self.stats.total} ({percentage:.1f}%)"

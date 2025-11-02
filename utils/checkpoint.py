"""
Checkpoint management for resume capability
"""

import json
from pathlib import Path
from typing import Set, Optional
from datetime import datetime


class CheckpointManager:
    """Manage checkpoints for pipeline progress"""
    
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        self.processed_ids: Set[str] = set()
        self.failed_ids: Set[str] = set()
        self.load()
    
    def load(self):
        """Load checkpoint from file"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get("processed_ids", []))
                    self.failed_ids = set(data.get("failed_ids", []))
            except Exception as e:
                print(f"⚠️  Warning: Could not load checkpoint: {e}")
                self.processed_ids = set()
                self.failed_ids = set()
    
    def save(self):
        """Save checkpoint to file"""
        try:
            data = {
                "processed_ids": list(self.processed_ids),
                "failed_ids": list(self.failed_ids),
                "last_updated": datetime.now().isoformat()
            }
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save checkpoint: {e}")
    
    def is_processed(self, article_id: str) -> bool:
        """Check if article has been processed"""
        return article_id in self.processed_ids
    
    def mark_processed(self, article_id: str):
        """Mark article as processed"""
        self.processed_ids.add(article_id)
        if article_id in self.failed_ids:
            self.failed_ids.remove(article_id)
        self.save()
    
    def mark_failed(self, article_id: str):
        """Mark article as failed"""
        self.failed_ids.add(article_id)
        self.save()
    
    def get_stats(self) -> dict:
        """Get checkpoint statistics"""
        return {
            "processed_count": len(self.processed_ids),
            "failed_count": len(self.failed_ids),
            "total": len(self.processed_ids) + len(self.failed_ids)
        }
    
    def reset(self):
        """Reset checkpoint (clear all progress)"""
        self.processed_ids = set()
        self.failed_ids = set()
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
    
    def filter_unprocessed(self, article_files: list) -> list:
        """Filter out already processed articles"""
        unprocessed = []
        for article_file in article_files:
            # Try to get article_id from filename or need to load
            article_id = None
            if "article_id" in str(article_file):
                # Try to extract from filename like extraction_tc_xxx.json
                parts = article_file.stem.split("_")
                if len(parts) >= 2:
                    article_id = "_".join(parts[1:])
            
            # If we can't determine from filename, need to load file
            if not article_id:
                try:
                    with open(article_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        article_id = data.get("article_id") or data.get("metadata", {}).get("article_id")
                except:
                    # If we can't load, include it (safer to process than skip)
                    unprocessed.append(article_file)
                    continue
            
            if article_id and not self.is_processed(article_id):
                unprocessed.append(article_file)
        
        return unprocessed


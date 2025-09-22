"""
Progress tracking system for resumable translations.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Set

class ProgressTracker:
    """Tracks translation progress and allows resuming from interruption."""
    
    def __init__(self, progress_file: str = "translation_progress.json"):
        self.progress_file = progress_file
        self.progress_data = self._load_progress()
    
    def _load_progress(self) -> Dict:
        """Load existing progress data."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Return default progress structure
        return {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "target_language": "",
            "total_chunks": 0,
            "completed_chunks": [],
            "failed_chunks": [],
            "start_time": None,
            "last_update": None,
            "output_file": ""
        }
    
    def start_session(self, target_language: str, total_chunks: int, output_file: str):
        """Start a new translation session."""
        self.progress_data = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "target_language": target_language,
            "total_chunks": total_chunks,
            "completed_chunks": [],
            "failed_chunks": [],
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "output_file": output_file
        }
        self._save_progress()
    
    def mark_chunk_completed(self, chunk_filename: str, output_size: int, duration: float):
        """Mark a chunk as completed."""
        if chunk_filename not in self.progress_data["completed_chunks"]:
            self.progress_data["completed_chunks"].append({
                "filename": chunk_filename,
                "completed_at": datetime.now().isoformat(),
                "output_size": output_size,
                "duration": duration
            })
        
        # Remove from failed chunks if it was there
        self.progress_data["failed_chunks"] = [
            chunk for chunk in self.progress_data["failed_chunks"] 
            if chunk.get("filename") != chunk_filename
        ]
        
        self.progress_data["last_update"] = datetime.now().isoformat()
        self._save_progress()
    
    def mark_chunk_failed(self, chunk_filename: str, error: str):
        """Mark a chunk as failed."""
        failed_chunk = {
            "filename": chunk_filename,
            "failed_at": datetime.now().isoformat(),
            "error": error
        }
        
        # Remove from completed chunks if it was there
        self.progress_data["completed_chunks"] = [
            chunk for chunk in self.progress_data["completed_chunks"] 
            if chunk.get("filename") != chunk_filename
        ]
        
        # Add to failed chunks if not already there
        if not any(chunk.get("filename") == chunk_filename for chunk in self.progress_data["failed_chunks"]):
            self.progress_data["failed_chunks"].append(failed_chunk)
        
        self.progress_data["last_update"] = datetime.now().isoformat()
        self._save_progress()
    
    def get_completed_chunks(self) -> Set[str]:
        """Get set of completed chunk filenames."""
        return {chunk["filename"] for chunk in self.progress_data["completed_chunks"]}
    
    def get_failed_chunks(self) -> Set[str]:
        """Get set of failed chunk filenames."""
        return {chunk["filename"] for chunk in self.progress_data["failed_chunks"]}
    
    def get_remaining_chunks(self, all_chunk_files: List[str]) -> List[str]:
        """Get list of chunks that still need to be processed."""
        completed = self.get_completed_chunks()
        return [chunk for chunk in all_chunk_files if chunk not in completed]
    
    def get_progress_stats(self) -> Dict:
        """Get progress statistics."""
        total = self.progress_data["total_chunks"]
        completed = len(self.progress_data["completed_chunks"])
        failed = len(self.progress_data["failed_chunks"])
        
        return {
            "total_chunks": total,
            "completed_chunks": completed,
            "failed_chunks": failed,
            "remaining_chunks": total - completed,
            "completion_percentage": (completed / total * 100) if total > 0 else 0,
            "session_id": self.progress_data["session_id"],
            "target_language": self.progress_data["target_language"]
        }
    
    def _save_progress(self):
        """Save progress data to file."""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"⚠️  Warning: Could not save progress: {e}")
    
    def clear_progress(self):
        """Clear all progress data."""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        self.progress_data = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "target_language": "",
            "total_chunks": 0,
            "completed_chunks": [],
            "failed_chunks": [],
            "start_time": None,
            "last_update": None,
            "output_file": ""
        }
    
    def is_session_active(self) -> bool:
        """Check if there's an active session that can be resumed."""
        return (len(self.progress_data["completed_chunks"]) > 0 or 
                len(self.progress_data["failed_chunks"]) > 0)
    
    def get_session_info(self) -> str:
        """Get formatted session information."""
        stats = self.get_progress_stats()
        return (f"Session: {stats['session_id']} | "
                f"Language: {stats['target_language']} | "
                f"Progress: {stats['completed_chunks']}/{stats['total_chunks']} "
                f"({stats['completion_percentage']:.1f}%)")

"""Archive Scanner Service"""

import os
import asyncio
import subprocess
import json
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.file_stats import FileStats, FolderStats
from app.services.utils import get_mime_type

# Video/Audio extensions that support duration extraction
MEDIA_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'
}


class ArchiveScanner:
    """Scanner for archive directory"""

    def __init__(self, db: AsyncSession, state: Dict[str, Any]):
        self.db = db
        self.state = state
        self.files_processed = 0
        self.folders_processed = 0

    def _get_archive_path(self) -> str:
        """Get the full archive path"""
        # Use local mounted path if available (recommended for reliability)
        if settings.NAS_LOCAL_PATH and os.path.exists(settings.NAS_LOCAL_PATH):
            return settings.NAS_LOCAL_PATH
        # Fallback to SMB path
        return f"\\\\{settings.NAS_HOST}\\{settings.NAS_SHARE}\\{settings.NAS_PATH}"

    async def scan(self, subpath: Optional[str] = None):
        """Scan the archive directory"""
        base_path = self._get_archive_path()
        if subpath:
            base_path = os.path.join(base_path, subpath)

        try:
            await self._scan_directory(base_path, depth=0)
        except Exception as e:
            print(f"Scan error: {e}")
            raise

    async def _scan_directory(self, path: str, depth: int, parent_path: Optional[str] = None):
        """Recursively scan a directory"""
        if not self.state.get("is_scanning", True):
            return  # Stop if scan was cancelled

        self.state["current_folder"] = path

        folder_stats = {
            "total_size": 0,
            "file_count": 0,
            "folder_count": 0,
            "total_duration": 0.0,
        }

        try:
            entries = os.scandir(path)
        except PermissionError:
            print(f"Permission denied: {path}")
            return
        except Exception as e:
            print(f"Error scanning {path}: {e}")
            return

        for entry in entries:
            if not self.state.get("is_scanning", True):
                break

            try:
                if entry.is_file():
                    # Process file
                    file_info = await self._process_file(entry, path)
                    folder_stats["total_size"] += file_info["size"]
                    folder_stats["file_count"] += 1
                    folder_stats["total_duration"] += file_info.get("duration", 0)

                    self.files_processed += 1
                    self.state["files_scanned"] = self.files_processed

                elif entry.is_dir():
                    # Recursively scan subdirectory
                    folder_stats["folder_count"] += 1
                    await self._scan_directory(entry.path, depth + 1, path)

                    # Add subdirectory stats to parent
                    sub_folder = await self._get_folder_stats(entry.path)
                    if sub_folder:
                        folder_stats["total_size"] += sub_folder.total_size
                        folder_stats["file_count"] += sub_folder.file_count
                        folder_stats["folder_count"] += sub_folder.folder_count
                        folder_stats["total_duration"] += sub_folder.total_duration

            except Exception as e:
                print(f"Error processing {entry.path}: {e}")
                continue

            # Yield control to event loop periodically
            if self.files_processed % 100 == 0:
                await asyncio.sleep(0)

        # Save folder stats
        await self._save_folder_stats(path, folder_stats, depth, parent_path)
        self.folders_processed += 1

        # Update progress
        if self.state.get("total_files_estimated", 0) > 0:
            self.state["progress"] = (
                self.files_processed / self.state["total_files_estimated"] * 100
            )

    def _get_media_duration(self, file_path: str) -> float:
        """Extract media duration using ffprobe (optimized)"""
        try:
            # Use faster options: only read format info, limit probe size
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-select_streams', 'v:0',  # Only first video stream
                    '-show_entries', 'format=duration',
                    '-of', 'json',
                    '-probesize', '5000000',  # Limit probe size to 5MB
                    '-analyzeduration', '5000000',  # Limit analyze duration
                    file_path
                ],
                capture_output=True,
                text=True,
                timeout=10  # Reduced timeout to 10 seconds
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data.get('format', {}).get('duration', 0))
                return duration
        except subprocess.TimeoutExpired:
            self._add_log(f"⏱️ Timeout: {os.path.basename(file_path)}")
        except json.JSONDecodeError:
            pass
        except Exception as e:
            self._add_log(f"❌ Error: {os.path.basename(file_path)} - {str(e)[:50]}")

        return 0.0

    def _add_log(self, message: str):
        """Add log message to shared state"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        if "logs" not in self.state:
            self.state["logs"] = []

        self.state["logs"].append(log_entry)
        # Keep only last 100 logs
        if len(self.state["logs"]) > 100:
            self.state["logs"] = self.state["logs"][-100:]

    async def _process_file(self, entry: os.DirEntry, folder_path: str) -> Dict[str, Any]:
        """Process a single file"""
        try:
            stat = entry.stat()
            ext = Path(entry.name).suffix.lower()

            # Check if file exists in DB first
            result = await self.db.execute(
                select(FileStats).where(FileStats.path == entry.path)
            )
            existing = result.scalar_one_or_none()

            # Determine if we need to extract duration
            duration = 0.0
            if ext in MEDIA_EXTENSIONS:
                # Skip duration extraction if already analyzed (has duration > 0)
                if existing and existing.duration > 0:
                    duration = existing.duration
                    self.state["media_files_processed"] = self.state.get("media_files_processed", 0) + 1
                    self.state["total_duration_found"] = self.state.get("total_duration_found", 0.0) + duration
                else:
                    # Run ffprobe in thread pool to not block async loop
                    duration = await asyncio.get_event_loop().run_in_executor(
                        None, self._get_media_duration, entry.path
                    )
                    # Update shared state for media tracking
                    self.state["media_files_processed"] = self.state.get("media_files_processed", 0) + 1
                    self.state["total_duration_found"] = self.state.get("total_duration_found", 0.0) + duration

                    # Log significant media files (every 10 files)
                    if self.state["media_files_processed"] % 10 == 0:
                        hours = self.state["total_duration_found"] / 3600
                        self._add_log(f"📹 {self.state['media_files_processed']} media files, {hours:.1f}h total")

            file_info = {
                "path": entry.path,
                "name": entry.name,
                "folder_path": folder_path,
                "extension": ext,
                "mime_type": get_mime_type(ext),
                "size": stat.st_size,
                "file_created_at": datetime.fromtimestamp(stat.st_ctime),
                "file_modified_at": datetime.fromtimestamp(stat.st_mtime),
                "duration": duration,
            }

            if existing:
                # Update existing (only if size or mtime changed, or duration was 0)
                if existing.size != stat.st_size or existing.duration == 0:
                    for key, value in file_info.items():
                        if key != "path":
                            setattr(existing, key, value)
            else:
                # Create new
                db_file = FileStats(**file_info)
                self.db.add(db_file)

            # Commit periodically
            if self.files_processed % 500 == 0:
                await self.db.commit()

            return file_info

        except Exception as e:
            print(f"Error processing file {entry.path}: {e}")
            return {"size": 0, "duration": 0}

    async def _save_folder_stats(
        self,
        path: str,
        stats: Dict[str, Any],
        depth: int,
        parent_path: Optional[str],
    ):
        """Save folder statistics"""
        name = os.path.basename(path) or path

        result = await self.db.execute(
            select(FolderStats).where(FolderStats.path == path)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.total_size = stats["total_size"]
            existing.file_count = stats["file_count"]
            existing.folder_count = stats["folder_count"]
            existing.total_duration = stats["total_duration"]
            existing.last_scanned_at = datetime.utcnow()
        else:
            folder = FolderStats(
                path=path,
                name=name,
                parent_path=parent_path,
                depth=depth,
                total_size=stats["total_size"],
                file_count=stats["file_count"],
                folder_count=stats["folder_count"],
                total_duration=stats["total_duration"],
                last_scanned_at=datetime.utcnow(),
            )
            self.db.add(folder)

        await self.db.commit()

    async def _get_folder_stats(self, path: str) -> Optional[FolderStats]:
        """Get folder stats from DB"""
        result = await self.db.execute(
            select(FolderStats).where(FolderStats.path == path)
        )
        return result.scalar_one_or_none()

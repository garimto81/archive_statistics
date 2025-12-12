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

# Media extensions (for duration extraction via ffprobe)
MEDIA_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.mxf'
}

# Video extensions for work tracking (used by WorkStatus)
VIDEO_EXTENSIONS_FOR_WORK = {'.mp4'}


def should_include_file(filename: str, extension: str) -> bool:
    """Check if file should be included in scan.

    모든 파일을 스캔합니다 (윈도우 탐색기와 동일한 결과).
    필터링/분류는 스캔 후 별도 작업에서 수행합니다.
    """
    # 모든 파일 포함 (필터 없음)
    return True


class ArchiveScanner:
    """Scanner for archive directory"""

    def __init__(
        self,
        db: AsyncSession,
        state: Dict[str, Any],
        scan_type: str = "full"
    ):
        self.db = db
        self.state = state
        self.scan_type = scan_type  # "full" or "incremental"
        self.files_processed = 0
        self.files_skipped = 0  # Incremental mode: unchanged files
        self.files_new = 0
        self.files_updated = 0
        self.folders_processed = 0
        self.last_scan_time: Optional[datetime] = None

    async def _get_last_scan_time(self) -> Optional[datetime]:
        """Get the last successful scan completion time"""
        from app.models.file_stats import ScanHistory

        result = await self.db.execute(
            select(ScanHistory)
            .where(ScanHistory.status == "completed")
            .order_by(ScanHistory.completed_at.desc())
            .limit(1)
        )
        last_scan = result.scalar_one_or_none()
        return last_scan.completed_at if last_scan else None

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

        # For incremental scan, get last scan time
        if self.scan_type == "incremental":
            self.last_scan_time = await self._get_last_scan_time()
            if self.last_scan_time:
                self._add_log(f"🔄 Incremental scan: checking files since {self.last_scan_time.strftime('%Y-%m-%d %H:%M')}")
            else:
                self._add_log("⚠️ No previous scan found, running full scan")
                self.scan_type = "full"  # Fallback to full scan
        else:
            self._add_log("📂 Full scan mode")

        try:
            await self._scan_directory(base_path, depth=0)

            # Log final statistics
            if self.scan_type == "incremental":
                self._add_log(
                    f"✅ Scan complete: {self.files_new} new, {self.files_updated} updated, "
                    f"{self.files_skipped} unchanged"
                )
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
                    # Check if file should be included (based on settings.SCAN_ALL_FILES)
                    ext = Path(entry.name).suffix.lower()
                    if not should_include_file(entry.name, ext):
                        continue  # Skip excluded files

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

    def _get_media_info(self, file_path: str) -> Dict[str, Any]:
        """Extract media duration and codec info using ffprobe (optimized)

        Returns:
            dict with keys: duration, video_codec, audio_codec
        """
        result_info = {"duration": 0.0, "video_codec": None, "audio_codec": None}

        try:
            # Use faster options: read format and stream info, limit probe size
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration:stream=codec_name,codec_type',
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

                # Extract duration
                result_info["duration"] = float(data.get('format', {}).get('duration', 0))

                # Extract codec info from streams
                for stream in data.get('streams', []):
                    codec_type = stream.get('codec_type')
                    codec_name = stream.get('codec_name')
                    if codec_type == 'video' and not result_info["video_codec"]:
                        result_info["video_codec"] = codec_name
                    elif codec_type == 'audio' and not result_info["audio_codec"]:
                        result_info["audio_codec"] = codec_name

        except subprocess.TimeoutExpired:
            self._add_log(f"⏱️ Timeout: {os.path.basename(file_path)}")
        except json.JSONDecodeError:
            pass
        except Exception as e:
            self._add_log(f"❌ Error: {os.path.basename(file_path)} - {str(e)[:50]}")

        return result_info

    def _get_media_duration(self, file_path: str) -> float:
        """Extract media duration using ffprobe (legacy compatibility)"""
        return self._get_media_info(file_path)["duration"]

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
        """Process a single file

        In incremental mode, skip files that haven't been modified since last scan.
        """
        try:
            stat = entry.stat()
            ext = Path(entry.name).suffix.lower()
            file_mtime = datetime.fromtimestamp(stat.st_mtime)

            # Check if file exists in DB first
            result = await self.db.execute(
                select(FileStats).where(FileStats.path == entry.path)
            )
            existing = result.scalar_one_or_none()

            # INCREMENTAL MODE: Skip unchanged files
            if self.scan_type == "incremental" and existing and self.last_scan_time:
                # File hasn't been modified since last scan - skip it
                if file_mtime <= self.last_scan_time:
                    self.files_skipped += 1
                    # Return existing data for folder stats calculation
                    return {
                        "size": existing.size,
                        "duration": existing.duration or 0.0,
                    }

            # Determine if we need to extract media info (duration + codec)
            duration = 0.0
            video_codec = None
            audio_codec = None
            if ext in MEDIA_EXTENSIONS:
                # Skip extraction if already analyzed (has duration > 0 AND codec info)
                if existing and existing.duration > 0 and existing.video_codec:
                    duration = existing.duration
                    video_codec = existing.video_codec
                    audio_codec = existing.audio_codec
                    self.state["media_files_processed"] = self.state.get("media_files_processed", 0) + 1
                    self.state["total_duration_found"] = self.state.get("total_duration_found", 0.0) + duration
                else:
                    # Run ffprobe in thread pool to not block async loop
                    media_info = await asyncio.get_event_loop().run_in_executor(
                        None, self._get_media_info, entry.path
                    )
                    duration = media_info["duration"]
                    video_codec = media_info["video_codec"]
                    audio_codec = media_info["audio_codec"]

                    # Update shared state for media tracking
                    self.state["media_files_processed"] = self.state.get("media_files_processed", 0) + 1
                    self.state["total_duration_found"] = self.state.get("total_duration_found", 0.0) + duration

                    # Log significant media files (every 10 files)
                    if self.state["media_files_processed"] % 10 == 0:
                        hours = self.state["total_duration_found"] / 3600
                        self._add_log(f"📹 {self.state['media_files_processed']} media files, {hours:.1f}h total")

            # 숨김 파일 판별 (파일명이 .으로 시작하거나 시스템 파일)
            is_hidden = entry.name.startswith('.') or entry.name.lower() in (
                'thumbs.db', 'desktop.ini', '.ds_store', '.gitignore', '.gitkeep'
            )

            file_info = {
                "path": entry.path,
                "name": entry.name,
                "folder_path": folder_path,
                "extension": ext,
                "mime_type": get_mime_type(ext),
                "size": stat.st_size,
                "file_created_at": datetime.fromtimestamp(stat.st_ctime),
                "file_modified_at": file_mtime,
                "duration": duration,
                "video_codec": video_codec,
                "audio_codec": audio_codec,
                "is_hidden": is_hidden,
            }

            if existing:
                # Update existing (if size changed, duration is 0, or codec info missing)
                needs_update = (
                    existing.size != stat.st_size or
                    existing.duration == 0 or
                    (ext in MEDIA_EXTENSIONS and not existing.video_codec)
                )
                if needs_update:
                    self.files_updated += 1
                    for key, value in file_info.items():
                        if key != "path":
                            setattr(existing, key, value)
            else:
                # Create new
                self.files_new += 1
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

"""Utility functions"""


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string"""
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index >= 3:  # GB or larger
        return f"{size:.2f} {units[unit_index]}"
    elif unit_index >= 1:  # KB or MB
        return f"{size:.1f} {units[unit_index]}"
    else:
        return f"{int(size)} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """Format seconds to human readable duration"""
    if seconds == 0:
        return "0h"

    hours = seconds / 3600
    if hours >= 1000:
        return f"{hours:,.0f} hrs"
    elif hours >= 1:
        return f"{hours:.1f} hrs"
    else:
        minutes = seconds / 60
        return f"{minutes:.0f} min"


def get_mime_type(extension: str) -> str:
    """Get MIME type category from extension"""
    extension = extension.lower().lstrip(".")

    video_exts = {"mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "mpg", "mpeg"}
    audio_exts = {"mp3", "wav", "flac", "aac", "ogg", "wma", "m4a"}
    image_exts = {"jpg", "jpeg", "png", "gif", "bmp", "tiff", "raw", "webp", "svg"}
    doc_exts = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf"}

    if extension in video_exts:
        return "video"
    elif extension in audio_exts:
        return "audio"
    elif extension in image_exts:
        return "image"
    elif extension in doc_exts:
        return "document"
    else:
        return "other"

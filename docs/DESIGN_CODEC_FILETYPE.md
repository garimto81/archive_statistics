# Design Document: Codec Info & File Type Detail Feature

**Version**: 1.0
**Date**: 2025-12-05
**Status**: Proposed

---

## 1. Overview

미디어 파일의 코덱 정보 및 파일 타입별 상세 분석 기능을 추가하여, 아카이브 내 파일에 대한 깊이 있는 기술적 정보를 제공합니다.

### 1.1 Goals
- 비디오/오디오 파일의 코덱, 해상도, 비트레이트 등 상세 정보 수집
- 파일 타입별 통계 페이지 제공
- 코덱별 분포 시각화
- 품질 기반 파일 분류 (4K, 1080p, 720p 등)

---

## 2. Database Schema Changes

### 2.1 FileStats 테이블 확장

```python
# backend/app/models/file_stats.py

class FileStats(Base):
    """File statistics model - Extended"""

    __tablename__ = "file_stats"

    # ... existing fields ...

    # NEW: Media Info Fields
    # Video
    video_codec = Column(String, nullable=True)          # h264, h265, vp9, av1
    video_codec_profile = Column(String, nullable=True)  # High, Main, Baseline
    width = Column(Integer, nullable=True)               # 1920
    height = Column(Integer, nullable=True)              # 1080
    frame_rate = Column(Float, nullable=True)            # 29.97, 60
    video_bitrate = Column(BigInteger, nullable=True)    # bits per second

    # Audio
    audio_codec = Column(String, nullable=True)          # aac, ac3, dts, flac
    audio_channels = Column(Integer, nullable=True)      # 2, 6 (5.1), 8 (7.1)
    audio_sample_rate = Column(Integer, nullable=True)   # 44100, 48000
    audio_bitrate = Column(BigInteger, nullable=True)    # bits per second

    # Container & Quality
    container_format = Column(String, nullable=True)     # mp4, mkv, avi
    quality_tier = Column(String, nullable=True)         # 4K, 1080p, 720p, SD
    hdr_format = Column(String, nullable=True)           # HDR10, Dolby Vision, HLG

    # Analysis metadata
    analyzed_at = Column(DateTime, nullable=True)
    analysis_error = Column(String, nullable=True)
```

### 2.2 새로운 CodecStats 집계 테이블

```python
class CodecStats(Base):
    """Aggregated codec statistics"""

    __tablename__ = "codec_stats"

    id = Column(Integer, primary_key=True, index=True)

    # Grouping
    codec_type = Column(String, nullable=False)    # video, audio
    codec_name = Column(String, nullable=False)    # h264, aac, etc.

    # Statistics
    file_count = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)
    total_duration = Column(Float, default=0.0)
    avg_bitrate = Column(BigInteger, nullable=True)

    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow)
```

### 2.3 QualityDistribution 집계 테이블

```python
class QualityDistribution(Base):
    """Quality tier distribution"""

    __tablename__ = "quality_distribution"

    id = Column(Integer, primary_key=True, index=True)
    quality_tier = Column(String, nullable=False)  # 4K, 1080p, 720p, SD

    file_count = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)
    total_duration = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)

    updated_at = Column(DateTime, default=datetime.utcnow)
```

---

## 3. Backend API Design

### 3.1 New Endpoints

```
GET /api/stats/codecs
GET /api/stats/codecs/{codec_type}  # video or audio
GET /api/stats/quality-distribution
GET /api/stats/file-types/{extension}
GET /api/files/{file_id}/media-info
```

### 3.2 Response Schemas

```python
# backend/app/schemas/stats.py

class CodecStatsResponse(BaseModel):
    codec_type: str           # "video" or "audio"
    codec_name: str           # "h264", "aac"
    file_count: int
    total_size: int
    total_size_formatted: str
    total_duration: float
    total_duration_formatted: str
    avg_bitrate: Optional[int]
    avg_bitrate_formatted: Optional[str]
    percentage: float

class QualityDistributionResponse(BaseModel):
    quality_tier: str         # "4K", "1080p", "720p", "SD"
    file_count: int
    total_size: int
    total_size_formatted: str
    total_duration: float
    total_duration_formatted: str
    percentage: float

class MediaInfoResponse(BaseModel):
    file_id: int
    file_name: str

    # Video
    video_codec: Optional[str]
    video_codec_profile: Optional[str]
    resolution: Optional[str]        # "1920x1080"
    frame_rate: Optional[float]
    video_bitrate: Optional[int]
    video_bitrate_formatted: Optional[str]

    # Audio
    audio_codec: Optional[str]
    audio_channels: Optional[int]
    audio_channels_formatted: Optional[str]  # "Stereo", "5.1", "7.1"
    audio_sample_rate: Optional[int]
    audio_bitrate: Optional[int]

    # Quality
    quality_tier: Optional[str]
    hdr_format: Optional[str]
    container_format: Optional[str]

    # Duration
    duration: float
    duration_formatted: str

class FileTypeDetailResponse(BaseModel):
    extension: str
    mime_type: str
    file_count: int
    total_size: int
    total_size_formatted: str
    total_duration: float
    total_duration_formatted: str
    percentage: float

    # Codec breakdown (for media files)
    video_codecs: Optional[List[CodecStatsResponse]]
    audio_codecs: Optional[List[CodecStatsResponse]]
    quality_distribution: Optional[List[QualityDistributionResponse]]

    # Sample files
    sample_files: List[MediaInfoResponse]
```

---

## 4. Scanner Enhancement

### 4.1 Enhanced ffprobe Output

```python
# backend/app/services/scanner.py

def _get_media_info(self, file_path: str) -> Dict[str, Any]:
    """Extract comprehensive media information using ffprobe"""
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_entries',
                'format=duration,format_name,bit_rate:'
                'stream=codec_name,codec_type,width,height,r_frame_rate,'
                'bit_rate,channels,sample_rate,profile,color_transfer',
                '-of', 'json',
                '-probesize', '10000000',
                '-analyzeduration', '10000000',
                file_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return self._parse_ffprobe_output(data)

    except Exception as e:
        return {"error": str(e)}

    return {}

def _parse_ffprobe_output(self, data: Dict) -> Dict[str, Any]:
    """Parse ffprobe JSON output"""
    info = {
        "duration": 0.0,
        "container_format": None,
        "video_codec": None,
        "video_codec_profile": None,
        "width": None,
        "height": None,
        "frame_rate": None,
        "video_bitrate": None,
        "audio_codec": None,
        "audio_channels": None,
        "audio_sample_rate": None,
        "audio_bitrate": None,
        "quality_tier": None,
        "hdr_format": None,
    }

    # Parse format
    format_info = data.get("format", {})
    info["duration"] = float(format_info.get("duration", 0))
    info["container_format"] = format_info.get("format_name", "").split(",")[0]

    # Parse streams
    for stream in data.get("streams", []):
        codec_type = stream.get("codec_type")

        if codec_type == "video":
            info["video_codec"] = stream.get("codec_name")
            info["video_codec_profile"] = stream.get("profile")
            info["width"] = stream.get("width")
            info["height"] = stream.get("height")
            info["video_bitrate"] = int(stream.get("bit_rate", 0) or 0)

            # Parse frame rate (format: "30000/1001" or "30/1")
            fps_str = stream.get("r_frame_rate", "0/1")
            try:
                num, den = map(int, fps_str.split("/"))
                info["frame_rate"] = round(num / den, 2) if den else 0
            except:
                info["frame_rate"] = 0

            # Detect HDR
            color_transfer = stream.get("color_transfer", "")
            if "smpte2084" in color_transfer or "bt2020" in color_transfer:
                info["hdr_format"] = "HDR10"
            elif "arib-std-b67" in color_transfer:
                info["hdr_format"] = "HLG"

        elif codec_type == "audio":
            info["audio_codec"] = stream.get("codec_name")
            info["audio_channels"] = stream.get("channels")
            info["audio_sample_rate"] = stream.get("sample_rate")
            info["audio_bitrate"] = int(stream.get("bit_rate", 0) or 0)

    # Determine quality tier
    height = info.get("height", 0) or 0
    if height >= 2160:
        info["quality_tier"] = "4K"
    elif height >= 1080:
        info["quality_tier"] = "1080p"
    elif height >= 720:
        info["quality_tier"] = "720p"
    elif height > 0:
        info["quality_tier"] = "SD"

    return info
```

---

## 5. Frontend Design

### 5.1 New Statistics Page (`/statistics`)

```
┌─────────────────────────────────────────────────────────────────┐
│  Statistics                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Total Files │  │ Video Files │  │ Audio Files │  │ 4K Files│ │
│  │   1,911     │  │   1,245     │  │    432      │  │   156   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│                                                                  │
│  ┌───────────────────────────────┐  ┌──────────────────────────┐│
│  │   Video Codec Distribution    │  │  Quality Distribution    ││
│  │   ┌─────────────────────┐     │  │  ┌────────────────────┐  ││
│  │   │    [Pie Chart]      │     │  │  │   [Bar Chart]      │  ││
│  │   │  H.264: 65%         │     │  │  │   4K:    8.2%      │  ││
│  │   │  H.265: 28%         │     │  │  │   1080p: 52.3%     │  ││
│  │   │  VP9:   5%          │     │  │  │   720p:  31.1%     │  ││
│  │   │  Other: 2%          │     │  │  │   SD:    8.4%      │  ││
│  │   └─────────────────────┘     │  │  └────────────────────┘  ││
│  └───────────────────────────────┘  └──────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │   File Type Detail Table                                     ││
│  │  ┌──────┬───────┬────────┬────────┬──────────┬────────────┐ ││
│  │  │ Ext  │ Count │  Size  │Duration│ Top Codec│ Quality    │ ││
│  │  ├──────┼───────┼────────┼────────┼──────────┼────────────┤ ││
│  │  │ .mp4 │  856  │ 12.5TB │ 320hrs │ H.264    │ 1080p (60%)│ ││
│  │  │ .mkv │  389  │  5.2TB │ 180hrs │ H.265    │ 4K (35%)   │ ││
│  │  │ .mov │   45  │  2.1TB │  45hrs │ ProRes   │ 4K (80%)   │ ││
│  │  │ .mp3 │  432  │  8.5GB │  28hrs │ MP3      │ -          │ ││
│  │  └──────┴───────┴────────┴────────┴──────────┴────────────┘ ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │   Audio Codec Distribution                                    ││
│  │   AAC: 45%  |  AC3: 25%  |  DTS: 15%  |  FLAC: 10%  | Other  ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 File Type Detail Modal

클릭 시 해당 파일 타입의 상세 정보를 모달로 표시:

```
┌──────────────────────────────────────────────────────────────┐
│  📁 .mp4 Files Detail                                    [X] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Overview                                                    │
│  ─────────────────────────────────────────────────           │
│  Total Files: 856                                            │
│  Total Size: 12.5 TB                                         │
│  Total Duration: 320 hrs                                     │
│                                                              │
│  Video Codecs           Audio Codecs                         │
│  ─────────────          ────────────                         │
│  H.264:  523 (61%)      AAC:   645 (75%)                     │
│  H.265:  298 (35%)      AC3:   156 (18%)                     │
│  VP9:     35 (4%)       DTS:    55 (7%)                      │
│                                                              │
│  Quality Distribution                                        │
│  ─────────────────────────────────────────────────           │
│  ████████████████░░░░ 4K:    124 files (14.5%)               │
│  ████████████████████████████████░░░░ 1080p: 498 (58.2%)     │
│  ████████████████░░░░ 720p:  189 files (22.1%)               │
│  ████░░░░░░░░░░░░ SD:     45 files (5.2%)                    │
│                                                              │
│  Sample Files                                                │
│  ─────────────────────────────────────────────────           │
│  📹 WSOP_2024_Main_Event_Final.mp4                          │
│     H.265 | 3840x2160 | 60fps | HDR10 | AAC 5.1 | 2.3GB     │
│                                                              │
│  📹 HCL_Poker_S2_EP05.mp4                                   │
│     H.264 | 1920x1080 | 30fps | AAC Stereo | 1.8GB          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 TypeScript Types

```typescript
// frontend/src/types/index.ts

export interface CodecStats {
  codec_type: 'video' | 'audio';
  codec_name: string;
  file_count: number;
  total_size: number;
  total_size_formatted: string;
  total_duration: number;
  total_duration_formatted: string;
  avg_bitrate: number | null;
  avg_bitrate_formatted: string | null;
  percentage: number;
}

export interface QualityDistribution {
  quality_tier: '4K' | '1080p' | '720p' | 'SD';
  file_count: number;
  total_size: number;
  total_size_formatted: string;
  total_duration: number;
  total_duration_formatted: string;
  percentage: number;
}

export interface MediaInfo {
  file_id: number;
  file_name: string;
  video_codec: string | null;
  video_codec_profile: string | null;
  resolution: string | null;
  frame_rate: number | null;
  video_bitrate: number | null;
  video_bitrate_formatted: string | null;
  audio_codec: string | null;
  audio_channels: number | null;
  audio_channels_formatted: string | null;
  audio_sample_rate: number | null;
  audio_bitrate: number | null;
  quality_tier: string | null;
  hdr_format: string | null;
  container_format: string | null;
  duration: number;
  duration_formatted: string;
}

export interface FileTypeDetail {
  extension: string;
  mime_type: string;
  file_count: number;
  total_size: number;
  total_size_formatted: string;
  total_duration: number;
  total_duration_formatted: string;
  percentage: number;
  video_codecs: CodecStats[] | null;
  audio_codecs: CodecStats[] | null;
  quality_distribution: QualityDistribution[] | null;
  sample_files: MediaInfo[];
}
```

---

## 6. Implementation Phases

### Phase 1: Database & Scanner (Priority: High)
1. Add new columns to `FileStats` model
2. Create migration script
3. Enhance `_get_media_info()` in scanner
4. Update scanner to populate new fields

### Phase 2: Backend API (Priority: High)
1. Create new schemas
2. Implement `/api/stats/codecs` endpoint
3. Implement `/api/stats/quality-distribution` endpoint
4. Implement `/api/stats/file-types/{extension}` endpoint

### Phase 3: Frontend Statistics Page (Priority: Medium)
1. Create `Statistics.tsx` page component
2. Add codec distribution charts
3. Add quality distribution charts
4. Add file type detail table

### Phase 4: File Detail Modal (Priority: Medium)
1. Create `FileTypeDetailModal` component
2. Implement sample files display
3. Add codec breakdown visualization

### Phase 5: Dashboard Integration (Priority: Low)
1. Add codec summary card to dashboard
2. Add quality tier quick stats

---

## 7. Performance Considerations

### 7.1 Scan Optimization
- 미디어 정보 분석은 기존 duration 분석과 통합
- 이미 분석된 파일 (analyzed_at 존재) 건너뛰기
- ffprobe 호출 최적화 (한 번의 호출로 모든 정보 추출)

### 7.2 Query Optimization
- 코덱 통계는 별도 집계 테이블 사용
- 주기적 집계 업데이트 (스캔 완료 후)
- 인덱스: `video_codec`, `audio_codec`, `quality_tier`

### 7.3 Caching
- 코덱 통계 결과 캐싱 (5분)
- 품질 분포 결과 캐싱 (5분)

---

## 8. Migration Plan

```sql
-- Add new columns to file_stats
ALTER TABLE file_stats ADD COLUMN video_codec VARCHAR(50);
ALTER TABLE file_stats ADD COLUMN video_codec_profile VARCHAR(50);
ALTER TABLE file_stats ADD COLUMN width INTEGER;
ALTER TABLE file_stats ADD COLUMN height INTEGER;
ALTER TABLE file_stats ADD COLUMN frame_rate REAL;
ALTER TABLE file_stats ADD COLUMN video_bitrate BIGINT;
ALTER TABLE file_stats ADD COLUMN audio_codec VARCHAR(50);
ALTER TABLE file_stats ADD COLUMN audio_channels INTEGER;
ALTER TABLE file_stats ADD COLUMN audio_sample_rate INTEGER;
ALTER TABLE file_stats ADD COLUMN audio_bitrate BIGINT;
ALTER TABLE file_stats ADD COLUMN container_format VARCHAR(20);
ALTER TABLE file_stats ADD COLUMN quality_tier VARCHAR(10);
ALTER TABLE file_stats ADD COLUMN hdr_format VARCHAR(20);
ALTER TABLE file_stats ADD COLUMN analyzed_at TIMESTAMP;
ALTER TABLE file_stats ADD COLUMN analysis_error TEXT;

-- Create indexes
CREATE INDEX idx_file_stats_video_codec ON file_stats(video_codec);
CREATE INDEX idx_file_stats_audio_codec ON file_stats(audio_codec);
CREATE INDEX idx_file_stats_quality_tier ON file_stats(quality_tier);
```

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Codec info extraction accuracy | > 95% |
| Scan time increase | < 20% |
| Statistics page load time | < 2 seconds |
| User satisfaction | > 4.0/5.0 |

---

## 10. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| ffprobe 처리 시간 증가 | Medium | 분석 결과 캐싱, 병렬 처리 |
| DB 스키마 변경 복잡성 | Medium | 점진적 마이그레이션 |
| 비표준 코덱 처리 | Low | Unknown으로 분류, 로깅 |

---

**Next Steps**: Issue 생성 및 Phase 1 구현 시작

---

# Part 2: Folder File List Feature

## 11. Folder File List Overview

폴더 트리에서 폴더 선택 시 해당 폴더의 실제 파일 목록을 표시하는 기능을 추가합니다.

### 11.1 Goals
- 폴더 클릭 시 해당 폴더 내 파일 목록 표시
- 파일별 상세 정보 (크기, 코덱, 해상도, 재생시간) 표시
- 정렬 및 필터링 기능
- 파일 미리보기/썸네일 (Phase 2)

---

## 12. Backend API for File List

### 12.1 New Endpoints

```
GET /api/folders/files
  - folder_path: string (required)
  - page: int (default: 1)
  - page_size: int (default: 50)
  - sort_by: string (name, size, duration, modified_at)
  - sort_order: string (asc, desc)
  - extension: string (optional filter)
```

### 12.2 Response Schema

```python
# backend/app/schemas/stats.py

class FileListItem(BaseModel):
    id: int
    name: str
    path: str
    extension: str
    size: int
    size_formatted: str
    duration: Optional[float]
    duration_formatted: Optional[str]

    # Media info (from codec feature)
    video_codec: Optional[str]
    audio_codec: Optional[str]
    resolution: Optional[str]
    quality_tier: Optional[str]

    # Timestamps
    file_created_at: Optional[datetime]
    file_modified_at: Optional[datetime]

class FileListResponse(BaseModel):
    items: List[FileListItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    folder_path: str
    folder_name: str
    folder_size_formatted: str
```

### 12.3 API Implementation

```python
# backend/app/api/folders.py

@router.get("/files", response_model=FileListResponse)
async def get_folder_files(
    folder_path: str = Query(..., description="Folder path"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=10, le=200),
    sort_by: str = Query(default="name", regex="^(name|size|duration|modified_at)$"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$"),
    extension: Optional[str] = Query(default=None, description="Filter by extension"),
    db: AsyncSession = Depends(get_db),
):
    """Get files in a specific folder"""

    # Build base query
    query = select(FileStats).where(FileStats.folder_path == folder_path)

    # Apply extension filter
    if extension:
        query = query.where(FileStats.extension == extension.lower())

    # Get total count
    count_result = await db.execute(
        select(func.count(FileStats.id)).where(FileStats.folder_path == folder_path)
    )
    total_count = count_result.scalar()

    # Apply sorting
    sort_column = getattr(FileStats, sort_by, FileStats.name)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    files = result.scalars().all()

    # Get folder info
    folder_result = await db.execute(
        select(FolderStats).where(FolderStats.path == folder_path)
    )
    folder = folder_result.scalar_one_or_none()

    return FileListResponse(
        items=[
            FileListItem(
                id=f.id,
                name=f.name,
                path=f.path,
                extension=f.extension or "",
                size=f.size,
                size_formatted=format_size(f.size),
                duration=f.duration,
                duration_formatted=format_duration(f.duration) if f.duration else None,
                video_codec=f.video_codec,
                audio_codec=f.audio_codec,
                resolution=f"{f.width}x{f.height}" if f.width and f.height else None,
                quality_tier=f.quality_tier,
                file_created_at=f.file_created_at,
                file_modified_at=f.file_modified_at,
            )
            for f in files
        ],
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=(total_count + page_size - 1) // page_size,
        folder_path=folder_path,
        folder_name=folder.name if folder else os.path.basename(folder_path),
        folder_size_formatted=format_size(folder.total_size) if folder else "0 B",
    )
```

---

## 13. Frontend File List Design

### 13.1 Enhanced Folder Tree with File Panel

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Folders Page                                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐  ┌────────────────────────────────────────┐  │
│  │   Folder Structure  │  │   📁 WSOP/2024/Main_Event              │  │
│  │   ─────────────────│  │   ─────────────────────────────────────│  │
│  │                     │  │   📊 156 files | 45.2 GB | 120.5 hrs   │  │
│  │   📁 ARCHIVE        │  │                                        │  │
│  │   ├─ 📁 WSOP ▼      │  │   Sort: [Name ▼] [Size] [Duration]     │  │
│  │   │  ├─ 📁 2024 ▼   │  │   Filter: [All Types ▼]                │  │
│  │   │  │  ├─ 📁▶Main  │  │                                        │  │
│  │   │  │  ├─ 📁 Side  │  │   ┌──────────────────────────────────┐ │  │
│  │   │  │  └─ 📁 Final │  │   │  File List                       │ │  │
│  │   │  ├─ 📁 2023     │  │   ├──────────────────────────────────┤ │  │
│  │   │  └─ 📁 2022     │  │   │ 📹 Main_Event_Day1_Part1.mp4     │ │  │
│  │   ├─ 📁 HCL         │  │   │    H.264 | 1080p | 2.3GB | 45min │ │  │
│  │   └─ 📁 Other       │  │   ├──────────────────────────────────┤ │  │
│  │                     │  │   │ 📹 Main_Event_Day1_Part2.mp4     │ │  │
│  │                     │  │   │    H.264 | 1080p | 2.1GB | 42min │ │  │
│  │                     │  │   ├──────────────────────────────────┤ │  │
│  │                     │  │   │ 📹 Main_Event_Day2_Full.mp4      │ │  │
│  │                     │  │   │    H.265 | 4K | 8.5GB | 3.2hrs   │ │  │
│  │                     │  │   ├──────────────────────────────────┤ │  │
│  │                     │  │   │ 🎵 Background_Music.mp3          │ │  │
│  │                     │  │   │    MP3 | Stereo | 5.2MB | 4min   │ │  │
│  │                     │  │   └──────────────────────────────────┘ │  │
│  │                     │  │                                        │  │
│  │   [Expand All]      │  │   Page: [< 1 2 3 ... 8 >]  50/page    │  │
│  └─────────────────────┘  └────────────────────────────────────────┘  │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 13.2 File List Item Component

```typescript
// frontend/src/components/FileListItem.tsx

interface FileListItemProps {
  file: FileListItem;
  onClick?: (file: FileListItem) => void;
}

function FileListItem({ file, onClick }: FileListItemProps) {
  const getFileIcon = (ext: string) => {
    const videoExts = ['.mp4', '.mkv', '.avi', '.mov'];
    const audioExts = ['.mp3', '.wav', '.flac', '.aac'];
    const imageExts = ['.jpg', '.png', '.gif', '.webp'];

    if (videoExts.includes(ext)) return <Film className="text-blue-500" />;
    if (audioExts.includes(ext)) return <Music className="text-purple-500" />;
    if (imageExts.includes(ext)) return <Image className="text-green-500" />;
    return <File className="text-gray-500" />;
  };

  return (
    <div
      className="flex items-center p-3 hover:bg-gray-50 border-b cursor-pointer"
      onClick={() => onClick?.(file)}
    >
      {/* Icon */}
      <div className="w-10">
        {getFileIcon(file.extension)}
      </div>

      {/* File info */}
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{file.name}</div>
        <div className="text-xs text-gray-500 flex gap-2">
          {file.video_codec && <span>{file.video_codec}</span>}
          {file.resolution && <span>{file.resolution}</span>}
          {file.quality_tier && (
            <span className={cn(
              "px-1 rounded",
              file.quality_tier === '4K' ? 'bg-purple-100 text-purple-700' :
              file.quality_tier === '1080p' ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-gray-700'
            )}>
              {file.quality_tier}
            </span>
          )}
          {file.audio_codec && <span>{file.audio_codec}</span>}
        </div>
      </div>

      {/* Size */}
      <div className="w-24 text-right text-sm text-gray-600">
        {file.size_formatted}
      </div>

      {/* Duration */}
      <div className="w-20 text-right text-sm text-gray-600">
        {file.duration_formatted || '-'}
      </div>
    </div>
  );
}
```

### 13.3 TypeScript Types

```typescript
// frontend/src/types/index.ts

export interface FileListItem {
  id: number;
  name: string;
  path: string;
  extension: string;
  size: number;
  size_formatted: string;
  duration: number | null;
  duration_formatted: string | null;
  video_codec: string | null;
  audio_codec: string | null;
  resolution: string | null;
  quality_tier: string | null;
  file_created_at: string | null;
  file_modified_at: string | null;
}

export interface FileListResponse {
  items: FileListItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  folder_path: string;
  folder_name: string;
  folder_size_formatted: string;
}
```

### 13.4 API Service

```typescript
// frontend/src/services/api.ts

export const foldersApi = {
  // ... existing methods ...

  getFiles: async (params: {
    folder_path: string;
    page?: number;
    page_size?: number;
    sort_by?: 'name' | 'size' | 'duration' | 'modified_at';
    sort_order?: 'asc' | 'desc';
    extension?: string;
  }): Promise<FileListResponse> => {
    const searchParams = new URLSearchParams();
    searchParams.append('folder_path', params.folder_path);
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.page_size) searchParams.append('page_size', params.page_size.toString());
    if (params.sort_by) searchParams.append('sort_by', params.sort_by);
    if (params.sort_order) searchParams.append('sort_order', params.sort_order);
    if (params.extension) searchParams.append('extension', params.extension);

    const { data } = await api.get(`/folders/files?${searchParams}`);
    return data;
  },
};
```

---

## 14. Enhanced Folders Page

### 14.1 Page Component Structure

```typescript
// frontend/src/pages/Folders.tsx

export default function FoldersPage() {
  const [selectedFolder, setSelectedFolder] = useState<FolderTreeNode | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'duration'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(1);
  const [extensionFilter, setExtensionFilter] = useState<string | null>(null);

  // Folder tree query
  const { data: folderTree } = useQuery({
    queryKey: ['folder-tree'],
    queryFn: () => foldersApi.getTree(undefined, 5),
  });

  // File list query (only when folder selected)
  const { data: fileList, isLoading: filesLoading } = useQuery({
    queryKey: ['folder-files', selectedFolder?.path, page, sortBy, sortOrder, extensionFilter],
    queryFn: () => foldersApi.getFiles({
      folder_path: selectedFolder!.path,
      page,
      page_size: 50,
      sort_by: sortBy,
      sort_order: sortOrder,
      extension: extensionFilter || undefined,
    }),
    enabled: !!selectedFolder,
  });

  const handleFolderSelect = (folder: FolderTreeNode) => {
    setSelectedFolder(folder);
    setPage(1);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
      {/* Left: Folder Tree */}
      <div className="lg:col-span-1">
        <FolderTree
          nodes={folderTree || []}
          onSelect={handleFolderSelect}
          selectedPath={selectedFolder?.path}
        />
      </div>

      {/* Right: File List Panel */}
      <div className="lg:col-span-2">
        {selectedFolder ? (
          <FileListPanel
            folder={selectedFolder}
            files={fileList}
            isLoading={filesLoading}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSortChange={(by, order) => {
              setSortBy(by);
              setSortOrder(order);
            }}
            page={page}
            onPageChange={setPage}
            extensionFilter={extensionFilter}
            onExtensionFilterChange={setExtensionFilter}
          />
        ) : (
          <EmptyState message="Select a folder to view files" />
        )}
      </div>
    </div>
  );
}
```

---

## 15. File Detail Modal (Optional)

파일 클릭 시 상세 정보를 보여주는 모달:

```
┌──────────────────────────────────────────────────────────────┐
│  📹 Main_Event_Day2_Full.mp4                            [X] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  General Information                                         │
│  ─────────────────────────────────────────────────           │
│  File Size:     8.5 GB                                       │
│  Duration:      3h 12m 45s                                   │
│  Container:     MP4 (MPEG-4 Part 14)                         │
│  Created:       2024-11-15 14:30:22                          │
│  Modified:      2024-11-15 16:45:10                          │
│                                                              │
│  Video Track                                                 │
│  ─────────────────────────────────────────────────           │
│  Codec:         H.265 (HEVC) Main 10 Profile                 │
│  Resolution:    3840 x 2160 (4K UHD)                         │
│  Frame Rate:    60.00 fps                                    │
│  Bitrate:       25.5 Mbps                                    │
│  HDR:           HDR10                                        │
│                                                              │
│  Audio Track                                                 │
│  ─────────────────────────────────────────────────           │
│  Codec:         AAC LC                                       │
│  Channels:      5.1 Surround                                 │
│  Sample Rate:   48000 Hz                                     │
│  Bitrate:       384 kbps                                     │
│                                                              │
│  Path                                                        │
│  ─────────────────────────────────────────────────           │
│  /mnt/nas/ARCHIVE/WSOP/2024/Main_Event/Day2/                │
│                                                              │
│                                         [Copy Path] [Close]  │
└──────────────────────────────────────────────────────────────┘
```

---

## 16. Updated Implementation Phases

### Phase 1: Database & Scanner (Priority: High)
1. Add codec/media columns to FileStats
2. Enhance ffprobe parsing
3. Create migration

### Phase 2: File List API (Priority: High)
1. Implement `/api/folders/files` endpoint
2. Add pagination, sorting, filtering
3. Return codec info with file list

### Phase 3: Statistics Page (Priority: Medium)
1. Create Statistics.tsx page
2. Codec distribution charts
3. Quality distribution charts
4. File type detail table

### Phase 4: Folders Page Enhancement (Priority: High)
1. Split Folders page into tree + file list panels
2. Create FileListPanel component
3. Add sorting/filtering controls
4. Implement pagination

### Phase 5: File Detail Modal (Priority: Low)
1. Create FileDetailModal component
2. Display full media info
3. Add copy path functionality

---

## 17. Performance Considerations for File List

### 17.1 Query Optimization
- 인덱스: `folder_path`, `extension`, `size`, `name`
- 페이지네이션 필수 (page_size 최대 200)
- 전체 카운트는 별도 쿼리로 분리

### 17.2 Frontend Optimization
- React Query 캐싱 활용
- 가상 스크롤 (대용량 폴더)
- 이미지 썸네일은 lazy loading

```sql
-- Additional indexes for file list queries
CREATE INDEX idx_file_stats_folder_path ON file_stats(folder_path);
CREATE INDEX idx_file_stats_folder_name ON file_stats(folder_path, name);
CREATE INDEX idx_file_stats_folder_size ON file_stats(folder_path, size DESC);
```

# GitHub Issues for Archive Statistics

This document contains planned issues to be created on GitHub.

---

## 🐛 Bug Fixes

### Issue #1: Alerts Page Not Implemented
**Labels**: `bug`, `enhancement`
**Priority**: Medium

**Description**:
The Alerts navigation item exists but the page is not implemented.

**Tasks**:
- [ ] Create Alerts page component
- [ ] Add alert threshold settings
- [ ] Implement notification system

---

### Issue #2: Settings Page Not Implemented
**Labels**: `bug`, `enhancement`
**Priority**: Medium

**Description**:
The Settings navigation item exists but the page is not implemented.

**Tasks**:
- [ ] Create Settings page component
- [ ] Add scan configuration options
- [ ] Add NAS connection settings

---

## ✨ Feature Requests

### Issue #3: Codec Info & Media Analysis 🆕
**Labels**: `enhancement`, `feature`, `priority-high`
**Priority**: High
**Design Doc**: `docs/DESIGN_CODEC_FILETYPE.md`

**Description**:
미디어 파일의 코덱 정보 및 상세 분석 기능 추가

**Features**:
- 비디오 코덱 정보 (H.264, H.265, VP9, AV1)
- 오디오 코덱 정보 (AAC, AC3, DTS, FLAC)
- 해상도 및 품질 등급 (4K, 1080p, 720p, SD)
- HDR 포맷 감지 (HDR10, Dolby Vision, HLG)
- 비트레이트, 프레임레이트 정보

**Tasks**:
- [ ] FileStats 모델에 코덱 컬럼 추가
- [ ] Scanner에 ffprobe 파싱 확장
- [ ] 코덱 통계 API 엔드포인트 구현
- [ ] 품질 분포 API 엔드포인트 구현
- [ ] Statistics 페이지 생성

**Database Changes**:
```sql
ALTER TABLE file_stats ADD COLUMN video_codec VARCHAR(50);
ALTER TABLE file_stats ADD COLUMN audio_codec VARCHAR(50);
ALTER TABLE file_stats ADD COLUMN width INTEGER;
ALTER TABLE file_stats ADD COLUMN height INTEGER;
ALTER TABLE file_stats ADD COLUMN quality_tier VARCHAR(10);
ALTER TABLE file_stats ADD COLUMN hdr_format VARCHAR(20);
```

---

### Issue #4: Folder File List View 🆕
**Labels**: `enhancement`, `feature`, `priority-high`
**Priority**: High
**Design Doc**: `docs/DESIGN_CODEC_FILETYPE.md` (Part 2)

**Description**:
폴더 트리에서 폴더 선택 시 해당 폴더의 실제 파일 목록을 표시

**Features**:
- 폴더 선택 시 파일 목록 패널 표시
- 파일별 상세 정보 (크기, 코덱, 해상도, 재생시간)
- 정렬 기능 (이름, 크기, 재생시간, 수정일)
- 확장자별 필터링
- 페이지네이션 (50개씩)
- 파일 상세 모달

**Tasks**:
- [ ] `/api/folders/files` 엔드포인트 구현
- [ ] FileListPanel 컴포넌트 생성
- [ ] Folders 페이지 2패널 레이아웃으로 변경
- [ ] 정렬/필터 컨트롤 구현
- [ ] 페이지네이션 구현
- [ ] FileDetailModal 컴포넌트 생성 (optional)

**API Endpoint**:
```
GET /api/folders/files
  - folder_path: string (required)
  - page: int (default: 1)
  - page_size: int (default: 50)
  - sort_by: name|size|duration|modified_at
  - sort_order: asc|desc
  - extension: string (optional)
```

---

### Issue #5: Statistics Page with Codec Charts 🆕
**Labels**: `enhancement`, `feature`, `priority-medium`
**Priority**: Medium

**Description**:
코덱 및 품질 분포를 시각화하는 통계 페이지 생성

**Features**:
- 비디오 코덱 분포 파이 차트
- 오디오 코덱 분포 차트
- 품질 등급 분포 바 차트 (4K, 1080p, 720p, SD)
- 파일 타입별 상세 테이블 (클릭 시 모달)
- 샘플 파일 목록

**UI Mockup**:
```
┌─────────────────────────────────────────────┐
│  Statistics                                  │
├─────────────────────────────────────────────┤
│  [Video Codec Pie] [Quality Distribution]   │
│  [Audio Codec Bar] [File Type Table]        │
└─────────────────────────────────────────────┘
```

---

### Issue #6: Add Email Notifications
**Labels**: `enhancement`, `feature`
**Priority**: Medium

**Description**:
Add email notification support for:
- Storage threshold alerts (e.g., 900TB reached)
- Scan completion notifications
- Error alerts

**Acceptance Criteria**:
- [ ] SMTP configuration in settings
- [ ] Email template for notifications
- [ ] Test email functionality

---

### Issue #7: Add Kanban Board View for Work Status
**Labels**: `enhancement`, `feature`
**Priority**: Low

**Description**:
Convert the Work Status table view to include a Kanban board option for better visualization of work progress.

**Tasks**:
- [ ] Implement drag-and-drop columns
- [ ] Status columns: 대기, 작업 중, 완료
- [ ] Filter by Archive/PIC

---

### Issue #8: Scheduled Automatic Scans
**Labels**: `enhancement`, `feature`
**Priority**: Medium

**Description**:
Add ability to schedule automatic scans at specified intervals.

**Tasks**:
- [ ] Add scheduler configuration in Settings
- [ ] Support cron-like scheduling
- [ ] Add scan schedule display in dashboard

---

### Issue #9: File Type Statistics Page Enhancement
**Labels**: `enhancement`
**Priority**: Low

**Description**:
Enhance the Statistics page with:
- Detailed file type breakdown
- Size distribution histogram
- Duration distribution for media files

---

### Issue #10: Dark Mode Support
**Labels**: `enhancement`, `ui`
**Priority**: Low

**Description**:
Add dark mode toggle for better viewing experience.

---

### Issue #11: Export Dashboard as PDF
**Labels**: `enhancement`, `feature`
**Priority**: Low

**Description**:
Allow users to export the current dashboard view as a PDF report.

---

## 🔧 Technical Improvements

### Issue #12: Add Unit Tests
**Labels**: `testing`, `tech-debt`
**Priority**: High

**Description**:
Add comprehensive unit tests for:
- Backend API endpoints
- Scanner service
- Frontend components

---

### Issue #13: Add CI/CD Pipeline
**Labels**: `devops`, `tech-debt`
**Priority**: Medium

**Description**:
Set up GitHub Actions for:
- Automated testing
- Docker image builds
- Deployment automation

---

## 📋 To Create on GitHub

Run these commands (requires `gh` CLI):

```bash
# Install gh CLI first if not installed
# Windows: winget install GitHub.cli

gh auth login

# Create issues (Priority order)
# High Priority - New Features
gh issue create --title "Codec Info & Media Analysis" --body "미디어 파일의 코덱, 해상도, 품질 정보 분석 기능" --label "enhancement,feature,priority-high"
gh issue create --title "Folder File List View" --body "폴더 선택 시 파일 목록 표시 기능" --label "enhancement,feature,priority-high"
gh issue create --title "Statistics Page with Codec Charts" --body "코덱 및 품질 분포 시각화 페이지" --label "enhancement,feature,priority-medium"

# Bug Fixes
gh issue create --title "Alerts Page Not Implemented" --body "알림 페이지 구현 필요" --label "bug,enhancement"
gh issue create --title "Settings Page Not Implemented" --body "설정 페이지 구현 필요" --label "bug,enhancement"

# Features
gh issue create --title "Add Email Notifications" --body "이메일 알림 기능" --label "enhancement,feature"
gh issue create --title "Add Kanban Board View for Work Status" --body "작업 현황 칸반 보드 뷰" --label "enhancement,feature"
gh issue create --title "Scheduled Automatic Scans" --body "자동 스캔 스케줄링" --label "enhancement,feature"
gh issue create --title "File Type Statistics Page Enhancement" --body "파일 타입 통계 개선" --label "enhancement"
gh issue create --title "Dark Mode Support" --body "다크 모드 지원" --label "enhancement,ui"
gh issue create --title "Export Dashboard as PDF" --body "대시보드 PDF 내보내기" --label "enhancement,feature"

# Technical
gh issue create --title "Add Unit Tests" --body "단위 테스트 추가" --label "testing,tech-debt"
gh issue create --title "Add CI/CD Pipeline" --body "CI/CD 파이프라인 구축" --label "devops,tech-debt"
```

---

## 📊 Issue Priority Matrix

| Priority | Issues | Status |
|----------|--------|--------|
| 🔴 High | #3 Codec Info, #4 File List | 📋 Designed |
| 🟠 Medium | #5 Statistics Page, #6 Email, #8 Auto Scan | Planned |
| 🟢 Low | #7 Kanban, #9-11 UI Features | Backlog |

**Design Document**: `docs/DESIGN_CODEC_FILETYPE.md`

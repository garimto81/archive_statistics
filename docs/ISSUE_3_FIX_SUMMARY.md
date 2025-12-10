# Issue 3 수정 요약: 폴더 하이어라키 데이터 불일치

**작성일**: 2025-12-09
**이슈**: #3 폴더별 데이터 불일치
**블럭**: data.consistency
**상태**: Phase 1 완료

---

## 적용된 수정 사항

### Phase 1: 데이터 투명화 (완료)

**목표**: NAS 기준 / 구글 시트 기준 진행률을 모두 표시하여 데이터 불일치를 명확히 함

**수정 파일**:
- `D:\AI\claude01\archive-statistics\backend\app\services\progress_service.py`

**변경 내용**:

#### 1. `work_summary`에 신규 필드 추가

```python
folder_dict["work_summary"] = {
    "task_count": len(work_statuses_matched),
    "total_files": folder.file_count,              # NAS 스캔 결과
    "total_done": total_done,                      # 구글 시트 excel_done 합계
    "combined_progress": round(combined_progress, 1),  # NAS 기준 (참고용)
    # 신규 필드
    "sheets_total_videos": sheets_total,           # 구글 시트 total_videos 합계
    "sheets_excel_done": total_done,               # 명시적 표시
    "actual_progress": round(actual_progress, 1),  # 시트 기준 (실제 진행률)
    # 데이터 불일치 정보
    "data_source_mismatch": data_mismatch,         # 10% 이상 차이 시 true
    "mismatch_count": sheets_total - folder.file_count,  # 양수/음수로 방향 표시
}
```

#### 2. 진행률 계산 로직

**combined_progress (NAS 기준)**:
```python
combined_progress = (total_done / folder.file_count * 100) if folder.file_count > 0 else 0
```

**actual_progress (시트 기준)**:
```python
actual_progress = (total_done / sheets_total * 100) if sheets_total > 0 else 0
```

#### 3. 데이터 불일치 감지

```python
data_mismatch = abs(folder.file_count - sheets_total) > max(folder.file_count, sheets_total) * 0.1
```
- 10% 이상 차이가 나면 `data_source_mismatch = true`
- `mismatch_count`: 양수면 시트가 더 많음, 음수면 NAS가 더 많음

---

## 검증 결과

### WSOP 폴더 예시

| 항목 | 값 | 설명 |
|------|-----|------|
| **file_count** (NAS) | 860 | NAS에 실제로 있는 파일 수 |
| **sheets_total_videos** | 110 | 구글 시트에서 관리하는 작업 대상 수 |
| **total_done** | 54 | 완료된 작업 수 |
| **combined_progress** | 6.3% | 54 / 860 (NAS 기준, 참고용) |
| **actual_progress** | 49.1% | 54 / 110 (실제 작업 진행률) |
| **data_source_mismatch** | true | 10% 이상 차이 |
| **mismatch_count** | -750 | NAS가 750개 더 많음 |

**해석**:
- NAS에는 860개 파일이 있지만, 실제 작업 대상은 110개
- 750개 차이는 하위 폴더 파일이거나 작업 대상 아님
- 실제 진행률은 49.1% (절반 완료)
- `combined_progress` 6.3%는 참고용 (전체 NAS 파일 대비)

### PAD 폴더 예시

| 항목 | 값 |
|------|-----|
| file_count (NAS) | 44 |
| sheets_total_videos | 44 |
| combined_progress | 0.0% |
| actual_progress | 0.0% |
| data_source_mismatch | false |

**해석**:
- NAS 파일 수와 구글 시트 수량 일치 (불일치 없음)
- 두 진행률이 동일

### MPP 폴더 예시

| 항목 | 값 |
|------|-----|
| file_count (NAS) | 11 |
| sheets_total_videos | 11 |
| combined_progress | 54.5% |
| actual_progress | 54.5% |
| data_source_mismatch | false |

**해석**:
- 데이터 일치, 진행률 동일

---

## API 응답 예시

### GET /api/folders?path=/mnt/nas/WSOP

```json
{
  "id": 123,
  "name": "WSOP",
  "path": "/mnt/nas/WSOP",
  "file_count": 860,
  "work_summary": {
    "task_count": 5,
    "total_files": 860,
    "total_done": 54,
    "combined_progress": 6.3,
    "sheets_total_videos": 110,
    "sheets_excel_done": 54,
    "actual_progress": 49.1,
    "data_source_mismatch": true,
    "mismatch_count": -750
  },
  "work_statuses": [
    {
      "category": "WSOP LA",
      "excel_done": 11,
      "total_videos": 11,
      "progress_percent": 100.0
    },
    {
      "category": "WSOP Cyprus",
      "excel_done": 6,
      "total_videos": 6,
      "progress_percent": 100.0
    },
    {
      "category": "WSOP Europe",
      "excel_done": 22,
      "total_videos": 41,
      "progress_percent": 53.7
    },
    {
      "category": "2023 WSOP Paradise",
      "excel_done": 9,
      "total_videos": 9,
      "progress_percent": 100.0
    },
    {
      "category": "2025 WSOP",
      "excel_done": 6,
      "total_videos": 43,
      "progress_percent": 14.0
    }
  ]
}
```

---

## 프론트엔드 연동 가이드

### 1. 진행률 표시

```tsx
// 기본: actual_progress 사용 (시트 기준 실제 진행률)
<ProgressBar value={workSummary.actual_progress} />

// 추가 정보 표시 (optional)
{workSummary.data_source_mismatch && (
  <Tooltip title={`NAS: ${workSummary.total_files}, Sheet: ${workSummary.sheets_total_videos}`}>
    <WarningIcon />
  </Tooltip>
)}
```

### 2. 데이터 불일치 경고

```tsx
{workSummary.data_source_mismatch && (
  <Alert severity="warning">
    <AlertTitle>데이터 출처 불일치</AlertTitle>
    NAS 파일 수({workSummary.total_files})와
    작업 대상 수({workSummary.sheets_total_videos})가 다릅니다.
    <br />
    차이: {Math.abs(workSummary.mismatch_count)}개
    ({workSummary.mismatch_count > 0 ? "시트가 더 많음" : "NAS가 더 많음"})
  </Alert>
)}
```

### 3. 상세 정보 패널

```tsx
<Stack spacing={1}>
  <Typography variant="body2">
    실제 진행률: {workSummary.actual_progress}%
    ({workSummary.total_done}/{workSummary.sheets_total_videos})
  </Typography>
  <Typography variant="caption" color="text.secondary">
    NAS 기준: {workSummary.combined_progress}%
    ({workSummary.total_done}/{workSummary.total_files})
  </Typography>
</Stack>
```

---

## 장점

1. **투명성**: 사용자가 데이터 출처 차이를 명확히 인지
2. **정확성**: 실제 작업 진행률(`actual_progress`)을 정확히 표시
3. **호환성**: 기존 필드(`combined_progress`) 유지로 하위 호환
4. **간단함**: 백엔드 로직 변경 최소화

---

## 다음 단계 (Phase 2-4)

### Phase 2: 매칭 로직 개선
- 폴더명과 카테고리 길이 비율 체크
- 단어 수 기반 포괄성 필터링
- 하위 폴더 패턴 제외

### Phase 3: 하이어라키 기반 매칭
- 하위 폴더 우선 매칭
- 상위 폴더는 하위 매칭 제외
- work_status에 `folder_path` 명시적 매핑 추가

### Phase 4: 데이터 정규화
- 구글 시트 ↔ NAS 데이터 동기화 자동화
- `total_videos` 자동 계산 (file_count 기반)
- 수동 조정이 필요한 경우 플래그 표시

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `backend/app/services/progress_service.py` | 수정된 핵심 로직 |
| `scripts/debug_hierarchy.py` | 디버깅 스크립트 |
| `scripts/analyze_wsop_mismatch.py` | WSOP 폴더 상세 분석 |
| `scripts/test_progress_fix.py` | Phase 1 검증 스크립트 |
| `docs/ISSUE_3_DATA_INCONSISTENCY_ANALYSIS.md` | 상세 분석 리포트 |

---

## 실행 방법

### 검증 스크립트 실행

```bash
cd D:\AI\claude01\archive-statistics
python scripts/test_progress_fix.py
```

**예상 출력**:
```
[WSOP]
  file_count: 860
  total_files: 860
  sheets_total_videos: 110
  combined_progress: 6.3%
  actual_progress: 49.1%
  data_source_mismatch: True
  [OK] actual_progress field exists
  [OK] data_source_mismatch field exists
```

### API 테스트

```bash
# 백엔드 서버 시작
cd D:\AI\claude01\archive-statistics\backend
uvicorn app.main:app --reload --port 8000

# 다른 터미널에서 API 호출
curl http://localhost:8000/api/folders?path=/mnt/nas/WSOP
```

---

## 결론

Phase 1 수정을 통해 폴더 하이어라키 데이터 불일치 문제를 **투명하게 표시**할 수 있게 되었습니다.

- **`actual_progress`**: 실제 작업 진행률 (구글 시트 기준)
- **`data_source_mismatch`**: 데이터 출처 불일치 플래그
- **`mismatch_count`**: 차이 수량 및 방향

프론트엔드에서는 `actual_progress`를 기본 진행률로 사용하고, `data_source_mismatch`가 true일 때 경고 메시지를 표시하면 됩니다.

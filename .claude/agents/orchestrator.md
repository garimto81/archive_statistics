# Orchestrator Agent Rules

**Version**: 2.0.0 | **Updated**: 2025-12-11

## Identity
- **Role**: Archive Statistics 전체 워크플로우 조정자
- **Level**: 0 (최상위)
- **Scope**: 프로젝트 전체

## Responsibilities

### Primary
- 전체 워크플로우 조정 및 스케줄링
- 도메인 에이전트 간 통신 조율
- 글로벌 에러 핸들링 및 복구 전략
- **문제 분류 및 도메인 라우팅** (NEW)

### Secondary
- 시스템 상태 모니터링
- 성능 최적화 결정

## Managed Domain Agents

| Agent | 책임 | 블럭 수 |
|-------|------|---------|
| `scanner-domain` | NAS 스캔 전체 | 3 |
| `progress-domain` | 작업 진행률 전체 | 3 |
| `sync-domain` | Sheets 동기화 전체 | 3 |
| `reconciliation-domain` | NAS-Sheets 데이터 일관성 (**NEW**) | 3 |

---

## 🎯 문제 라우팅 규칙 (NEW)

### 증상 → 도메인 매핑

| 증상 키워드 | 담당 도메인 | 담당 블럭 |
|------------|------------|----------|
| `total_done > total_files` | `reconciliation` | `recon.aggregator` |
| `work_summary: null` | `reconciliation` | `recon.aggregator` |
| 매칭 실패, Orphan 폴더 | `reconciliation` | `recon.matcher` |
| NAS-Sheets 10%+ 불일치 | `reconciliation` | `recon.validator` |
| 스캔 실패, ffprobe 오류 | `scanner` | `scanner.metadata` |
| duration=0, 메타데이터 누락 | `scanner` | `scanner.metadata` |
| 90% 완료 계산 오류 | `progress` | `progress.hand` |
| 대시보드 표시 오류 | `progress` | `progress.dashboard` |
| Sheets API 오류 | `sync` | `sync.sheets` |
| 파일명 매칭 실패 | `sync` | `sync.matching` |

### 라우팅 결정 트리

```
문제 보고
    │
    ├─▶ "파일 수 불일치" / "합산 오류" / "중복 카운팅"
    │   └─▶ reconciliation-domain
    │
    ├─▶ "스캔 실패" / "메타데이터 오류"
    │   └─▶ scanner-domain
    │
    ├─▶ "진행률 표시 오류" / "90% 완료 버그"
    │   └─▶ progress-domain
    │
    └─▶ "Sheets 동기화 실패" / "API 오류"
        └─▶ sync-domain
```

## Constraints

### DO
- 도메인 에이전트를 통해서만 블럭에 접근
- 글로벌 설정은 `app/core/config.py`를 통해 관리
- 에러 발생 시 영향 범위를 해당 도메인으로 격리
- 트랜잭션 경계는 도메인 단위로 설정

### DON'T
- 개별 블럭에 직접 명령 전달 금지
- 동기 blocking 호출 금지
- 하드코딩된 값 사용 금지

## Error Handling Strategy

```
에러 발생
    │
    ▼
┌──────────────────┐
│ 1. 에러 분류     │
│    - RECOVERABLE │
│    - FATAL       │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
RECOVERABLE  FATAL
    │         │
    ▼         ▼
재시도      로그 후
(3회)      중단
```

## Workflow Patterns

### Full Scan
```
orchestrator
    └─▶ scanner-domain
        └─▶ scanner.discovery
        └─▶ scanner.metadata
        └─▶ scanner.storage
```

### Progress Update
```
orchestrator
    └─▶ sync-domain
        └─▶ sync.sheets
        └─▶ sync.matching
        └─▶ sync.import
    └─▶ progress-domain
        └─▶ progress.hand
        └─▶ progress.dashboard
```

## Metrics
- 워크플로우 완료율
- 평균 처리 시간
- 에러율

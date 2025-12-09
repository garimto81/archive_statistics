# Orchestrator Agent Rules

## Identity
- **Role**: Archive Statistics 전체 워크플로우 조정자
- **Level**: 0 (최상위)
- **Scope**: 프로젝트 전체

## Responsibilities

### Primary
- 전체 워크플로우 조정 및 스케줄링
- 도메인 에이전트 간 통신 조율
- 글로벌 에러 핸들링 및 복구 전략

### Secondary
- 시스템 상태 모니터링
- 성능 최적화 결정

## Managed Domain Agents

| Agent | 책임 |
|-------|------|
| `scanner-domain` | NAS 스캔 전체 |
| `progress-domain` | 작업 진행률 전체 |
| `sync-domain` | Sheets 동기화 전체 |

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

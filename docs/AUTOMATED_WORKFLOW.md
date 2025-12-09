# Automated Workflow with Block Agent System

**Version**: 1.0.0 | **Date**: 2025-12-09 | **Status**: Draft

> 사용자 최종 검증 전까지 모든 작업을 자동화하는 워크플로우 설계

---

## 목차

1. [개요](#1-개요)
2. [워크플로우 통합 아키텍처](#2-워크플로우-통합-아키텍처)
3. [Phase별 에이전트 매핑](#3-phase별-에이전트-매핑)
4. [블럭 기반 자동화](#4-블럭-기반-자동화)
5. [향상된 /work 커맨드](#5-향상된-work-커맨드)
6. [사용자 검증 지점](#6-사용자-검증-지점)
7. [구현 가이드](#7-구현-가이드)

---

## 1. 개요

### 1.1 목표

| 목표 | 설명 |
|------|------|
| **완전 자동화** | 사용자 최종 검증 전까지 모든 단계 자동 실행 |
| **블럭 격리** | 작업 범위를 해당 블럭으로 제한하여 오류 최소화 |
| **병렬 처리** | 독립적인 작업은 병렬로 실행하여 시간 단축 |
| **점진적 검증** | 각 단계별 자동 검증으로 오류 조기 발견 |

### 1.2 기존 커맨드 분석

| 커맨드 | 역할 | 블럭 연동 |
|--------|------|-----------|
| `/pre-work` | 솔루션 검색, 중복 확인 | - |
| `/work` | 전체 워크플로우 | 모든 도메인 |
| `/parallel dev` | 병렬 개발 | 해당 블럭 |
| `/parallel test` | 병렬 테스트 | 테스트 블럭 |
| `/parallel review` | 병렬 리뷰 | 해당 블럭 |
| `/tdd` | TDD 워크플로우 | 해당 블럭 |
| `/check` | 품질 검사 | 전체 |
| `/commit` | 커밋 생성 | - |
| `/create-pr` | PR 생성 | - |

---

## 2. 워크플로우 통합 아키텍처

### 2.1 전체 흐름

```
사용자 요청
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Phase 0: Pre-Work                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   솔루션    │  │    중복     │  │ Make vs Buy │        │
│  │   검색      │  │    확인     │  │   분석      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────┬───────────────────────────────────┘
                          │ 자동 승인 (중복 없음 + 직접 개발 권장)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 Phase 1: Block 분석 (병렬)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Orchestrator Agent                      │   │
│  └────────────────────────┬────────────────────────────┘   │
│               ┌───────────┼───────────┐                    │
│               ▼           ▼           ▼                    │
│        ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│        │ Scanner  │ │ Progress │ │   Sync   │            │
│        │  Agent   │ │  Agent   │ │  Agent   │            │
│        └──────────┘ └──────────┘ └──────────┘            │
│                                                            │
│  결과: 영향 블럭 식별, 변경 범위 정의                      │
└─────────────────────────┬───────────────────────────────────┘
                          │ 자동 진행
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Phase 2: 이슈 + 문서 생성                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   이슈      │  │    PRD     │  │   문서      │        │
│  │   생성      │  │   생성      │  │   업데이트  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────┬───────────────────────────────────┘
                          │ 자동 진행
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 3: TDD 개발 (블럭 단위)                  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Block-Aware TDD Loop                    │   │
│  │                                                       │   │
│  │   🔴 RED ────▶ 🟢 GREEN ────▶ ♻️ REFACTOR          │   │
│  │     │              │               │                  │   │
│  │     ▼              ▼               ▼                  │   │
│  │  테스트 작성    구현 완료      리팩토링              │   │
│  │  (블럭 범위)   (블럭 범위)    (블럭 범위)            │   │
│  │                                                       │   │
│  │  AGENT_RULES.md 참조하여 범위 제한                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  각 사이클마다 자동 커밋                                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ 자동 진행
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               Phase 4: 검증 (병렬)                          │
│                                                              │
│    ┌──────────────────────────────────────────────────┐    │
│    │           /parallel test (자동 실행)              │    │
│    │                                                    │    │
│    │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │    │
│    │  │ Unit   │ │ Integ  │ │  E2E   │ │Security│   │    │
│    │  │ Test   │ │ Test   │ │  Test  │ │  Test  │   │    │
│    │  └────────┘ └────────┘ └────────┘ └────────┘   │    │
│    └──────────────────────────────────────────────────┘    │
│                                                              │
│    ┌──────────────────────────────────────────────────┐    │
│    │           /parallel review (자동 실행)            │    │
│    │                                                    │    │
│    │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │    │
│    │  │Security│ │ Logic  │ │ Style  │ │  Perf  │   │    │
│    │  │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │   │    │
│    │  └────────┘ └────────┘ └────────┘ └────────┘   │    │
│    └──────────────────────────────────────────────────┘    │
│                                                              │
│  실패 시: 자동 수정 시도 (최대 2회) → 실패 시 중단          │
└─────────────────────────┬───────────────────────────────────┘
                          │ 자동 진행
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 Phase 5: PR 준비                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   최종      │  │    PR      │  │   보고서    │        │
│  │   커밋      │  │   생성      │  │   작성      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              🛑 사용자 최종 검증 지점                       │
│                                                              │
│  제공 정보:                                                 │
│  - 구현 요약                                                │
│  - 변경된 파일 목록                                         │
│  - 테스트 결과                                              │
│  - 코드 리뷰 결과                                           │
│  - PR 링크                                                  │
│                                                              │
│  사용자 선택:                                               │
│  [승인] → PR 머지 진행                                      │
│  [수정 요청] → 피드백 기반 재작업                           │
│  [취소] → 브랜치 삭제                                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 자동 진행 조건

| Phase | 자동 진행 조건 | 중단 조건 |
|-------|----------------|-----------|
| 0 → 1 | 중복 이슈 없음 | 중복 발견 → 사용자 확인 |
| 1 → 2 | 영향 블럭 식별 완료 | 영향 범위 불명확 → 사용자 확인 |
| 2 → 3 | 이슈/문서 생성 완료 | - |
| 3 → 4 | 모든 테스트 통과 | 테스트 실패 → 자동 수정 시도 |
| 4 → 5 | 리뷰 Critical 0개 | Critical 이슈 발견 → 자동 수정 시도 |
| 5 → 검증 | PR 생성 완료 | - |

---

## 3. Phase별 에이전트 매핑

### 3.1 Phase 0: Pre-Work

```
┌─────────────────────────────────────────────────────────────┐
│                     Pre-Work Phase                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  에이전트: general-purpose (병렬 3개)                       │
│                                                              │
│  Agent 1: 솔루션 검색                                       │
│    - GitHub 오픈소스 검색                                   │
│    - 웹 검색 (기술 문서, 블로그)                            │
│                                                              │
│  Agent 2: 중복 확인                                         │
│    - gh issue list 검색                                     │
│    - gh pr list 검색                                        │
│                                                              │
│  Agent 3: 기술 분석                                         │
│    - 의존성 분석                                            │
│    - Make vs Buy 평가                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Phase 1: Block 분석

```
┌─────────────────────────────────────────────────────────────┐
│                    Block Analysis Phase                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Orchestrator → 작업 분배                                   │
│        │                                                     │
│        ├─▶ Scanner Domain Agent                             │
│        │     └─ 스캔 관련 변경 여부 분석                    │
│        │     └─ AGENT_RULES.md 참조                         │
│        │                                                     │
│        ├─▶ Progress Domain Agent                            │
│        │     └─ 진행률 관련 변경 여부 분석                  │
│        │     └─ 90% 완료 로직 영향 분석                     │
│        │                                                     │
│        └─▶ Sync Domain Agent                                │
│              └─ Sheets 동기화 관련 변경 여부 분석           │
│                                                              │
│  출력: AffectedBlocks = ["scanner.metadata", "progress.hand"]│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Phase 3: TDD 개발

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD Development Phase                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  For each AffectedBlock:                                    │
│                                                              │
│    1. Load AGENT_RULES.md                                   │
│       └─ 블럭 범위, 제약사항, 의존성 확인                   │
│                                                              │
│    2. 🔴 RED: 테스트 작성                                   │
│       └─ 테스트 위치: AGENT_RULES.md의 Testing 섹션 참조    │
│       └─ 자동 커밋: "test: Add {feature} test (RED)"        │
│                                                              │
│    3. 🟢 GREEN: 구현                                        │
│       └─ DO/DON'T 규칙 준수                                 │
│       └─ 자동 커밋: "feat: Implement {feature} (GREEN)"     │
│                                                              │
│    4. ♻️ REFACTOR: 개선                                     │
│       └─ 블럭 내부만 리팩토링                               │
│       └─ 자동 커밋: "refactor: Improve {feature}"           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Phase 4: 검증

```
┌─────────────────────────────────────────────────────────────┐
│                    Validation Phase                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  /parallel test (자동 실행)                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Unit Test Agent      → pytest tests/unit/ -v       │   │
│  │  Integration Agent    → pytest tests/integration/   │   │
│  │  E2E Agent           → playwright test              │   │
│  │  Security Agent      → bandit -r src/               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  /parallel review (자동 실행)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Security Agent      → 취약점 검사                   │   │
│  │  Logic Agent         → 로직 정확성 검증             │   │
│  │  Style Agent         → 코드 스타일 검사             │   │
│  │  Performance Agent   → 성능 분석                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  실패 처리:                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  attempt = 0                                         │   │
│  │  while attempt < 3:                                  │   │
│  │      result = run_validation()                       │   │
│  │      if result.success:                             │   │
│  │          break                                       │   │
│  │      else:                                           │   │
│  │          auto_fix(result.errors)  # 자동 수정       │   │
│  │          attempt += 1                                │   │
│  │  if attempt >= 3:                                    │   │
│  │      create_failed_issue()  # 수동 개입 요청        │   │
│  │      halt_workflow()                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 블럭 기반 자동화

### 4.1 블럭별 자동화 규칙

| 블럭 | 자동화 범위 | AGENT_RULES 참조 |
|------|-------------|------------------|
| `scanner.discovery` | NAS 경로, 스캔 API | `api/AGENT_RULES.md` |
| `scanner.metadata` | ffprobe, duration | `services/AGENT_RULES.md` |
| `scanner.storage` | DB 저장, 모델 | `models/AGENT_RULES.md` |
| `progress.video` | 비디오 상태 | `api/AGENT_RULES.md` |
| `progress.hand` | 90% 완료 로직 | `models/AGENT_RULES.md` |
| `progress.dashboard` | 통계 집계 | `api/AGENT_RULES.md` |

### 4.2 블럭 컨텍스트 로딩

```python
# 작업 시작 시 해당 블럭의 AGENT_RULES.md 자동 로딩
def load_block_context(block_id: str) -> BlockContext:
    """
    블럭 컨텍스트 로딩

    1. 블럭 ID로 AGENT_RULES.md 위치 결정
    2. 규칙 파싱 (DO, DON'T, Dependencies)
    3. 관련 파일 목록 생성
    """
    block_mapping = {
        "scanner.discovery": "backend/app/api/AGENT_RULES.md",
        "scanner.metadata": "backend/app/services/AGENT_RULES.md",
        "scanner.storage": "backend/app/models/AGENT_RULES.md",
        "progress.video": "backend/app/api/AGENT_RULES.md",
        "progress.hand": "backend/app/models/AGENT_RULES.md",
        "progress.dashboard": "backend/app/api/AGENT_RULES.md",
    }

    rules_path = block_mapping.get(block_id)
    return parse_agent_rules(rules_path)
```

### 4.3 블럭 범위 강제

```python
# AI 에이전트가 블럭 범위를 벗어나면 자동 차단
def validate_file_access(file_path: str, block_context: BlockContext) -> bool:
    """
    파일 접근 검증

    Returns:
        True: 접근 허용
        False: 접근 거부 + 경고
    """
    allowed_paths = block_context.scope

    if not any(file_path.startswith(p) for p in allowed_paths):
        logger.warning(f"Block boundary violation: {file_path}")
        return False

    return True
```

---

## 5. 향상된 /work 커맨드

### 5.1 블럭 통합 버전

```markdown
# /work-enhanced - 블럭 에이전트 통합 워크플로우

## 실행 흐름

/work-enhanced <작업 지시>
    │
    ├─ Phase 0: Pre-Work (/pre-work 자동 실행)
    │      └─ 솔루션 검색, 중복 확인
    │      └─ 자동 승인 또는 사용자 확인 요청
    │
    ├─ Phase 1: Block 분석
    │      └─ Orchestrator → Domain Agents (병렬)
    │      └─ 영향 블럭 식별
    │      └─ 각 블럭의 AGENT_RULES.md 로딩
    │
    ├─ Phase 2: 이슈 + 문서 생성
    │      └─ GitHub 이슈 생성
    │      └─ PRD/문서 업데이트
    │
    ├─ Phase 3: TDD 개발 (블럭 단위)
    │      └─ For each block in AffectedBlocks:
    │           └─ Load AGENT_RULES.md
    │           └─ RED → GREEN → REFACTOR
    │           └─ 자동 커밋
    │
    ├─ Phase 4: 검증 (/parallel test + /parallel review)
    │      └─ 테스트 실행
    │      └─ 코드 리뷰
    │      └─ 실패 시 자동 수정 (최대 2회)
    │
    ├─ Phase 5: PR 준비
    │      └─ 최종 커밋
    │      └─ PR 생성
    │      └─ 보고서 작성
    │
    └─ 🛑 사용자 최종 검증
           └─ 승인 / 수정 요청 / 취소
```

### 5.2 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--block <id>` | 특정 블럭만 대상 | `/work --block scanner.metadata "메타데이터 추출 개선"` |
| `--skip-pre-work` | Pre-Work 스킵 | `/work --skip-pre-work "빠른 수정"` |
| `--no-auto-fix` | 자동 수정 비활성화 | `/work --no-auto-fix "정밀 작업"` |
| `--strict` | 엄격 모드 (1회 실패 시 중단) | `/work --strict "프로덕션 배포"` |

---

## 6. 사용자 검증 지점

### 6.1 검증 지점 정의

| 지점 | 조건 | 사용자 액션 |
|------|------|-------------|
| **Pre-Work 확인** | 중복 이슈 발견 또는 라이브러리 권장 | 진행/중단 선택 |
| **Block 범위 확인** | 영향 범위가 3개 블럭 초과 | 범위 승인 |
| **최종 검증** | 모든 Phase 완료 | 승인/수정/취소 |

### 6.2 최종 검증 UI

```markdown
# 작업 완료 - 검증 요청

## 요약
- **작업 지시**: NAS 스캔 성능 최적화
- **영향 블럭**: scanner.discovery, scanner.metadata
- **소요 시간**: 15분

## 변경 사항
| 파일 | 변경 | 블럭 |
|------|------|------|
| `api/scan.py` | +20/-5 | scanner.discovery |
| `services/scanner.py` | +45/-12 | scanner.metadata |

## 테스트 결과
- Unit: 24/24 ✅
- Integration: 8/8 ✅
- E2E: 5/5 ✅

## 코드 리뷰 결과
- Critical: 0 ✅
- High: 0 ✅
- Medium: 2 (스타일 권고)
- Score: 92/100

## PR
- [#123 - NAS 스캔 성능 최적화](link)

---

**다음 중 선택해주세요:**

[✅ 승인] PR 머지 진행
[📝 수정 요청] 피드백 입력
[❌ 취소] 브랜치 삭제
```

---

## 7. 구현 가이드

### 7.1 단계별 구현

| 단계 | 작업 | 우선순위 |
|------|------|----------|
| 1 | 기존 AGENT_RULES.md 파일 완성 | ✅ 완료 |
| 2 | Block 분석 로직 구현 | High |
| 3 | /work 커맨드 블럭 통합 | High |
| 4 | 자동 검증/수정 로직 | Medium |
| 5 | 사용자 검증 UI | Medium |

### 7.2 파일 생성 필요

```
archive-statistics/
├── .claude/
│   ├── agents/              ✅ 완료
│   │   ├── orchestrator.md
│   │   ├── scanner-domain.md
│   │   ├── progress-domain.md
│   │   └── sync-domain.md
│   │
│   └── commands/            📝 생성 필요
│       └── work-enhanced.md  # 향상된 /work 커맨드
│
└── backend/app/
    ├── api/AGENT_RULES.md   ✅ 완료
    ├── services/AGENT_RULES.md ✅ 완료
    └── models/AGENT_RULES.md ✅ 완료
```

### 7.3 연동 구조

```mermaid
graph TD
    A[사용자 요청] --> B[/work-enhanced]
    B --> C[/pre-work]
    C --> D{중복?}
    D -->|No| E[Block 분석]
    D -->|Yes| F[사용자 확인]
    F --> E
    E --> G[이슈/문서 생성]
    G --> H[TDD 개발]
    H --> I[/parallel test]
    I --> J[/parallel review]
    J --> K{Pass?}
    K -->|No| L[자동 수정]
    L --> I
    K -->|Yes| M[PR 생성]
    M --> N[최종 검증]
    N --> O{승인?}
    O -->|Yes| P[머지]
    O -->|No| Q[수정/취소]
```

---

---

## 8. 완전 자동화 버전: /work-auto

사용자 검증을 **최종 보고서 확인 1회**로 최소화한 완전 자동화 버전입니다.

### 핵심 차이점

| 항목 | /work-block | /work-auto |
|------|-------------|------------|
| 사용자 개입 | 각 Phase 후 확인 가능 | 최종 보고서만 |
| E2E 검증 | /parallel test | Playwright 7단계 전체 |
| 자동 수정 | 2회 | 3회 |
| 보고서 | 간략 | 상세 (Visual Gallery 포함) |

### E2E Strict Validation 7단계

```
Level 1: Functional Testing     → 기능 검증
Level 2: Visual Regression      → UI 변경 감지
Level 3: Accessibility          → WCAG 2.1 AA 준수
Level 4: API Testing            → 백엔드 검증
Level 5: Performance            → 성능 측정
Level 6: Security               → 보안 검증
Level 7: Cross-Browser          → 호환성 검증
```

상세: [E2E_STRICT_VALIDATION.md](./E2E_STRICT_VALIDATION.md)
커맨드: `.claude/commands/work-auto.md`

---

## 참조

| 문서 | 설명 |
|------|------|
| [BLOCK_AGENT_SYSTEM.md](./BLOCK_AGENT_SYSTEM.md) | 블럭 에이전트 아키텍처 |
| [E2E_STRICT_VALIDATION.md](./E2E_STRICT_VALIDATION.md) | E2E 엄격 검증 파이프라인 |
| [VIDEO_COMPLETION_SPEC.md](./VIDEO_COMPLETION_SPEC.md) | 90% 완료 기준 설계 |
| `.claude/commands/work.md` | 기존 /work 커맨드 |
| `.claude/commands/work-auto.md` | 완전 자동화 커맨드 |
| `.claude/commands/parallel.md` | 병렬 실행 커맨드 |

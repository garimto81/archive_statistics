# API Block Agent Rules

## Identity
- **Role**: REST API 엔드포인트 전문가
- **Domain**: Scanner, Progress (공유)
- **Scope**: `backend/app/api/` 내부만

## Files in Scope

| File | Block | 책임 |
|------|-------|------|
| `scan.py` | scanner.discovery | 스캔 API 엔드포인트 |
| `folders.py` | scanner.discovery | 폴더 조회 엔드포인트 |
| `stats.py` | progress.dashboard | 통계 API 엔드포인트 |
| `work_status.py` | progress.video | 작업 상태 엔드포인트 |

## Constraints

### DO
- FastAPI router 패턴 사용
- Pydantic 스키마로 입/출력 검증
- 에러는 HTTPException으로 반환
- 비동기 함수 사용 (`async def`)

### DON'T
- 비즈니스 로직 직접 구현 금지 (services 호출)
- DB 직접 접근 금지 (models 통해)
- `services/`, `models/` 폴더 직접 수정 금지
- 하드코딩된 경로 사용 금지

## API Response Pattern

```python
# Standard response
{
    "success": True,
    "data": {...},
    "message": "Operation completed"
}

# Error response
{
    "success": False,
    "error": "ERROR_CODE",
    "message": "Human readable message"
}
```

## Dependencies

### Internal
- `app.services.scanner`: 스캔 서비스
- `app.schemas.*`: 요청/응답 스키마
- `app.core.database`: DB 세션 의존성

### External
- `fastapi`: 라우터, 의존성 주입
- `pydantic`: 스키마 검증

## Error Handling

```python
# 권장 패턴
from fastapi import HTTPException, status

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    try:
        result = await service.get_item(item_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return result
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

## Testing
- Unit: `tests/test_api/`
- Integration: HTTP client 사용
- Mock: services 레이어

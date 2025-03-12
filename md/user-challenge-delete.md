## 기본 정보

- **API 경로**: /v1/user-challenges/delete
- **Method**: POST
- **Description**: 사용자의 특정 챌린지 컨테이너를 삭제합니다.

## Request

### Path Parameters

| 파라미터명   | 타입   | 필수 여부 | 설명                           |
| ------------ | ------ | --------- | ------------------------------ |
| challenge_id | int    | Yes       | 삭제할 Challenge의 고유 식별자 |
| username     | string | Yes       | 사용자 닉네임                  |

### Request Header

| 헤더명       | 필수 여부 | 설명             |
| ------------ | --------- | ---------------- |
| Content-Type | Yes       | application/json |

## Response

### Response Body

| 필드    | 타입    | 필수 여부 | 설명           |
| ------- | ------- | --------- | -------------- |
| success | boolean | Yes       | 삭제 성공 여부 |
| message | string  | Yes       | 결과 메시지    |

### 성공 응답 예시 (200 OK)

```json
{
  "message": "챌린지가 성공적으로 삭제되었습니다."
}
```

### 실패 응답 예시

### 403 Forbidden

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "해당 챌린지를 삭제할 권한이 없습니다."
  }
}
```

### 404 Not Found

```json
{
  "error": {
    "code": "CHALLENGE_NOT_FOUND",
    "message": "요청한 챌린지를 찾을 수 없습니다."
  }
}
```

### 500 Internal Server Error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "챌린지 삭제 중 오류가 발생했습니다."
  }
}
```

## 비고

- 삭제 요청 시 실행 중인 컨테이너도 함께 종료됩니다.
- 삭제된 챌린지는 복구할 수 없습니다.
- 사용자는 자신이 생성한 챌린지만 삭제할 수 있습니다.

## 제한사항

- 삭제 요청은 챌린지 소유자만 가능

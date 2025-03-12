## 기본 정보

- **API 경로**: /v1/user-challenges
- **Method**: POST
- **Description**: 사용자별 챌린지 컨테이너 정보를 조회합니다.

## Request

### Path Parameters

| 파라미터명   | 타입   | 필수 여부 | 설명                           |
| ------------ | ------ | --------- | ------------------------------ |
| challenge_id | int    | Yes       | 생성할 Challenge의 고유 식별자 |
| username     | string | Yes       | 사용자 아이디                  |

### Request Body

```json
{
  "challenge_id": 1,
  "username": "test"
}
```

### Request Header

| 헤더명       | 필수 여부 | 설명             |
| ------------ | --------- | ---------------- |
| Content-Type | Yes       | application/json |

## Response

### Response Body

| 필드        | 타입   | 필수 여부 | 설명                                             |
| ----------- | ------ | --------- | ------------------------------------------------ |
| data.status | string | Yes       | 생성된 컨테이너의 상태 정보                      |
| data.port   | int    | No        | 컨테이너 포트 번호, Running 상태일 경우에만 반환 |

컨테이너 상태값

| 상태    | 설명   |
| ------- | ------ |
| None    | 생성중 |
| Running | 실행중 |
| Deleted | 삭제됨 |
| Error   | 에러   |

### 성공 응답 예시 (200 OK)

```json
{
    "data": {
        "status": "Running"
        "port" : 12345
    }
}

```

### 실패 응답 예시

### 404 Not Found

```json
{
  "error": {
    "type": "CHALLENGE_NOT_FOUND",
    "message": "Challenge not found"
  }
}
```

### 500 Internal Server Error

```json
{
  "error": {
    "type": "INTERNAL_SERVER_ERROR",
    "message": "컨테이너 생성 중 오류가 발생했습니다."
  }
}
```

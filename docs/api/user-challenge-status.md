## Basic Information

- **API Path**: /v2/user-challenges
- **Method**: POST
- **Description**: Retrieves user-specific challenge container information.

## Request

### Path Parameters

| Parameter Name | Type   | Required | Description                    |
| -------------- | ------ | -------- | ------------------------------ |
| challenge_id   | int    | Yes      | Unique identifier of the Challenge to create |
| username       | string | Yes      | User ID                        |

### Request Body

```json
{
  "challenge_id": 1,
  "username": "test"
}
```

### Request Header

| Header Name    | Required | Description         |
| -------------- | -------- | ------------------- |
| Content-Type   | Yes      | application/json    |

## Response

### Response Body

| Field         | Type   | Required | Description                                    |
| ------------- | ------ | -------- | ---------------------------------------------- |
| data.status   | string | Yes      | Status information of the created container   |
| data.port     | int    | No       | Container port number, returned only when status is Running |

Container Status Values

| Status   | Description    |
| -------- | -------------- |
| None     | Creating       |
| Running  | Running        |
| Deleted  | Deleted        |
| Error    | Error          |

### Success Response Example (200 OK)

```json
{
    "data": {
        "status": "Running",
        "port": 12345
    }
}
```

### Error Response 
- For more details, please refer to [Error Response](./error-response.md) documentation.
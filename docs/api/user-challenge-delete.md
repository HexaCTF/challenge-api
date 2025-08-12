## Basic Information

- **API Path**: /v2/user-challenges/delete
- **Method**: POST
- **Description**: Delete user challenge

## Request

### Path Parameters

| Parameter Name | Type   | Required | Description                    |
| -------------- | ------ | -------- | ------------------------------ |
| challenge_id   | int    | Yes      | Unique identifier of the Challenge to delete |
| username       | string | Yes      | User nickname                  |

### Request Header

| Header Name    | Required | Description         |
| -------------- | -------- | ------------------- |
| Content-Type   | Yes      | application/json    |

## Response

### Response Body

| Field   | Type    | Required | Description        |
| ------- | ------- | -------- | ------------------ |
| success | boolean | Yes      | Deletion success status |
| message | string  | Yes      | Result message     |

### Success Response Example (200 OK)

```json
{
  "message": "Challenge has been successfully deleted."
}
```

### Error Response
- For more details, please refer to [Error repsone](./error-response.md) documentation.

## Notes

- When deleting, running containers will also be terminated.
- Deleted challenges cannot be recovered.
- Users can only delete challenges they have created.

## Limitations

- Only the challenge owner can make deletion requests

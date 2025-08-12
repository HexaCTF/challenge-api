# Error Response

This document describes the standard error response format and all possible error codes used in the Challenge API.

## Standard Error Response Format

All error responses follow a consistent JSON structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

## HTTP Status Codes

### 4xx Client Errors

#### 400 Bad Request
- **Code**: `BAD_REQUEST`
- **Description**: The request could not be understood or contained invalid parameters
- **Example**:
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid request parameters"
  }
}
```

#### 401 Unauthorized
- **Code**: `UNAUTHORIZED`
- **Description**: Authentication is required to access this resource
- **Example**:
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

#### 403 Forbidden
- **Code**: `FORBIDDEN`
- **Description**: The server understood the request but refuses to authorize it
- **Example**:
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to access this resource"
  }
}
```

#### 404 Not Found
- **Code**: `NOT_FOUND`
- **Description**: The requested resource could not be found
- **Example**:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource could not be found"
  }
}
```

#### 405 Method Not Allowed
- **Code**: `METHOD_NOT_ALLOWED`
- **Description**: The HTTP method used is not allowed for this resource
- **Example**:
```json
{
  "error": {
    "code": "METHOD_NOT_ALLOWED",
    "message": "Method not allowed for this endpoint"
  }
}
```

#### 409 Conflict
- **Code**: `CONFLICT`
- **Description**: The request conflicts with the current state of the resource
- **Example**:
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Resource conflict occurred"
  }
}
```

#### 422 Unprocessable Entity
- **Code**: `UNPROCESSABLE_ENTITY`
- **Description**: The request was well-formed but contains semantic errors
- **Example**:
```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Validation failed for the provided data"
  }
}
```

#### 429 Too Many Requests
- **Code**: `TOO_MANY_REQUESTS`
- **Description**: The user has sent too many requests in a given amount of time
- **Example**:
```json
{
  "error": {
    "code": "TOO_MANY_REQUESTS",
    "message": "Rate limit exceeded. Please try again later."
  }
}
```

### 5xx Server Errors

#### 500 Internal Server Error
- **Code**: `INTERNAL_SERVER_ERROR`
- **Description**: An unexpected error occurred on the server
- **Example**:
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again later."
  }
}
```

#### 502 Bad Gateway
- **Code**: `BAD_GATEWAY`
- **Description**: The server received an invalid response from an upstream server
- **Example**:
```json
{
  "error": {
    "code": "BAD_GATEWAY",
    "message": "Bad gateway error occurred"
  }
}
```

#### 503 Service Unavailable
- **Code**: `SERVICE_UNAVAILABLE`
- **Description**: The server is temporarily unable to handle the request
- **Example**:
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Service is temporarily unavailable. Please try again later."
  }
}
```

#### 504 Gateway Timeout
- **Code**: `GATEWAY_TIMEOUT`
- **Description**: The server did not receive a timely response from an upstream server
- **Example**:
```json
{
  "error": {
    "code": "GATEWAY_TIMEOUT",
    "message": "Gateway timeout occurred"
  }
}
```

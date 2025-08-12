## Introduction
This is an API for managing the Challenge object that is Kubernetes Custom Resources(CR).

> [!TIP]  
> For more details about the Challenge resource, please refer to the [Challenge Operator](https://github.com/HexaCTF/challenge-operator) repository.

## Features
- Create, delete, and retrieve detailed information about a Challenge based on user requests.
- (Deprecated) Retrieve Challenge status from the queue and save it to the database.

## Changelog

### API Framework Updated: Flask → FastAPI
We migrated from Flask to FastAPI to enhance code maintainability and improve the development experience.

### Database Framework Updated: Flask-SQLAlchemy → SQLAlchemy 2.0+
We replaced Flask-SQLAlchemy (which was tightly coupled with Flask) with SQLAlchemy 2.0+ to take advantage of modern features and framework independence.

### Kafka Deprecated
We removed the Kafka-based message queue infrastructure, as it introduced unnecessary complexity without sufficient benefits.

## API
|                           Endpoint                            | Method |     Description     |
| :-----------------------------------------------------------: | :----: | :-----------------: |
|        [/v2/user-challenges](./docs/api/user-challenge.md)        |  POST  |   Create Challenge    |
| [/v2/user-challenges/delete](./docs/api/user-challenge-delete.md) |  POST  |   Delete Challenge    |
| [/v2/user-challenges/status](./docs/api/user-challenge-status.md) |  GET   | Get a Challenge |

## 🧪 Experimentation API Service (A/B Testing Platform)

This project is a take-home assessment designed to demonstrate the construction of a simplified **Experimentation API** for basic A/B testing. It implements core functionalities for creating experiments, assigning users to variants, recording events, and retrieving performance results.

### ✨ Features

  * **Experiment Management**: Create new experiments with multiple variants and defined traffic allocations.
  * **Idempotent User Assignment**: Guarantees a user receives the same variant assignment for an experiment persistently.
  * **Configurable Traffic Allocation**: Supports percentage-based traffic distribution across variants.
  * **Event Tracking**: Record detailed user events (e.g., "click", "purchase") with flexible properties.
  * **Performance Reporting**: An extensible endpoint for calculating experiment results, accounting for events only *after* a user's assignment.
  * **Secure API**: All endpoints are protected using **Bearer Token Authentication**.
  * **Containerized Deployment**: Simple setup via `docker-compose`.

-----

## 🛠️ Setup and Running

### Prerequisites

You need **Docker** and **Docker Compose** installed on your system.

### 1\. Build and Run the Containers

Use the provided `docker-compose.yml` file to build the service and the database.

```bash
docker-compose up --build -d
```

This command:

1.  Builds the Python application image.
2.  Starts a **PostgreSQL** database container.
3.  Runs alembic migrations for the application against the postgres database
4.  Starts a PgAdmin container for easy access for inspecting the postgresql database container. Accessible via localhost:5050.
3.  Starts the **API service** container, which connects to the database. 

### 2\. Initial Database Setup

The API service uses a relational database (PostgreSQL in this setup) for persistence. 
The initial setup requires running database migrations and is handled by the `migrate` service in the docker-compose.yml.



### 3\. Access the API

The API service will be accessible at: `http://localhost:8000`.

-----

## 🔑 Authentication

All endpoints require a valid **Bearer Token** in the `Authorization` header.

In this takehome application, tokens are hardcoded in the settings.py file. 

**Example Header:**

```
Authorization: Bearer token
```

For this implementation, the valid tokens are stored internally in the settings.py file

-----

## 🚀 API Endpoints

Below are the documented endpoints, including example usage (using `curl`).

An up to date version of the endpoint documentation can be found at localhost:8000/docs when running the app. 

### 1\. Create a New Experiment

**`POST /experiments`**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `name` | string | A unique name for the experiment. |
| `variants` | list of objects | List of variants with `name` and `traffic_percent`. |

**Example Request:**

```bash
curl --location 'localhost:8000/experiments' \
--header 'Authorization: Bearer token' \
--header 'Content-Type: application/json' \
--data '{
    "name": "experiment2", 
    "description": "test experiment", 
    "status": "DRAFT", 
    "primary_metric_name": "click", 
    "variants": [{"variant_name": "variant1", "traffic_allocation_percent": 50, "configuration_json": {}}, {"variant_name": "variant2", "traffic_allocation_percent": 50, "configuration_json": {}}]
}'
```

**Expected Response:**
```shell

```

-----

### 2\. Get User's Variant Assignment

**`GET /experiments/{id}/assignment/{user_id}`**

Retrieves or creates a persistent variant assignment for a given user in a specified experiment.

| Path Parameter | Type | Description |
| :--- | :--- | :--- |
| `id` | int | The experiment ID. |
| `user_id` | string | The ID of the user (can be a UUID, numeric ID, etc.). |

**Idempotency Check:** Repeated calls for the same `experiment_id` and `user_id` will return the *identical* assignment and assignment time.

**Example Request (Initial Assignment):**

```bash
curl -X GET http://localhost:8000/experiments/1/assignment/user_xyz_123 \
-H "Authorization: Bearer my-secret-auth-token"
```

**Example Response:**

```json
{
    "experiment_id": 1,
    "user_id": "user_xyz_123",
    "variant_name": "V1",
    "assignment_timestamp": "2023-10-23T20:00:00Z"
}
```

-----

### 3\. Record Events/Conversions

**`POST /events`**

Records an event associated with a user, used later for experiment analysis.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `user_id` | string | The user who performed the event. |
| `type` | string | The type of event (e.g., "click", "purchase", "signup"). |
| `timestamp` | datetime | The time the event occurred. |
| `properties` | JSON object | Flexible JSON object for additional context (e.g., purchase value, page URL). |

**Example Request:**

```bash
curl -X POST http://localhost:8000/events \
-H "Authorization: Bearer my-secret-auth-token" \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user_xyz_123",
    "type": "purchase",
    "timestamp": "2023-10-23T20:05:30Z",
    "properties": {
        "value": 49.99,
        "product_sku": "SKU-PRO-001"
    }
}'
```

-----

### 4\. Get Experiment Performance Summary

**`GET /experiments/{id}/results`**

Retrieves a summary of the experiment's performance, comparing the results of all variants.

**Core Logic:** Only events that occurred *after* a user's assignment timestamp are included in the results calculation.

| Path Parameter | Type | Description |
| :--- | :--- | :--- |
| `id` | int | The experiment ID. |

| Query Parameter | Type | Description |
| :--- | :--- | :--- |
| `event_type` | string | **(Required)** The specific event type to analyze (e.g., "purchase", "signup"). |
| `start_date` | datetime | Filter events occurring after this time. |
| `end_date` | datetime | Filter events occurring before this time. |
| `aggregation` | string | Level of aggregation (e.g., "daily", "total"). |

**Design Philosophy (Results Endpoint):**

This endpoint is designed to be **flexible and analytical**, recognizing that different stakeholders need different views:

  * **Real-time Monitoring**: The default response focuses on key metrics (e.g., **conversion rate**, total conversions) for a quick health check.
  * **Deep Analysis**: Query parameters (`start_date`, `end_date`, `aggregation`) allow analysts to slice the data over time or by custom buckets.
  * **Executive Summaries**: The top-level response structure prioritizes easy-to-read comparative metrics (e.g., absolute conversion difference, lift).

**Example Request (Focus on 'purchase' event):**

```bash
curl -X GET 'http://localhost:8000/experiments/1/results' \
-H "Authorization: Bearer token"
```

**Example Response Structure (Conceptual):**

```json
{
    "name": "experiment18",
    "description": "test experiment",
    "start_time": "2025-10-23T22:25:05.548612",
    "end_time": null,
    "experiment_days_running": 0,
    "status": "DRAFT",
    "total_variants": 2,
    "total_events": 8,
    "primary_metric_name": "click",
    "total_users_in_experiment": 3,
    "global_conversion_rate": 0.3333333333333333,
    "variant_stats": {
        "variant1": {
            "total_assigned_users": 0,
            "conversion_rate": 0.0,
            "conversion_count": 0,
            "event_counts": {},
            "metrics": {
                "total_revenue": 0.0
            },
            "traffic_allocation": 30.0
        },
        "variant2": {
            "total_assigned_users": 3,
            "conversion_rate": 0.3333333333333333,
            "conversion_count": 1,
            "event_counts": {
                "click": 7,
                "purchase": 1
            },
            "metrics": {
                "total_revenue": 1000.0
            },
            "traffic_allocation": 70.0
        }
    }
}
```
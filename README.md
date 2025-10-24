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

The database can be accessed using the pgadmin service provisioned by docker-compose. Navigate to localhost:5050 after running `docker-compose up` to access pgadmin. 


### 3\. Access the API

The API service will be accessible at: `http://localhost:8000`.

-----

## 🔑 Authentication

All endpoints require a valid **Bearer Token** in the `Authorization` header.

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

**POST /experiments**


**Example Request:**

```bash
curl --location 'localhost:8000/experiments' \
--header 'Authorization: Bearer token' \
--header 'Content-Type: application/json' \
--data '{
    "name": "experiment18", 
    "description": "test experiment", 
    "status": "RUNNING", 
    "primary_metric_name": "purchase", 
    "variants": [{"variant_name": "variant1", "traffic_allocation_percent": 30, "configuration_json": {}}, {"variant_name": "variant2", "traffic_allocation_percent": 70, "configuration_json": {}}]
}'
```

**Expected Response:**
```josn
{
    "experiment_id": "6fae61db-a90b-4f35-889d-279fa5416fc4",
    "name": "experiment18",
    "description": "test experiment",
    "status": "DRAFT",
    "start_time": "2025-10-23T22:25:05.548612",
    "end_time": null,
    "variants": [
        {
            "variant_id": "d195a1fd-ad1a-4ee8-9a60-b930bad7e060",
            "variant_name": "variant1",
            "traffic_allocation_percent": 30.0
        },
        {
            "variant_id": "233248a1-e150-4239-912f-3f8118668af5",
            "variant_name": "variant2",
            "traffic_allocation_percent": 70.0
        }
    ],
    "primary_metric_name": "click"
}
```

-----

### 2\. Get User's Variant Assignment

**`GET /experiments/{experiment_id}/assignment/{user_id}`**

Retrieves or creates a persistent variant assignment for a given user in a specified experiment.

**Idempotency Check:** Repeated calls for the same `experiment_id` and `user_id` will return the *identical* assignment and assignment time.

**Example Request (Initial Assignment):**

```bash
curl --location 'localhost:8000/experiments/6fae61db-a90b-4f35-889d-279fa5416fc4/assignment/test-user-18' \
--header 'Authorization: Bearer token'
```

**Expected Response:**

```json
{
    "experiment_id": "6fae61db-a90b-4f35-889d-279fa5416fc4",
    "user_id": "test-user-18",
    "variant_id": "d195a1fd-ad1a-4ee8-9a60-b930bad7e060",
    "assignment_timestamp": "2025-10-23T23:12:54.173787"
}
```

-----

### 3\. Record Events/Conversions

**`POST /events`**

Records an event associated with a user, used later for experiment analysis.

**Example Request:**

```bash
curl --location 'localhost:8000/events' \
--header 'Authorization: Bearer token' \
--header 'Content-Type: application/json' \
--data '{
    "user_id": "test-user-2", 
    "type": "purchase", 
    "properties": {"price": 1000.00, "currency": "USD"}, 
    "experiment_id": "6fae61db-a90b-4f35-889d-279fa5416fc4"
}'
```

**Expected Response:**

```json
{
    "event_id": "5d4e0388-64c8-4dfe-8ebd-08b692e55ee3",
    "experiment_id": "6fae61db-a90b-4f35-889d-279fa5416fc4"
}
```

-----

### 4\. Get Experiment Performance Summary

**`GET /experiments/{experiment_id}/results`**

Retrieves a summary of the experiment's performance, comparing the results of all variants.

**Core Logic:** Only events that occurred *after* a user's assignment timestamp are included in the results calculation.

| Path Parameter  | Type   | Description |
|:----------------|:-------| :--- |
| `experiment_id` | string | The experiment ID. |

| Query Parameter | Type   | Description                                                      |
|:----------------|:-------|:-----------------------------------------------------------------|
| `event_type`    | string | The specific event type to analyze (e.g., "purchase", "signup"). |
| `start_date`    | date   | Filter events occurring after this time (e.g. 2025-10-22)        |
| `end_date`      | date   | Filter events occurring before this time (e.g. 2025-10-22)                          |

**Design Philosophy (Results Endpoint):**

This endpoint is designed to be **flexible and analytical**, recognizing that different stakeholders need different views:

  * **Real-time Monitoring**: 
    - The default response focuses on key metrics (e.g., **conversion rate**, total conversions) for a quick health check.
  * **Deep Analysis**: Query parameters (`start_date`, `end_date`, `aggregation`) allow analysts to slice the data over time or by custom buckets.
  * **Executive Summaries**: The top-level response structure prioritizes easy-to-read comparative metrics (e.g., absolute conversion difference, lift).

**Example Request (Focus on 'purchase' event):**

```bash
curl --location 'localhost:8000/experiments/6fae61db-a90b-4f35-889d-279fa5416fc4/results' \
--header 'Authorization: Bearer token'
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

-----

##  Architecture Discussion

Here is a brief overview of the architecture and its core components:

---

### 1. Presentation Layer (FastAPI)

The API is handled entirely by FastAPI, which acts as the front door for all client requests.

* **Security Enforcement:** Authentication is handled by applying the **`require_auth_token` dependency globally**. This ensures that every endpoint is protected by a Bearer Token check before any business logic executes, standardizing the security model across the entire application.
* **Request Validation:** All incoming and outgoing data is validated using **Pydantic models** (`EventCreateModel`, `ExperimentResponseModel`). This ensures data integrity at the system boundaries.
* **Query Handling:** FastAPI automatically maps URL path segments (`experiment_id`), query parameters (`event_type`, `start_date`), and dependencies (`db` session) to the Python function signatures.

---

### 2. Business Logic Layer (Services)

The service layer contains the core logic and coordinates work between the API and the data layer.

* **`ExperimentService`:** Manages the lifecycle of A/B tests. Its key responsibility is the **assignment logic**, where it checks the database for an existing user assignment and, if none exists, determines the variant the user should see (the `_allocate_variant` function).
* **`EventService`:** The primary job here is **data enrichment**. When an event comes in, the service looks up the user's *active assignment* and attaches that context (`experiment_id`, `variant_id`) to the event data *before* saving it.

---

### 3. Data Persistence Layer (Repository and ORM)

This layer handles all direct communication with the relational database (PostgreSQL/SQLAlchemy).

* **Repositories:** Classes like `EventRepository` and `AssignmentRepository` contain SQLAlchemy queries. They are responsible for CRUD operations and advanced filtering (like the `get_events_for_experiment` method).
* **ORM Models:** The **SQLAlchemy ORM** models (`ExperimentORM`, `EventORM`, etc.) define the database schema, handle foreign key relationships, and map database rows to Python objects.
* **Transaction Management:** Repositories enforce transactional integrity by explicitly calling `self.db.commit()` and handling exceptions (`IntegrityError`, `OperationalError`) with immediate **`self.db.rollback()`** calls. This keeps the database session healthy and provides robust error handling.

---

### Core A/B Testing Workflow

The system's core function is realized through the interaction of these layers:

1.  **Assignment:** A request hits `ExperimentService`. It checks the `AssignmentORM` via the repository. If not found, it runs the allocation logic, creates a new `AssignmentORM`, and commits it instantly.
2.  **Event Tracking:** A request hits `EventService`. The service looks up the persistent assignment, attaches the contextual ID, and saves the enhanced event as an `EventORM` record.
3.  **Reporting:** Requests hit the `/results` endpoint, triggering repository methods that join `AssignmentORM` and `EventORM` data to calculate conversion rates and provide analytics.


### Extending the application for production 

1. Have /events endpoint write events to SQS instead of directly to database. Prevents loss of events from errors during processing, allows for batching of writes to database (i.e. pull 10 events from queue and batch insert into db)
2. Utilize a secrets manager for credentials instead of hardcoding them
3. Send all logs to a centralized service like Cloudwatch for observability
4. Utilize connection pooling when interacting with the database. Reduces latency from having to establish a new session connection each request
5. Have postgres database utilize read replicas to decouple read from write traffic. 
6. Deploy application to EKS for automatic scaling, load balancing, health checks, and service discovery.
7. Make the endpoints async instead 

### Improvement to prioritize next

TODO: Add 

### Explanation of /results endpoint 

The result will provide a holistic view of the experiment and then drill down into the specifics of the variants. 


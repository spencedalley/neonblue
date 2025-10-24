#!/bin/bash

RANDOM_UUID=$(uuidgen)

# 1. Execute curl and capture the JSON response into a variable
JSON_RESPONSE=$(curl --location 'localhost:8000/experiments' \
--header 'Authorization: Bearer token' \
--header 'Content-Type: application/json' \
--data '{
    "name": "'"${RANDOM_UUID}"'",
    "description": "test experiment",
    "status": "RUNNING",
    "primary_metric_name": "purchase",
    "variants": [
      {"variant_name": "variant1", "traffic_allocation_percent": 25, "configuration_json": {}},
      {"variant_name": "variant2", "traffic_allocation_percent": 25, "configuration_json": {}},
      {"variant_name": "variant3", "traffic_allocation_percent": 25, "configuration_json": {}},
      {"variant_name": "variant4", "traffic_allocation_percent": 25, "configuration_json": {}}
    ]
}')

# 2. Echo the raw JSON response
echo
echo "$JSON_RESPONSE"
echo

# Extract the experiment_id using string manipulation
EXPERIMENT_ID=$(echo "$JSON_RESPONSE" | \
    grep -o '"experiment_id":"[^"]*"' | \
    cut -d ':' -f 2 | \
    tr -d '"'
)

# Echo the result
echo
echo "\nExtracted Experiment ID: $EXPERIMENT_ID"
echo


# Create 3 assignments for the experiment
EVENT_URL='localhost:8000/events'
AUTH_HEADER="Authorization: Bearer token"
CONTENT_TYPE='Content-Type: application/json'

# Array of user IDs to iterate over
USER_IDS=("user_id1" "user_id2" "user_id3")
EVENT_TYPES=("click" "purchase" "add_to_cart")

# Loop through the array
for user_id in "${USER_IDS[@]}"; do
    # Construct the full URL for the current user ID
    FULL_URL="localhost:8000/experiments/${EXPERIMENT_ID}/assignment/${user_id}"

    echo "--- Calling API for User ID: $user_id ---"

    # Execute the curl command
    curl --location "$FULL_URL" \
         --header "$AUTH_HEADER"

    # Add a newline for clean separation in the output
    echo

    # Loop through the event types for each user
    for event_type in "${EVENT_TYPES[@]}"; do
        echo "--- Sending event: $event_type for $user_id ---"

        # Construct the JSON data, substituting the current event_type
        # We use single quotes around the JSON body to prevent Bash from interpreting
        # the JSON structure, except for the variable which is placed directly.
        JSON_PAYLOAD='{
            "user_id": "'"${user_id}"'",
            "type": "'"${event_type}"'",
            "properties": {"price": 1000.00, "currency": "USD"},
            "experiment_id": "'"${EXPERIMENT_ID}"'"
        }'

        # Execute the curl command
        curl --location "$EVENT_URL" \
             --header "$AUTH_HEADER" \
             --header "$CONTENT_TYPE" \
             --data "$JSON_PAYLOAD"

        echo # Add a newline for clean output separation
    done
done

echo "--- Calling results API for Experiment ID: $EXPERIMENT_ID ---"

RESULTS_URL="localhost:8000/experiments/${EXPERIMENT_ID}/results"
curl --location "$RESULTS_URL" \
     --header "$AUTH_HEADER"



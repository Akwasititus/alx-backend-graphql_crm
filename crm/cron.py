from datetime import datetime
import requests

def log_crm_heartbeat():
    """
    Logs a heartbeat message every 5 minutes to confirm CRM is alive.
    Optionally checks the GraphQL hello field.
    """
    # Prepare log entry
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM is alive"

    # Optional: Verify GraphQL endpoint
    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ hello }"},
            timeout=5
        )
        if response.status_code == 200:
            message += " - GraphQL OK"
        else:
            message += f" - GraphQL ERR ({response.status_code})"
    except Exception as e:
        message += f" - GraphQL ERROR: {e}"

    # Append to log file
    with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
        log_file.write(message + "\n")

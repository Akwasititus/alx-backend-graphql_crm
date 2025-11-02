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


def update_low_stock():
    """
    Runs every 12 hours to trigger the GraphQL mutation
    and log updated products to /tmp/low_stock_updates_log.txt
    """
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_path = "/tmp/low_stock_updates_log.txt"

    mutation = """
    mutation {
        updateLowStockProducts {
            success
            message
            updatedProducts {
                name
                stock
            }
        }
    }
    """

    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": mutation},
            timeout=10
        )
        data = response.json()

        if "data" in data and data["data"]["updateLowStockProducts"]["success"]:
            message = f"[{timestamp}] {data['data']['updateLowStockProducts']['message']}\n"
            for p in data["data"]["updateLowStockProducts"]["updatedProducts"]:
                message += f" - {p['name']}: new stock {p['stock']}\n"
        else:
            message = f"[{timestamp}] Failed to update or no low-stock products.\n"

    except Exception as e:
        message = f"[{timestamp}] ERROR: {e}\n"

    with open(log_path, "a") as f:
        f.write(message + "\n")

        
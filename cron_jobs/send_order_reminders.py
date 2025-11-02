#!/usr/bin/env python3
"""
send_order_reminders.py
Queries GraphQL endpoint for orders placed within the last 7 days
and logs reminders to /tmp/order_reminders_log.txt
"""

from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import sys

# Configure GraphQL transport
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=False,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# Calculate date range for last 7 days
seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

# GraphQL query to get recent orders
query = gql(f"""
query {{
  orders(orderDate_Gte: "{seven_days_ago}") {{
    id
    customer {{
      email
    }}
  }}
}}
""")

try:
    response = client.execute(query)
    orders = response.get("orders", [])

    # Write logs
    with open("/tmp/order_reminders_log.txt", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for order in orders:
            order_id = order.get("id")
            email = order.get("customer", {}).get("email", "N/A")
            log_file.write(f"{timestamp} - Reminder for Order {order_id} ({email})\n")

    print("Order reminders processed!")

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

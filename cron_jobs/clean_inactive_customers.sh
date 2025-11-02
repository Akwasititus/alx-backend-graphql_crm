#!/bin/bash
# Script: clean_inactive_customers.sh
# Purpose: Delete customers with no orders in the past year
# Logs the cleanup activity to /tmp/customer_cleanup_log.txt

# Navigate to the Django project root
cd "$(dirname "$0")/../" || exit

# Run the Django shell command
deleted_count=$(python3 manage.py shell -c "
from datetime import datetime, timedelta
from crm.models import Customer
cutoff_date = datetime.now() - timedelta(days=365)
inactive_customers = Customer.objects.filter(orders__isnull=True, created_at__lt=cutoff_date)
count = inactive_customers.count()
inactive_customers.delete()
print(count)
")

# Log the result with timestamp
echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Deleted \$deleted_count inactive customers\" >> /tmp/customer_cleanup_log.txt

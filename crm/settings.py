CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),  # existing
    ('0 */12 * * *', 'crm.cron.update_low_stock'),  # new job
]

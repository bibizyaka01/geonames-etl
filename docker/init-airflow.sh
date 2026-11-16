#!/usr/bin/env bash
set -euo pipefail

# Only shared runtime volumes need root ownership setup.
mkdir -p /opt/airflow/logs /opt/airflow/data
chown 50000:0 /opt/airflow/logs /opt/airflow/data
chmod 2775 /opt/airflow/logs /opt/airflow/data

# Drop privileges before migrations and user creation. The official entrypoint
# prepares the airflow user environment after switching with runuser.
exec runuser -u airflow -- /entrypoint python /opt/airflow/docker/init-airflow.py

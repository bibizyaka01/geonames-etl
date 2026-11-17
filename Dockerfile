FROM apache/airflow:3.4.0-python3.12

USER airflow

COPY --chown=airflow:root requirements.txt /opt/airflow/requirements.txt
COPY --chown=airflow:root docker/constraints-3.12.txt /opt/airflow/constraints-3.12.txt

# Keep Airflow at the base image version when resolving extra dependencies.
RUN pip install --no-cache-dir \
    "apache-airflow==3.4.0" \
    --constraint /opt/airflow/constraints-3.12.txt \
    --requirement /opt/airflow/requirements.txt \
    && pip check

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False

COPY --chown=airflow:root dags/ /opt/airflow/dags/
COPY --chown=airflow:root src/ /opt/airflow/src/
COPY --chown=airflow:root sql/ /opt/airflow/sql/
COPY --chown=airflow:root docker/init-airflow.sh docker/init-airflow.py /opt/airflow/docker/
COPY --chown=airflow:root docker/check-dags.py /opt/airflow/docker/

ENV PYTHONPATH="/opt/airflow/src"

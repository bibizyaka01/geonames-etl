"""Manual initial load. Re-running replaces the entire geoname dataset."""

from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task


@dag(
    dag_id="geonames_initial",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=1)},
    tags=["geonames", "initial"],
)
def geonames_initial():
    @task(execution_timeout=timedelta(hours=12))
    def load():
        from geonames_etl.initial import load_initial

        return load_initial()

    load()


geonames_initial()

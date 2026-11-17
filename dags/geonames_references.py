"""Daily reload of small GeoNames reference files."""

from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task


@dag(
    dag_id="geonames_references",
    description="GeoNames countries, admin1, feature codes and timezones",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    schedule="@daily",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(seconds=30)},
    max_active_runs=1,
    max_active_tasks=1,
    tags=["geonames", "references"],
)
def geonames_references():
    @task(execution_timeout=timedelta(minutes=10))
    def load(reference: str) -> int:
        from geonames_etl.references import load_reference

        return load_reference(reference)

    country = load.override(task_id="load_country")("country")
    admin1 = load.override(task_id="load_admin1")("admin1")
    features = load.override(task_id="load_feature_code")("feature_code")
    timezones = load.override(task_id="load_timezone")("timezone")
    country >> admin1 >> features >> timezones


geonames_references()

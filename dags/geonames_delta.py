"""Daily publications; manual dates allow ordered recovery of missed days."""

from datetime import datetime, timedelta, timezone

from airflow.sdk import Param, dag, get_current_context, task


@dag(
    dag_id="geonames_delta",
    start_date=datetime(2026, 11, 17, tzinfo=timezone.utc),
    schedule="0 8 * * *",
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    default_args={"retries": 3, "retry_delay": timedelta(minutes=30)},
    params={"change_date": Param("", type="string", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")},
    tags=["geonames", "delta"],
)
def geonames_delta():
    @task(execution_timeout=timedelta(hours=2))
    def load():
        from geonames_etl.delta import load_delta

        context = get_current_context()
        publication = context["params"]["change_date"]
        if not publication:
            publication = (
                context["data_interval_end"].in_timezone("UTC").date() - timedelta(days=1)
            ).isoformat()
        return load_delta(publication)

    load()


geonames_delta()

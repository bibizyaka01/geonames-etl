"""CI smoke check: load exactly the expected DAGs, without network or a DB."""

from airflow.dag_processing.dagbag import DagBag

EXPECTED = {
    "geonames_references": {"load_country", "load_admin1", "load_feature_code", "load_timezone"},
    "geonames_initial": {"load"},
    "geonames_delta": {"load"},
}


def main():
    bag = DagBag("/opt/airflow/dags")
    if bag.import_errors:
        raise RuntimeError(f"DAG import errors: {bag.import_errors}")
    if set(bag.dags) != set(EXPECTED):
        raise RuntimeError(f"Expected DAGs {sorted(EXPECTED)}, found {sorted(bag.dags)}")
    for name, tasks in EXPECTED.items():
        dag = bag.dags[name]
        dag.validate()
        if set(dag.task_ids) != tasks:
            raise RuntimeError(f"Unexpected tasks in {name}: {dag.task_ids}")
        print(f"OK: {name}: {sorted(tasks)}")


if __name__ == "__main__":
    main()

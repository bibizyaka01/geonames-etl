"""Apply consecutive GeoNames publication dates atomically."""

import logging
import os
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
import requests

LOG = logging.getLogger(__name__)


def iter_delta_rows(path, columns):
    with Path(path).open(encoding="utf-8-sig") as source:
        number = 0
        while line := source.readline(1024 * 1024):
            number += 1
            if len(line) >= 1024 * 1024:
                raise ValueError("Delta line exceeds 1 MiB")
            if not line.strip():
                continue
            fields = line.rstrip("\r\n").split("\t", 2 if columns == 3 else -1)
            if len(fields) != columns:
                raise ValueError(f"Delta line {number}: expected {columns} columns")
            yield fields


def download_delta(filename, path):
    size = 0
    with requests.get(
        f"https://download.geonames.org/export/dump/{filename}",
        stream=True, timeout=(15, 120),
    ) as response:
        response.raise_for_status()
        with path.open("wb") as target:
            for chunk in response.iter_content(64 * 1024):
                size += len(chunk)
                if size > 256 * 1024**2:
                    raise ValueError("Delta exceeds 256 MiB")
                target.write(chunk)
    # A valid published file may contain no changes. HTTP 404 is an error.
    LOG.info("Downloaded %s: %s bytes", filename, size)


def apply_delta(connection, publication_date, mode, modifications, deletes):
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext('geonames.geoname'))")
        cursor.execute(
            "SELECT mode, COALESCE(last_delta_date, (loaded_at AT TIME ZONE 'UTC')::date) "
            "FROM core.dataset_state WHERE dataset='geoname' FOR UPDATE"
        )
        state = cursor.fetchone()
        if not state:
            raise ValueError("Run initial load before delta")
        if state[0] != mode or mode not in ("lite", "full"):
            raise ValueError("Mode differs from initial load; reinitialize the dataset")
        previous = state[1]
        if publication_date <= previous:
            return {"status": "already_processed", "publication_date": str(publication_date)}
        if publication_date != previous + timedelta(days=1):
            raise ValueError(f"Missing delta dates: expected {previous + timedelta(days=1)}")
        cursor.execute("TRUNCATE stg.delta_geoname, stg.delta_deletes")
        for table, path, columns in (
            ("delta_geoname", modifications, 19), ("delta_deletes", deletes, 3)
        ):
            with cursor.copy(f"COPY stg.{table} FROM STDIN") as copy:
                for row in iter_delta_rows(path, columns):
                    copy.write_row(row)
        cursor.execute(
            Path(f"/opt/airflow/sql/transformations/delta_{mode}.sql").read_text()
        )
        changed = cursor.rowcount
        cursor.execute(
            "DELETE FROM core.geoname g USING stg.delta_deletes d "
            "WHERE g.geonameid = d.geonameid::bigint"
        )
        removed = cursor.rowcount
        cursor.execute(
            "UPDATE core.dataset_state SET last_delta_date=%s, "
            "row_count=(SELECT count(*) FROM core.geoname) WHERE dataset='geoname'",
            (publication_date,),
        )
    return {"publication_date": str(publication_date), "changed": changed, "deleted": removed}


def load_delta(publication_date):
    from airflow.sdk import Connection

    day = date.fromisoformat(publication_date)
    mode = os.environ.get("GEONAMES_MODE", "lite")
    settings = Connection.get("geonames_dwh")
    directory = Path(os.environ.get("GEONAMES_DATA_DIR", "/opt/airflow/data"))
    directory.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="delta-", dir=directory) as temporary:
        modifications = Path(temporary) / f"modifications-{day}.txt"
        deletes = Path(temporary) / f"deletes-{day}.txt"
        download_delta(modifications.name, modifications)
        download_delta(deletes.name, deletes)
        with psycopg.connect(
            host=settings.host, port=settings.port or 5432, dbname=settings.schema,
            user=settings.login, password=settings.password, connect_timeout=15,
        ) as connection:
            result = apply_delta(connection, day, mode, modifications, deletes)
    LOG.info("Delta result: %s", result)
    return result

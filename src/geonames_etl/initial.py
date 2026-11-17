"""Stream GeoNames ZIP contents into PostgreSQL without extraction to disk."""

import io
import logging
import os
from pathlib import Path
from zipfile import ZipFile

import psycopg
import requests

LOG = logging.getLogger(__name__)
DATASETS = {"lite": "cities15000", "full": "allCountries"}


def iter_geonames(archive, member):
    with ZipFile(archive) as zipped:
        info = zipped.getinfo(member)
        if info.file_size > 20 * 1024**3:
            raise ValueError("Uncompressed dataset exceeds 20 GiB")
        with zipped.open(info) as stream, io.TextIOWrapper(stream, encoding="utf-8") as text:
            number = 0
            while line := text.readline(1024 * 1024):
                number += 1
                if len(line) >= 1024 * 1024:
                    raise ValueError(f"Line {number} exceeds 1 MiB")
                fields = line.rstrip("\r\n").split("\t")
                if len(fields) != 19:
                    raise ValueError(f"Line {number}: expected 19 columns, got {len(fields)}")
                yield fields


def download_archive(name, destination):
    partial = destination.with_suffix(".zip.part")
    size = 0
    with requests.get(
        f"https://download.geonames.org/export/dump/{name}.zip",
        stream=True, timeout=(15, 120),
    ) as response:
        response.raise_for_status()
        with partial.open("wb") as target:
            for chunk in response.iter_content(64 * 1024):
                size += len(chunk)
                if size > 2 * 1024**3:
                    raise ValueError("Archive exceeds 2 GiB")
                target.write(chunk)
    if size == 0:
        raise ValueError("Downloaded an empty archive")
    partial.replace(destination)
    LOG.info("Downloaded %s.zip: %s bytes", name, size)


def replace_dataset(connection, archive, mode):
    name = DATASETS[mode]
    count = 0
    with connection.cursor() as cursor:
        # Future delta loads must acquire the same lock.
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext('geonames.geoname'))")
        for reference in ("country", "admin1", "feature_code", "timezone"):
            cursor.execute(f"SELECT EXISTS (SELECT 1 FROM core.{reference})")
            if not cursor.fetchone()[0]:
                raise ValueError("Load geonames_references before initial load")
        cursor.execute("TRUNCATE stg.geoname")
        with cursor.copy("COPY stg.geoname FROM STDIN") as copy:
            for row in iter_geonames(archive, f"{name}.txt"):
                copy.write_row(row)
                count += 1
        if count == 0:
            raise ValueError("No records; refusing to replace core.geoname")
        cursor.execute(Path("/opt/airflow/sql/transformations/initial_geoname.sql").read_text())
        cursor.execute("SELECT count(*) FROM core.geoname")
        if cursor.fetchone()[0] != count:
            raise ValueError("Staging and core counts differ")
        cursor.execute(
            "INSERT INTO core.dataset_state (dataset, mode, row_count) VALUES ('geoname', %s, %s) "
            "ON CONFLICT (dataset) DO UPDATE SET mode=excluded.mode, "
            "row_count=excluded.row_count, loaded_at=now(), last_delta_date=NULL", (mode, count),
        )
    return count


def load_initial():
    from airflow.sdk import Connection

    mode = os.environ.get("GEONAMES_MODE", "lite")
    if mode not in DATASETS:
        raise ValueError("GEONAMES_MODE must be lite or full")
    directory = Path(os.environ.get("GEONAMES_DATA_DIR", "/opt/airflow/data")) / "initial"
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / f"{DATASETS[mode]}.zip"
    download_archive(DATASETS[mode], archive)
    settings = Connection.get("geonames_dwh")
    with psycopg.connect(
        host=settings.host, port=settings.port or 5432, dbname=settings.schema,
        user=settings.login, password=settings.password, connect_timeout=15,
    ) as connection:
        count = replace_dataset(connection, archive, mode)
    # Commit has succeeded. Retain failed archives for diagnostics/retry.
    archive.unlink()
    LOG.info("Loaded core.geoname: mode=%s rows=%s; archive removed", mode, count)
    return {"mode": mode, "rows": count}

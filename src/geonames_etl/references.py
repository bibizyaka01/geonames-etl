"""Bounded downloads and transactional reloads of GeoNames reference files."""

import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
import requests
from psycopg import sql

SOURCES = {
    "country": ("countryInfo.txt", 19),
    "admin1": ("admin1CodesASCII.txt", 4),
    "feature_code": ("featureCodes_en.txt", 3),
    "timezone": ("timeZones.txt", 5),
}
BASE_URL = "https://download.geonames.org/export/dump/"
MAX_BYTES = 10 * 1024 * 1024
LOG = logging.getLogger(__name__)


def iter_rows(path, reference):
    """Preserve literal quotes, backslashes and empty fields in TSV sources."""
    expected = SOURCES[reference][1]
    with Path(path).open(encoding="utf-8-sig") as source:
        for number, line in enumerate(source, 1):
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.rstrip("\r\n").split("\t")
            if reference == "timezone" and fields[:2] == ["CountryCode", "TimeZoneId"]:
                continue
            if len(fields) != expected:
                raise ValueError(f"{reference}: line {number}: expected {expected} columns, got {len(fields)}")
            yield fields


def download(reference, path):
    filename = SOURCES[reference][0]
    size = 0
    with requests.get(BASE_URL + filename, stream=True, timeout=(15, 60)) as response:
        response.raise_for_status()
        with Path(path).open("wb") as target:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError(f"Reference file exceeds {MAX_BYTES} bytes")
                target.write(chunk)
    if size == 0:
        raise ValueError("Downloaded an empty reference file")
    LOG.info("Downloaded %s: %s bytes", filename, size)


def reload_reference(connection, reference, path):
    """Caller commits the transaction; failures preserve the previous core data."""
    if reference not in SOURCES:
        raise ValueError(f"Unknown reference: {reference}")
    count = 0
    with connection.cursor() as cursor:
        # Serialize manual or concurrent writers of this same reference.
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"geonames.{reference}",))
        cursor.execute(sql.SQL("TRUNCATE {}").format(sql.Identifier("stg", reference)))
        with cursor.copy(sql.SQL("COPY {} FROM STDIN").format(sql.Identifier("stg", reference))) as copy:
            for row in iter_rows(path, reference):
                copy.write_row(row)
                count += 1
        if count == 0:
            raise ValueError(f"No records in {reference}; refusing to replace core")
        statement = (Path("/opt/airflow/sql/transformations") / f"reference_{reference}.sql").read_text()
        cursor.execute(statement)
        cursor.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier("core", reference)))
        if cursor.fetchone()[0] != count:
            raise ValueError(f"Row count mismatch for {reference}")
    return count


def load_reference(reference):
    # Resolve secrets only at task execution, through the Airflow 3 Task SDK.
    from airflow.sdk import Connection

    if reference not in SOURCES:
        raise ValueError(f"Unknown reference: {reference}")
    settings = Connection.get("geonames_dwh")
    directory = Path(os.environ.get("GEONAMES_DATA_DIR", "/opt/airflow/data"))
    directory.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f"ref-{reference}-", dir=directory) as temporary:
        path = Path(temporary) / SOURCES[reference][0]
        download(reference, path)
        with psycopg.connect(
            host=settings.host, port=settings.port or 5432,
            dbname=settings.schema, user=settings.login, password=settings.password,
            connect_timeout=15,
        ) as connection:
            count = reload_reference(connection, reference, path)
    LOG.info("Loaded core.%s: %s rows", reference, count)
    return count

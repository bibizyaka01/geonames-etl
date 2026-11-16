"""Migrate Airflow metadata and create the initial FAB user if missing."""

import json
import os
import subprocess


def main():
    subprocess.run(["airflow", "db", "migrate"], check=True)
    result = subprocess.run(
        ["airflow", "users", "list", "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    username = os.environ["AIRFLOW_ADMIN_USERNAME"]
    users = json.loads(result.stdout)
    if any(user["username"] == username for user in users):
        print("Initial administrator already exists; keeping existing credentials.")
        return

    subprocess.run(
        [
            "airflow", "users", "create",
            "--username", username,
            "--password", os.environ["AIRFLOW_ADMIN_PASSWORD"],
            "--firstname", "Platform",
            "--lastname", "Admin",
            "--role", "Admin",
            "--email", os.environ["AIRFLOW_ADMIN_EMAIL"],
        ],
        check=True,
    )


if __name__ == "__main__":
    main()

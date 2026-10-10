"""Run without pytest: python3 -m unittest discover -s tests -p test_database_safety.py -v"""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from database_safety import (
    TEST_POSTGRES_PORT,
    isolated_postgres_environment,
    local_connection_parameters,
)


class DatabaseEnvironmentSafetyTests(unittest.TestCase):
    def test_hostile_defaults_are_removed_until_cleanup_and_restored(self):
        hostile = {
            "PGHOSTADDR": "192.0.2.1",
            "PGHOST": "unreachable.example.invalid",
            "PGSERVICE": "production",
            "PGSERVICEFILE": "/do-not-read/services",
            "PGSYSCONFDIR": "/do-not-read/system",
            "PGPASSFILE": "/do-not-read/passwords",
            "PGPORT": "5432",
            "PGDATABASE": "existing",
            "PGUSER": "production",
            "PGOPTIONS": "hostile options",
        }
        with patch.dict(os.environ, hostile), tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            directory = Path(temporary)
            with self.assertRaisesRegex(RuntimeError, "synthetic teardown"):
                with isolated_postgres_environment(directory):
                    actual = {key: value for key, value in os.environ.items() if key.startswith("PG")}
                    self.assertEqual(actual, {
                        "PGPASSFILE": str(directory / "client.pgpass"),
                        "PGSERVICEFILE": str(directory / "client.pgservice"),
                        "PGSYSCONFDIR": str(directory),
                    })
                    self.assertEqual((directory / "client.pgpass").read_text(), "")
                    self.assertEqual((directory / "client.pgservice").read_text(), "")
                    self.assertEqual((directory / "client.pgpass").stat().st_mode & 0o777, 0o600)
                    for database in ("postgres", "test_random"):
                        parameters = local_connection_parameters(directory / "s", database)
                        self.assertEqual(parameters, {
                            "host": str(directory / "s"), "hostaddr": "",
                            "port": TEST_POSTGRES_PORT, "user": "jat_test",
                            "dbname": database, "passfile": str(directory / "client.pgpass"),
                        })
                    raise RuntimeError("synthetic teardown")
            for key, value in hostile.items():
                self.assertEqual(os.environ[key], value)


if __name__ == "__main__":
    unittest.main()

from unittest.mock import patch

import pytest

import conftest


def test_failed_shutdown_preserves_cluster_files(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "postmaster.pid").write_text("simulated server")

    with patch.object(
        conftest,
        "_run",
        side_effect=RuntimeError("shutdown failed"),
    ) as mock_run:
        with patch.object(conftest.shutil, "rmtree") as mock_remove:
            with pytest.raises(RuntimeError, match="shutdown failed"):
                conftest._stop_postgres_and_cleanup(
                    "fake-pg-ctl",
                    data,
                    tmp_path,
                    {},
                )

    mock_run.assert_called_once()
    mock_remove.assert_not_called()
    assert (data / "postmaster.pid").exists()


def test_successful_shutdown_removes_cluster_files(tmp_path):
    data = tmp_path / "data"
    data.mkdir()

    with patch.object(conftest, "_run") as mock_run:
        conftest._stop_postgres_and_cleanup(
            "fake-pg-ctl",
            data,
            tmp_path,
            {},
        )

    mock_run.assert_called_once()
    assert not tmp_path.exists()

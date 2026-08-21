"""
Pytest unit tests for MCP DB Server Rollback Manager.
Tests dry-run preview, before-state snapshotting, inverse SQL generation, and rollback execution.
"""

import os
import gc
import uuid
import tempfile
import pytest
from rollback_manager import RollbackManager


@pytest.fixture
def temp_rollback_mgr():
    db_name = f"test_rollback_{uuid.uuid4().hex[:8]}.db"
    mgr = RollbackManager(db_path=db_name)
    yield mgr
    del mgr
    gc.collect()
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
        except PermissionError:
            pass


def test_dry_run_inspection(temp_rollback_mgr):
    sql = "DELETE FROM customers WHERE created_at < '2022-01-01' AND status = 'inactive';"
    inspection = temp_rollback_mgr.inspect_and_dry_run("conn_test", sql)

    assert inspection["operation_type"] == "DELETE"
    assert inspection["target_table"] == "customers"
    assert inspection["risk_level"] == "high"
    assert "estimated_rows" in inspection


def test_snapshot_and_rollback_flow(temp_rollback_mgr):
    conn_id = "conn_mock_test"
    sql = "UPDATE products SET unit_price = unit_price * 1.15 WHERE category = 'Furniture';"

    # 1. Snapshot and Execute
    exec_res = temp_rollback_mgr.snapshot_and_execute(conn_id, sql)
    assert exec_res["success"] is True
    assert "rollback_id" in exec_res
    rollback_id = exec_res["rollback_id"]

    # 2. Check log saved
    logs = temp_rollback_mgr.list_logs(conn_id)
    assert len(logs) == 1
    assert logs[0]["rollback_id"] == rollback_id
    assert logs[0]["status"] == "active"

    # 3. Rollback execution
    rb_res = temp_rollback_mgr.execute_rollback(rollback_id)
    assert rb_res["success"] is True

    # 4. Check status updated
    updated_logs = temp_rollback_mgr.list_logs(conn_id)
    assert updated_logs[0]["status"] == "rolled_back"

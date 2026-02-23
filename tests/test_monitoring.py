"""Tests for BlackRoad 30K Agent Monitoring."""
import os, sys, pytest
from pathlib import Path
from datetime import datetime, timedelta

os.environ["MON_DB"] = "/tmp/test_monitoring.db"
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from monitoring import (
    get_conn, seed_demo, run_health_checks, detect_dead_agents,
    get_performance, get_load_distribution, fire_alert, escalate_alerts,
    get_open_alerts, generate_report, HealthCheck, _now,
)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "mon.db"
    monkeypatch.setenv("MON_DB", str(db))
    import monitoring
    monitoring.DB_PATH = db
    yield


def test_seed_creates_records():
    conn = get_conn(); seed_demo(conn)
    checks = run_health_checks(conn)
    assert len(checks) == 50


def test_detect_dead_agents():
    conn = get_conn(); seed_demo(conn)
    dead = detect_dead_agents(conn)
    assert len(dead) >= 1
    assert all(not d.recovered for d in dead)


def test_health_check_severity():
    h = HealthCheck(check_id="x", agent_id="a", node_id="n", status="dead",
                    heartbeat_age_s=400, response_time_ms=100,
                    cpu_pct=50, mem_pct=50, error_count=0, checked_at=_now())
    assert h.is_dead() is True
    assert h.severity() == "critical"


def test_fire_alert_stores():
    conn = get_conn()
    a = fire_alert(conn, "node-1", "node", "critical", "Test alert", "details")
    open_alerts = get_open_alerts(conn)
    assert any(al.alert_id == a.alert_id for al in open_alerts)


def test_escalate_old_alerts():
    conn = get_conn()
    # Fire an alert backdated 20 minutes
    a = fire_alert(conn, "agent-001", "agent", "critical", "Old alert")
    old_time = (datetime.utcnow() - timedelta(minutes=20)).isoformat(timespec="seconds")
    conn.execute("UPDATE alerts SET fired_at=? WHERE alert_id=?", (old_time, a.alert_id))
    conn.commit()
    escalated = escalate_alerts(conn, age_minutes=15)
    assert any(e.alert_id == a.alert_id for e in escalated)


def test_performance_efficiency_score():
    from monitoring import PerformanceMetric
    m = PerformanceMetric(metric_id="x", agent_id="a", node_id="n",
                          timestamp=_now(), tasks_per_min=10,
                          avg_task_ms=200, p95_task_ms=300, p99_task_ms=500,
                          error_rate_pct=1.0, throughput_kbps=500)
    score = m.efficiency_score()
    assert 0 <= score <= 100


def test_load_distribution_overload():
    from monitoring import LoadDistribution
    d = LoadDistribution(dist_id="x", node_id="n", total_agents=1000,
                         active_agents=950, queued_tasks=100,
                         load_pct=95.0, imbalance_score=20.0, recorded_at=_now())
    assert d.is_overloaded() is True


def test_generate_report_structure():
    conn = get_conn(); seed_demo(conn)
    rep = generate_report(conn)
    assert "healthy" in rep
    assert "dead" in rep
    assert "open_alerts" in rep
    assert rep["total_checked"] == 50

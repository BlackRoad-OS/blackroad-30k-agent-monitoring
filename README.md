# blackroad-30k-agent-monitoring

30K agent monitoring system for the BlackRoad fleet. Health checks, dead-agent detection, performance metrics, load distribution analysis, and alert escalation.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Health checks
python src/monitoring.py health
python src/monitoring.py health --only-problems

# Dead agent detection
python src/monitoring.py dead

# Performance metrics
python src/monitoring.py metrics --node octavia-pi --limit 10

# Load distribution
python src/monitoring.py load

# Alerts
python src/monitoring.py alert
python src/monitoring.py alert --fire critical "Node octavia-pi unresponsive"

# Full monitoring report
python src/monitoring.py report
```

## Architecture

- SQLite multi-table: `health_checks`, `dead_agents`, `performance_metrics`, `load_distribution`, `alerts`
- Dataclasses: `HealthCheck`, `DeadAgent`, `PerformanceMetric`, `LoadDistribution`, `Alert`
- Automatic alert escalation for unacknowledged critical alerts

## Development

```bash
pip install pytest pytest-cov flake8
pytest tests/ -v --cov=src
```

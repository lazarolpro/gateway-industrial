import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gateway", ROOT / "gateway.py")
gateway = importlib.util.module_from_spec(spec)
sys.modules["gateway"] = gateway
spec.loader.exec_module(gateway)


def test_map_loads_with_registers():
    device = gateway.load_registers()
    assert device["device"]
    assert len(device["registers"]) >= 4
    assert all(r.unit for r in device["registers"])


def test_normalize_shape_and_scaling():
    device = gateway.load_registers()
    sim = gateway.SimulatedDevice(device["registers"], seed=1)
    payload = gateway.normalize(device, sim.read_all())
    assert payload["device"] == device["device"]
    assert payload["timestamp"]
    assert len(payload["readings"]) == len(device["registers"])
    for reading in payload["readings"]:
        assert set(reading) == {"tag", "value", "unit", "status"}
        assert reading["status"] in {"ok", "alarma"}


def test_readings_are_reproducible_with_seed():
    device = gateway.load_registers()
    a = gateway.normalize(device, gateway.SimulatedDevice(device["registers"], seed=3).read_all())
    b = gateway.normalize(device, gateway.SimulatedDevice(device["registers"], seed=3).read_all())
    assert json.dumps(a["readings"]) == json.dumps(b["readings"])

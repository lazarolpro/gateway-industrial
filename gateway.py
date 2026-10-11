#!/usr/bin/env python3
"""Gateway de integracion: dispositivo de campo -> API REST normalizada.

Capacidad 2 - Ingenieria de aplicacion / integracion de sistemas.

Simula un dispositivo industrial con un mapa de registros (estilo Modbus),
los lee, aplica escalado y unidades, y los expone como una API REST/JSON con
endpoints de salud y de lecturas. Tambien puede emitir una lectura por consola
para encadenar con otros sistemas.

Uso:
    python gateway.py --once                 # una lectura normalizada en JSON
    python gateway.py --serve --port 8000    # API REST en http://localhost:8000
    python gateway.py --demo                 # imprime una muestra y el mapa

Solo biblioteca estandar de Python 3.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

CONFIG = Path(__file__).parent / "config" / "device_map.json"


@dataclass
class Register:
    name: str
    address: int
    kind: str          # "holding" | "input"
    scale: float
    unit: str
    warn: float | None = None


def load_registers(path: Path = CONFIG) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        "device": raw["device"],
        "protocol": raw.get("protocol", "modbus-tcp-sim"),
        "unit_id": raw.get("unit_id", 1),
        "registers": [Register(**r) for r in raw["registers"]],
    }


class SimulatedDevice:
    """Reemplaza la lectura Modbus real. Devuelve valores crudos (enteros)."""

    def __init__(self, registers: list[Register], seed: int | None = None):
        self._rng = random.Random(seed)
        self._registers = registers
        self._tick = 0

    def read_all(self) -> dict[int, int]:
        self._tick += 1
        out = {}
        for reg in self._registers:
            # Onda lenta + ruido para que el valor sea creible y reproducible.
            base = 1000 if reg.kind == "holding" else 0
            wave = 200 * (1 + (self._tick % 20) / 20)
            noise = self._rng.randint(-5, 5)
            out[reg.address] = int(base + wave + noise)
        return out


def normalize(device: dict, raw: dict[int, int]) -> dict:
    readings = []
    for reg in device["registers"]:
        value = raw.get(reg.address, 0) * reg.scale
        value = round(value, 3)
        status = "ok"
        if reg.warn is not None and value >= reg.warn:
            status = "alarma"
        readings.append({
            "tag": reg.name,
            "value": value,
            "unit": reg.unit,
            "status": status,
        })
    return {
        "device": device["device"],
        "protocol": device["protocol"],
        "unit_id": device["unit_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "readings": readings,
    }


def _handler_factory(device: dict, sim: SimulatedDevice):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 (API de BaseHTTPRequestHandler)
            path = urlparse(self.path).path
            if path == "/health":
                self._send(200, {"status": "up", "device": device["device"]})
            elif path in ("/api/readings", "/"):
                self._send(200, normalize(device, sim.read_all()))
            else:
                self._send(404, {"error": "not found", "path": path})

        def log_message(self, *args) -> None:  # silencio para una salida limpia
            pass

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Gateway de integracion de dispositivo")
    parser.add_argument("--once", action="store_true", help="una lectura normalizada y sale")
    parser.add_argument("--serve", action="store_true", help="levanta la API REST")
    parser.add_argument("--demo", action="store_true", help="muestra el mapa y una lectura")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    device = load_registers()
    sim = SimulatedDevice(device["registers"], seed=args.seed)

    if args.demo:
        print(json.dumps({
            "mapa_dispositivo": {
                "device": device["device"],
                "protocol": device["protocol"],
                "registros": [r.__dict__ for r in device["registers"]],
            },
            "lectura_normalizada": normalize(device, sim.read_all()),
        }, ensure_ascii=False, indent=2))
        return 0

    if args.serve:
        server = HTTPServer(("0.0.0.0", args.port), _handler_factory(device, sim))
        print(f"[ok] API en http://localhost:{args.port}  (GET /health, GET /api/readings)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[ok] servidor detenido")
        return 0

    print(json.dumps(normalize(device, sim.read_all()), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

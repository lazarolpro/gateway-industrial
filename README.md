# Capa 2 — Ingeniería de aplicación / integración de sistemas

[![CI](https://github.com/lazarolpro/gateway-industrial/actions/workflows/ci.yml/badge.svg)](https://github.com/lazarolpro/gateway-industrial/actions/workflows/ci.yml)
[`lazarolpro/gateway-industrial`](https://github.com/lazarolpro/gateway-industrial) · parte del [portafolio de 9 capacidades](https://github.com/lazarolpro/portafolio)

**Capacidad demostrada:** conectar un equipo de campo con un sistema de
información, normalizando los datos y exponiéndolos como una API REST/JSON.

## Problema real

Los equipos industriales hablan protocolos de campo (Modbus, OPC-UA) y los
sistemas de gestión esperan JSON/HTTP. Sin una capa de integración, los datos
quedan aislados o se copian a mano.

## Qué hace

- Define un **mapa de registros** (dirección, tipo, escala, unidad, alarma).
- Simula la lectura del dispositivo (reemplazable por Modbus real).
- Normaliza y escala cada registro a unidades de ingeniería.
- Expone `GET /health` y `GET /api/readings` por HTTP.
- Puede publicar una lectura por consola para encadenar con otros sistemas.

## Cómo ejecutar

```bash
python gateway.py --once                 # una lectura normalizada (JSON)
python gateway.py --serve --port 8000    # API REST
python gateway.py --demo                 # mapa + lectura de ejemplo
python -m pytest -q
```

Prueba la API:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/readings
```

## Evidencia que produce

- `config/device_map.json` — contrato de integración versionado.
- Salida JSON reproducible (`--once` / `--demo`).
- Pruebas de integración en verde.

## Stack

Python 3 (biblioteca estándar: `http.server`). Sin dependencias externas.

## Por qué le importa a la empresa

Cubre la **integración con APIs de terceros y sistemas internos**: el mismo
patrón (leer → escalar → normalizar → exponer) sirve para cualquier equipo.

**En mantenimiento:** permite que un equipo de campo alimente el sistema de gestión
sin copiar datos a mano.

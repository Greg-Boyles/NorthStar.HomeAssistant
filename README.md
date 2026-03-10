# NorthStar Polestar – Home Assistant Integration

A custom Home Assistant integration that connects to the [NorthStar.Api](https://github.com/Greg-Boyles/NorthStar.Api) proxy to bring Polestar vehicle data into Home Assistant.

## Features

### Sensors
- **Battery**: Charge level (%), estimated range, charging power/current/voltage, time to full
- **Odometer & Trips**: Total odometer, trip auto/manual/since-charge distance, average speed, average consumption
- **Climate**: Interior temperature, climate runtime remaining
- **Other**: Software version

### Binary Sensors
- **Charging**: Charging status, charger connected
- **Doors**: Front left/right, rear left/right, hood, tailgate
- **Locks**: Central lock, tailgate lock
- **Windows**: Front left/right, rear left/right, sunroof
- **Other**: Vehicle online status, climate running

### Integration Features
- UI-based configuration via Settings → Devices & Services
- Encrypted credential storage with automatic token renewal
- Configurable polling interval (default 15 minutes)
- **Optional streaming mode** for near real-time updates (60s polling via server-side cache)
- One device per car with all entities grouped together

## Prerequisites

- Home Assistant 2024.1 or later
- A running [NorthStar.Api](https://github.com/Greg-Boyles/NorthStar.Api) instance
- Polestar ID credentials

## Installation

### Manual
1. Copy `custom_components/northstar/` to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration → NorthStar Polestar**
4. Enter your NorthStar API URL and Polestar credentials

### HACS (Custom Repository)
1. In HACS, go to **Integrations → ⋮ → Custom repositories**
2. Add `https://github.com/Greg-Boyles/NorthStar.HomeAssistant` as an **Integration**
3. Install **NorthStar Polestar**
4. Restart Home Assistant
5. Add the integration via **Settings → Devices & Services**

## Configuration

### Initial Setup
| Field | Description | Default |
|-------|-------------|---------|
| API URL | NorthStar.Api base URL | `https://localhost:7261` |
| Email | Polestar ID email | – |
| Password | Polestar ID password | – |
| Enable streaming | Use streaming cache for faster updates | Off |

### Options
| Option | Description | Default |
|--------|-------------|---------|
| Update interval | Polling interval in seconds (when streaming is off) | 900 (15 min) |
| Enable streaming | Use streaming cache for faster updates | Off |

### Streaming Mode

When streaming is enabled:
- The integration polls the NorthStar API's streaming cache endpoint every **60 seconds** (vs 15 minutes)
- NorthStar.Api maintains active gRPC connections to Polestar and caches vehicle data in Redis
- Provides near real-time updates without the overhead of per-poll gRPC streams
- Automatically falls back to snapshot polling if streaming is unavailable
- Uses more API resources — only enable if you need frequent updates

**Note**: Streaming requires NorthStar.Api v1.2+ with Redis streaming cache support.

## Architecture

```
Home Assistant  →  NorthStar.Api  →  Polestar GraphQL / gRPC APIs
   (this)            (.NET 8)          (Polestar cloud)
```

The integration communicates with your NorthStar.Api instance over HTTP. NorthStar.Api handles the complexity of authenticating with Polestar and querying their GraphQL and gRPC services.

## Entities per Vehicle

Each car appears as a **Device** in Home Assistant with ~30 entities:

- 15 sensors (battery, trips, climate, software)
- 17 binary sensors (doors, locks, windows, charging, connectivity)

## Future Enhancements

- Lock/unlock services
- Climate control services (start/stop preheating)
- Charging schedule management
- Lovelace dashboard card

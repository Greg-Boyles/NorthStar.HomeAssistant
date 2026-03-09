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

### Options
| Option | Description | Default |
|--------|-------------|---------|
| Update interval | Polling interval in seconds | 900 (15 min) |

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

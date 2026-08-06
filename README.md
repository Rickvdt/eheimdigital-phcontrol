# EHEIM Digital – pHcontrol+e (custom integration)

A drop-in **fork of Home Assistant's official [`eheimdigital`](https://www.home-assistant.io/integrations/eheimdigital/) integration** that adds support for the **EHEIM pHcontrol+e**, which core does not yet expose.

The heavy lifting already lives in the underlying [`eheimdigital`](https://github.com/autinerd/eheimdigital) Python library (which fully models the pHcontrol+e). Core's integration simply never created entities for it — this fork does.

> [!IMPORTANT]
> This integration uses the domain `eheimdigital`, the **same** as the built-in one. Home Assistant loads a custom component **in preference over the built-in** with the same domain, so installing this **replaces** the core integration. That's intentional: the pHcontrol lives on the same hub as your other EHEIM devices, so there must be exactly one integration owning that connection. All your existing EHEIM devices and their config entry keep working — you just gain pHcontrol entities. HA will log a warning that you're using a custom integration; that's expected.

## What it adds

For each discovered pHcontrol+e device:

| Platform | Entity | Notes |
|---|---|---|
| sensor | pH | current measured pH (`SensorDeviceClass.PH`) |
| sensor | Carbonate hardness | °dH (diagnostic) |
| sensor | Alarm | enum: no alarm / pH too high / pH too low / electrode missing (diagnostic) |
| sensor | Time until electrode service | days (diagnostic) |
| binary_sensor | Dosing valve | valve open/closed (`opening`) |
| binary_sensor | Problem | on when an alarm is active (diagnostic) |
| switch | (main) | control active on/off |
| switch | Acclimatization | config |
| switch | Expert mode | config |
| number | Target pH | 6.0–9.0, step 0.1 |
| number | Hysteresis low / high | config |
| number | Calibration offset | config |
| number | Night pH offset | config (daycycle mode) |
| select | Operation mode | Manual / Bio day-night |
| time | Day start / Night start | config (daycycle mode) |

> [!NOTE]
> **Value ranges/units for the config numbers (hysteresis, offset, night pH offset) are sensible defaults, not confirmed against hardware.** They may need tuning. If a value looks wrong, capture a `PH_DATA` packet (see below) and open an issue — this is the main thing that benefits from testing on a real device.

## Requirements

- Home Assistant **2026.8.0** or newer (forked from that release).
- The `eheimdigital==1.7.1` Python library — installed automatically by Home Assistant.

## Installation (HACS)

1. HACS → three-dot menu → **Custom repositories**.
2. Add this repository's URL, category **Integration**.
3. Install **EHEIM Digital (pHcontrol)** and **restart Home Assistant**.
4. If you already had the EHEIM integration configured, it's picked up automatically. Otherwise add it via **Settings → Devices & services → Add integration → EHEIM Digital** (or it's auto-discovered via zeroconf).

Manual install: copy `custom_components/eheimdigital/` into your HA `config/custom_components/` folder and restart.

## Verifying against your device

Owning the hardware is the fastest way to confirm the fields. Enable debug logging and download diagnostics (**device page → three dots → Download diagnostics**) — the dump includes the raw `ph_data` packet. Use it to confirm the units/scaling of `kH`, `serviceTime`, `offset`, `hystLow/High`, and `nReduce`.

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.eheimdigital: debug
    eheimdigital: debug
```

## Relationship to core & upstreaming

- This fork tracks the **released** core integration (2026.8.0), not `dev`. Core PR [#177948](https://github.com/home-assistant/core/pull/177948) ("Eheimdigital revamp") restructures the coordinator to one-per-message-type; once it lands, the pHcontrol additions should be ported onto that model and submitted upstream (see HA discussion [#3219](https://github.com/orgs/home-assistant/discussions/3219)).
- **When core ships pHcontrol support, uninstall this** and the built-in integration takes over automatically (same domain, same entity unique IDs where possible).

## Not yet included

- **Guided electrode calibration** (the app's pH7 → pH4/pH9 buffer flow). The library exposes a calibration `offset` (surfaced here as a number), but not the full guided state machine. Contributions welcome.

## Credits & license

- Integration code © the Home Assistant project, forked from `home-assistant/core` (Apache-2.0). Original code owner: [@autinerd](https://github.com/autinerd).
- Underlying library: [autinerd/eheimdigital](https://github.com/autinerd/eheimdigital) (MIT).
- This fork is distributed under **Apache-2.0** (see `LICENSE`). Not affiliated with or endorsed by EHIM or the Home Assistant project.

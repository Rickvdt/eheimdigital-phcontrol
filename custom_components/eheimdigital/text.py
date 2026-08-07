"""EHEIM Digital text entities."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, override

from eheimdigital.device import EheimDigitalDevice
from eheimdigital.ph_control import EheimDigitalPHControl

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import EheimDigitalConfigEntry, EheimDigitalUpdateCoordinator
from .entity import EheimDigitalEntity, exception_handler

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class EheimDigitalTextDescription[_DeviceT: EheimDigitalDevice](TextEntityDescription):
    """Class describing EHEIM Digital text entities."""

    value_fn: Callable[[_DeviceT], str | None]
    set_value_fn: Callable[[_DeviceT, str], Awaitable[None]]


async def _set_schedule(device: EheimDigitalPHControl, value: str) -> None:
    """Parse a JSON schedule and send it to the device.

    The schedule is a list of ``[minute_of_day, pH * 10]`` pairs, e.g.
    ``[[450, 74], [1080, 78]]`` (pH 7.4 from 07:30, pH 7.8 from 18:00).
    """
    try:
        schedule = json.loads(value)
    except json.JSONDecodeError as err:
        raise HomeAssistantError(f"Invalid daycycle schedule JSON: {err}") from err
    await device.set_schedule(schedule)


PHCONTROL_DESCRIPTIONS: tuple[
    EheimDigitalTextDescription[EheimDigitalPHControl], ...
] = (
    EheimDigitalTextDescription[EheimDigitalPHControl](
        key="partner_name",
        translation_key="partner_name",
        entity_category=EntityCategory.CONFIG,
        native_max=32,
        value_fn=lambda device: device.partner_name,
        set_value_fn=lambda device, value: device.set_partner_name(value),
    ),
    EheimDigitalTextDescription[EheimDigitalPHControl](
        key="sync",
        translation_key="sync",
        entity_category=EntityCategory.CONFIG,
        native_max=32,
        value_fn=lambda device: device.sync,
        set_value_fn=lambda device, value: device.set_sync(value),
    ),
    EheimDigitalTextDescription[EheimDigitalPHControl](
        key="daycycle_schedule",
        translation_key="daycycle_schedule",
        entity_category=EntityCategory.CONFIG,
        native_max=255,
        value_fn=lambda device: json.dumps(device.schedule),
        set_value_fn=_set_schedule,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EheimDigitalConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up callbacks for the coordinator to add texts as devices are found."""
    coordinator = entry.runtime_data

    def async_setup_device_entities(
        device_address: dict[str, EheimDigitalDevice],
    ) -> None:
        """Set up the text entities for one or multiple devices."""
        entities: list[EheimDigitalText[Any]] = []
        for device in device_address.values():
            if device.is_missing_data:
                continue
            if isinstance(device, EheimDigitalPHControl):
                entities.extend(
                    EheimDigitalText[EheimDigitalPHControl](
                        coordinator, device, description
                    )
                    for description in PHCONTROL_DESCRIPTIONS
                )

        async_add_entities(entities)

    coordinator.add_platform_callback(async_setup_device_entities)
    async_setup_device_entities(coordinator.hub.devices)


class EheimDigitalText[_DeviceT: EheimDigitalDevice](
    EheimDigitalEntity[_DeviceT], TextEntity
):
    """Represent an EHEIM Digital text entity."""

    entity_description: EheimDigitalTextDescription[_DeviceT]

    def __init__(
        self,
        coordinator: EheimDigitalUpdateCoordinator,
        device: _DeviceT,
        description: EheimDigitalTextDescription[_DeviceT],
    ) -> None:
        """Initialize an EHEIM Digital text entity."""
        super().__init__(coordinator, device)
        self.entity_description = description
        self._attr_unique_id = f"{self._device_address}_{description.key}"

    @override
    @exception_handler
    async def async_set_value(self, value: str) -> None:
        """Change the value."""
        await self.entity_description.set_value_fn(self._device, value)

    @override
    def _async_update_attrs(self) -> None:
        self._attr_native_value = self.entity_description.value_fn(self._device)

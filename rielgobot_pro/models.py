import dataclasses
import typing as ty


@dataclasses.dataclass
class Location:
    longitude: float
    latitude: float


@dataclasses.dataclass
class FlatInfo:
    location: ty.Optional[Location] = None
    address: str | None = None
    rooms: int | None = None
    area: float | None = None
    price: str | None = None
    images: list[str] = dataclasses.field(default_factory=list)

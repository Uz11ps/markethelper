from pydantic import BaseModel


class EnumBase(BaseModel):
    code: str
    name: str


class TariffOut(EnumBase):
    id: int

    class Config:
        from_attributes = True


class StatusOut(BaseModel):
    id: int
    type: str
    code: str
    name: str

    class Config:
        from_attributes = True


class DurationOut(BaseModel):
    id: int
    months: int

    class Config:
        from_attributes = True


class AudienceOut(EnumBase):
    id: int

    class Config:
        from_attributes = True


class FileTypeOut(EnumBase):
    id: int

    class Config:
        from_attributes = True


class LevelOut(BaseModel):
    id: int
    code: str
    name: str
    xp_required: int

    class Config:
        from_attributes = True


class ExperienceOut(EnumBase):
    id: int

    class Config:
        from_attributes = True


class PlatformOut(EnumBase):
    id: int

    class Config:
        from_attributes = True


class TrafficSourceOut(EnumBase):
    id: int

    class Config:
        from_attributes = True

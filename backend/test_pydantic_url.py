
from pydantic import BaseModel, HttpUrl, field_validator


class M(BaseModel):
    url: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if not v:
            return v
        # this will raise validation error if invalid
        HttpUrl(v)
        return str(HttpUrl(v))

m = M(url="https://example.com  ")
print(type(m.url))
print(m.model_dump())

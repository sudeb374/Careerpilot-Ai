from pydantic import BaseModel, field_validator, HttpUrl
from typing import Optional

class M(BaseModel):
    url: Optional[str] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        # this will raise validation error if invalid
        HttpUrl(v)
        return str(HttpUrl(v))

m = M(url="https://example.com  ")
print(type(m.url))
print(m.model_dump())

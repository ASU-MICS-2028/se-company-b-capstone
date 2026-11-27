import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

PHONE = re.compile(r"^\+\d{8,15}$")  # E.164


def normalise_phone(value: str) -> str:
    """'+233 20 000-0001' -> '+233200000001'. Spaces, dashes, dots and brackets are ignored."""
    return re.sub(r"[\s\-.()]", "", value)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120, examples=["Ama Mensah"])
    email: EmailStr | None = Field(None, examples=["ama@example.com"])
    phone: str | None = Field(
        None, examples=["+233 20 123 4567"], description="International format; spaces allowed"
    )
    password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("full_name is blank")
        return v.strip()

    @field_validator("email")
    @classmethod
    def _lower_email(cls, v: str | None) -> str | None:
        return v.lower() if v else v

    @field_validator("phone")
    @classmethod
    def _e164(cls, v: str | None) -> str | None:
        if not v:
            return None
        v = normalise_phone(v)
        if not PHONE.match(v):
            raise ValueError("phone must be in international format, e.g. +233201234567")
        return v

    @model_validator(mode="after")
    def _email_or_phone(self):
        if not (self.email or self.phone):
            raise ValueError("email or phone is required")
        return self


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, description="Email or phone", examples=["ama@example.com"])
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr | None
    phone: str | None
    role: str = Field(examples=["driver"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until the token expires")
    user: UserOut

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.modules.auth.models import ROLES  # noqa: F401  (documented in contract)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120, examples=["Ama Mensah"])
    email: EmailStr | None = Field(None, examples=["ama@example.com"])
    phone: str | None = Field(None, pattern=r"^\+\d{8,15}$", examples=["+233201234567"])
    password: str = Field(min_length=8)

    @model_validator(mode="after")
    def _email_or_phone(self):
        if not (self.email or self.phone):
            raise ValueError("email or phone is required")
        return self


class LoginRequest(BaseModel):
    login: str = Field(description="Email or phone", examples=["ama@example.com"])
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
    user: UserOut

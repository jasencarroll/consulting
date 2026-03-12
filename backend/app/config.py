from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    resend_api_key: str = ""
    from_email: str = "Consulting <consulting@jasencarroll.com>"
    contact_email_to: str = "jasen@jasencarroll.com"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

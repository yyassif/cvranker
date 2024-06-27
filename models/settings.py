from logger import get_logger
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = get_logger(__name__)


class ResendSettings(BaseSettings):
    model_config = SettingsConfigDict(validate_default=False)
    resend_api_key: str = "null"

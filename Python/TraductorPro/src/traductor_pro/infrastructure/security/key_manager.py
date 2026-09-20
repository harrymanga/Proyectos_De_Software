import logging
from typing import Optional

from traductor_pro.domain.interfaces import KeyManagerPort

logger = logging.getLogger(__name__)


class KeyringKeyManager(KeyManagerPort):
    SERVICE_NAME = "TraductorPro"

    def get_key(self, service: str) -> Optional[str]:
        try:
            import keyring
            key = keyring.get_password(self.SERVICE_NAME, service)
            return key
        except Exception as e:
            logger.warning("No se pudo obtener key de keyring para %s: %s", service, e)
            return None

    def set_key(self, service: str, api_key: str) -> None:
        try:
            import keyring
            keyring.set_password(self.SERVICE_NAME, service, api_key)
            logger.info("API key guardada para %s", service)
        except Exception as e:
            logger.error("No se pudo guardar key en keyring para %s: %s", service, e)
            raise RuntimeError(f"Error guardando API key: {e}")

    def delete_key(self, service: str) -> None:
        try:
            import keyring
            keyring.delete_password(self.SERVICE_NAME, service)
            logger.info("API key eliminada para %s", service)
        except keyring.errors.PasswordDeleteError:
            logger.warning("No existía key para %s", service)
        except Exception as e:
            logger.error("No se pudo eliminar key de keyring para %s: %s", service, e)

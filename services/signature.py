import hmac
import hashlib
import base64
import time
import json
import logging
from typing import Optional

from config_data.config import Config, load_config


logger = logging.getLogger(__name__)

config: Config = load_config('.env')

SECRET_KEY = config.bot.signature.encode()
USED_SIGNATURES: dict[bytes, int] = {}

def generate_payload(data: dict) -> str:
    assert "action" in data, "Payload must include 'action'"
    data["ts"] = int(time.time())

    payload_json = json.dumps(data, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
    payload_raw = payload_json.encode()

    signature = hmac.new(SECRET_KEY, payload_raw, hashlib.sha256).digest()

    encoded_payload = base64.urlsafe_b64encode(payload_raw).decode()
    encoded_sig = base64.urlsafe_b64encode(signature).decode()

    full = f"{encoded_payload}.{encoded_sig}"

    return f'<span class="tg-spoiler">{data["action"]}:{full}</span>'



def verify_payload(spoiler_text: str, max_uses: int = 1) -> Optional[dict]:
    try:
        action, encoded = spoiler_text.split(":", 1)
        encoded_payload, encoded_sig = encoded.split(".", 1)

        payload_raw = base64.urlsafe_b64decode(encoded_payload.encode())
        sig = base64.urlsafe_b64decode(encoded_sig.encode())

        expected_sig = hmac.new(SECRET_KEY, payload_raw, hashlib.sha256).digest()

        uses = USED_SIGNATURES.get(sig, 0)
        if uses >= max_uses:
            logger.debug(
                "Сигнатура уже использована %s раз(а), лимит исчерпан",
                uses
            )
            return None

        if not hmac.compare_digest(sig, expected_sig):
            logger.debug("Несовпадение сигнатуры, отклоняем данный payload")
            return None

        data = json.loads(payload_raw.decode())
        USED_SIGNATURES[sig] = uses + 1
        return data

    except Exception as e:
        logger.debug("Ошибка при верификации payload'а: %s", e)
        return None



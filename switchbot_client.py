"""
switchbot_client.py
------------------------------------------------------------
SwitchBot API v1.1 への署名付きリクエストを送るクライアント。
------------------------------------------------------------
"""

import base64
import hashlib
import hmac
import time
import uuid

import requests
from pydantic import BaseModel


class SwitchBotResponse(BaseModel):
    ok: bool
    message: str = ""


class SwitchBotClient(BaseModel):
    token: str
    secret: str

    def _headers(self) -> dict:
        t = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4())
        sign_str = self.token + t + nonce
        sign = base64.b64encode(
            hmac.new(
                self.secret.encode("utf-8"),
                msg=sign_str.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode()
        return {
            "Authorization": self.token,
            "sign": sign,
            "t": t,
            "nonce": nonce,
            "Content-Type": "application/json; charset=utf8",
        }

    def list_devices(self) -> dict:
        """登録済みデバイス一覧(deviceId含む)を取得する。詳細は list_devices.py 参照。"""
        resp = requests.get(
            "https://api.switch-bot.com/v1.1/devices",
            headers=self._headers(),
            timeout=10,
        )
        return resp.json()

    def send_command(self, device_id: str, command: str, parameter: str = "default") -> SwitchBotResponse:
        payload = {"command": command, "parameter": parameter, "commandType": "command"}
        try:
            resp = requests.post(
                f"https://api.switch-bot.com/v1.1/devices/{device_id}/commands",
                headers=self._headers(),
                json=payload,
                timeout=10,
            )
            data = resp.json()
            return SwitchBotResponse(ok=data.get("statusCode") == 100, message=data.get("message", ""))
        except Exception as e:  # noqa: BLE001
            return SwitchBotResponse(ok=False, message=str(e))

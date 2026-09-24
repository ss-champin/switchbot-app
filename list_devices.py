"""
list_devices.py
------------------------------------------------------------
SwitchBot API から登録済みデバイス一覧(deviceId 含む)を取得して表示する。

secrets.toml の AIRCON_DEVICE_ID / LIGHT_DEVICE_ID を調べるためのツール。
エアコン・シーリングライトは赤外線リモコンなので「赤外線リモコン」欄に出てくる。

使い方:
    SWITCHBOT_TOKEN=xxx SWITCHBOT_SECRET=yyy uv run python list_devices.py
------------------------------------------------------------
"""

import os
import sys

from switchbot_client import SwitchBotClient


def main() -> None:
    token = os.environ.get("SWITCHBOT_TOKEN")
    secret = os.environ.get("SWITCHBOT_SECRET")
    if not token or not secret:
        print("環境変数 SWITCHBOT_TOKEN / SWITCHBOT_SECRET を設定してください。", file=sys.stderr)
        raise SystemExit(1)

    client = SwitchBotClient(token=token, secret=secret)
    data = client.list_devices()

    if data.get("statusCode") != 100:
        print(f"取得失敗: {data.get('message')}", file=sys.stderr)
        raise SystemExit(1)

    body = data["body"]

    print("=== 物理デバイス (deviceList) ===")
    for d in body.get("deviceList", []):
        print(f"{d.get('deviceName')}\t{d.get('deviceType')}\t{d.get('deviceId')}")

    print("\n=== 赤外線リモコン (infraredRemoteList) ===")
    for d in body.get("infraredRemoteList", []):
        print(f"{d.get('deviceName')}\t{d.get('remoteType')}\t{d.get('deviceId')}")


if __name__ == "__main__":
    main()

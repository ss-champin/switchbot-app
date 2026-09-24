"""
models.py
------------------------------------------------------------
エアコン・ライトの状態や操作履歴を Pydantic モデルとして定義する。
値の範囲(温度16〜30℃、明るさ1〜100など)はモデル側で保証される。
------------------------------------------------------------
"""

from typing import Literal

from pydantic import BaseModel, Field

AirconMode = Literal["冷房", "除湿", "送風", "暖房"]
FanSpeed = Literal["自動", "弱", "中", "強"]

MODE_META: dict[AirconMode, dict] = {
    "冷房": {"emoji": "❄️", "code": 2, "color": "#48cae4"},
    "除湿": {"emoji": "💧", "code": 3, "color": "#90e0ef"},
    "送風": {"emoji": "🌬️", "code": 4, "color": "#caf0f8"},
    "暖房": {"emoji": "🔥", "code": 5, "color": "#ffb703"},
}
FAN_CODE: dict[FanSpeed, int] = {"自動": 1, "弱": 2, "中": 3, "強": 4}


class AirconState(BaseModel):
    power: bool = False
    temp: int = Field(26, ge=16, le=30)
    mode: AirconMode = "冷房"
    fan: FanSpeed = "自動"

    def to_parameter(self) -> str:
        """SwitchBotのsetAllコマンド用パラメータ文字列を組み立てる"""
        power_str = "on" if self.power else "off"
        return f"{self.temp},{MODE_META[self.mode]['code']},{FAN_CODE[self.fan]},{power_str}"

    def label(self) -> str:
        power_str = "on" if self.power else "off"
        return f"{power_str} / {self.temp}℃ / {self.mode} / {self.fan}"


class HistoryEntry(BaseModel):
    time: str
    who: str
    device: str
    detail: str
    ok: bool

    def result_label(self) -> str:
        return "✅ 成功" if self.ok else "❌ 失敗"

    def as_row(self) -> dict:
        return {
            "時刻": self.time,
            "誰が": self.who,
            "デバイス": self.device,
            "内容": self.detail,
            "結果": self.result_label(),
        }

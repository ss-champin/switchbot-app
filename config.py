"""
config.py
------------------------------------------------------------
シークレット情報(.streamlit/secrets.toml)を Pydantic モデルとして
読み込み、型・必須項目をチェックする。
------------------------------------------------------------
"""

import streamlit as st
from pydantic import BaseModel, Field, ValidationError


class Settings(BaseModel):
    switchbot_token: str = Field(..., min_length=1)
    switchbot_secret: str = Field(..., min_length=1)
    aircon_device_id: str = Field(..., min_length=1)
    light_device_id: str = Field(..., min_length=1)
    app_password: str = Field(..., min_length=1)


def load_settings() -> Settings:
    """secrets.toml から設定を読み込む。足りない/不正な場合は画面にエラーを出して停止する。"""
    try:
        return Settings(
            switchbot_token=st.secrets["SWITCHBOT_TOKEN"],
            switchbot_secret=st.secrets["SWITCHBOT_SECRET"],
            aircon_device_id=st.secrets["AIRCON_DEVICE_ID"],
            light_device_id=st.secrets["LIGHT_DEVICE_ID"],
            app_password=st.secrets["APP_PASSWORD"],
        )
    except (KeyError, ValidationError) as e:
        st.error(
            "secrets.toml の設定が足りない、または不正です。\n\n"
            "secrets.toml.example を参考に `.streamlit/secrets.toml` を作成し、"
            "値を入力してください。\n\n"
            f"詳細: {e}"
        )
        st.stop()
        raise SystemExit  # 型チェッカー向け(st.stop()到達後は実行されない)

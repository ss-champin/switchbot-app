"""
おうちリモコン - SwitchBot Streamlit アプリ
------------------------------------------------------------
エアコンとシーリングライトを、楽しく・簡単に遠隔操作するためのアプリ。

シークレットは .streamlit/secrets.toml で管理(config.pyでPydantic検証)。
状態・履歴は models.py の Pydantic モデルで管理。
SwitchBot API呼び出しは switchbot_client.py に分離。

※ 赤外線リモコン(エアコン・ライト)はSwitchBot側から実際の状態を
  取得できないため、画面上の状態は「最後に送信した操作」を表示している。
------------------------------------------------------------
"""

from datetime import datetime

import streamlit as st

from config import load_settings
from models import FAN_CODE, MODE_META, AirconState, HistoryEntry
from switchbot_client import SwitchBotClient

# ------------------------------------------------------------
# 基本設定
# ------------------------------------------------------------
st.set_page_config(page_title="おうちリモコン", page_icon="🏠", layout="centered")

settings = load_settings()
client = SwitchBotClient(token=settings.switchbot_token, secret=settings.switchbot_secret)


# ------------------------------------------------------------
# 見た目(CSS)
# ------------------------------------------------------------
def inject_css(accent: str) -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Zen Maru Gothic', sans-serif;
        }}

        .stApp {{
            background: linear-gradient(160deg, #fdf6ec 0%, #ffffff 55%, {accent}22 100%);
        }}

        .block-container {{
            padding-left: clamp(12px, 4vw, 48px);
            padding-right: clamp(12px, 4vw, 48px);
        }}

        .st-key-aircon_card, .st-key-light_card {{
            background: #ffffff;
            border-radius: 28px;
            padding: clamp(16px, 5vw, 28px) clamp(14px, 4vw, 24px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.06);
            border: 2px solid {accent}55;
            margin-bottom: 20px;
        }}

        .rc-temp {{
            font-size: clamp(40px, 14vw, 64px);
            font-weight: 900;
            text-align: center;
            color: {accent};
            margin: 0;
            word-break: keep-all;
        }}

        .rc-emoji {{
            font-size: clamp(28px, 9vw, 40px);
            text-align: center;
        }}

        .stButton>button {{
            border-radius: 20px;
            height: 3em;
            font-weight: 700;
            font-size: clamp(15px, 4vw, 18px);
            border: none;
            width: 100%;
            white-space: nowrap;
        }}

        div[data-testid="stToggle"] label p {{
            font-size: clamp(15px, 4vw, 18px);
            font-weight: 700;
        }}

        /* 運転モード・風量の横並びラジオがiPhoneなどの狭い画面で
           はみ出さず折り返して表示されるようにする */
        div[role="radiogroup"] {{
            flex-wrap: wrap !important;
            row-gap: 8px;
        }}

        /* タブ見出しが横スクロールでも読みやすいように余白を詰める */
        button[data-baseweb="tab"] {{
            padding-left: clamp(6px, 2vw, 16px);
            padding-right: clamp(6px, 2vw, 16px);
            font-size: clamp(13px, 3.2vw, 16px);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# session_state 初期化
# ------------------------------------------------------------
defaults = {
    "authed": False,
    "your_name": "自分",
    "aircon_power": False,
    "aircon_temp": 26,
    "aircon_mode": "冷房",
    "aircon_fan": "自動",
    "light_power": False,
    "light_brightness": 60,
    "history": [],  # list[HistoryEntry]
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# サーバー再起動やブラウザの再接続直後、ブラウザ側に残っていた古いウィジェットの値が
# まとめて新しいセッションに送られ、複数のon_changeが同時発火してしまうことがある
# (意図しないデバイスへのコマンド送信の原因)。1回のスクリプト実行につき実際に
# コマンドを送信するのは最初の1件だけに制限し、同時発火した残りを捨てて防ぐ。
st.session_state["_command_sent_this_run"] = False


def log_history(device: str, detail: str, ok: bool) -> None:
    entry = HistoryEntry(
        time=datetime.now().strftime("%H:%M:%S"),
        who=st.session_state.your_name,
        device=device,
        detail=detail,
        ok=ok,
    )
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:30]


# ------------------------------------------------------------
# 合言葉ゲート
# ------------------------------------------------------------
def check_password() -> None:
    inject_css("#8ecae6")
    st.markdown("<div class='rc-emoji'>🔐</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>おうちリモコン</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>合言葉を入力してね</p>", unsafe_allow_html=True)
    pw = st.text_input("合言葉", type="password", label_visibility="collapsed")
    if st.button("入る 🚪", key="login_btn", width="stretch"):
        if pw == settings.app_password:
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("合言葉が違うみたい…もう一度確認してね")


if not st.session_state.authed:
    check_password()
    st.stop()


# ------------------------------------------------------------
# コマンド送信ロジック(Pydanticモデルで組み立てて送信)
# ------------------------------------------------------------
def send_aircon_command() -> None:
    state = AirconState(
        power=st.session_state.aircon_power,
        temp=st.session_state.aircon_temp,
        mode=st.session_state.aircon_mode,
        fan=st.session_state.aircon_fan,
    )
    resp = client.send_command(settings.aircon_device_id, "setAll", state.to_parameter())
    log_history("エアコン", state.label(), resp.ok)
    if resp.ok:
        st.toast(f"❄️ エアコンに反映したよ({state.label()})")
        if state.power:
            st.balloons()
    else:
        st.toast(f"⚠️ 送信できなかった: {resp.message}")


def guarded_send_aircon_command() -> None:
    """トグル/ラジオのon_change用。ブラウザ再接続直後などに複数ウィジェットの
    変化が同時に届いてしまった場合の多重送信だけを防ぐ(ボタンのon_clickからは
    経由しないので、まとめてオフなどの意図的な複数送信は妨げない)。"""
    if st.session_state.get("_command_sent_this_run"):
        return
    st.session_state["_command_sent_this_run"] = True
    send_aircon_command()


def dec_temp() -> None:
    st.session_state.aircon_temp = max(16, st.session_state.aircon_temp - 1)
    send_aircon_command()


def inc_temp() -> None:
    st.session_state.aircon_temp = min(30, st.session_state.aircon_temp + 1)
    send_aircon_command()


def send_light_power_command() -> None:
    command = "turnOn" if st.session_state.light_power else "turnOff"
    resp = client.send_command(settings.light_device_id, command)
    label = f"on(明るさ目安{st.session_state.light_brightness})" if st.session_state.light_power else "off"
    log_history("シーリングライト", label, resp.ok)
    if resp.ok:
        st.toast(f"💡 ライトに反映したよ({label})")
    else:
        st.toast(f"⚠️ 送信できなかった: {resp.message}")


def guarded_send_light_power_command() -> None:
    """トグルのon_change用。guarded_send_aircon_commandと同じ理由のガード。"""
    if st.session_state.get("_command_sent_this_run"):
        return
    st.session_state["_command_sent_this_run"] = True
    send_light_power_command()


def step_light_brightness(direction: str) -> None:
    """赤外線リモコンの照明はsetBrightness(数値指定)に対応していないため、
    本体の明るさUP/DOWNボタンを1段階分押す。画面の数値は目安表示。"""
    command = "brightnessUp" if direction == "up" else "brightnessDown"
    resp = client.send_command(settings.light_device_id, command)
    if resp.ok:
        delta = 10 if direction == "up" else -10
        st.session_state.light_brightness = min(100, max(1, st.session_state.light_brightness + delta))
    label = f"明るさ{'up' if direction == 'up' else 'down'}(目安{st.session_state.light_brightness})"
    log_history("シーリングライト", label, resp.ok)
    if resp.ok:
        st.toast(f"💡 明るさを変えたよ({label})")
    else:
        st.toast(f"⚠️ 送信できなかった: {resp.message}")


def turn_all_off() -> None:
    st.session_state.aircon_power = False
    send_aircon_command()
    st.session_state.light_power = False
    send_light_power_command()
    st.toast("🌙 まとめてオフにしたよ")


# ------------------------------------------------------------
# 画面
# ------------------------------------------------------------
current_mode = MODE_META[st.session_state.aircon_mode]
inject_css(current_mode["color"] if st.session_state.aircon_power else "#ffb703")

st.markdown("<h1 style='text-align:center;'>🏠 おうちリモコン</h1>", unsafe_allow_html=True)

st.button(
    "🌙 まとめて電源オフ",
    key="all_off_btn",
    on_click=turn_all_off,
    width="stretch",
    type="primary",
)

with st.sidebar:
    st.markdown("### 👤 あなたのお名前")
    st.session_state.your_name = st.selectbox(
        "操作履歴に記録する名前", ["自分", "同居人"], label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("### 📜 最近の操作")
    if not st.session_state.history:
        st.caption("まだ操作していません")
    for h in st.session_state.history[:8]:
        row = h.as_row()
        st.caption(f"{row['時刻']}｜{row['誰が']}｜{row['デバイス']}｜{row['内容']}｜{row['結果']}")

tab_aircon, tab_light, tab_history = st.tabs(["❄️ エアコン", "💡 ライト", "📜 履歴"])

with tab_aircon:
    with st.container(key="aircon_card"):
        st.toggle(
            f"電源 {'🟢 ON' if st.session_state.aircon_power else '⚪️ OFF'}",
            key="aircon_power",
            on_change=guarded_send_aircon_command,
        )

        st.markdown(f"<div class='rc-emoji'>{current_mode['emoji']}</div>", unsafe_allow_html=True)
        st.markdown(f"<p class='rc-temp'>{st.session_state.aircon_temp}℃</p>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        c1.button("－ 1℃", key="aircon_temp_dec", on_click=dec_temp, width="stretch")
        c2.button("＋ 1℃", key="aircon_temp_inc", on_click=inc_temp, width="stretch")

        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.radio(
            "運転モード",
            options=list(MODE_META.keys()),
            key="aircon_mode",
            horizontal=True,
            on_change=guarded_send_aircon_command,
            format_func=lambda m: f"{MODE_META[m]['emoji']} {m}",
        )
        st.radio(
            "風量",
            options=list(FAN_CODE.keys()),
            key="aircon_fan",
            horizontal=True,
            on_change=guarded_send_aircon_command,
        )

with tab_light:
    with st.container(key="light_card"):
        st.toggle(
            f"電源 {'🟢 ON' if st.session_state.light_power else '⚪️ OFF'}",
            key="light_power",
            on_change=guarded_send_light_power_command,
        )

        glow = "💡" if st.session_state.light_power else "🌑"
        st.markdown(f"<div class='rc-emoji'>{glow}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p class='rc-temp' style='font-size:40px;'>明るさ {st.session_state.light_brightness}</p>",
            unsafe_allow_html=True,
        )
        st.caption("赤外線リモコンのため正確な数値は指定できません。本体の段階を目安表示しています。")

        lc1, lc2 = st.columns(2)
        lc1.button(
            "🔅 暗く",
            key="light_brightness_dec",
            on_click=step_light_brightness,
            args=("down",),
            width="stretch",
        )
        lc2.button(
            "🔆 明るく",
            key="light_brightness_inc",
            on_click=step_light_brightness,
            args=("up",),
            width="stretch",
        )

with tab_history:
    st.markdown("### 📜 操作履歴(最新30件)")
    if st.session_state.history:
        st.dataframe([h.as_row() for h in st.session_state.history], width="stretch", hide_index=True)
    else:
        st.info("まだ何も操作していません。エアコンかライトを動かしてみよう!")

# 🏠 おうちリモコン

SwitchBot API を使って、エアコンとシーリングライトを楽しく・簡単に遠隔操作するための Streamlit アプリ。

## 構成

| ファイル | 役割 |
| --- | --- |
| `app.py` | 画面本体(Streamlit UI・操作ロジック) |
| `config.py` | `.streamlit/secrets.toml` の読み込み・検証(Pydantic) |
| `models.py` | エアコン/ライトの状態・操作履歴のモデル(値の範囲もここで保証) |
| `switchbot_client.py` | SwitchBot API v1.1 への署名付きリクエストクライアント |

赤外線リモコン(エアコン・ライト)は SwitchBot 側から実際の状態を取得できないため、画面上の状態は「最後に送信した操作」を表示しています。

## 必要なもの

- [mise](https://mise.jdx.dev)(Python / uv のバージョン管理)
- [uv](https://docs.astral.sh/uv/)(Python パッケージ管理。`mise install` で自動的に入ります)
- SwitchBot の Token / Secret、操作したいデバイスの deviceId

## セットアップ

```bash
# 1. このディレクトリを信頼し、Python・uv を用意する
mise trust
mise install

# 2. 依存パッケージをインストールする(uv sync)
mise run install

# 3. secrets.toml のひな形を .streamlit/ にコピーする(初回のみ)
mise run secrets:init
```

`.streamlit/secrets.toml` を開き、`secrets.toml.example` を参考に以下の値を入力してください。

```toml
SWITCHBOT_TOKEN = "ここにSwitchBotのTokenを貼り付け"
SWITCHBOT_SECRET = "ここにSwitchBotのSecretを貼り付け"
AIRCON_DEVICE_ID = "ここにエアコンのdeviceIdを貼り付け"
LIGHT_DEVICE_ID = "ここにシーリングライトのdeviceIdを貼り付け"
APP_PASSWORD = "自分と同居人で決めた合言葉"
```

> `.streamlit/secrets.toml` は秘匿情報を含むため、Git 管理下に置く場合は必ず `.gitignore` に追加してください。

### SWITCHBOT_TOKEN / SWITCHBOT_SECRET の取得方法

SwitchBot アプリ →「プロフィール」→「設定」→「アプリバージョン」を連打(10回程度)すると「開発者向けオプション」が現れます。そこで Token・Secret を発行できます。

### AIRCON_DEVICE_ID / LIGHT_DEVICE_ID の調べ方

deviceId は SwitchBot API から取得できます。Token/Secret を発行したら、同梱の `list_devices.py` で一覧表示できます。

```bash
SWITCHBOT_TOKEN=xxx SWITCHBOT_SECRET=yyy mise run devices:list
```

「赤外線リモコン (infraredRemoteList)」欄に、エアコン・シーリングライトとして登録した名前と deviceId が表示されるので、それを `AIRCON_DEVICE_ID` / `LIGHT_DEVICE_ID` に貼り付けてください。

## 起動

```bash
mise run dev
```

`uv sync` → `uv run streamlit run app.py` が実行され、ブラウザでアプリが開きます。起動後、`APP_PASSWORD` に設定した合言葉を入力すると操作画面に入れます。

## 依存パッケージの管理(uv)

このプロジェクトは依存管理に [uv](https://docs.astral.sh/uv/) を使用しています。

```bash
uv add <パッケージ名>       # 依存を追加
uv remove <パッケージ名>    # 依存を削除
uv sync                    # pyproject.toml / uv.lock どおりに環境を再現
uv run <コマンド>           # 仮想環境(.venv)経由でコマンドを実行
```

`pyproject.toml` に依存の定義、`uv.lock` にバージョン固定情報が記録されます。

# Axion Lab - Artifact-first Experiment Evaluation System

成果物（artifact）を中心に実験の評価・比較・再計算を行う実験管理システム。

## 特徴

- **成果物中心**: run の出来栄えを成果物ベースで評価・比較
- **品質指標の後付け**: Run Metric を後から追加・再計算可能
- **階層管理**: Org > Project > Batch > Run の階層構造
- **garbage 運用**: 不要な run を非表示化（復活可能）
- **DP (差分再計算)**: 増分更新・部分推論に対応した効率的な集計

## クイックスタート

### 必要条件

- Python 3.12+
- Docker & Docker Compose (PostgreSQL, MinIO 用)

### セットアップ

1. **リポジトリをクローン**

```bash
git clone <repository-url>
cd axion_lab
```

2. **依存関係のインストール**

```bash
# uv を使用する場合
uv sync

# pip を使用する場合
pip install -e .
```

3. **ミドルウェアの起動**

```bash
docker compose up -d
```

これにより以下が起動します:
- PostgreSQL (port: 5432)
- MinIO (API: 9000, Console: 9001)

4. **環境変数の設定**

```bash
cp .env.example .env
# 必要に応じて .env を編集
```

5. **データベースの初期化**

```bash
axion-lab init-db
```

6. **API サーバーの起動**

```bash
axion-lab server --reload
```

API は http://localhost:8000 で起動します。
OpenAPI ドキュメントは http://localhost:8000/docs で確認できます。

### SQLite を使用する場合 (Docker 不要)

`.env` を以下のように設定:

```env
DATABASE_URL=sqlite+aiosqlite:///./axion_lab.db
DATABASE_TYPE=sqlite
OBJECT_STORE_PROVIDER=local
OBJECT_STORE_LOCAL_PATH=./data/object_store
```

## UI 開発 (Storybook)

Axion Lab の UI コンポーネントは Storybook で開発・確認できます。

### Docker Compose で起動

```bash
# Storybook のみ起動 (port: 6006)
make storybook-dev

# または全サービスと一緒に起動
make start-compose-dev
```

Storybook は http://localhost:6006 でアクセスできます。

### ローカルで起動 (Docker 不要)

```bash
cd axion_lab_ui
pnpm install
pnpm storybook
```

### Storybook のビルド

```bash
# 静的ファイルとしてビルド
make storybook-build

# または直接
cd axion_lab_ui && pnpm build-storybook
```

ビルド成果物は `axion_lab_ui/storybook-static/` に出力されます。

## API 概要

### 管理階層

- `POST /v1/orgs` - Organization 作成
- `POST /v1/orgs/{orgId}/projects` - Project 作成
- `POST /v1/projects/{projectId}/batches` - Batch 作成
- `POST /v1/batches/{batchId}/runs` - Run 作成

### Run 操作

- `GET /v1/batches/{batchId}/runs` - Run 一覧
- `GET /v1/batches/{batchId}/runs/summary` - Run サマリー (Champion/Recent/UserSelected)
- `GET /v1/runs/{runId}` - Run 詳細
- `PATCH /v1/runs/{runId}` - Run 更新 (status, tags 等)

### Artifact

- `POST /v1/runs/{runId}/artifacts` - Artifact 追加
- `GET /v1/runs/{runId}/artifacts` - Artifact 一覧

### Pin

- `POST /v1/runs/{runId}/pins` - Pin 設定 (champion/user_selected)
- `DELETE /v1/runs/{runId}/pins/{pinType}` - Pin 解除

### Run Metrics & Comparison Indicators

- `GET /v1/runs/{runId}/run-metrics` - Run Metric 一覧
- `GET /v1/runs/{runId}/comparison-indicators` - CI 一覧

### DP ジョブ

- `POST /v1/batches/{batchId}/dp/compute` - DP 計算トリガー
- `GET /v1/dp/jobs/{jobId}` - ジョブ状態取得

## 使用例

### 1. 組織・プロジェクト・バッチの作成

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000/v1")

# Org 作成
org = client.post("/orgs", json={"name": "MyOrg"}).json()

# Project 作成
project = client.post(
    f"/orgs/{org['orgId']}/projects",
    json={"name": "ImageClassification"}
).json()

# Batch 作成
batch = client.post(
    f"/projects/{project['projectId']}/batches",
    json={"name": "experiment-2026-02"}
).json()
```

### 2. Run と Artifact の登録

```python
# Run 作成
run = client.post(
    f"/batches/{batch['batchId']}/runs",
    json={
        "name": "resnet50-v2",
        "status": "active",
        "tags": ["resnet", "pretrained"]
    }
).json()

# 評価結果を Artifact として追加
client.post(
    f"/runs/{run['runId']}/artifacts",
    json={
        "kind": "inline_json",
        "type": "evaluation",
        "label": "case_scores",
        "payload": {
            "schema": "case_score_v1",
            "cases": [
                {"case_id": "img001", "score": 0.95},
                {"case_id": "img002", "score": 0.87},
                {"case_id": "img003", "score": 0.92}
            ]
        }
    }
)

# レイテンシを Artifact として追加
client.post(
    f"/runs/{run['runId']}/artifacts",
    json={
        "kind": "inline_number",
        "type": "latency_p95_ms",
        "label": "p95",
        "payload": 312
    }
)
```

### 3. DP 計算の実行

```python
# DP ジョブをトリガー
job = client.post(
    f"/batches/{batch['batchId']}/dp/compute",
    json={"mode": "active_only", "recompute": True}
).json()

# 結果を確認
qm = client.get(f"/runs/{run['runId']}/run-metrics").json()
print(qm)  # mean_case_score, median_case_score, failure_rate など
```

## プロジェクト構造

```
axion_lab/src/axion_lab/
├── api/                  # FastAPI ルーター
│   ├── app.py           # アプリケーションファクトリ
│   ├── deps.py          # 依存性注入
│   └── routers/         # 各エンドポイント
├── dp/                   # DP Runner
│   └── runner.py        # Embedded DP Runner
├── models/               # SQLAlchemy モデル
│   └── entities.py      # エンティティ定義
├── repositories/         # データアクセス層
├── schemas/              # Pydantic スキーマ
├── storage/              # Object Storage Adapter
│   ├── base.py          # インタフェース
│   ├── local.py         # Local FS 実装
│   └── s3.py            # S3/MinIO 実装
├── config.py            # 設定
├── database.py          # DB 接続管理
└── cli.py               # CLI エントリポイント
```

## ライセンス

MIT License

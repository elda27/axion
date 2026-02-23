# Axion Lab Examples

Axion Lab SDK (`axion_lab.AxionLabClient`) の使い方を示すサンプルスクリプト集です。

## 前提条件

- Axion Lab サーバーが起動していること（デフォルト: `http://localhost:8000`）
- Python 3.12+

```bash
# サーバー起動 (Docker Compose)
docker compose -f compose.yaml -f compose.dev.yaml up -d

# または直接起動
uv run axion-lab server --reload
```

## SDK の使い方

```python
from axion_lab import AxionLabClient

client = AxionLabClient()  # http://localhost:8000

org = client.orgs.create("My Org")
project = client.projects.create(org.org_id, "My Project")
batch = client.batches.create(project.project_id, "Batch-1")
run = client.runs.create(batch.batch_id, "run-v1", tags=["gpt-4o"])
artifact = client.artifacts.create(
    run.run_id, kind="inline_number", type="evaluation",
    label="score", payload=0.95,
)
```

すべてのレスポンスは Pydantic モデル（`OrgResponse`, `RunResponse` 等）として返されます。

## Examples

### 1. `quickstart.py` — クイックスタート

Org → Project → Batch → Run → Artifact の基本フローを一通り実行します。

```bash
uv run python examples/quickstart.py
```

### 2. `evaluation_workflow.py` — 評価ワークフロー

複数の Run を作成し、スコア Artifact を登録した後、DP（差分再計算）ジョブを実行して品質指標 (Quality Metric) と比較指標 (Comparison Indicator) を自動算出するフローを示します。

```bash
uv run python examples/evaluation_workflow.py
```

### 3. `champion_comparison.py` — チャンピオン比較

チャンピオン Run を設定し、新しい Run と比較するユースケースを示します。Pin の操作や RunSummary の取得を含みます。

```bash
uv run python examples/champion_comparison.py
```

## 環境変数

| 変数名           | デフォルト値            | 説明                   |
| ---------------- | ----------------------- | ---------------------- |
| `AXION_LAB_BASE_URL` | `http://localhost:8000` | Axion Lab API のベース URL |

```bash
AXION_LAB_BASE_URL=http://localhost:8000 uv run python examples/quickstart.py
```

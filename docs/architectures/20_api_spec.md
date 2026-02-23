# API仕様（v0.1）

## ルーティング方針

- 階層：`/orgs/{orgId}/projects/{projectId}/batches/{batchId}/runs`
- 参照頻度が高いものは runId 直指定も用意する（詳細/更新系）

---

## Org / Project / Batch

### Org

| Method | Endpoint                  | 説明 |
| ------ | ------------------------- | ---- |
| POST   | `/v1/orgs`                | 作成 |
| GET    | `/v1/orgs?limit=&cursor=` | 一覧 |
| GET    | `/v1/orgs/{orgId}`        | 詳細 |

### Project

| Method | Endpoint                                   | 説明 |
| ------ | ------------------------------------------ | ---- |
| POST   | `/v1/orgs/{orgId}/projects`                | 作成 |
| GET    | `/v1/orgs/{orgId}/projects?limit=&cursor=` | 一覧 |
| GET    | `/v1/projects/{projectId}`                 | 詳細 |

### Batch

| Method | Endpoint                                          | 説明 |
| ------ | ------------------------------------------------- | ---- |
| POST   | `/v1/projects/{projectId}/batches`                | 作成 |
| GET    | `/v1/projects/{projectId}/batches?limit=&cursor=` | 一覧 |
| GET    | `/v1/batches/{batchId}`                           | 詳細 |

### Aggregation（集計グループ）

Batch と並列する概念。Batch 内や Batch 間を超えて、メタデータに基づいて Run を集計するための仕組み。
主なユースケース:
- ML 時系列（epoch）× 手法の Loss/metric 比較
- LLM モデル × agent 実装バージョンを横断した比較

| Method | Endpoint                                                      | 説明                |
| ------ | ------------------------------------------------------------- | ------------------- |
| POST   | `/v1/projects/{projectId}/aggregations`                       | 作成                |
| GET    | `/v1/projects/{projectId}/aggregations?limit=&cursor=`        | 一覧                |
| GET    | `/v1/aggregations/{aggregationId}`                            | 詳細                |
| DELETE | `/v1/aggregations/{aggregationId}`                            | 削除                |
| POST   | `/v1/aggregations/{aggregationId}/members`                    | メンバー（Run）追加 |
| GET    | `/v1/aggregations/{aggregationId}/members?limit=&cursor=`     | メンバー一覧        |
| DELETE | `/v1/aggregations/{aggregationId}/members/{runId}`            | メンバー削除        |
| GET    | `/v1/aggregations/{aggregationId}/quality-metrics?key=`       | 集計内 QM 一覧      |
| GET    | `/v1/aggregations/{aggregationId}/comparison-indicators?key=` | 集計内 CI 一覧      |

> v0.1では CRUD のうち 作成＋一覧＋詳細があれば十分（削除は後回しでOK）

---

## Run

### 作成

```
POST /v1/batches/{batchId}/runs
```

**Request**
```json
{
  "name": "reranker-v2-sweep-001",
  "status": "active",
  "tags": ["candidate", "reranker"],
  "note": "optional short text"
}
```

**Response**
```json
{
  "runId": "run_01H...",
  "createdAt": "2026-02-03T..."
}
```

### 一覧（通常）

```
GET /v1/batches/{batchId}/runs?status=&tag=&q=&limit=&cursor=
```

- 既定動作：`status!=garbage`（ただし `include_garbage=true` で上書き可）
- `q`：run名 / tag / artifact.label への部分一致（v0.1はrun名+tagだけでも可）

### サマリー（Champion / Recent3 / User Selected / Others）

```
GET /v1/batches/{batchId}/runs/summary?include_garbage=false
```

**Response**
```json
{
  "champion": {
    "runId": "run_c",
    "name": "champion-2026-02-01"
  },
  "recentCollapsed": {
    "defaultOpen": false,
    "runs": [
      { "runId": "run_r3", "name": "latest-3" },
      { "runId": "run_r2", "name": "latest-2" },
      { "runId": "run_r1", "name": "latest-1" }
    ]
  },
  "userSelected": [
    { "runId": "run_u1", "name": "ablation-A" }
  ],
  "others": {
    "cursor": "cur_...",
    "runs": [{ "runId": "run_o1", "name": "..." }]
  }
}
```

### 詳細 / 更新

| Method | Endpoint           | 説明                 |
| ------ | ------------------ | -------------------- |
| GET    | `/v1/runs/{runId}` | 詳細取得             |
| PATCH  | `/v1/runs/{runId}` | name/status/tags更新 |

**PATCH Request**
```json
{
  "status": "garbage",
  "tags": ["garbage", "tmp"]
}
```

---

## Pin（Champion / User Selected）

### 設定

```
POST /v1/runs/{runId}/pins
```

**Request（champion）**
```json
{
  "pinType": "champion"
}
```

**Request（user_selected）**
```json
{
  "pinType": "user_selected"
}
```

### 解除

```
DELETE /v1/runs/{runId}/pins/{pinType}
```

### 制約（仕様として固定）

- `champion` は batch内で最大1件
- `user_selected` は複数可
- championを付け替える場合は upsert（既存champion解除→新champion）

---

## Artifact（Signal受け口を兼ねる）

### 追加

```
POST /v1/runs/{runId}/artifacts
```

**Request（URL）**
```json
{
  "kind": "url",
  "type": "langfuse_trace",
  "label": "trace",
  "payload": "https://<langfuse>/trace/abc",
  "meta": { "trace_id": "abc" }
}
```

**Request（Local path）**
```json
{
  "kind": "local",
  "type": "file",
  "label": "local-eval-json",
  "payload": "./outputs/eval.json",
  "meta": { "base": "repo_root" }
}
```

**Request（Inline JSON：評価結果など）**
```json
{
  "kind": "inline_json",
  "type": "evaluation",
  "label": "case_scores",
  "payload": {
    "cases": [
      {"id": "c1", "score": 0.9}
    ]
  },
  "meta": { "schema": "case_score_v1" }
}
```

### 一覧 / 削除

| Method | Endpoint                     | 説明 |
| ------ | ---------------------------- | ---- |
| GET    | `/v1/runs/{runId}/artifacts` | 一覧 |
| DELETE | `/v1/artifacts/{artifactId}` | 削除 |

---

## Quality Metric（QM）/ DerivedMetric（QMの一種）

> **重要**: QMとCIは絶対に混ぜない（APIも分ける）

| Method | Endpoint                                                    | 説明              |
| ------ | ----------------------------------------------------------- | ----------------- |
| GET    | `/v1/runs/{runId}/quality-metrics`                          | Run単位           |
| GET    | `/v1/batches/{batchId}/quality-metrics?key=&limit=&cursor=` | Batch単位（任意） |

**返却例**
```json
[
  {
    "key": "f1_macro",
    "value": 0.913,
    "source": "derived",
    "computedAt": "..."
  },
  {
    "key": "latency_p95_ms",
    "value": 320,
    "source": "raw",
    "computedAt": "..."
  }
]
```

---

## Comparison Indicator（CI）

| Method | Endpoint                                                          | 説明              |
| ------ | ----------------------------------------------------------------- | ----------------- |
| GET    | `/v1/runs/{runId}/comparison-indicators`                          | Run単位           |
| GET    | `/v1/batches/{batchId}/comparison-indicators?key=&limit=&cursor=` | Batch単位（任意） |

**返却例**
```json
[
  {
    "key": "delta_vs_champion_f1_macro",
    "value": 0.012,
    "baselineRef": "run_c",
    "computedAt": "..."
  },
  {
    "key": "rank_overall",
    "value": 2,
    "computedAt": "..."
  }
]
```

---

## DPトリガー（外部→内蔵Runner実行）

### 起動

```
POST /v1/batches/{batchId}/dp/compute
```

**Request**
```json
{
  "mode": "active_only",
  "recompute": true
}
```

**Response**
```json
{
  "jobId": "job_01H...",
  "status": "queued"
}
```

### 状態取得

```
GET /v1/dp/jobs/{jobId}
```

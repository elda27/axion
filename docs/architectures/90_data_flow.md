# データフローとシーケンス図

## Artifact挿入（pytest/CI側）

```mermaid
sequenceDiagram
  autonumber
  participant X as pytest/CI/CLI
  participant API as Registry API
  participant DB as Metadata DB

  X->>API: POST /orgs/{org}/projects/{proj}/batches/{batch}/runs
  API->>DB: INSERT Run
  DB-->>API: ok(run_id)
  API-->>X: 201 Created(run_id)

  X->>API: POST /runs/{run_id}/artifacts (url/local/inline*)
  API->>DB: INSERT Artifacts (as Signal receptacle)
  DB-->>API: ok
  API-->>X: 200 OK

  X->>API: POST /runs/{run_id}/pins (champion/user_selected) [optional]
  API->>DB: UPSERT Pin
  API-->>X: 200 OK
```

---

## DPトリガー（外部から叩くが、計算は内蔵Runner）

```mermaid
sequenceDiagram
  autonumber
  participant X as pytest/CI/CLI or UI
  participant API as Registry API
  participant EDP as Embedded DP Runner
  participant DB as Metadata DB
  participant OS as Object Storage (optional)

  X->>API: POST /dp/compute (scope=batch, mode=active_only)
  API->>EDP: enqueue/execute compute(batch_id)

  EDP->>DB: SELECT Runs (active only, exclude garbage)
  EDP->>DB: SELECT Artifacts (inputs)
  alt large payload needed
    EDP->>OS: GET big eval payload by artifact reference
    OS-->>EDP: payload
  end

  EDP->>EDP: Compute QualityMetrics (QM)
  Note right of EDP: includes DerivedMetric (source=derived)<br/>case-level DP full scan
  EDP->>EDP: Compute ComparisonIndicators (CI)
  Note right of EDP: vs champion/user-selected<br/>rank/Δ/win-rate etc.

  EDP->>DB: UPSERT quality_metrics
  EDP->>DB: UPSERT comparison_indicators
  DB-->>EDP: ok
  EDP-->>API: done(job_id/status)
  API-->>X: 202 Accepted(job_id) or 200 OK
```

---

## UIの「Champion / Recent(3) / User Selected」配置

```mermaid
flowchart LR
  A["Champion (pinned)"] --> B["Recent (collapsed)\nshows latest 3 when expanded"]
  B --> C["User Selected (pinned list)"]
  C --> D["Others (paginated)"]
```

### UIに直結する「固定＋折りたたみ」設計

**要件：**
- **固定枠：** Champion、User Selected
- **折りたたみ枠：** ChampionとUser Selectedの "間" に Recent（直近3）

**Recent の条件：**
- `status=active` かつ（pinでない）
- 直近 `created_at` 上位3（などルール化）

**表示の基本：**
- **QM：** 常に見せる（主表示）
- **CI：** 補助（比較のときに見せる、または小さく表示）

---

## 外部参照（Langfuse等）の扱い

- Registry は Langfuseのデータを持たない（必要なら "参照情報" だけArtifactに保存）
- DP Runner が必要に応じて Langfuse API を読むのはあり（ただし認証/レートが課題なので v0.1 は "URL + trace_id を保存" が無難）

```mermaid
flowchart TB
  subgraph Registry["Experiment Registry"]
    API["Registry API"]
    DB["Metadata DB"]
  end

  subgraph External["External Systems"]
    LF["Langfuse"]
    OS["Object Storage"]
  end

  API -.->|"Store reference only<br/>(url + trace_id)"| LF
  API <-->|"Store/Fetch payloads"| OS

  Note["Langfuse is NOT integrated.<br/>Registry stores references only."]
```

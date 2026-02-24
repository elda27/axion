# 運用設計（Ops / Lifecycle / Recovery）

## 運用の目的

- 実験が増え続けても UIとDBが破綻しない
- DP（case-level全数計算）を必要なときに確実に回せる
- 失敗したときに原因追跡・再実行が容易
- Object Storage を切り替えても参照が壊れにくい

---

## 役割分担（実行主体）

### 外部実行（CI / pytest / 手元CLI）

やることは**登録とトリガーだけ**。

- Run作成
- Artifact追加（評価結果・参照・小さい値）
- pin（champion/user_selected）設定（必要なら）
- DPトリガー（`POST /dp/compute`）
- テスト（pytestでQM/CIをassert）

### サービス内実行（Embedded DP Runner）

- DPジョブ実行
- QM/CIの書き込み
- ジョブ状態の更新（queued/running/succeeded/failed）

> **スケジュール（定期実行）はCI側で良い**  
> **実行器はサービス内に必須**

---

## 通常運用フロー

### フローA：開発（ローカル）

1. SQLiteで起動
2. 手元CLI/pytestで Run + Artifact を登録
3. `POST /dp/compute` でDP回す
4. UIで確認 or APIでQM/CI取得

### フローB：CI（Pull Request）

1. 評価テスト実行（pytest）
2. 生成された評価結果を Artifact として登録
3. DPトリガー
4. QM/CIを取得して期待値検証（回帰テスト）
5. PRに結果をコメント（任意）

### フローC：本番/共有環境（main branch）

1. mainにマージ
2. nightly（GitHub Actions schedule）で
   - "直近N batch" など対象を絞って DPトリガー
3. UIでChampion/Recent/UserSelectedを見て意思決定

---

## DPジョブ運用

### 同一batchの同時実行ポリシー

- 同一batchで `running` がある場合：
  - 後続は `queued` に積む（直列化）
- キャンセル（v0.1任意）：
  - queuedのみキャンセル可にしても良い

### 再実行（recompute）

`recompute=true`：QM/CIを再計算し、最新上書き（v0.1）

何が変わるか：
- Artifactが追加された
- championが変わった
- DPロジックのversionが上がった

> v0.2で version を活かして履歴保持  
> v0.1は "最新のみ保持" で運用を軽くする

### 冪等性（重要）

DP Runner は：
- 入力（Artifact集合 + champion/user_selected状態 + DP version）が同じなら
- 出力（QM/CI）が同じになる

→ `dp_jobs` に `input_fingerprint`（hash）を入れるのが理想（v0.2）  
→ v0.1では job単位のログだけでも可

---

## garbage運用（増殖前提のライフサイクル）

### ルール

- 既定表示から除外
- 既定DP対象から除外
- ただし**復活可能**（activeへ戻す）
- "無限に増える" ので、古いgarbageはアーカイブ対象

### 実装する運用コマンド（API）

```
PATCH /runs/{runId} { "status": "garbage" }
PATCH /runs/{runId} { "status": "active" }  # 復活
POST /batches/{batchId}/dp/compute { "mode": "active_only" }  # 既定
```

### 削除はしない（v0.1）

- 完全削除は事故りやすい
- まずは `archived` で退避していく

---

## アーカイブ運用（DB負荷を抑える）

### アーカイブの対象

基本ルール（推奨）：
- `status=garbage AND pinnedでない AND 最終更新がX日より古い`
- または "runs件数が閾値超過" で古い順に

### アーカイブ方式（2段階）

#### Stage 1（v0.1推奨：軽い）

- DBから消さない
- ただし UIの既定一覧に出さない（`status=archived`）
- 大きいpayloadはObject Storageへ移す（Artifact参照へ置換）

#### Stage 2（v0.2以降：本格）

- DBの詳細（巨大Artifact/Signals）を削り
- `archive_manifest.json` をObject Storageへ退避
- DBには "インデックス用の薄い要約" のみ保持

### archive manifest（例）

Object Storageに保存（プロバイダ差し替え可）：

```json
{
  "orgId": "org1",
  "projectId": "p1",
  "batchId": "b1",
  "runId": "r1",
  "archivedAt": "2026-02-03T12:00:00Z",
  "artifacts": [...],
  "runMetrics": [...],
  "comparisonIndicators": [...],
  "notes": "optional"
}
```

---

## Object Storage運用（差し替え前提）

### "参照の壊れにくさ" のためのルール

Artifactに 生URL（`s3://…`）だけ を入れるとプロバイダ移行に弱いので、推奨は：

| フィールド | 内容                                         |
| ---------- | -------------------------------------------- |
| `payload`  | logical_key（例：`org1/p1/b1/r1/eval.json`） |
| `meta`     | `provider`, `bucket`, `region` など          |

### プロバイダ切替の運用手順（例）

1. 新ストアにデータコピー
2. `OBJECT_STORE_PROVIDER` を切替
3. presign URLなどを新ストアから生成
4. 古いストアをread-only化して段階的に廃止

---

## 障害・失敗時の運用（Recovery）

### DPジョブ失敗

`GET /dp/jobs/{jobId}` の `error_text` を見て判断

| 原因                                               | 対応                                                                       |
| -------------------------------------------------- | -------------------------------------------------------------------------- |
| 入力Artifactが壊れている（schema不一致、JSON不正） | Artifactを差し替え → recompute                                             |
| 外部参照（Langfuse等）が取れない                   | v0.1：CI/QMのうち外部依存部分のみ null でも成功扱いにする設計が安全        |
| OutOfMemory / 時間超過                             | 入力をObject Storageに置いてストリーミング処理（v0.2）またはcase対象を絞る |

### DB障害

- PostgreSQLダウン時は書き込み不可
- `dp_jobs` の `queued` が溜まるだけにする（実行しない）

### 参照切れ（Artifact URL 404）

- URL直参照の場合は起きる
- logical_key運用を推奨

---

## 監査ログ（最低限）

v0.1で最低限残すべきイベント：

- status変更（active/garbage/archived）
- pin変更（champion/user_selected）
- DPジョブ開始/完了/失敗（dp_jobsで担保）

---

## GitHub Actions（運用テンプレ案）

### PR時（pytest＋登録＋DP＋検証）

1. pytest 実行
2. registryへ artifact 登録
3. dp compute
4. qm/ci 取得してassert

### Nightly（対象を絞る）

- "直近のbatchのみ"
- "active runが増えたbatchのみ"（v0.2：差分検知があると良い）

> 仕様としては「CIがトリガーとなる」ことを明示し、具体YAMLは実装側でOK

---

## 復元（Archiveから戻す）

v0.1は「復元可能」を仕様として残す（実装は後でもOK）

復元とは：
- archived runを active に戻す
- archive manifest から artifacts/qm/ci をDBへ再投入する

API案（将来）：
```
POST /runs/{runId}/restore  # manifest key指定
```

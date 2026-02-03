# セキュリティ / 認証 / 権限設計

## セキュリティ目標

- Org境界の分離（他Orgのデータに触れない）
- CI/pytestなど "機械実行" が安全に書き込める
- UIユーザは原則 読み取り中心（必要なら限定的な書き込み）
- 外部参照（Langfuse等）を含めても秘密情報を漏らさない
- 監査可能（いつ誰が何を変えたか追える）

---

## 認証方式（v0.1推奨）

### APIトークン（Bearer）

```
Authorization: Bearer <token>
```

- トークンは **Orgスコープ** を持つ（最低でも org_id を含む）
- 可能ならJWT（署名付き）だが、v0.1は DB発行の固定トークンでも可

### トークン種別（2種類で十分）

| 種別              | 用途        | 権限                                                                            |
| ----------------- | ----------- | ------------------------------------------------------------------------------- |
| **Machine Token** | CI/pytest用 | 書き込み：Run/Artifact/DPトリガーが可能、UI操作（pin/status変更）も必要なら許可 |
| **User Token**    | UI用        | 読み取り中心、書き込みが必要なら "pin/status" のみ許可など最小化                |

---

## 権限モデル（RBAC最小）

### 役割（Role）

| Role         | 説明                                   |
| ------------ | -------------------------------------- |
| `org_reader` | 閲覧のみ                               |
| `org_writer` | Run/Artifact追加・更新、pin/status変更 |
| `org_runner` | DPトリガー実行（compute開始）          |
| `org_admin`  | トークン発行・削除、Org設定            |

> v0.1では reader / writer / admin でも回るが、DPトリガーを分けたいので runner を推奨

### 権限（Permission）マッピング

| 操作                               | reader | writer    | runner | admin |
| ---------------------------------- | ------ | --------- | ------ | ----- |
| Org/Project/Batch/Run 読み取り     | ✅      | ✅         | ✅      | ✅     |
| Run作成 / 更新（tags/status）      | ❌      | ✅         | ✅      | ✅     |
| Artifact 追加 / 削除               | ❌      | ✅         | ✅      | ✅     |
| Pin 操作（champion/user_selected） | ❌      | ✅         | ✅      | ✅     |
| DP compute トリガー                | ❌      | ❌（任意） | ✅      | ✅     |
| トークン管理                       | ❌      | ❌         | ❌      | ✅     |

**運用的には：**
- CIは `writer + runner`
- UIは `reader`（+必要なら `writer`）

---

## スコープ（Org / Project / Batch / Run）

### 強制ルール

- APIはすべての読み書きで `org_id` を必ず検証
- Run単体エンドポイント（`/runs/{runId}`）も、内部で
  - run→batch→project→org を辿り
  - トークンの `org_id` と一致しない限り拒否

### "Cross-org参照" の禁止

- Artifactに外部URLを入れられるため、データの境界はアプリ側で守る
- DBのアクセス制御が最終防衛線
- UI表示も `org_id` で完全フィルタ

---

## CI/pytest運用（秘密情報の扱い）

### GitHub Actions Secrets

- `REGISTRY_API_TOKEN` を Secrets に入れる
- 権限は最小（`org_writer + org_runner`）
- PR from fork を想定するなら
  - Secretが渡らないため "登録系ジョブ" は main/内部PRだけに限定

### トークンのローテーション

- トークンに `created_at` / `expires_at` を持たせる（推奨）
- 期限前に新トークンを発行し、CI Secrets を差し替え

---

## 外部参照（Langfuse等）のセキュリティ

### 原則

Registryは外部ツールを統合しない＝認証情報を持たない方が安全。

Artifactとして保存するのは：
- 公開/社内限定URL
- trace_idなどの非機密メタ

もしDP RunnerがLangfuse APIを読む場合でも：
- 別途 Langfuse token を渡す設計（RegistryのDBに恒久保存しない）
- v0.1では "読まない" のが最も安全

### URLの取り扱い

UIでクリック可能にする場合：
- 許可ドメイン（allowlist）を設ける選択肢（v0.2）
- まずは `artifact.meta` に `sensitivity: public|internal|secret` を付けるのが軽い

---

## 入力バリデーション（Artifactの安全性）

Artifactは "任意JSON/テキスト" を受け入れるため、以下を必須にする：

| 対象                     | ルール                                                                |
| ------------------------ | --------------------------------------------------------------------- |
| kind ごとの payload 検証 | `inline_number` は数値のみ、`inline_json` はJSONサイズ制限（例：1MB） |
| type/label の長さ制限    | 例：`<= 120`                                                          |
| meta_json のサイズ制限   | 例：`<= 10KB`                                                         |
| URL                      | スキーム制限（`http` / `https` / `s3` / `gs` / `az` 等）              |

> セキュリティというより "運用事故防止" に直結します

---

## 監査ログ（Securityの最低ライン）

### 監査対象イベント

- Run status変更（active/garbage/archived）
- Pin変更（champion/user_selected）
- Artifact追加/削除
- DPジョブ開始/完了/失敗
- トークン発行/削除（admin）

### 監査ログの書式（例）

**audit_events テーブル**

| Column         | Type      | 説明                                    |
| -------------- | --------- | --------------------------------------- |
| `event_id`     | TEXT      | PRIMARY KEY                             |
| `org_id`       | TEXT      |                                         |
| `actor_type`   | TEXT      | `user` \| `machine`                     |
| `actor_id`     | TEXT      | token id / user id                      |
| `action`       | TEXT      | `RUN_STATUS_CHANGED` 等                 |
| `target_type`  | TEXT      | `run` / `artifact` / `dp_job` / `token` |
| `target_id`    | TEXT      |                                         |
| `payload_json` | TEXT      |                                         |
| `created_at`   | TIMESTAMP |                                         |

> v0.1は `dp_jobs` だけでも回るが、pin/statusは最低限欲しい（運用で揉めるので）

---

## エラーモデル（権限・認証）

| Status             | 意味                                                                   |
| ------------------ | ---------------------------------------------------------------------- |
| `401 Unauthorized` | トークンなし/無効                                                      |
| `403 Forbidden`    | トークンは有効だが権限不足                                             |
| `404 Not Found`    | 他OrgのIDを指定した場合も 404 を返す運用にすると情報漏洩が減る（推奨） |

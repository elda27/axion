# Object Storage Adapter

## 目的

プロバイダを変えても Artifact参照・DP入力・アーカイブ が壊れないようにする。

---

## インタフェース（言語非依存・擬似）

```typescript
interface ObjectStore {
  put_bytes(key: string, bytes: Buffer, content_type?: string, metadata?: Record<string, string>): ObjectRef
  get_bytes(key: string): Buffer
  exists(key: string): boolean
  list(prefix: string): ObjectRef[]
  delete(key: string): void
  presign_get(key: string, expires_sec: number): string  // optional
}
```

---

## サポート対象プロバイダ

| プロバイダ           | 用途                    |
| -------------------- | ----------------------- |
| Amazon S3            | 本番環境（AWS）         |
| Google Cloud Storage | 本番環境（GCP）         |
| Azure Blob Storage   | 本番環境（Azure）       |
| MinIO                | セルフホスト / オンプレ |
| Local FS             | ローカル開発            |

---

## Artifactへの保存ルール

### 推奨形式

Artifactに 生URL（`s3://…`）だけ を入れるとプロバイダ移行に弱いので、推奨は：

| フィールド | 内容                                         |
| ---------- | -------------------------------------------- |
| `payload`  | logical_key（例：`org1/p1/b1/r1/eval.json`） |
| `meta`     | `provider`, `bucket`, `region` など          |

### 移行時の手順

1. 新ストアにデータコピー
2. `OBJECT_STORE_PROVIDER` を切替
3. presign URLなどを新ストアから生成
4. 古いストアをread-only化して段階的に廃止

---

## "参照の壊れにくさ" のためのルール

### type=object_storage の場合

**方式A（推奨）:**
```json
{
  "kind": "url",
  "type": "object_storage",
  "payload": "org1/p1/b1/r1/eval.json",
  "meta": {
    "provider": "s3",
    "bucket": "my-bucket",
    "region": "ap-northeast-1"
  }
}
```

**方式B（シンプル）:**
```json
{
  "kind": "url",
  "type": "object_storage",
  "payload": "s3://my-bucket/org1/p1/b1/r1/eval.json"
}
```

> v0.1は どちらかに統一（おすすめ：payload_textに論理キー＋metaにprovider/bucket）

---

## ローカル開発

- Local FS 実装で同じIFを満たす
- 基底パス（例：`./data/object_store/`）配下にファイルを配置
- 本番移行時は論理キーをそのまま使用可能

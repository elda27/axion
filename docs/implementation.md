
## 概要
本稿では、`axion_lab_server`の設計について詳述する。
KWHは知識の保存、管理、検索を効率的に行うための包括的なプラットフォームである。
本ドキュメントでは、システムのアーキテクチャ、主要コンポーネント、データフロー、および技術スタックについて説明する。

## 構成
### モジュール構成

```
axion_lab_server/
├── shared/              # 共有ライブラリ
|   ├── kernel/          # アプリ起動と横断基盤のみを実装
|   ├── domain/          # 共通のモデル（エンティティ、値オブジェクト等）DB層に依存しない
|   └── libs/            # 共通ライブラリ（ログ、ユーティリティ等）
├── features/          # 機能実装
├── repos/         # ストレージやDBアクセスなどの永続化層
|   ├── storage/          # オブジェクトストレージアクセス
|   ├── fast_store/        # 高速Storeアクセス
|   |     └── parquet/        # Parquetアクセス等
|   └── rdb/               # RDBアクセス, ORM等
├── gateways/      # 外部サービス連携などのインターフェース
|   ├── web_service/     # Web APIサーバー\
|   |   ├── base/        # base api
|   |   ├── mlflow/        # MLflow連携
|   |   └── langfuse/        # MLflow連携
|   ├── 
└── ops/           # 横断機能


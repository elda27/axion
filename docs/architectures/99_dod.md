# 完了条件（Definition of Done）

## MVP完了条件（v0.1）

### 機能面

- [ ] Run作成 → link追加 → 一覧で表示できる
- [ ] garbageにすると既定一覧から消える（フィルタで復活表示可能）
- [ ] champion/user selected/latest を固定表示できる
- [ ] DPジョブを実行すると derived が保存され一覧に表示される
- [ ] アーカイブ対象を判定して退避できる（最小でも退避ファイル生成＋DB側フラグ更新）

### 運用面

- [ ] CI/pytestが Run+Artifact を登録できる
- [ ] CI/pytestまたはUIが DP compute を叩ける
- [ ] DPが失敗しても job が追える（error_text）
- [ ] garbageが既定表示/既定DPから除外され、復活できる
- [ ] ObjectStoreを切り替えても logical_key で参照が成立する（少なくとも設計上）

### セキュリティ面

- [ ] org境界が全APIで強制される
- [ ] CI用トークンで Run/Artifact登録、DPトリガー が可能
- [ ] UI用トークンで閲覧可能
- [ ] pin/status変更・DP実行が権限で制御できる
- [ ] 監査ログが最低限残る（pin/status/DP）

---

## 次にやるべき実装チケット（そのまま分割可能）

1. DBスキーマ作成（runs/artifacts/quality_metrics/comparison_indicators/pins）
2. Run CRUD API
3. Artifact CRUD API
4. Run一覧UI（garbage非表示、フィルタ、固定枠）
5. Pin操作（champion/user selected）
6. DPジョブ（active_only、QM/CI保存）
7. アーカイブジョブ（退避ファイル生成＋status更新）

---

## v0.2以降の拡張候補

- [ ] QM/CIのバージョン履歴保持
- [ ] アーカイブからの完全復元機能
- [ ] 検索基盤（OpenSearch等）によるアーカイブ検索
- [ ] DP入力の差分検知（変更があったbatchのみ再計算）
- [ ] トークンの自動ローテーション
- [ ] 許可ドメイン（allowlist）によるURL検証

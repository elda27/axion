# Run Lifecycle & Storage Tiers

Runs are never deleted by default.
They move between states and storage tiers.

Logical states:
- active
- garbage
- archived
- pinned

Storage tiers:
- HOT (latest)
- WARM
- COLD (object storage)

Garbage and archived runs are excluded from recomputation.
Restoring a run rehydrates it from COLD.

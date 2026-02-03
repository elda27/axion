# Data Model

## OutputRow (flat)
Mandatory:
- run_id
- case_id
- output_id
- payload_ref
- payload_hash
- created_at

User-defined:
- stage
- agent
- component
- is_final
- parent_output_id
- any other domain columns

The system does not interpret these columns.
They exist to support queries and metrics.

import { Chip } from "@mui/material";
import type { RunStatus } from "../types";

const statusConfig: Record<
  RunStatus,
  { label: string; color: "success" | "default" | "warning" }
> = {
  active: { label: "Active", color: "success" },
  garbage: { label: "Garbage", color: "default" },
  archived: { label: "Archived", color: "warning" },
};

interface RunStatusChipProps {
  status: RunStatus;
  size?: "small" | "medium";
}

export default function RunStatusChip({
  status,
  size = "small",
}: RunStatusChipProps) {
  const cfg = statusConfig[status];
  return (
    <Chip label={cfg.label} color={cfg.color} size={size} variant="outlined" />
  );
}

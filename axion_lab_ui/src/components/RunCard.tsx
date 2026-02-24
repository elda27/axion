import {
  Card,
  CardActionArea,
  CardContent,
  Typography,
  Box,
  Chip,
  Stack,
} from "@mui/material";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import PushPinIcon from "@mui/icons-material/PushPin";
import RunStatusChip from "./RunStatusChip";
import type { RunResponse, RunMetricResponse } from "../types";

interface RunCardProps {
  run: RunResponse;
  pinLabel?: "champion" | "user_selected" | null;
  onClick?: () => void;
  compact?: boolean;
  metrics?: RunMetricResponse[];
}

function formatMetricValue(value: unknown): string {
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  }
  return String(value);
}

export default function RunCard({
  run,
  pinLabel,
  onClick,
  compact,
  metrics,
}: RunCardProps) {
  const displayMetrics = (metrics ?? []).slice(0, 3);
  return (
    <Card
      sx={{
        borderLeft: pinLabel === "champion" ? 4 : undefined,
        borderLeftColor: pinLabel === "champion" ? "warning.main" : undefined,
      }}
    >
      <CardActionArea onClick={onClick} disabled={!onClick}>
        <CardContent sx={{ py: compact ? 1.5 : 2 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
            {pinLabel === "champion" && (
              <EmojiEventsIcon fontSize="small" color="warning" />
            )}
            {pinLabel === "user_selected" && (
              <PushPinIcon fontSize="small" color="secondary" />
            )}
            <Typography
              variant={compact ? "body1" : "h6"}
              fontWeight={600}
              noWrap
            >
              {run.name}
            </Typography>
            <RunStatusChip status={run.status} />
          </Box>

          {!compact && run.tags.length > 0 && (
            <Stack
              direction="row"
              spacing={0.5}
              sx={{ mt: 1, flexWrap: "wrap" }}
            >
              {run.tags.map((tag) => (
                <Chip key={tag} label={tag} size="small" variant="outlined" />
              ))}
            </Stack>
          )}

          {displayMetrics.length > 0 && (
            <Stack
              direction="row"
              spacing={1}
              sx={{ mt: 0.5, flexWrap: "wrap" }}
            >
              {displayMetrics.map((m) => (
                <Chip
                  key={m.qmId}
                  label={`${m.key}: ${formatMetricValue(m.value)}`}
                  size="small"
                  variant="outlined"
                  color="info"
                  sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}
                />
              ))}
            </Stack>
          )}
        </CardContent>
      </CardActionArea>
    </Card>
  );
}

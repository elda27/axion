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
import type { RunResponse } from "../types";

interface RunCardProps {
  run: RunResponse;
  pinLabel?: "champion" | "user_selected" | null;
  onClick?: () => void;
  compact?: boolean;
}

export default function RunCard({
  run,
  pinLabel,
  onClick,
  compact,
}: RunCardProps) {
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

          {!compact && (
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

          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mt: 0.5, display: "block" }}
          >
            {new Date(run.createdAt).toLocaleString()}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}

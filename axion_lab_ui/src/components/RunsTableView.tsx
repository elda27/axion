import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
  Stack,
  Box,
} from "@mui/material";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import PushPinIcon from "@mui/icons-material/PushPin";
import RunStatusChip from "./RunStatusChip";
import type { RunResponse } from "../types";

interface RunsTableViewProps {
  runs: RunResponse[];
  championRunId?: string | null;
  userSelectedRunIds?: Set<string>;
  onRunClick?: (runId: string) => void;
}

export default function RunsTableView({
  runs,
  championRunId,
  userSelectedRunIds,
  onRunClick,
}: RunsTableViewProps) {
  if (runs.length === 0) {
    return (
      <Box sx={{ py: 3, textAlign: "center" }}>
        <Typography color="text.secondary" variant="body2">
          No runs to display
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 700 }} />
            <TableCell sx={{ fontWeight: 700 }}>Name</TableCell>
            <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
            <TableCell sx={{ fontWeight: 700 }}>Tags</TableCell>
            <TableCell sx={{ fontWeight: 700 }}>Note</TableCell>
            <TableCell sx={{ fontWeight: 700 }}>Created</TableCell>
            <TableCell sx={{ fontWeight: 700 }}>Updated</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {runs.map((run) => {
            const isChampion = run.runId === championRunId;
            const isUserSelected = userSelectedRunIds?.has(run.runId) ?? false;

            return (
              <TableRow
                key={run.runId}
                hover
                sx={{
                  cursor: onRunClick ? "pointer" : undefined,
                  borderLeft: isChampion ? 4 : undefined,
                  borderLeftColor: isChampion ? "warning.main" : undefined,
                }}
                onClick={() => onRunClick?.(run.runId)}
              >
                <TableCell sx={{ width: 40, px: 1 }}>
                  {isChampion && (
                    <EmojiEventsIcon fontSize="small" color="warning" />
                  )}
                  {isUserSelected && !isChampion && (
                    <PushPinIcon fontSize="small" color="secondary" />
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight={600} noWrap>
                    {run.name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <RunStatusChip status={run.status} />
                </TableCell>
                <TableCell>
                  <Stack
                    direction="row"
                    spacing={0.5}
                    sx={{ flexWrap: "wrap" }}
                  >
                    {run.tags.map((tag) => (
                      <Chip
                        key={tag}
                        label={tag}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Stack>
                </TableCell>
                <TableCell>
                  {run.note && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      noWrap
                      sx={{ maxWidth: 200 }}
                    >
                      {run.note}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="caption" color="text.secondary" noWrap>
                    {new Date(run.createdAt).toLocaleString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="caption" color="text.secondary" noWrap>
                    {new Date(run.updatedAt).toLocaleString()}
                  </Typography>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

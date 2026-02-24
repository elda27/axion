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
  Box,
} from "@mui/material";
import type { RunMetricResponse } from "../types";

interface RunMetricsTableProps {
  metrics: RunMetricResponse[];
}

function formatValue(value: unknown): string {
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  }
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

const sourceColor: Record<string, "primary" | "secondary" | "default"> = {
  raw: "primary",
  derived: "secondary",
  manual: "default",
};

export default function RunMetricsTable({ metrics }: RunMetricsTableProps) {
  if (metrics.length === 0) {
    return (
      <Box sx={{ py: 3, textAlign: "center" }}>
        <Typography color="text.secondary" variant="body2">
          No run metrics available
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 700 }}>Key</TableCell>
            <TableCell sx={{ fontWeight: 700 }} align="right">
              Value
            </TableCell>
            <TableCell sx={{ fontWeight: 700 }}>Source</TableCell>
            <TableCell sx={{ fontWeight: 700 }}>Evaluation Type</TableCell>
            <TableCell sx={{ fontWeight: 700 }}>Computed</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {metrics.map((m) => (
            <TableRow key={m.qmId} hover>
              <TableCell>
                <Typography
                  variant="body2"
                  fontWeight={600}
                  fontFamily="monospace"
                >
                  {m.key}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="body2" fontFamily="monospace">
                  {formatValue(m.value)}
                </Typography>
              </TableCell>
              <TableCell>
                <Chip
                  label={m.source}
                  size="small"
                  color={sourceColor[m.source] ?? "default"}
                  variant="outlined"
                />
              </TableCell>
              <TableCell>
                {m.evaluationTypes.length > 0 ? (
                  <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                    {m.evaluationTypes.map((t) => (
                      <Chip key={t} label={t} size="small" variant="outlined" />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="caption" color="text.disabled">
                    —
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                <Typography variant="caption" color="text.secondary">
                  {new Date(m.computedAt).toLocaleString()}
                </Typography>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

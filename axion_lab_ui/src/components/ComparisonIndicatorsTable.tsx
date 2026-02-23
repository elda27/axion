import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
} from "@mui/material";
import type { ComparisonIndicatorResponse } from "../types";

interface ComparisonIndicatorsTableProps {
  indicators: ComparisonIndicatorResponse[];
}

function formatValue(value: unknown): string {
  if (typeof value === "number") {
    const sign = value > 0 ? "+" : "";
    return Number.isInteger(value)
      ? `${sign}${value}`
      : `${sign}${value.toFixed(4)}`;
  }
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function valueColor(value: unknown): string {
  if (typeof value === "number") {
    if (value > 0) return "success.main";
    if (value < 0) return "error.main";
  }
  return "text.primary";
}

export default function ComparisonIndicatorsTable({
  indicators,
}: ComparisonIndicatorsTableProps) {
  if (indicators.length === 0) {
    return (
      <Box sx={{ py: 3, textAlign: "center" }}>
        <Typography color="text.secondary" variant="body2">
          No comparison indicators available
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
            <TableCell sx={{ fontWeight: 700 }}>Baseline</TableCell>
            <TableCell sx={{ fontWeight: 700 }}>Computed</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {indicators.map((ci) => (
            <TableRow key={ci.ciId} hover>
              <TableCell>
                <Typography
                  variant="body2"
                  fontWeight={600}
                  fontFamily="monospace"
                >
                  {ci.key}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography
                  variant="body2"
                  fontFamily="monospace"
                  fontWeight={700}
                  color={valueColor(ci.value)}
                >
                  {formatValue(ci.value)}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  fontFamily="monospace"
                >
                  {ci.baselineRef ?? "—"}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="caption" color="text.secondary">
                  {new Date(ci.computedAt).toLocaleString()}
                </Typography>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

import { Box, Typography, Paper } from "@mui/material";
import InboxIcon from "@mui/icons-material/Inbox";
import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <Paper
      variant="outlined"
      sx={{
        py: 8,
        px: 4,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        textAlign: "center",
        borderStyle: "dashed",
      }}
    >
      <Box sx={{ color: "text.secondary", mb: 2 }}>
        {icon ?? <InboxIcon sx={{ fontSize: 48 }} />}
      </Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      {description && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 2, maxWidth: 400 }}
        >
          {description}
        </Typography>
      )}
      {action}
    </Paper>
  );
}

import { Box, CircularProgress, Typography, Alert } from "@mui/material";

interface LoadingProps {
  message?: string;
}

export function Loading({ message = "Loading..." }: LoadingProps) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        py: 8,
        gap: 2,
      }}
    >
      <CircularProgress size={24} />
      <Typography color="text.secondary">{message}</Typography>
    </Box>
  );
}

interface ErrorAlertProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorAlert({ message, onRetry }: ErrorAlertProps) {
  return (
    <Alert
      severity="error"
      sx={{ mb: 2 }}
      action={
        onRetry ? (
          <Box
            component="button"
            onClick={onRetry}
            sx={{
              cursor: "pointer",
              background: "none",
              border: "none",
              color: "inherit",
              textDecoration: "underline",
              fontFamily: "inherit",
            }}
          >
            Retry
          </Box>
        ) : undefined
      }
    >
      {message}
    </Alert>
  );
}

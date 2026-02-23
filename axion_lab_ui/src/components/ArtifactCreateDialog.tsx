import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
  Stack,
  MenuItem,
  Autocomplete,
} from "@mui/material";
import type { ArtifactKind, ArtifactCreate } from "../types";

const KINDS: { value: ArtifactKind; label: string }[] = [
  { value: "url", label: "URL" },
  { value: "local", label: "Local Path" },
  { value: "inline_text", label: "Inline Text" },
  { value: "inline_number", label: "Inline Number" },
  { value: "inline_json", label: "Inline JSON" },
];

/** Suggestions shown in the Type dropdown (freeSolo allows arbitrary input). */
const TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "langfuse_trace", label: "Langfuse Trace" },
  { value: "object_storage", label: "Object Storage" },
  { value: "note", label: "Note" },
  { value: "dashboard", label: "Dashboard" },
  { value: "git_commit", label: "Git Commit" },
  { value: "file", label: "File" },
  { value: "evaluation", label: "Evaluation" },
  { value: "other", label: "Other" },
];

interface ArtifactCreateDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: ArtifactCreate) => Promise<void>;
}

export default function ArtifactCreateDialog({
  open,
  onClose,
  onSubmit,
}: ArtifactCreateDialogProps) {
  const [kind, setKind] = useState<ArtifactKind>("url");
  const [type, setType] = useState<string>("langfuse_trace");
  const [label, setLabel] = useState("");
  const [payload, setPayload] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parsePayload = (): unknown => {
    if (kind === "inline_number") return Number(payload);
    if (kind === "inline_json") return JSON.parse(payload);
    return payload;
  };

  const handleSubmit = async () => {
    if (!label.trim() || !payload.trim() || !type.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const parsed = parsePayload();
      await onSubmit({ kind, type, label: label.trim(), payload: parsed });
      setLabel("");
      setPayload("");
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create artifact",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Artifact</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField
            select
            label="Kind"
            value={kind}
            onChange={(e) => setKind(e.target.value as ArtifactKind)}
            disabled={loading}
          >
            {KINDS.map((k) => (
              <MenuItem key={k.value} value={k.value}>
                {k.label}
              </MenuItem>
            ))}
          </TextField>
          <Autocomplete
            freeSolo
            options={TYPE_OPTIONS.map((t) => t.value)}
            getOptionLabel={(option) => {
              const found = TYPE_OPTIONS.find((t) => t.value === option);
              return found ? found.label : option;
            }}
            value={type}
            onChange={(_e, newValue) => setType(newValue ?? "")}
            onInputChange={(_e, newInput) => setType(newInput)}
            disabled={loading}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Type"
                placeholder="Select or enter custom type"
                helperText="Choose a preset or type a custom value"
              />
            )}
          />
          <TextField
            label="Label"
            fullWidth
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            disabled={loading}
          />
          <TextField
            label="Payload"
            fullWidth
            multiline={kind === "inline_json"}
            rows={kind === "inline_json" ? 4 : 1}
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            disabled={loading}
            placeholder={
              kind === "url"
                ? "https://..."
                : kind === "local"
                  ? "./path/to/file"
                  : kind === "inline_number"
                    ? "0.913"
                    : kind === "inline_json"
                      ? '{"key": "value"}'
                      : "Text content"
            }
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !label.trim() || !payload.trim() || !type.trim()}
        >
          Add
        </Button>
      </DialogActions>
    </Dialog>
  );
}

import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
  Chip,
  Box,
  Typography,
  InputAdornment,
  IconButton,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import type { AggregationCreate } from "../types";

interface AggregationCreateDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: AggregationCreate) => Promise<void>;
}

export default function AggregationCreateDialog({
  open,
  onClose,
  onSubmit,
}: AggregationCreateDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [groupByKeys, setGroupByKeys] = useState<string[]>([]);
  const [keyInput, setKeyInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addKey = () => {
    const key = keyInput.trim();
    if (key && !groupByKeys.includes(key)) {
      setGroupByKeys([...groupByKeys, key]);
    }
    setKeyInput("");
  };

  const removeKey = (key: string) => {
    setGroupByKeys(groupByKeys.filter((k) => k !== key));
  };

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        name: name.trim(),
        description: description.trim() || undefined,
        groupByKeys: groupByKeys.length > 0 ? groupByKeys : undefined,
      });
      setName("");
      setDescription("");
      setGroupByKeys([]);
      setKeyInput("");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setName("");
    setDescription("");
    setGroupByKeys([]);
    setKeyInput("");
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create Aggregation</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <TextField
          autoFocus
          margin="dense"
          label="Aggregation Name"
          placeholder="e.g. Epoch Comparison, Model × Version"
          fullWidth
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={loading}
        />
        <TextField
          margin="dense"
          label="Description (optional)"
          placeholder="e.g. Compare Loss across epochs for each model"
          fullWidth
          multiline
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={loading}
        />
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Group-by Keys
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mb: 1, display: "block" }}
          >
            Metadata keys used to group runs (e.g. epoch, model_name,
            agent_version)
          </Typography>
          <TextField
            size="small"
            placeholder="Add a key..."
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addKey();
              }
            }}
            disabled={loading}
            fullWidth
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      size="small"
                      onClick={addKey}
                      disabled={!keyInput.trim()}
                    >
                      <AddIcon fontSize="small" />
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />
          {groupByKeys.length > 0 && (
            <Box
              sx={{
                display: "flex",
                flexWrap: "wrap",
                gap: 0.5,
                mt: 1,
              }}
            >
              {groupByKeys.map((key) => (
                <Chip
                  key={key}
                  label={key}
                  size="small"
                  onDelete={() => removeKey(key)}
                  disabled={loading}
                />
              ))}
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !name.trim()}
        >
          Create
        </Button>
      </DialogActions>
    </Dialog>
  );
}

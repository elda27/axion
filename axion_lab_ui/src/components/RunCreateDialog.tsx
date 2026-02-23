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
  Chip,
  Box,
  InputAdornment,
  IconButton,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";

interface RunCreateDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: {
    name: string;
    tags: string[];
    note?: string;
  }) => Promise<void>;
}

export default function RunCreateDialog({
  open,
  onClose,
  onSubmit,
}: RunCreateDialogProps) {
  const [name, setName] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addTag = () => {
    const t = tagInput.trim();
    if (t && !tags.includes(t)) {
      setTags([...tags, t]);
    }
    setTagInput("");
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        name: name.trim(),
        tags,
        note: note.trim() || undefined,
      });
      setName("");
      setTags([]);
      setNote("");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create run");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create Run</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField
            autoFocus
            label="Run Name"
            fullWidth
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={loading}
          />
          <Box>
            <TextField
              label="Tags"
              fullWidth
              size="small"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addTag();
                }
              }}
              disabled={loading}
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton size="small" onClick={addTag}>
                        <AddIcon fontSize="small" />
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
              helperText="Press Enter to add a tag"
            />
            {tags.length > 0 && (
              <Stack
                direction="row"
                spacing={0.5}
                sx={{ mt: 1, flexWrap: "wrap" }}
              >
                {tags.map((tag) => (
                  <Chip
                    key={tag}
                    label={tag}
                    size="small"
                    onDelete={() => removeTag(tag)}
                  />
                ))}
              </Stack>
            )}
          </Box>
          <TextField
            label="Note (optional)"
            fullWidth
            multiline
            rows={2}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            disabled={loading}
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
          disabled={loading || !name.trim()}
        >
          Create
        </Button>
      </DialogActions>
    </Dialog>
  );
}

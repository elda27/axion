import { useState } from "react";
import {
  Typography,
  Box,
  Button,
  Stack,
  Chip,
  Paper,
  Divider,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  Alert,
  TextField,
  Tabs,
  Tab,
} from "@mui/material";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import PushPinIcon from "@mui/icons-material/PushPin";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import RestoreIcon from "@mui/icons-material/Restore";
import AddIcon from "@mui/icons-material/Add";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import EditIcon from "@mui/icons-material/Edit";
import SaveIcon from "@mui/icons-material/Save";
import CancelIcon from "@mui/icons-material/Cancel";
import { useParams, useNavigate } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import {
  getRun,
  updateRun,
  getRunMetrics,
  getRunComparisonIndicators,
  listArtifacts,
  createArtifact,
  deleteArtifact,
  createPin,
  deletePin,
} from "../api/client";
import RunStatusChip from "../components/RunStatusChip";
import RunMetricsTable from "../components/RunMetricsTable";
import ComparisonIndicatorsTable from "../components/ComparisonIndicatorsTable";
import ArtifactList from "../components/ArtifactList";
import ArtifactCreateDialog from "../components/ArtifactCreateDialog";
import Breadcrumbs from "../components/Breadcrumbs";
import { Loading, ErrorAlert } from "../components/Feedback";

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();

  const [tab, setTab] = useState(0);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [artifactDialogOpen, setArtifactDialogOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editNote, setEditNote] = useState("");
  const [actionMessage, setActionMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const {
    data: run,
    loading: runLoading,
    error: runError,
    refetch: refetchRun,
  } = useApi(() => getRun(runId!), [runId]);

  const {
    data: metrics,
    loading: metricsLoading,
    refetch: refetchMetrics,
  } = useApi(() => getRunMetrics(runId!), [runId]);

  const { data: indicators, loading: indicatorsLoading } = useApi(
    () => getRunComparisonIndicators(runId!),
    [runId],
  );

  const { data: artifactsData, refetch: refetchArtifacts } = useApi(
    () => listArtifacts(runId!),
    [runId],
  );

  const artifacts = artifactsData?.items ?? [];

  const handleAction = async (
    action: () => Promise<unknown>,
    successMsg: string,
  ) => {
    try {
      await action();
      setActionMessage({ type: "success", text: successMsg });
      refetchRun();
    } catch (err) {
      setActionMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Action failed",
      });
    }
    setMenuAnchor(null);
  };

  const startEditing = () => {
    if (run) {
      setEditName(run.name);
      setEditNote(run.note ?? "");
      setEditing(true);
    }
  };

  const saveEdit = async () => {
    await handleAction(
      () => updateRun(runId!, { name: editName, note: editNote || undefined }),
      "Run updated",
    );
    setEditing(false);
  };

  if (runLoading) return <Loading />;
  if (runError) return <ErrorAlert message={runError} onRetry={refetchRun} />;
  if (!run) return null;

  return (
    <Box>
      <Breadcrumbs
        crumbs={[
          { label: "Organizations", to: "/orgs" },
          { label: "Runs", to: `/batches/${run.batchId}/runs` },
          { label: run.name },
        ]}
      />

      {actionMessage && (
        <Alert
          severity={actionMessage.type}
          sx={{ mb: 2 }}
          onClose={() => setActionMessage(null)}
        >
          {actionMessage.text}
        </Alert>
      )}

      {/* ── Header ── */}
      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
          }}
        >
          <Box sx={{ flex: 1 }}>
            {editing ? (
              <Stack spacing={2}>
                <TextField
                  label="Name"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  size="small"
                  fullWidth
                />
                <TextField
                  label="Note"
                  value={editNote}
                  onChange={(e) => setEditNote(e.target.value)}
                  size="small"
                  fullWidth
                  multiline
                  rows={2}
                />
                <Stack direction="row" spacing={1}>
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={saveEdit}
                  >
                    Save
                  </Button>
                  <Button
                    size="small"
                    startIcon={<CancelIcon />}
                    onClick={() => setEditing(false)}
                  >
                    Cancel
                  </Button>
                </Stack>
              </Stack>
            ) : (
              <>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1.5,
                    mb: 1,
                  }}
                >
                  <Typography variant="h4">{run.name}</Typography>
                  <RunStatusChip status={run.status} size="medium" />
                  <Tooltip title="Edit">
                    <IconButton size="small" onClick={startEditing}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                {run.note && (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 1 }}
                  >
                    {run.note}
                  </Typography>
                )}
                <Stack direction="row" spacing={0.5} sx={{ mb: 1 }}>
                  {run.tags.map((tag) => (
                    <Chip
                      key={tag}
                      label={tag}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Stack>
                <Typography variant="caption" color="text.secondary">
                  Created {new Date(run.createdAt).toLocaleString()} · Updated{" "}
                  {new Date(run.updatedAt).toLocaleString()}
                </Typography>
              </>
            )}
          </Box>

          {!editing && (
            <Box>
              <Tooltip title="Actions">
                <IconButton onClick={(e) => setMenuAnchor(e.currentTarget)}>
                  <MoreVertIcon />
                </IconButton>
              </Tooltip>
              <Menu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={() => setMenuAnchor(null)}
              >
                <MenuItem
                  onClick={() =>
                    handleAction(
                      () => createPin(runId!, { pinType: "champion" }),
                      "Set as Champion",
                    )
                  }
                >
                  <ListItemIcon>
                    <EmojiEventsIcon fontSize="small" color="warning" />
                  </ListItemIcon>
                  <ListItemText>Set as Champion</ListItemText>
                </MenuItem>
                <MenuItem
                  onClick={() =>
                    handleAction(
                      () => createPin(runId!, { pinType: "user_selected" }),
                      "Pinned as User Selected",
                    )
                  }
                >
                  <ListItemIcon>
                    <PushPinIcon fontSize="small" color="secondary" />
                  </ListItemIcon>
                  <ListItemText>Pin (User Selected)</ListItemText>
                </MenuItem>
                <Divider />
                <MenuItem
                  onClick={() =>
                    handleAction(
                      () => deletePin(runId!, "champion"),
                      "Removed Champion pin",
                    )
                  }
                >
                  <ListItemText>Remove Champion Pin</ListItemText>
                </MenuItem>
                <MenuItem
                  onClick={() =>
                    handleAction(
                      () => deletePin(runId!, "user_selected"),
                      "Removed User Selected pin",
                    )
                  }
                >
                  <ListItemText>Remove User Selected Pin</ListItemText>
                </MenuItem>
                <Divider />
                {run.status === "active" ? (
                  <MenuItem
                    onClick={() =>
                      handleAction(
                        () => updateRun(runId!, { status: "garbage" }),
                        "Marked as garbage",
                      )
                    }
                  >
                    <ListItemIcon>
                      <DeleteOutlineIcon fontSize="small" color="error" />
                    </ListItemIcon>
                    <ListItemText>Mark as Garbage</ListItemText>
                  </MenuItem>
                ) : (
                  <MenuItem
                    onClick={() =>
                      handleAction(
                        () => updateRun(runId!, { status: "active" }),
                        "Restored to active",
                      )
                    }
                  >
                    <ListItemIcon>
                      <RestoreIcon fontSize="small" color="success" />
                    </ListItemIcon>
                    <ListItemText>Restore to Active</ListItemText>
                  </MenuItem>
                )}
              </Menu>
            </Box>
          )}
        </Box>
      </Paper>

      {/* ── Tabs ── */}
      <Paper variant="outlined" sx={{ mb: 3 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Insight" />
          <Tab label={`Artifacts (${artifacts.length})`} />
        </Tabs>
      </Paper>

      {/* ── Tab: Insight ── */}
      {tab === 0 && (
        <Stack spacing={3}>
          {/* Run Metrics (primary) */}
          <Box>
            <Typography variant="h5" sx={{ mb: 2 }}>
              Run Metrics
            </Typography>
            {metricsLoading ? (
              <Loading message="Loading metrics..." />
            ) : (
              <RunMetricsTable metrics={metrics ?? []} />
            )}
          </Box>

          {/* Comparison Indicators (auxiliary) */}
          <Box>
            <Typography variant="h5" sx={{ mb: 1 }}>
              Comparison Indicators
              <Typography
                component="span"
                variant="body2"
                color="text.secondary"
                sx={{ ml: 1 }}
              >
                (vs baseline)
              </Typography>
            </Typography>
            {indicatorsLoading ? (
              <Loading message="Loading indicators..." />
            ) : (
              <ComparisonIndicatorsTable indicators={indicators ?? []} />
            )}
          </Box>
        </Stack>
      )}

      {/* ── Tab: Artifacts ── */}
      {tab === 1 && (
        <Box>
          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => setArtifactDialogOpen(true)}
            >
              Add Artifact
            </Button>
          </Box>
          <ArtifactList
            artifacts={artifacts}
            onDelete={async (artifactId) => {
              await deleteArtifact(artifactId);
              refetchArtifacts();
            }}
          />
        </Box>
      )}

      <ArtifactCreateDialog
        open={artifactDialogOpen}
        onClose={() => setArtifactDialogOpen(false)}
        onSubmit={async (data) => {
          await createArtifact(runId!, data);
          refetchArtifacts();
        }}
      />
    </Box>
  );
}

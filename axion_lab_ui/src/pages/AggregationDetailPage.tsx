import { useState } from "react";
import {
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Stack,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import PersonRemoveIcon from "@mui/icons-material/PersonRemove";
import GroupWorkIcon from "@mui/icons-material/GroupWork";
import DirectionsRunIcon from "@mui/icons-material/DirectionsRun";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useNavigate, useParams } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import {
  getAggregation,
  listAggregationMembers,
  addAggregationMember,
  removeAggregationMember,
  deleteAggregation,
  getRun,
} from "../api/client";
import Breadcrumbs from "../components/Breadcrumbs";
import EmptyState from "../components/EmptyState";
import { Loading, ErrorAlert } from "../components/Feedback";
import type { AggregationMemberResponse, RunResponse } from "../types";

/** Member enriched with run details */
interface MemberWithRun extends AggregationMemberResponse {
  run?: RunResponse;
}

export default function AggregationDetailPage() {
  const { aggregationId } = useParams<{ aggregationId: string }>();
  const navigate = useNavigate();

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  const {
    data: aggregation,
    loading: aggLoading,
    error: aggError,
    refetch: refetchAgg,
  } = useApi(() => getAggregation(aggregationId!), [aggregationId]);

  const {
    data: membersData,
    loading: membersLoading,
    error: membersError,
    refetch: refetchMembers,
  } = useApi(() => listAggregationMembers(aggregationId!), [aggregationId]);

  const [enrichedMembers, setEnrichedMembers] = useState<MemberWithRun[]>([]);
  const [enriching, setEnriching] = useState(false);

  // Enrich members with run data when members change
  const members = membersData?.items ?? [];
  if (
    members.length > 0 &&
    enrichedMembers.length !== members.length &&
    !enriching
  ) {
    setEnriching(true);
    Promise.all(
      members.map(async (m) => {
        try {
          const run = await getRun(m.runId);
          return { ...m, run };
        } catch {
          return { ...m };
        }
      }),
    ).then((results) => {
      setEnrichedMembers(results);
      setEnriching(false);
    });
  }

  const handleDeleteAggregation = async () => {
    try {
      await deleteAggregation(aggregationId!);
      if (aggregation) {
        navigate(`/projects/${aggregation.projectId}/batches`);
      } else {
        navigate("/");
      }
    } catch {
      // ignore
    }
  };

  const handleRemoveMember = async (runId: string) => {
    await removeAggregationMember(aggregationId!, runId);
    setEnrichedMembers([]);
    refetchMembers();
    refetchAgg();
  };

  const loading = aggLoading || membersLoading;
  const error = aggError || membersError;

  return (
    <Box>
      <Breadcrumbs
        crumbs={[
          { label: "Organizations", to: "/orgs" },
          {
            label: "Batches",
            to: aggregation
              ? `/projects/${aggregation.projectId}/batches`
              : undefined,
          },
          { label: aggregation?.name ?? "..." },
        ]}
      />

      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 1,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Tooltip title="Back">
            <IconButton
              onClick={() =>
                aggregation
                  ? navigate(`/projects/${aggregation.projectId}/batches`)
                  : navigate("/")
              }
              size="small"
            >
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
          <GroupWorkIcon color="secondary" />
          <Typography variant="h4">
            {aggregation?.name ?? "Aggregation"}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddDialogOpen(true)}
          >
            Add Run
          </Button>
          <Tooltip title="Delete aggregation">
            <IconButton
              color="error"
              onClick={() => setDeleteConfirmOpen(true)}
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {aggregation?.description && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 1, ml: 6 }}
        >
          {aggregation.description}
        </Typography>
      )}

      {aggregation &&
        aggregation.groupByKeys &&
        aggregation.groupByKeys.length > 0 && (
          <Box sx={{ mb: 3, ml: 6 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
              Group-by keys:
            </Typography>
            {aggregation.groupByKeys.map((key) => (
              <Chip
                key={key}
                label={key}
                size="small"
                variant="outlined"
                sx={{ mr: 0.5 }}
              />
            ))}
          </Box>
        )}

      {loading && <Loading />}
      {error && (
        <ErrorAlert
          message={error}
          onRetry={() => {
            refetchAgg();
            refetchMembers();
          }}
        />
      )}

      <Typography variant="h6" sx={{ mb: 2 }}>
        Members ({aggregation?.memberCount ?? 0})
      </Typography>

      {!loading && members.length === 0 && (
        <EmptyState
          icon={<DirectionsRunIcon sx={{ fontSize: 48 }} />}
          title="No runs in this aggregation"
          description="Add runs to compare metrics across batches, epochs, models, or any metadata dimension."
          action={
            <Button variant="outlined" onClick={() => setAddDialogOpen(true)}>
              Add a Run
            </Button>
          }
        />
      )}

      {(enrichedMembers.length > 0 || (members.length > 0 && !enriching)) && (
        <Grid container spacing={2}>
          {(enrichedMembers.length > 0 ? enrichedMembers : members).map(
            (member) => {
              const em = member as MemberWithRun;
              return (
                <Grid key={member.memberId} size={{ xs: 12, sm: 6, md: 4 }}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                        }}
                      >
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            cursor: "pointer",
                            "&:hover": { textDecoration: "underline" },
                          }}
                          onClick={() => navigate(`/runs/${member.runId}`)}
                        >
                          <DirectionsRunIcon fontSize="small" color="primary" />
                          <Typography variant="subtitle1" fontWeight={600}>
                            {em.run?.name ?? member.runId}
                          </Typography>
                        </Box>
                        <Tooltip title="Remove from aggregation">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleRemoveMember(member.runId)}
                          >
                            <PersonRemoveIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                      {Object.keys(member.metadata).length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          {Object.entries(member.metadata).map(([k, v]) => (
                            <Chip
                              key={k}
                              label={`${k}: ${String(v)}`}
                              size="small"
                              variant="outlined"
                              sx={{ mr: 0.5, mb: 0.5 }}
                            />
                          ))}
                        </Box>
                      )}
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ mt: 1, display: "block" }}
                      >
                        Added {new Date(member.addedAt).toLocaleDateString()}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              );
            },
          )}
        </Grid>
      )}

      {/* Add Run Dialog */}
      <AddMemberDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        onSubmit={async (runId, metadata) => {
          await addAggregationMember(aggregationId!, {
            runId,
            metadata: metadata || undefined,
          });
          setEnrichedMembers([]);
          refetchMembers();
          refetchAgg();
        }}
        groupByKeys={aggregation?.groupByKeys ?? []}
      />

      {/* Delete confirmation */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
      >
        <DialogTitle>Delete Aggregation?</DialogTitle>
        <DialogContent>
          <Typography>
            This will permanently delete the aggregation
            <strong> {aggregation?.name}</strong> and all its member
            associations. The runs themselves will not be deleted.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            onClick={handleDeleteAggregation}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// ── Add Member Dialog ──

function AddMemberDialog({
  open,
  onClose,
  onSubmit,
  groupByKeys,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (runId: string, metadata: Record<string, unknown>) => Promise<void>;
  groupByKeys: string[];
}) {
  const [runId, setRunId] = useState("");
  const [metadataValues, setMetadataValues] = useState<Record<string, string>>(
    {},
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!runId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const metadata: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(metadataValues)) {
        if (v.trim()) {
          // Try to parse as number
          const num = Number(v);
          metadata[k] = isNaN(num) ? v.trim() : num;
        }
      }
      await onSubmit(runId.trim(), metadata);
      setRunId("");
      setMetadataValues({});
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add run");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setRunId("");
    setMetadataValues({});
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Run to Aggregation</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <TextField
          autoFocus
          margin="dense"
          label="Run ID"
          placeholder="Paste a run ID"
          fullWidth
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
          disabled={loading}
        />
        {groupByKeys.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              Metadata values
            </Typography>
            {groupByKeys.map((key) => (
              <TextField
                key={key}
                margin="dense"
                label={key}
                placeholder={`Value for ${key}`}
                fullWidth
                size="small"
                value={metadataValues[key] ?? ""}
                onChange={(e) =>
                  setMetadataValues({
                    ...metadataValues,
                    [key]: e.target.value,
                  })
                }
                disabled={loading}
              />
            ))}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !runId.trim()}
        >
          Add
        </Button>
      </DialogActions>
    </Dialog>
  );
}

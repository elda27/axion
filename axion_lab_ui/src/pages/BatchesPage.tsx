import { useState } from "react";
import {
  Typography,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Grid,
  Chip,
  Divider,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import LayersIcon from "@mui/icons-material/Layers";
import GroupWorkIcon from "@mui/icons-material/GroupWork";
import { useNavigate, useParams } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import {
  listBatches,
  createBatch,
  listAggregations,
  createAggregation,
  getProject,
} from "../api/client";
import CreateDialog from "../components/CreateDialog";
import AggregationCreateDialog from "../components/AggregationCreateDialog";
import Breadcrumbs from "../components/Breadcrumbs";
import EmptyState from "../components/EmptyState";
import { Loading, ErrorAlert } from "../components/Feedback";
import type { AggregationCreate } from "../types";

export default function BatchesPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [batchDialogOpen, setBatchDialogOpen] = useState(false);
  const [aggDialogOpen, setAggDialogOpen] = useState(false);

  const { data: project } = useApi(() => getProject(projectId!), [projectId]);
  const {
    data: batchData,
    loading: batchLoading,
    error: batchError,
    refetch: refetchBatches,
  } = useApi(() => listBatches(projectId!), [projectId]);

  const {
    data: aggData,
    loading: aggLoading,
    error: aggError,
    refetch: refetchAggs,
  } = useApi(() => listAggregations(projectId!), [projectId]);

  return (
    <Box>
      <Breadcrumbs
        crumbs={[
          { label: "Organizations", to: "/orgs" },
          {
            label: project?.orgId ? "Projects" : "...",
            to: project ? `/orgs/${project.orgId}/projects` : undefined,
          },
          { label: project?.name ?? "..." },
        ]}
      />

      {/* ── Batches ── */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 2,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <LayersIcon color="primary" />
          <Typography variant="h5">Batches</Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setBatchDialogOpen(true)}
        >
          New Batch
        </Button>
      </Box>

      {batchLoading && <Loading />}
      {batchError && (
        <ErrorAlert message={batchError} onRetry={refetchBatches} />
      )}

      {batchData && batchData.items.length === 0 && (
        <EmptyState
          icon={<LayersIcon sx={{ fontSize: 48 }} />}
          title="No batches yet"
          description="Create a batch to group experiment runs together."
          action={
            <Button variant="outlined" onClick={() => setBatchDialogOpen(true)}>
              Create Batch
            </Button>
          }
        />
      )}

      {batchData && batchData.items.length > 0 && (
        <Grid container spacing={2}>
          {batchData.items.map((batch) => (
            <Grid key={batch.batchId} size={{ xs: 12, sm: 6, md: 4 }}>
              <Card>
                <CardActionArea
                  onClick={() => navigate(`/batches/${batch.batchId}/runs`)}
                >
                  <CardContent>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        mb: 1,
                      }}
                    >
                      <LayersIcon color="primary" />
                      <Typography variant="h6">{batch.name}</Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Created {new Date(batch.createdAt).toLocaleDateString()}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <CreateDialog
        open={batchDialogOpen}
        onClose={() => setBatchDialogOpen(false)}
        onSubmit={async (name) => {
          await createBatch(projectId!, { name });
          refetchBatches();
        }}
        title="Create Batch"
        label="Batch Name"
      />

      <Divider sx={{ my: 4 }} />

      {/* ── Aggregations ── */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 2,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <GroupWorkIcon color="secondary" />
          <Typography variant="h5">Aggregations</Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setAggDialogOpen(true)}
        >
          New Aggregation
        </Button>
      </Box>

      {aggLoading && <Loading />}
      {aggError && <ErrorAlert message={aggError} onRetry={refetchAggs} />}

      {aggData && aggData.items.length === 0 && (
        <EmptyState
          icon={<GroupWorkIcon sx={{ fontSize: 48 }} />}
          title="No aggregations yet"
          description="Create an aggregation to compare runs across batches by metadata dimensions like model, epoch, or dataset."
          action={
            <Button variant="outlined" onClick={() => setAggDialogOpen(true)}>
              Create Aggregation
            </Button>
          }
        />
      )}

      {aggData && aggData.items.length > 0 && (
        <Grid container spacing={2}>
          {aggData.items.map((agg) => (
            <Grid key={agg.aggregationId} size={{ xs: 12, sm: 6, md: 4 }}>
              <Card>
                <CardActionArea
                  onClick={() => navigate(`/aggregations/${agg.aggregationId}`)}
                >
                  <CardContent>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        mb: 1,
                      }}
                    >
                      <GroupWorkIcon color="secondary" />
                      <Typography variant="h6">{agg.name}</Typography>
                    </Box>
                    {agg.description && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mb: 1 }}
                        noWrap
                      >
                        {agg.description}
                      </Typography>
                    )}
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        flexWrap: "wrap",
                      }}
                    >
                      <Chip size="small" label={`${agg.memberCount} runs`} />
                      {agg.groupByKeys?.map((key) => (
                        <Chip
                          key={key}
                          size="small"
                          variant="outlined"
                          label={key}
                        />
                      ))}
                    </Box>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ mt: 1, display: "block" }}
                    >
                      Created {new Date(agg.createdAt).toLocaleDateString()}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <AggregationCreateDialog
        open={aggDialogOpen}
        onClose={() => setAggDialogOpen(false)}
        onSubmit={async (data: AggregationCreate) => {
          await createAggregation(projectId!, data);
          refetchAggs();
        }}
      />
    </Box>
  );
}

import { useState } from "react";
import {
  Typography,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Grid,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import LayersIcon from "@mui/icons-material/Layers";
import { useNavigate, useParams } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { listBatches, createBatch, getProject } from "../api/client";
import CreateDialog from "../components/CreateDialog";
import Breadcrumbs from "../components/Breadcrumbs";
import EmptyState from "../components/EmptyState";
import { Loading, ErrorAlert } from "../components/Feedback";

export default function BatchesPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: project } = useApi(() => getProject(projectId!), [projectId]);
  const { data, loading, error, refetch } = useApi(
    () => listBatches(projectId!),
    [projectId],
  );

  return (
    <Box>
      <Breadcrumbs
        crumbs={[
          { label: "Organizations", to: "/" },
          {
            label: project?.orgId ? "Projects" : "...",
            to: project ? `/orgs/${project.orgId}/projects` : undefined,
          },
          { label: project?.name ?? "..." },
        ]}
      />

      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 3,
        }}
      >
        <Typography variant="h4">Batches</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
        >
          New Batch
        </Button>
      </Box>

      {loading && <Loading />}
      {error && <ErrorAlert message={error} onRetry={refetch} />}

      {data && data.items.length === 0 && (
        <EmptyState
          icon={<LayersIcon sx={{ fontSize: 48 }} />}
          title="No batches yet"
          description="Create a batch to group experiment runs together."
          action={
            <Button variant="outlined" onClick={() => setDialogOpen(true)}>
              Create Batch
            </Button>
          }
        />
      )}

      {data && data.items.length > 0 && (
        <Grid container spacing={2}>
          {data.items.map((batch) => (
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
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={async (name) => {
          await createBatch(projectId!, { name });
          refetch();
        }}
        title="Create Batch"
        label="Batch Name"
      />
    </Box>
  );
}

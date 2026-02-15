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
import FolderIcon from "@mui/icons-material/Folder";
import { useNavigate, useParams } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { listProjects, createProject, getOrg } from "../api/client";
import CreateDialog from "../components/CreateDialog";
import Breadcrumbs from "../components/Breadcrumbs";
import EmptyState from "../components/EmptyState";
import { Loading, ErrorAlert } from "../components/Feedback";

export default function ProjectsPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: org } = useApi(() => getOrg(orgId!), [orgId]);
  const { data, loading, error, refetch } = useApi(
    () => listProjects(orgId!),
    [orgId],
  );

  return (
    <Box>
      <Breadcrumbs
        crumbs={[
          { label: "Organizations", to: "/orgs" },
          { label: org?.name ?? "..." },
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
        <Typography variant="h4">Projects</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
        >
          New Project
        </Button>
      </Box>

      {loading && <Loading />}
      {error && <ErrorAlert message={error} onRetry={refetch} />}

      {data && data.items.length === 0 && (
        <EmptyState
          icon={<FolderIcon sx={{ fontSize: 48 }} />}
          title="No projects yet"
          description="Create a project to organize your experiment batches."
          action={
            <Button variant="outlined" onClick={() => setDialogOpen(true)}>
              Create Project
            </Button>
          }
        />
      )}

      {data && data.items.length > 0 && (
        <Grid container spacing={2}>
          {data.items.map((proj) => (
            <Grid key={proj.projectId} size={{ xs: 12, sm: 6, md: 4 }}>
              <Card>
                <CardActionArea
                  onClick={() =>
                    navigate(`/projects/${proj.projectId}/batches`)
                  }
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
                      <FolderIcon color="primary" />
                      <Typography variant="h6">{proj.name}</Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Created {new Date(proj.createdAt).toLocaleDateString()}
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
          await createProject(orgId!, { name });
          refetch();
        }}
        title="Create Project"
        label="Project Name"
      />
    </Box>
  );
}

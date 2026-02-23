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
import BusinessIcon from "@mui/icons-material/Business";
import { useNavigate } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { listOrgs, createOrg } from "../api/client";
import CreateDialog from "../components/CreateDialog";
import EmptyState from "../components/EmptyState";
import { Loading, ErrorAlert } from "../components/Feedback";

export default function OrgsPage() {
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data, loading, error, refetch } = useApi(() => listOrgs(), []);

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 3,
        }}
      >
        <Typography variant="h4">Organizations</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
        >
          New Organization
        </Button>
      </Box>

      {loading && <Loading />}
      {error && <ErrorAlert message={error} onRetry={refetch} />}

      {data && data.items.length === 0 && (
        <EmptyState
          icon={<BusinessIcon sx={{ fontSize: 48 }} />}
          title="No organizations yet"
          description="Create your first organization to start managing experiments."
          action={
            <Button variant="outlined" onClick={() => setDialogOpen(true)}>
              Create Organization
            </Button>
          }
        />
      )}

      {data && data.items.length > 0 && (
        <Grid container spacing={2}>
          {data.items.map((org) => (
            <Grid key={org.orgId} size={{ xs: 12, sm: 6, md: 4 }}>
              <Card>
                <CardActionArea
                  onClick={() => navigate(`/orgs/${org.orgId}/projects`)}
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
                      <BusinessIcon color="primary" />
                      <Typography variant="h6">{org.name}</Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Created {new Date(org.createdAt).toLocaleDateString()}
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
          await createOrg({ name });
          refetch();
        }}
        title="Create Organization"
        label="Organization Name"
      />
    </Box>
  );
}

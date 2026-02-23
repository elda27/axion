import { useEffect, useState } from "react";
import {
  Typography,
  Box,
  Card,
  CardActionArea,
  CardContent,
  Grid,
  Stack,
  Chip,
  Divider,
  Skeleton,
  Alert,
} from "@mui/material";
import DirectionsRunIcon from "@mui/icons-material/DirectionsRun";
import LayersIcon from "@mui/icons-material/Layers";
import BusinessIcon from "@mui/icons-material/Business";
import FolderIcon from "@mui/icons-material/Folder";
import { useNavigate } from "react-router-dom";
import { listOrgs, listProjects, listBatches, listRuns } from "../api/client";
import type {
  OrgResponse,
  ProjectResponse,
  BatchResponse,
  RunResponse,
} from "../types";
import RunStatusChip from "../components/RunStatusChip";
import SetupWizardDialog from "../components/SetupWizardDialog";

/** Recent run with parent context for navigation */
interface RunWithContext extends RunResponse {
  batchName?: string;
  projectName?: string;
  orgName?: string;
}

/** Recent batch with parent context */
interface BatchWithContext extends BatchResponse {
  projectName?: string;
  orgName?: string;
}

/** Project with org context */
interface ProjectWithContext extends ProjectResponse {
  orgName?: string;
}

export default function TopPage() {
  const navigate = useNavigate();

  const [orgs, setOrgs] = useState<OrgResponse[]>([]);
  const [projects, setProjects] = useState<ProjectWithContext[]>([]);
  const [batches, setBatches] = useState<BatchWithContext[]>([]);
  const [runs, setRuns] = useState<RunWithContext[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Setup wizard state
  const [setupMode, setSetupMode] = useState<"both" | "project-only" | null>(
    null,
  );
  const [setupOrg, setSetupOrg] = useState<OrgResponse | undefined>();
  const [fetchKey, setFetchKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function fetchDashboard() {
      try {
        setLoading(true);
        setError(null);

        // 1) Fetch all orgs
        const orgRes = await listOrgs(20);
        if (cancelled) return;
        const orgList = orgRes.items;
        setOrgs(orgList);

        if (orgList.length === 0) {
          setSetupMode("both");
          setSetupOrg(undefined);
          setLoading(false);
          return;
        }

        // 2) Fetch projects for each org (parallel)
        const projectResults = await Promise.all(
          orgList.map((org) => listProjects(org.orgId, 10)),
        );
        if (cancelled) return;

        const allProjects: ProjectWithContext[] = projectResults.flatMap(
          (res, i) =>
            res.items.map((p) => ({
              ...p,
              orgName: orgList[i].name,
            })),
        );
        // Sort by createdAt desc to get most recent
        allProjects.sort(
          (a, b) =>
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
        );
        setProjects(allProjects);

        if (allProjects.length === 0) {
          // Orgs exist but no projects — show project-only setup
          setSetupMode("project-only");
          setSetupOrg(orgList[0]);
          setLoading(false);
          return;
        }

        // 3) Fetch batches for recent projects (top 10 projects)
        const recentProjects = allProjects.slice(0, 10);
        const batchResults = await Promise.all(
          recentProjects.map((p) => listBatches(p.projectId, 5)),
        );
        if (cancelled) return;

        const projectMap = new Map(recentProjects.map((p) => [p.projectId, p]));
        const allBatches: BatchWithContext[] = batchResults.flatMap(
          (res, i) => {
            const proj = recentProjects[i];
            return res.items.map((b) => ({
              ...b,
              projectName: proj.name,
              orgName: proj.orgName,
            }));
          },
        );
        allBatches.sort(
          (a, b) =>
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
        );
        setBatches(allBatches);

        if (allBatches.length === 0) {
          setLoading(false);
          return;
        }

        // 4) Fetch runs for recent batches (top 10 batches)
        const recentBatches = allBatches.slice(0, 10);
        const runResults = await Promise.all(
          recentBatches.map((b) => listRuns(b.batchId, { limit: 5 })),
        );
        if (cancelled) return;

        const allRuns: RunWithContext[] = runResults.flatMap((res, i) => {
          const batch = recentBatches[i];
          const proj = projectMap.get(batch.projectId);
          return res.items.map((r) => ({
            ...r,
            batchName: batch.name,
            projectName: proj?.name ?? batch.projectName,
            orgName: proj?.orgName ?? batch.orgName,
          }));
        });
        allRuns.sort(
          (a, b) =>
            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
        );
        setRuns(allRuns);
        setLoading(false);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setLoading(false);
        }
      }
    }

    fetchDashboard();
    return () => {
      cancelled = true;
    };
  }, [fetchKey]);

  const recentRuns = runs.slice(0, 8);
  const recentBatches = batches.slice(0, 6);

  return (
    <Box>
      {/* Setup wizard when no org or no project exists */}
      {setupMode && (
        <SetupWizardDialog
          mode={setupMode}
          existingOrg={setupOrg}
          onComplete={(_org, project) => {
            setSetupMode(null);
            navigate(`/projects/${project.projectId}/batches`);
          }}
        />
      )}

      <Typography variant="h4" sx={{ mb: 1 }}>
        Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Recent activity across your organizations
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* ── Recent Runs ── */}
      <SectionHeader
        icon={<DirectionsRunIcon color="primary" />}
        title="Recent Runs"
        count={runs.length}
      />
      {loading ? (
        <SkeletonCards count={4} />
      ) : recentRuns.length === 0 ? (
        <EmptySection message="No runs yet" />
      ) : (
        <Grid container spacing={2} sx={{ mb: 4 }}>
          {recentRuns.map((run) => (
            <Grid key={run.runId} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card
                variant="outlined"
                sx={{
                  height: "100%",
                  transition: "box-shadow 0.15s",
                  "&:hover": { boxShadow: 3 },
                }}
              >
                <CardActionArea
                  onClick={() => navigate(`/runs/${run.runId}`)}
                  sx={{ height: "100%" }}
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
                      <Typography variant="subtitle1" fontWeight={600} noWrap>
                        {run.name}
                      </Typography>
                      <RunStatusChip status={run.status} size="small" />
                    </Box>
                    <Stack spacing={0.5}>
                      <ContextLabel
                        icon={<LayersIcon sx={{ fontSize: 14 }} />}
                        text={run.batchName ?? ""}
                      />
                      <ContextLabel
                        icon={<FolderIcon sx={{ fontSize: 14 }} />}
                        text={`${run.orgName} / ${run.projectName}`}
                      />
                    </Stack>
                    {run.tags.length > 0 && (
                      <Stack
                        direction="row"
                        spacing={0.5}
                        sx={{ mt: 1, flexWrap: "wrap" }}
                      >
                        {run.tags.slice(0, 3).map((tag) => (
                          <Chip
                            key={tag}
                            label={tag}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Stack>
                    )}
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ mt: 1, display: "block" }}
                    >
                      {formatRelative(run.updatedAt)}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* ── Recent Batches ── */}
      <SectionHeader
        icon={<LayersIcon color="primary" />}
        title="Recent Batches"
        count={batches.length}
      />
      {loading ? (
        <SkeletonCards count={3} />
      ) : recentBatches.length === 0 ? (
        <EmptySection message="No batches yet" />
      ) : (
        <Grid container spacing={2} sx={{ mb: 4 }}>
          {recentBatches.map((batch) => (
            <Grid key={batch.batchId} size={{ xs: 12, sm: 6, md: 4 }}>
              <Card
                variant="outlined"
                sx={{
                  transition: "box-shadow 0.15s",
                  "&:hover": { boxShadow: 3 },
                }}
              >
                <CardActionArea
                  onClick={() => navigate(`/batches/${batch.batchId}/runs`)}
                >
                  <CardContent>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        mb: 0.5,
                      }}
                    >
                      <LayersIcon color="primary" fontSize="small" />
                      <Typography variant="subtitle1" fontWeight={600} noWrap>
                        {batch.name}
                      </Typography>
                    </Box>
                    <ContextLabel
                      icon={<FolderIcon sx={{ fontSize: 14 }} />}
                      text={`${batch.orgName} / ${batch.projectName}`}
                    />
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ mt: 1, display: "block" }}
                    >
                      Created {formatRelative(batch.createdAt)}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* ── Organizations & Projects ── */}
      <SectionHeader
        icon={<BusinessIcon color="primary" />}
        title="Organizations & Projects"
        count={orgs.length}
      />
      {loading ? (
        <SkeletonCards count={3} />
      ) : orgs.length === 0 ? (
        <EmptySection message="No organizations yet. Create one to get started." />
      ) : (
        <Grid container spacing={2}>
          {orgs.map((org) => {
            const orgProjects = projects.filter((p) => p.orgId === org.orgId);
            return (
              <Grid key={org.orgId} size={{ xs: 12, sm: 6, md: 4 }}>
                <Card
                  variant="outlined"
                  sx={{
                    height: "100%",
                    transition: "box-shadow 0.15s",
                    "&:hover": { boxShadow: 3 },
                  }}
                >
                  <CardActionArea
                    onClick={() => navigate(`/orgs/${org.orgId}/projects`)}
                    sx={{ height: "100%" }}
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
                      {orgProjects.length > 0 ? (
                        <Stack spacing={0.5}>
                          {orgProjects.slice(0, 5).map((proj) => (
                            <Box
                              key={proj.projectId}
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 0.5,
                              }}
                            >
                              <FolderIcon
                                sx={{ fontSize: 14, color: "text.secondary" }}
                              />
                              <Typography variant="body2" noWrap>
                                {proj.name}
                              </Typography>
                            </Box>
                          ))}
                          {orgProjects.length > 5 && (
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              +{orgProjects.length - 5} more
                            </Typography>
                          )}
                        </Stack>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No projects yet
                        </Typography>
                      )}
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ mt: 1, display: "block" }}
                      >
                        Created {formatRelative(org.createdAt)}
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
}

// ── Helper components ──

function SectionHeader({
  icon,
  title,
  count,
}: {
  icon: React.ReactNode;
  title: string;
  count: number;
}) {
  return (
    <>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
        {icon}
        <Typography variant="h6">{title}</Typography>
        {count > 0 && <Chip label={count} size="small" variant="outlined" />}
      </Box>
    </>
  );
}

function ContextLabel({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 0.5,
        color: "text.secondary",
      }}
    >
      {icon}
      <Typography variant="caption" noWrap>
        {text}
      </Typography>
    </Box>
  );
}

function SkeletonCards({ count }: { count: number }) {
  return (
    <Grid container spacing={2} sx={{ mb: 4 }}>
      {Array.from({ length: count }).map((_, i) => (
        <Grid key={i} size={{ xs: 12, sm: 6, md: count <= 3 ? 4 : 3 }}>
          <Skeleton variant="rounded" height={120} />
        </Grid>
      ))}
    </Grid>
  );
}

function EmptySection({ message }: { message: string }) {
  return (
    <Box
      sx={{
        mb: 4,
        py: 3,
        textAlign: "center",
        color: "text.secondary",
        bgcolor: "action.hover",
        borderRadius: 1,
      }}
    >
      <Typography variant="body2">{message}</Typography>
    </Box>
  );
}

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

import { useState } from "react";
import {
  Typography,
  Box,
  Button,
  Stack,
  Collapse,
  Divider,
  Alert,
  Paper,
  IconButton,
  Tooltip,
  FormControlLabel,
  Switch,
  ToggleButtonGroup,
  ToggleButton,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import PushPinIcon from "@mui/icons-material/PushPin";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import ViewListIcon from "@mui/icons-material/ViewList";
import TableChartIcon from "@mui/icons-material/TableChart";
import { useNavigate, useParams } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import {
  getRunSummary,
  listRuns,
  createRun,
  getBatch,
  getProject,
  triggerDPCompute,
} from "../api/client";
import type { RunResponse } from "../types";
import RunCard from "../components/RunCard";
import RunCreateDialog from "../components/RunCreateDialog";
import RunsTableView from "../components/RunsTableView";
import Breadcrumbs from "../components/Breadcrumbs";
import EmptyState from "../components/EmptyState";
import { Loading, ErrorAlert } from "../components/Feedback";

type ViewMode = "cards" | "table";

export default function RunsPage() {
  const { batchId } = useParams<{ batchId: string }>();
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [recentOpen, setRecentOpen] = useState(false);
  const [includeGarbage, setIncludeGarbage] = useState(false);
  const [dpMessage, setDpMessage] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("cards");

  const { data: batch } = useApi(() => getBatch(batchId!), [batchId]);
  const { data: project } = useApi(
    () => (batch ? getProject(batch.projectId) : Promise.resolve(null)),
    [batch?.projectId],
  );
  const {
    data: summary,
    loading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useApi(
    () => getRunSummary(batchId!, includeGarbage),
    [batchId, includeGarbage],
  );

  // Load runs listed in the summary
  const { data: allRuns } = useApi(
    () => listRuns(batchId!, { limit: 50, includeGarbage }),
    [batchId, includeGarbage],
  );

  const runMap = new Map<string, RunResponse>();
  allRuns?.items.forEach((r) => runMap.set(r.runId, r));

  const handleTriggerDP = async () => {
    try {
      const job = await triggerDPCompute(batchId!);
      setDpMessage(`DP job started: ${job.jobId} (${job.status})`);
    } catch (err) {
      setDpMessage(
        `DP trigger failed: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  };

  const championRun = summary?.champion
    ? runMap.get(summary.champion.runId)
    : null;

  const recentRuns = (summary?.recentCollapsed.runs ?? [])
    .map((r) => runMap.get(r.runId))
    .filter((r): r is RunResponse => !!r);

  const userSelectedRuns = (summary?.userSelected ?? [])
    .map((r) => runMap.get(r.runId))
    .filter((r): r is RunResponse => !!r);

  const otherRuns = (summary?.others.runs ?? [])
    .map((r) => runMap.get(r.runId))
    .filter((r): r is RunResponse => !!r);

  const hasAnyRuns =
    !!championRun ||
    recentRuns.length > 0 ||
    userSelectedRuns.length > 0 ||
    otherRuns.length > 0;

  return (
    <Box>
      <Breadcrumbs
        crumbs={[
          { label: "Organizations", to: "/orgs" },
          {
            label: project?.name ? "Projects" : "...",
            to: project ? `/orgs/${project.orgId}/projects` : undefined,
          },
          {
            label: batch?.name ? "Batches" : "...",
            to: batch ? `/projects/${batch.projectId}/batches` : undefined,
          },
          { label: batch?.name ?? "..." },
        ]}
      />

      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 2,
        }}
      >
        <Typography variant="h4">Runs</Typography>
        <Stack direction="row" spacing={1}>
          <Tooltip title="Trigger DP Compute">
            <Button
              variant="outlined"
              startIcon={<PlayArrowIcon />}
              onClick={handleTriggerDP}
            >
              Compute
            </Button>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDialogOpen(true)}
          >
            New Run
          </Button>
        </Stack>
      </Box>

      <Box
        sx={{
          mb: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <FormControlLabel
          control={
            <Switch
              checked={includeGarbage}
              onChange={(e) => setIncludeGarbage(e.target.checked)}
              size="small"
            />
          }
          label={
            <Typography variant="body2" color="text.secondary">
              Include garbage runs
            </Typography>
          }
        />
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(_, v) => v && setViewMode(v as ViewMode)}
          size="small"
        >
          <ToggleButton value="cards" aria-label="Card view">
            <Tooltip title="Card view">
              <ViewListIcon fontSize="small" />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="table" aria-label="Table view">
            <Tooltip title="Table view">
              <TableChartIcon fontSize="small" />
            </Tooltip>
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {dpMessage && (
        <Alert
          severity="info"
          sx={{ mb: 2 }}
          onClose={() => setDpMessage(null)}
        >
          {dpMessage}
        </Alert>
      )}

      {summaryLoading && <Loading />}
      {summaryError && (
        <ErrorAlert message={summaryError} onRetry={refetchSummary} />
      )}

      {summary && !hasAnyRuns && (
        <EmptyState
          title="No runs in this batch"
          description="Create your first run to start evaluating experiments."
          action={
            <Button variant="outlined" onClick={() => setDialogOpen(true)}>
              Create Run
            </Button>
          }
        />
      )}

      {summary && hasAnyRuns && viewMode === "cards" && (
        <Stack spacing={3}>
          {/* ── Champion ── */}
          {championRun && (
            <Box>
              <Box
                sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}
              >
                <EmojiEventsIcon color="warning" />
                <Typography variant="h6" color="warning.main">
                  Champion
                </Typography>
              </Box>
              <RunCard
                run={championRun}
                pinLabel="champion"
                onClick={() => navigate(`/runs/${championRun.runId}`)}
              />
            </Box>
          )}

          {/* ── Recent (collapsed) ── */}
          {recentRuns.length > 0 && (
            <Box>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  mb: 1,
                  cursor: "pointer",
                }}
                onClick={() => setRecentOpen(!recentOpen)}
              >
                <Typography variant="h6" color="text.secondary">
                  Recent ({recentRuns.length})
                </Typography>
                <IconButton size="small">
                  {recentOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>
              <Collapse in={recentOpen}>
                <Stack spacing={1}>
                  {recentRuns.map((run) => (
                    <RunCard
                      key={run.runId}
                      run={run}
                      compact
                      onClick={() => navigate(`/runs/${run.runId}`)}
                    />
                  ))}
                </Stack>
              </Collapse>
              {!recentOpen && (
                <Paper
                  variant="outlined"
                  sx={{ p: 1.5, cursor: "pointer", textAlign: "center" }}
                  onClick={() => setRecentOpen(true)}
                >
                  <Typography variant="body2" color="text.secondary">
                    Click to expand {recentRuns.length} recent runs
                  </Typography>
                </Paper>
              )}
            </Box>
          )}

          {/* ── User Selected ── */}
          {userSelectedRuns.length > 0 && (
            <Box>
              <Box
                sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}
              >
                <PushPinIcon color="secondary" />
                <Typography variant="h6" color="secondary.main">
                  User Selected
                </Typography>
              </Box>
              <Stack spacing={1}>
                {userSelectedRuns.map((run) => (
                  <RunCard
                    key={run.runId}
                    run={run}
                    pinLabel="user_selected"
                    onClick={() => navigate(`/runs/${run.runId}`)}
                  />
                ))}
              </Stack>
            </Box>
          )}

          {/* ── Others ── */}
          {otherRuns.length > 0 && (
            <Box>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1.5 }}>
                Others
              </Typography>
              <Stack spacing={1}>
                {otherRuns.map((run) => (
                  <RunCard
                    key={run.runId}
                    run={run}
                    compact
                    onClick={() => navigate(`/runs/${run.runId}`)}
                  />
                ))}
              </Stack>
            </Box>
          )}
        </Stack>
      )}

      {summary && hasAnyRuns && viewMode === "table" && (
        <RunsTableView
          runs={allRuns?.items ?? []}
          championRunId={summary.champion?.runId}
          userSelectedRunIds={new Set(summary.userSelected.map((r) => r.runId))}
          onRunClick={(runId) => navigate(`/runs/${runId}`)}
        />
      )}

      <RunCreateDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={async ({ name, tags, note }) => {
          await createRun(batchId!, { name, tags, note });
          refetchSummary();
        }}
      />
    </Box>
  );
}

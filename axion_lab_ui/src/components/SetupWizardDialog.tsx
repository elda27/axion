import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Box,
  Typography,
} from "@mui/material";
import BusinessIcon from "@mui/icons-material/Business";
import FolderIcon from "@mui/icons-material/Folder";
import { createOrg, createProject } from "../api/client";
import type { OrgResponse, ProjectResponse } from "../types";

type SetupMode = "both" | "project-only";

interface SetupWizardDialogProps {
  /** "both" = no org exists, "project-only" = org exists but no project */
  mode: SetupMode;
  /** Pre-selected org (when mode = "project-only") */
  existingOrg?: OrgResponse;
  /** Called after setup completes with the created org & project */
  onComplete: (org: OrgResponse, project: ProjectResponse) => void;
}

const STEPS_BOTH = ["Create Organization", "Create Project"];
const STEPS_PROJECT = ["Create Project"];

export default function SetupWizardDialog({
  mode,
  existingOrg,
  onComplete,
}: SetupWizardDialogProps) {
  const steps = mode === "both" ? STEPS_BOTH : STEPS_PROJECT;

  const [activeStep, setActiveStep] = useState(0);
  const [orgName, setOrgName] = useState("");
  const [projectName, setProjectName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track created resources
  const [createdOrg, setCreatedOrg] = useState<OrgResponse | null>(
    existingOrg ?? null,
  );

  const isOrgStep = mode === "both" && activeStep === 0;
  const isProjectStep =
    mode === "project-only" || (mode === "both" && activeStep === 1);

  const handleNext = async () => {
    setError(null);
    setLoading(true);

    try {
      if (isOrgStep) {
        if (!orgName.trim()) return;
        const org = await createOrg({ name: orgName.trim() });
        setCreatedOrg(org);
        setActiveStep(1);
      } else if (isProjectStep) {
        if (!projectName.trim() || !createdOrg) return;
        const project = await createProject(createdOrg.orgId, {
          name: projectName.trim(),
        });
        onComplete(createdOrg, project);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open maxWidth="sm" fullWidth disableEscapeKeyDown>
      <DialogTitle>Welcome to Axion Lab</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {mode === "both"
            ? "Let's set up your workspace. Create an organization and your first project to get started."
            : "Create a project to start organizing your experiment batches."}
        </Typography>

        {steps.length > 1 && (
          <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {isOrgStep && (
          <Box>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                mb: 2,
              }}
            >
              <BusinessIcon color="primary" />
              <Typography variant="h6">Organization</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              An organization is the top-level container for all your projects
              and experiments.
            </Typography>
            <TextField
              autoFocus
              margin="dense"
              label="Organization Name"
              placeholder="e.g. My Team, Research Lab"
              fullWidth
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleNext()}
              disabled={loading}
            />
          </Box>
        )}

        {isProjectStep && (
          <Box>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                mb: 2,
              }}
            >
              <FolderIcon color="primary" />
              <Typography variant="h6">Project</Typography>
            </Box>
            {createdOrg && (
              <Box
                sx={{
                  mb: 2,
                  p: 1.5,
                  bgcolor: "action.hover",
                  borderRadius: 1,
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                }}
              >
                <BusinessIcon fontSize="small" color="primary" />
                <Typography variant="body2">
                  Organization: <strong>{createdOrg.name}</strong>
                </Typography>
              </Box>
            )}
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              A project groups related experiment batches and runs together.
            </Typography>
            <TextField
              autoFocus
              margin="dense"
              label="Project Name"
              placeholder="e.g. RAG Evaluation, Model Comparison"
              fullWidth
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleNext()}
              disabled={loading}
            />
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        {mode === "both" && activeStep > 0 && (
          <Button
            onClick={() => setActiveStep(0)}
            disabled={loading}
            sx={{ mr: "auto" }}
          >
            Back
          </Button>
        )}
        <Button
          onClick={handleNext}
          variant="contained"
          disabled={
            loading ||
            (isOrgStep && !orgName.trim()) ||
            (isProjectStep && !projectName.trim())
          }
        >
          {isProjectStep ? "Create & Get Started" : "Next"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

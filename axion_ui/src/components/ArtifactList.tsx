import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Typography,
  Chip,
  Box,
  Paper,
  Tooltip,
  Link as MuiLink,
} from "@mui/material";
import LinkIcon from "@mui/icons-material/Link";
import FolderIcon from "@mui/icons-material/Folder";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import DataObjectIcon from "@mui/icons-material/DataObject";
import NumbersIcon from "@mui/icons-material/Numbers";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import type { ArtifactResponse, ArtifactKind } from "../types";

const kindIcons: Record<ArtifactKind, React.ReactElement> = {
  url: <LinkIcon />,
  local: <FolderIcon />,
  inline_text: <TextSnippetIcon />,
  inline_number: <NumbersIcon />,
  inline_json: <DataObjectIcon />,
};

interface ArtifactListProps {
  artifacts: ArtifactResponse[];
  onDelete?: (artifactId: string) => void;
}

export default function ArtifactList({
  artifacts,
  onDelete,
}: ArtifactListProps) {
  if (artifacts.length === 0) {
    return (
      <Box sx={{ py: 3, textAlign: "center" }}>
        <Typography color="text.secondary" variant="body2">
          No artifacts
        </Typography>
      </Box>
    );
  }

  return (
    <Paper variant="outlined">
      <List dense disablePadding>
        {artifacts.map((art, idx) => (
          <ListItem
            key={art.artifactId}
            divider={idx < artifacts.length - 1}
            secondaryAction={
              <Box>
                {art.kind === "url" && typeof art.payload === "string" && (
                  <Tooltip title="Open link">
                    <IconButton
                      size="small"
                      component="a"
                      href={art.payload}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <OpenInNewIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
                {onDelete && (
                  <Tooltip title="Delete artifact">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => onDelete(art.artifactId)}
                    >
                      <DeleteOutlineIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            }
          >
            <ListItemIcon sx={{ minWidth: 36 }}>
              {kindIcons[art.kind]}
            </ListItemIcon>
            <ListItemText
              primary={
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Typography variant="body2" fontWeight={600}>
                    {art.label}
                  </Typography>
                  <Chip label={art.type} size="small" variant="outlined" />
                  <Chip label={art.kind} size="small" />
                </Box>
              }
              secondary={
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{
                    display: "block",
                    maxWidth: 500,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {art.kind === "url" ? (
                    <MuiLink
                      href={String(art.payload)}
                      target="_blank"
                      rel="noopener noreferrer"
                      underline="hover"
                    >
                      {String(art.payload)}
                    </MuiLink>
                  ) : typeof art.payload === "object" ? (
                    JSON.stringify(art.payload)
                  ) : (
                    String(art.payload)
                  )}
                </Typography>
              }
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}

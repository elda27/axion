import { Breadcrumbs as MuiBreadcrumbs, Link, Typography } from "@mui/material";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";
import { useNavigate } from "react-router-dom";

export interface Crumb {
  label: string;
  to?: string;
}

interface BreadcrumbsProps {
  crumbs: Crumb[];
}

export default function Breadcrumbs({ crumbs }: BreadcrumbsProps) {
  const navigate = useNavigate();

  return (
    <MuiBreadcrumbs
      separator={<NavigateNextIcon fontSize="small" />}
      sx={{ mb: 2 }}
    >
      {crumbs.map((c, i) =>
        i < crumbs.length - 1 && c.to ? (
          <Link
            key={i}
            underline="hover"
            color="inherit"
            sx={{ cursor: "pointer" }}
            onClick={() => navigate(c.to!)}
          >
            {c.label}
          </Link>
        ) : (
          <Typography key={i} color="text.primary" fontWeight={600}>
            {c.label}
          </Typography>
        ),
      )}
    </MuiBreadcrumbs>
  );
}

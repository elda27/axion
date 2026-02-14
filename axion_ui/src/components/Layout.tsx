import { type ReactNode } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Container,
  IconButton,
} from "@mui/material";
import ScienceIcon from "@mui/icons-material/Science";
import { useNavigate } from "react-router-dom";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar
        position="static"
        elevation={0}
        sx={{ borderBottom: 1, borderColor: "divider" }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate("/")}
            sx={{ mr: 1 }}
          >
            <ScienceIcon />
          </IconButton>
          <Typography
            variant="h6"
            sx={{
              cursor: "pointer",
              fontWeight: 700,
              letterSpacing: "-0.02em",
            }}
            onClick={() => navigate("/")}
          >
            Axion
          </Typography>
          <Typography variant="body2" sx={{ ml: 1.5, opacity: 0.7, mt: 0.3 }}>
            Experiment Evaluation
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ flex: 1, py: 3 }}>
        {children}
      </Container>
    </Box>
  );
}

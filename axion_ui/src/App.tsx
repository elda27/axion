import { ThemeProvider, CssBaseline } from "@mui/material";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import theme from "./theme";
import Layout from "./components/Layout";
import OrgsPage from "./pages/OrgsPage";
import ProjectsPage from "./pages/ProjectsPage";
import BatchesPage from "./pages/BatchesPage";
import RunsPage from "./pages/RunsPage";
import RunDetailPage from "./pages/RunDetailPage";

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<OrgsPage />} />
            <Route path="/orgs/:orgId/projects" element={<ProjectsPage />} />
            <Route
              path="/projects/:projectId/batches"
              element={<BatchesPage />}
            />
            <Route path="/batches/:batchId/runs" element={<RunsPage />} />
            <Route path="/runs/:runId" element={<RunDetailPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;

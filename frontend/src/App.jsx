import React, { useState, useEffect, useCallback } from "react";
import {
  Box, AppBar, Toolbar, Typography, Container, Tabs, Tab,
  Autocomplete, TextField, Button, Dialog, DialogTitle,
  DialogContent, DialogActions, Stack, Chip, Paper,
} from "@mui/material";
import { listUsers, createUser, getUser, listDocuments, startVerification, getLatestVerification } from "./api/client";
import DocumentUpload from "./components/DocumentUpload";
import VerificationProgress from "./components/VerificationProgress";
import ResultDisplay from "./components/ResultDisplay";

export default function App() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [tab, setTab] = useState(0);

  // Document & verification state
  const [docs, setDocs] = useState([]);
  const [job, setJob] = useState(null);
  const [activeJobId, setActiveJobId] = useState(null);

  // Add User dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", email: "" });

  const loadUsers = useCallback(() => {
    listUsers().then(setUsers).catch(console.error);
  }, []);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  // Load docs & latest job when user changes
  const loadDocs = useCallback(() => {
    if (!selectedUser) { setDocs([]); return; }
    listDocuments(selectedUser.id).then(setDocs).catch(console.error);
  }, [selectedUser]);

  const loadLatest = useCallback(() => {
    if (!selectedUser) { setJob(null); return; }
    getLatestVerification(selectedUser.id)
      .then((j) => { setJob(j); setActiveJobId(null); })
      .catch(() => setJob(null));
  }, [selectedUser]);

  useEffect(() => {
    loadDocs();
    loadLatest();
  }, [loadDocs, loadLatest]);

  const handleCreateUser = async () => {
    try {
      const newUser = await createUser(form);
      setDialogOpen(false);
      setForm({ name: "", phone: "", email: "" });
      loadUsers();
      setSelectedUser(newUser);
    } catch (err) {
      alert(err.response?.data?.detail || "Error creating user");
    }
  };

  const handleVerify = async () => {
    if (!selectedUser) return;
    try {
      const newJob = await startVerification(selectedUser.id);
      setActiveJobId(newJob.id);
      setJob(null);
    } catch (err) {
      alert(err.response?.data?.detail || "Error starting verification");
    }
  };

  const handleVerificationComplete = (finalJob) => {
    setJob(finalJob);
    setActiveJobId(null);
  };

  const docTypeLabels = {
    civil_id: "Civil ID",
    bank_statement: "Bank Statement",
    salary_transfer: "Salary Transfer",
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Document Verification Service
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ mt: 3, mb: 3, flex: 1 }}>
        {/* User selector bar */}
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
          <Autocomplete
            sx={{ flex: 1 }}
            options={users}
            getOptionLabel={(u) => u.name}
            value={selectedUser}
            onChange={(_, val) => setSelectedUser(val)}
            isOptionEqualToValue={(opt, val) => opt.id === val.id}
            renderInput={(params) => (
              <TextField {...params} label="Select User" size="small" />
            )}
          />
          <Button variant="contained" onClick={() => setDialogOpen(true)}>
            Add User
          </Button>
        </Stack>

        {/* Tabs */}
        {selectedUser && (
          <Paper sx={{ p: 0 }}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)}>
              <Tab label="Documents" />
              <Tab label="Verification" />
              <Tab label="Results" />
            </Tabs>

            <Box sx={{ p: 3 }}>
              {/* Documents Tab */}
              {tab === 0 && (
                <Box>
                  {docs.length > 0 && (
                    <Stack spacing={1} mb={2}>
                      {docs.map((d) => (
                        <Chip
                          key={d.id}
                          label={`${docTypeLabels[d.doc_type] || d.doc_type}: ${d.filename}`}
                          color="primary"
                          variant="outlined"
                        />
                      ))}
                    </Stack>
                  )}
                  <DocumentUpload userId={selectedUser.id} onUploaded={loadDocs} />
                </Box>
              )}

              {/* Verification Tab */}
              {tab === 1 && (
                <Box>
                  <Stack direction="row" spacing={2} alignItems="center" mb={2}>
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={handleVerify}
                      disabled={docs.length === 0 || activeJobId !== null}
                    >
                      {activeJobId ? "Running..." : "Verify Documents"}
                    </Button>
                  </Stack>

                  {activeJobId && (
                    <VerificationProgress
                      jobId={activeJobId}
                      onComplete={handleVerificationComplete}
                    />
                  )}
                </Box>
              )}

              {/* Results Tab */}
              {tab === 2 && (
                <Box>
                  {job && !activeJobId ? (
                    <ResultDisplay job={job} />
                  ) : (
                    <Typography color="text.secondary">
                      No results yet. Upload documents and run verification.
                    </Typography>
                  )}
                </Box>
              )}
            </Box>
          </Paper>
        )}

        {!selectedUser && (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: 300,
              bgcolor: "white",
              borderRadius: 2,
              border: "1px dashed #ccc",
            }}
          >
            <Typography color="text.secondary">
              Select a user to get started
            </Typography>
          </Box>
        )}
      </Container>

      {/* Add User Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New User</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Phone"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              fullWidth
            />
            <TextField
              label="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateUser} disabled={!form.name.trim()}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

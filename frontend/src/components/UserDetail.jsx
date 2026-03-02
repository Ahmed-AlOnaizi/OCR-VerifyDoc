import React, { useState, useEffect, useCallback } from "react";
import {
  Paper, Typography, Stack, Chip, Divider, Button, Box,
} from "@mui/material";
import { getUser, listDocuments, startVerification, getLatestVerification } from "../api/client";
import DocumentUpload from "./DocumentUpload";
import VerificationProgress from "./VerificationProgress";
import ResultDisplay from "./ResultDisplay";

export default function UserDetail({ userId }) {
  const [user, setUser] = useState(null);
  const [docs, setDocs] = useState([]);
  const [job, setJob] = useState(null);
  const [activeJobId, setActiveJobId] = useState(null);

  const loadUser = useCallback(() => {
    getUser(userId).then(setUser).catch(console.error);
  }, [userId]);

  const loadDocs = useCallback(() => {
    listDocuments(userId).then(setDocs).catch(console.error);
  }, [userId]);

  const loadLatest = useCallback(() => {
    getLatestVerification(userId).then((j) => {
      setJob(j);
      setActiveJobId(null);
    }).catch(() => setJob(null));
  }, [userId]);

  useEffect(() => {
    loadUser();
    loadDocs();
    loadLatest();
  }, [loadUser, loadDocs, loadLatest]);

  const handleVerify = async () => {
    try {
      const newJob = await startVerification(userId);
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

  if (!user) return null;

  const docTypeLabels = {
    civil_id: "Civil ID",
    bank_statement: "Bank Statement",
    salary_transfer: "Salary Transfer",
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>{user.name_en}</Typography>
      {user.name_ar && (
        <Typography variant="h6" color="text.secondary" gutterBottom dir="rtl">
          {user.name_ar}
        </Typography>
      )}

      <Stack direction="row" spacing={1} mb={2}>
        <Chip label={`Civil ID: ${user.civil_id}`} />
        {user.employer && <Chip label={user.employer} variant="outlined" />}
        {user.salary > 0 && <Chip label={`KWD ${user.salary}`} variant="outlined" />}
      </Stack>

      <Divider sx={{ mb: 2 }} />

      <Typography variant="h6" gutterBottom>Documents</Typography>

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

      <DocumentUpload userId={userId} onUploaded={loadDocs} />

      <Divider sx={{ my: 2 }} />

      <Stack direction="row" spacing={2} alignItems="center" mb={2}>
        <Typography variant="h6">Verification</Typography>
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

      {job && !activeJobId && <ResultDisplay job={job} />}
    </Paper>
  );
}

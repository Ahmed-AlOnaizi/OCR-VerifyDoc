import React, { useEffect, useState } from "react";
import {
  Box, Stepper, Step, StepLabel, LinearProgress, Typography,
} from "@mui/material";
import { subscribeToJob, getJob } from "../api/client";

const PHASES = [
  { key: "ingest", label: "Ingest Documents" },
  { key: "ocr", label: "OCR Processing" },
  { key: "extract", label: "Field Extraction" },
  { key: "verify", label: "Verification" },
  { key: "decision", label: "Decision" },
];

export default function VerificationProgress({ jobId, onComplete }) {
  const [phase, setPhase] = useState("pending");
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("pending");

  useEffect(() => {
    const source = subscribeToJob(
      jobId,
      (data) => {
        setPhase(data.phase);
        setProgress(data.progress);
        setStatus(data.status);

        if (data.status === "completed" || data.status === "failed") {
          // Fetch final job state from API
          getJob(jobId).then((finalJob) => {
            onComplete(finalJob);
          });
        }
      },
      (err) => {
        console.error("SSE error:", err);
        // Fallback: poll the job
        getJob(jobId).then((finalJob) => {
          onComplete(finalJob);
        });
      }
    );

    return () => source.close();
  }, [jobId, onComplete]);

  const activeStep = PHASES.findIndex((p) => p.key === phase);

  return (
    <Box sx={{ mb: 2 }}>
      <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 2 }}>
        {PHASES.map((p) => (
          <Step key={p.key}>
            <StepLabel>{p.label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{ height: 8, borderRadius: 4 }}
      />

      <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
        {status === "running" ? `Processing: ${phase} (${Math.round(progress)}%)` : status}
      </Typography>
    </Box>
  );
}

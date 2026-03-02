import React from "react";
import {
  Box, Typography, Chip, Accordion, AccordionSummary,
  AccordionDetails, List, ListItem, ListItemIcon, ListItemText, Alert,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import WarningIcon from "@mui/icons-material/Warning";

const DOC_LABELS = {
  civil_id: "Civil ID",
  bank_statement: "Bank Statement",
  salary_transfer: "Salary Transfer",
};

export default function ResultDisplay({ job }) {
  if (!job) return null;

  if (job.status === "failed") {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Verification failed: {job.error || "Unknown error"}
      </Alert>
    );
  }

  if (job.status !== "completed" || !job.result) return null;

  const { decision, verifications, errors } = job.result;
  const passed = decision === "PASS";

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Chip
          label={decision}
          color={passed ? "success" : "error"}
          sx={{ fontSize: "1.2rem", fontWeight: "bold", px: 2, py: 3 }}
        />
        <Typography variant="body1" color="text.secondary">
          {job.result.documents_verified} document(s) verified
        </Typography>
      </Box>

      {errors && errors.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>Issues Found:</Typography>
          {errors.map((err, i) => (
            <Typography key={i} variant="body2">- {err}</Typography>
          ))}
        </Alert>
      )}

      {verifications && Object.entries(verifications).map(([docType, v]) => (
        <Accordion key={docType} defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              {v.passed ? (
                <CheckCircleIcon color="success" />
              ) : (
                <CancelIcon color="error" />
              )}
              <Typography variant="subtitle1">
                {DOC_LABELS[docType] || docType}
              </Typography>
              <Chip
                size="small"
                label={v.passed ? "PASS" : "FAIL"}
                color={v.passed ? "success" : "error"}
                variant="outlined"
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {v.checks && v.checks.map((check, i) => (
                <ListItem key={i}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {check.match ? (
                      <CheckCircleIcon color="success" fontSize="small" />
                    ) : (
                      <CancelIcon color="error" fontSize="small" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={check.field}
                    secondary={formatCheck(check)}
                  />
                </ListItem>
              ))}
            </List>

            {v.has_loans && (
              <Alert severity="info" sx={{ mt: 1 }}>
                Loans detected: {v.loan_count} loan payment(s) found
              </Alert>
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}

function formatCheck(check) {
  const parts = [];
  if (check.expected !== undefined) parts.push(`Expected: ${check.expected}`);
  if (check.extracted !== undefined) parts.push(`Found: ${check.extracted}`);
  if (check.score !== undefined) parts.push(`Score: ${check.score}`);
  if (check.threshold !== undefined) parts.push(`Threshold: ${check.threshold}`);
  if (check.method) parts.push(`Method: ${check.method}`);
  if (check.months_found !== undefined) parts.push(`Months: ${check.months_found}/${check.min_required}`);
  if (check.average !== undefined) parts.push(`Avg: ${check.average.toFixed(3)}`);
  return parts.join(" | ");
}

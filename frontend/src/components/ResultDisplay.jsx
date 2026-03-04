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

function getDecisionChip(decision) {
  if (decision === "PASS") return { color: "success", label: "PASS" };
  if (decision === "NOT_ELIGIBLE") return { color: "warning", label: "NOT ELIGIBLE" };
  return { color: "error", label: "FAIL" };
}

function getBankStatusLabel(v) {
  if (v.eligible === undefined) return v.passed ? "PASS" : "FAIL";
  return v.eligible ? "ELIGIBLE" : "NOT ELIGIBLE";
}

function getBankStatusColor(v) {
  if (v.eligible === undefined) return v.passed ? "success" : "error";
  return v.eligible ? "success" : "warning";
}

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
  const chip = getDecisionChip(decision);

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Chip
          label={chip.label}
          color={chip.color}
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

      {verifications && Object.entries(verifications).map(([docType, v]) => {
        const isBankStatement = docType === "bank_statement";
        const statusLabel = isBankStatement ? getBankStatusLabel(v) : (v.passed ? "PASS" : "FAIL");
        const statusColor = isBankStatement ? getBankStatusColor(v) : (v.passed ? "success" : "error");
        const statusIcon = statusLabel === "PASS" || statusLabel === "ELIGIBLE"
          ? <CheckCircleIcon color="success" />
          : statusLabel === "NOT ELIGIBLE"
            ? <WarningIcon color="warning" />
            : <CancelIcon color="error" />;

        return (
          <Accordion key={docType} defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                {statusIcon}
                <Typography variant="subtitle1">
                  {DOC_LABELS[docType] || docType}
                </Typography>
                <Chip
                  size="small"
                  label={statusLabel}
                  color={statusColor}
                  variant="outlined"
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {getActionableFeedback(docType, v).map((msg, fi) => (
                <Alert key={fi} severity="error" sx={{ mb: 1 }}>{msg}</Alert>
              ))}
              <List dense>
                {v.checks && v.checks.map((check, i) => (
                  <ListItem key={i}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {check.match ? (
                        <CheckCircleIcon color="success" fontSize="small" />
                      ) : check.match === false ? (
                        <CancelIcon color="error" fontSize="small" />
                      ) : (
                        <WarningIcon color="info" fontSize="small" />
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

              {isBankStatement && v.debt_to_salary_ratio > 0 && (
                <Alert severity={v.debt_to_salary_ratio > 0.4 ? "error" : "success"} sx={{ mt: 1 }}>
                  Debt-to-salary ratio: {(v.debt_to_salary_ratio * 100).toFixed(1)}%
                  (max allowed: 40%)
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>
        );
      })}
    </Box>
  );
}

function getActionableFeedback(docType, v) {
  const messages = [];

  if (docType === "civil_id" && v.checks) {
    const nameCheck = v.checks.find((c) => c.field?.toLowerCase().includes("name"));
    if (nameCheck && nameCheck.match === false) {
      if (nameCheck.score === 0) {
        messages.push("The name on the Civil ID does not match the registered name. Please upload the correct document.");
      } else if (nameCheck.score !== undefined && nameCheck.threshold !== undefined && nameCheck.score < nameCheck.threshold) {
        messages.push("The scanned Civil ID may be unclear. Try re-uploading at higher quality.");
      }
    }
  }

  if (docType === "bank_statement" && v.checks) {
    const salaryCheck = v.checks.find((c) => c.field?.toLowerCase().includes("salary"));
    if (salaryCheck) {
      if (salaryCheck.months_found === 0) {
        messages.push("No salary deposits were detected in the bank statement.");
      } else if (salaryCheck.months_found !== undefined && salaryCheck.min_required !== undefined && salaryCheck.months_found < salaryCheck.min_required) {
        messages.push(`Only ${salaryCheck.months_found} of ${salaryCheck.min_required} required months of salary found.`);
      }
    }
    if (v.debt_to_salary_ratio !== undefined && v.debt_to_salary_ratio > 0.4) {
      messages.push(`Monthly debt exceeds 40% of salary (ratio: ${(v.debt_to_salary_ratio * 100).toFixed(1)}%). Applicant is not eligible.`);
    }
  }

  if (docType === "salary_transfer" && v.checks) {
    for (const check of v.checks) {
      if (check.match === false) {
        const field = (check.field || "").toLowerCase();
        if (field.includes("name")) {
          messages.push("Employee name on the salary certificate does not match.");
        } else if (field.includes("civil") || field.includes("id")) {
          messages.push("Civil ID number on the salary certificate does not match.");
        } else if (field.includes("salary") || field.includes("amount")) {
          messages.push("Salary amount on the certificate does not match the declared amount.");
        }
      }
    }
  }

  return messages;
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
  if (check.ratio !== undefined) parts.push(`Ratio: ${(check.ratio * 100).toFixed(1)}%`);
  if (check.max_allowed !== undefined) parts.push(`Max: ${(check.max_allowed * 100).toFixed(0)}%`);
  if (check.total_monthly_debt !== undefined) parts.push(`Monthly debt: ${check.total_monthly_debt.toFixed(3)}`);
  return parts.join(" | ");
}

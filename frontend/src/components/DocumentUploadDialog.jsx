import React, { useState, useRef, useCallback } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Grid, Paper, Typography, Box, IconButton,
  CircularProgress, Chip,
} from "@mui/material";
import BadgeIcon from "@mui/icons-material/Badge";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import DescriptionIcon from "@mui/icons-material/Description";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CloseIcon from "@mui/icons-material/Close";
import { uploadDocument } from "../api/client";

const DOC_TYPES = [
  { key: "civil_id", label: "Civil ID", icon: <BadgeIcon sx={{ fontSize: 40 }} /> },
  { key: "bank_statement", label: "Bank Statement", icon: <AccountBalanceIcon sx={{ fontSize: 40 }} /> },
  { key: "salary_transfer", label: "Salary Transfer", icon: <DescriptionIcon sx={{ fontSize: 40 }} /> },
];

const ACCEPT = ".pdf,.png,.jpg,.jpeg";

function isAccepted(file) {
  const ext = "." + file.name.split(".").pop().toLowerCase();
  return ACCEPT.split(",").includes(ext);
}

export default function DocumentUploadDialog({ open, onClose, userId, docs, onUploaded }) {
  const [files, setFiles] = useState({});       // { civil_id: File, ... }
  const [statuses, setStatuses] = useState({});  // { civil_id: "idle"|"uploading"|"done"|"error" }
  const [errors, setErrors] = useState({});
  const inputRefs = useRef({});

  const existingByType = {};
  (docs || []).forEach((d) => { existingByType[d.doc_type] = d; });

  const setFileForType = (docType, file) => {
    setFiles((prev) => ({ ...prev, [docType]: file }));
    setStatuses((prev) => ({ ...prev, [docType]: "idle" }));
    setErrors((prev) => ({ ...prev, [docType]: null }));
  };

  const removeFile = (docType) => {
    setFiles((prev) => { const n = { ...prev }; delete n[docType]; return n; });
    setStatuses((prev) => ({ ...prev, [docType]: "idle" }));
  };

  const handleDrop = useCallback((docType) => (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && isAccepted(file)) setFileForType(docType, file);
  }, []);

  const handleDragOver = (e) => e.preventDefault();

  const handleFileInput = (docType) => (e) => {
    const file = e.target.files[0];
    if (file) setFileForType(docType, file);
    e.target.value = "";
  };

  const hasFiles = Object.keys(files).length > 0;

  const handleUpload = async () => {
    const entries = Object.entries(files);
    if (entries.length === 0) return;

    for (const [docType, file] of entries) {
      setStatuses((prev) => ({ ...prev, [docType]: "uploading" }));
      try {
        await uploadDocument(userId, file, docType);
        setStatuses((prev) => ({ ...prev, [docType]: "done" }));
      } catch (err) {
        setStatuses((prev) => ({ ...prev, [docType]: "error" }));
        setErrors((prev) => ({
          ...prev,
          [docType]: err.response?.data?.detail || "Upload failed",
        }));
      }
    }
  };

  const allDone = hasFiles && Object.entries(files).every(
    ([dt]) => statuses[dt] === "done"
  );

  const anyUploading = Object.values(statuses).some((s) => s === "uploading");

  const handleClose = () => {
    if (allDone) onUploaded();
    setFiles({});
    setStatuses({});
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="md">
      <DialogTitle>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          Add Documents
          <IconButton onClick={handleClose} size="small"><CloseIcon /></IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 0.5 }}>
          {DOC_TYPES.map(({ key, label, icon }) => {
            const file = files[key];
            const status = statuses[key] || "idle";
            const existing = existingByType[key];

            return (
              <Grid item xs={12} sm={4} key={key}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    border: "2px dashed",
                    borderColor: status === "done" ? "success.main"
                      : status === "error" ? "error.main"
                      : file ? "primary.main" : "grey.400",
                    textAlign: "center",
                    cursor: status === "uploading" ? "default" : "pointer",
                    minHeight: 200,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    "&:hover": status !== "uploading" ? { borderColor: "primary.main", bgcolor: "action.hover" } : {},
                  }}
                  onDrop={handleDrop(key)}
                  onDragOver={handleDragOver}
                  onClick={() => {
                    if (status !== "uploading") inputRefs.current[key]?.click();
                  }}
                >
                  <input
                    type="file"
                    hidden
                    accept={ACCEPT}
                    ref={(el) => { inputRefs.current[key] = el; }}
                    onChange={handleFileInput(key)}
                  />

                  <Box sx={{ color: status === "done" ? "success.main" : "text.secondary", mb: 1 }}>
                    {status === "done" ? <CheckCircleIcon sx={{ fontSize: 40 }} color="success" /> : icon}
                  </Box>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    {label}
                  </Typography>

                  {status === "uploading" && <CircularProgress size={24} sx={{ my: 1 }} />}

                  {status === "error" && (
                    <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                      {errors[key]}
                    </Typography>
                  )}

                  {status === "done" && (
                    <Typography variant="body2" color="success.main">Uploaded</Typography>
                  )}

                  {status === "idle" && file && (
                    <Box sx={{ mt: 1 }}>
                      <Chip
                        label={file.name}
                        onDelete={(e) => { e.stopPropagation(); removeFile(key); }}
                        size="small"
                        color="primary"
                      />
                    </Box>
                  )}

                  {status === "idle" && !file && existing && (
                    <Chip
                      label={existing.filename}
                      size="small"
                      variant="outlined"
                      color="success"
                      sx={{ mt: 1 }}
                    />
                  )}

                  {status === "idle" && !file && !existing && (
                    <Box sx={{ mt: 1, color: "text.secondary" }}>
                      <CloudUploadIcon fontSize="small" sx={{ mr: 0.5, verticalAlign: "middle" }} />
                      <Typography variant="body2" component="span">
                        Drag & drop or click to upload
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </Grid>
            );
          })}
        </Grid>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose}>
          {allDone ? "Done" : "Cancel"}
        </Button>
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!hasFiles || anyUploading || allDone}
        >
          {anyUploading ? "Uploading..." : "Upload"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

import React, { useState } from "react";
import {
  Stack, Button, FormControl, InputLabel, Select, MenuItem, Typography,
} from "@mui/material";
import { uploadDocument } from "../api/client";

const DOC_TYPES = [
  { value: "civil_id", label: "Civil ID" },
  { value: "bank_statement", label: "Bank Statement" },
  { value: "salary_transfer", label: "Salary Transfer Letter" },
];

export default function DocumentUpload({ userId, onUploaded }) {
  const [file, setFile] = useState(null);
  const [docType, setDocType] = useState("civil_id");
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await uploadDocument(userId, file, docType);
      setFile(null);
      onUploaded();
    } catch (err) {
      alert(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Stack direction="row" spacing={2} alignItems="center">
      <FormControl size="small" sx={{ minWidth: 180 }}>
        <InputLabel>Document Type</InputLabel>
        <Select
          value={docType}
          label="Document Type"
          onChange={(e) => setDocType(e.target.value)}
        >
          {DOC_TYPES.map((t) => (
            <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <Button variant="outlined" component="label">
        {file ? file.name : "Choose File"}
        <input
          type="file"
          hidden
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={(e) => setFile(e.target.files[0] || null)}
        />
      </Button>

      <Button
        variant="contained"
        onClick={handleUpload}
        disabled={!file || uploading}
      >
        {uploading ? "Uploading..." : "Upload"}
      </Button>
    </Stack>
  );
}

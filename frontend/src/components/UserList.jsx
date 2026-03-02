import React, { useState, useEffect } from "react";
import {
  Paper, List, ListItemButton, ListItemText, Typography, Button,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, Stack,
} from "@mui/material";
import { listUsers, createUser } from "../api/client";

export default function UserList({ selectedUserId, onSelectUser }) {
  const [users, setUsers] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    civil_id: "", name_en: "", name_ar: "", employer: "", salary: "",
  });

  const load = () => listUsers().then(setUsers).catch(console.error);

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    try {
      await createUser({
        ...form,
        salary: parseFloat(form.salary) || 0,
      });
      setOpen(false);
      setForm({ civil_id: "", name_en: "", name_ar: "", employer: "", salary: "" });
      load();
    } catch (err) {
      alert(err.response?.data?.detail || "Error creating user");
    }
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="h6">Users</Typography>
        <Button size="small" variant="contained" onClick={() => setOpen(true)}>
          Add User
        </Button>
      </Stack>

      <List dense>
        {users.map((u) => (
          <ListItemButton
            key={u.id}
            selected={u.id === selectedUserId}
            onClick={() => onSelectUser(u.id)}
          >
            <ListItemText
              primary={u.name_en}
              secondary={`ID: ${u.civil_id}`}
            />
          </ListItemButton>
        ))}
        {users.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 1 }}>
            No users yet
          </Typography>
        )}
      </List>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New User</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Civil ID" value={form.civil_id}
              onChange={(e) => setForm({ ...form, civil_id: e.target.value })} fullWidth />
            <TextField label="Name (English)" value={form.name_en}
              onChange={(e) => setForm({ ...form, name_en: e.target.value })} fullWidth />
            <TextField label="Name (Arabic)" value={form.name_ar}
              onChange={(e) => setForm({ ...form, name_ar: e.target.value })} fullWidth />
            <TextField label="Employer" value={form.employer}
              onChange={(e) => setForm({ ...form, employer: e.target.value })} fullWidth />
            <TextField label="Monthly Salary (KWD)" type="number" value={form.salary}
              onChange={(e) => setForm({ ...form, salary: e.target.value })} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate}>Create</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}

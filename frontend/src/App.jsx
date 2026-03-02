import React, { useState } from "react";
import { Box, AppBar, Toolbar, Typography, Container, Grid } from "@mui/material";
import UserList from "./components/UserList";
import UserDetail from "./components/UserDetail";

export default function App() {
  const [selectedUserId, setSelectedUserId] = useState(null);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Document Verification Service
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 3, mb: 3, flex: 1 }}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 4 }}>
            <UserList
              selectedUserId={selectedUserId}
              onSelectUser={setSelectedUserId}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 8 }}>
            {selectedUserId ? (
              <UserDetail userId={selectedUserId} />
            ) : (
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
                  Select a user to view details
                </Typography>
              </Box>
            )}
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

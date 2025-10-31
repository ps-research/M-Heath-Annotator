import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const ExportPanel = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Export Data
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1" color="text.secondary">
          Configure and export annotation data in various formats.
        </Typography>
      </Paper>
    </Box>
  );
};

export default ExportPanel;

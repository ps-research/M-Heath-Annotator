import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const DataViewerPanel = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Data Viewer
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1" color="text.secondary">
          Browse and filter annotation data.
        </Typography>
      </Paper>
    </Box>
  );
};

export default DataViewerPanel;

import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const PromptEditorPanel = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Prompt Editor
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1" color="text.secondary">
          Edit and manage prompts for each annotator and domain.
        </Typography>
      </Paper>
    </Box>
  );
};

export default PromptEditorPanel;

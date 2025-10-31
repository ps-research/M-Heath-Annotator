import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

/**
 * Loading spinner component
 */
const LoadingSpinner = ({ size = 'medium', message, fullScreen = false }) => {
  const sizeMap = {
    small: 24,
    medium: 40,
    large: 60,
  };

  const circularSize = sizeMap[size] || sizeMap.medium;

  const content = (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      gap={2}
      sx={{
        ...(fullScreen && {
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 9999,
        }),
      }}
    >
      <CircularProgress size={circularSize} />
      {message && (
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      )}
    </Box>
  );

  return content;
};

export default LoadingSpinner;

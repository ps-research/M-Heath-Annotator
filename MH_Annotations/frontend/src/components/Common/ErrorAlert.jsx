import React from 'react';
import { Alert, AlertTitle, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

/**
 * Error alert component
 */
const ErrorAlert = ({ error, severity = 'error', title, onClose }) => {
  if (!error) return null;

  const errorMessage = typeof error === 'string' ? error : error.message || 'An error occurred';

  return (
    <Alert
      severity={severity}
      action={
        onClose && (
          <IconButton
            aria-label="close"
            color="inherit"
            size="small"
            onClick={onClose}
          >
            <CloseIcon fontSize="inherit" />
          </IconButton>
        )
      }
      sx={{ mb: 2 }}
    >
      {title && <AlertTitle>{title}</AlertTitle>}
      {errorMessage}
    </Alert>
  );
};

export default ErrorAlert;

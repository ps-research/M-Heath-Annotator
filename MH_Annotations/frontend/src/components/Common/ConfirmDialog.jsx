import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  TextField,
  Alert,
} from '@mui/material';

/**
 * Confirmation dialog component
 */
const ConfirmDialog = ({
  open,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  severity = 'warning',
  requireTextConfirmation = false,
  confirmationText = 'DELETE',
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isConfirmEnabled, setIsConfirmEnabled] = useState(!requireTextConfirmation);

  useEffect(() => {
    if (requireTextConfirmation) {
      setIsConfirmEnabled(inputValue === confirmationText);
    }
  }, [inputValue, confirmationText, requireTextConfirmation]);

  useEffect(() => {
    // Reset input when dialog opens/closes
    if (!open) {
      setInputValue('');
    }
  }, [open]);

  const handleConfirm = () => {
    if (requireTextConfirmation && inputValue !== confirmationText) {
      return;
    }
    onConfirm();
    setInputValue('');
  };

  const handleCancel = () => {
    setInputValue('');
    onCancel();
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && isConfirmEnabled) {
      handleConfirm();
    } else if (event.key === 'Escape') {
      handleCancel();
    }
  };

  const severityColorMap = {
    error: 'error',
    warning: 'warning',
    info: 'primary',
  };

  const buttonColor = severityColorMap[severity] || 'primary';

  return (
    <Dialog
      open={open}
      onClose={handleCancel}
      maxWidth="sm"
      fullWidth
      onKeyPress={handleKeyPress}
    >
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          {message}
        </DialogContentText>

        {requireTextConfirmation && (
          <>
            <Alert severity="warning" sx={{ mb: 2 }}>
              This action cannot be undone. Please type <strong>{confirmationText}</strong> to confirm.
            </Alert>
            <TextField
              autoFocus
              fullWidth
              label={`Type "${confirmationText}" to confirm`}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              error={inputValue.length > 0 && inputValue !== confirmationText}
              helperText={
                inputValue.length > 0 && inputValue !== confirmationText
                  ? `Must match "${confirmationText}" exactly`
                  : ''
              }
            />
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancel} color="inherit">
          {cancelText}
        </Button>
        <Button
          onClick={handleConfirm}
          color={buttonColor}
          variant="contained"
          disabled={!isConfirmEnabled}
        >
          {confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;

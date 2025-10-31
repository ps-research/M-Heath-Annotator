import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import { Save as SaveIcon } from '@mui/icons-material';

const SaveVersionDialog = ({
  open,
  onClose,
  onSave,
  saving,
  annotatorId,
  domain,
  nextVersionNumber,
}) => {
  const [versionName, setVersionName] = useState('');
  const [description, setDescription] = useState('');
  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    if (open) {
      // Reset form when dialog opens
      setVersionName('');
      setDescription('');
      setValidationError('');
    }
  }, [open]);

  const validateVersionName = (name) => {
    if (!name || name.trim().length === 0) {
      return 'Version name is required';
    }
    if (!/^[a-zA-Z0-9_]+$/.test(name)) {
      return 'Only letters, numbers, and underscores allowed';
    }
    if (name.length > 50) {
      return 'Version name too long (max 50 characters)';
    }
    return '';
  };

  const handleVersionNameChange = (e) => {
    const name = e.target.value;
    setVersionName(name);
    setValidationError(validateVersionName(name));
  };

  const handleDescriptionChange = (e) => {
    const desc = e.target.value;
    if (desc.length <= 500) {
      setDescription(desc);
    }
  };

  const generatePreviewFilename = () => {
    if (!versionName) return '';
    const sanitized = versionName.replace(/[^a-zA-Z0-9_]/g, '_').replace(/_+/g, '_');
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[T:]/g, '_').replace(/-/g, '_');
    return `v${nextVersionNumber}_${sanitized}_${timestamp}.txt`;
  };

  const handleSave = () => {
    const error = validateVersionName(versionName);
    if (error) {
      setValidationError(error);
      return;
    }
    onSave(versionName, description);
  };

  const isValid = versionName && !validationError;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Save Prompt Version</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 1 }}>
          <TextField
            autoFocus
            fullWidth
            label="Version Name"
            placeholder="e.g., crisis_enhanced_detection"
            value={versionName}
            onChange={handleVersionNameChange}
            error={!!validationError}
            helperText={validationError || 'Letters, numbers, and underscores only'}
            required
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="Description (Optional)"
            placeholder="e.g., Enhanced crisis detection with more specific level 4 indicators"
            value={description}
            onChange={handleDescriptionChange}
            multiline
            rows={3}
            helperText={`${description.length}/500 characters`}
            sx={{ mb: 2 }}
          />

          {versionName && !validationError && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Preview Filename:
              </Typography>
              <Alert severity="info" sx={{ wordBreak: 'break-all' }}>
                {generatePreviewFilename()}
              </Alert>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <LoadingButton
          onClick={handleSave}
          loading={saving}
          disabled={!isValid}
          loadingPosition="start"
          startIcon={<SaveIcon />}
          variant="contained"
        >
          Save
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default SaveVersionDialog;

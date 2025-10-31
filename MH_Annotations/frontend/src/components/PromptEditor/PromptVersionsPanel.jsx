import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Radio,
  RadioGroup,
  FormControlLabel,
  Button,
  IconButton,
  Stack,
  Divider,
  Chip,
  Skeleton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

const PromptVersionsPanel = ({
  annotatorId,
  domain,
  versions,
  activeFilename,
  onSelectVersion,
  onDeleteVersion,
  onPreviewVersion,
  loading,
  onRefresh,
}) => {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [versionToDelete, setVersionToDelete] = useState(null);

  const handleSelectVersion = (event) => {
    const filename = event.target.value === 'base' ? null : event.target.value;
    onSelectVersion(filename);
  };

  const handleDeleteClick = (version) => {
    if (version.is_active) {
      alert('Cannot delete the active version. Switch to another version first.');
      return;
    }
    setVersionToDelete(version);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (versionToDelete) {
      onDeleteVersion(versionToDelete.filename);
      setDeleteDialogOpen(false);
      setVersionToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setVersionToDelete(null);
  };

  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch (e) {
      return timestamp;
    }
  };

  const domainNames = {
    urgency: 'Urgency',
    therapeutic: 'Therapeutic',
    intensity: 'Intensity',
    adjunct: 'Adjunct',
    modality: 'Modality',
    redressal: 'Redressal',
  };

  if (loading) {
    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Typography variant="h6" gutterBottom>
          Saved Versions
        </Typography>
        <Stack spacing={2} sx={{ mt: 2 }}>
          <Skeleton variant="rectangular" height={80} />
          <Skeleton variant="rectangular" height={80} />
          <Skeleton variant="rectangular" height={80} />
        </Stack>
      </Paper>
    );
  }

  if (!versions) {
    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Typography variant="h6" gutterBottom>
          Saved Versions
        </Typography>
        <Alert severity="info" sx={{ mt: 2 }}>
          Select an annotator and domain to view versions
        </Alert>
      </Paper>
    );
  }

  const allVersions = [];

  // Add base version
  if (versions.base) {
    allVersions.push({
      ...versions.base,
      type: 'base',
    });
  }

  // Add saved versions
  if (versions.versions) {
    allVersions.push(
      ...versions.versions.map((v) => ({
        ...v,
        type: 'version',
      }))
    );
  }

  const totalVersions = versions.versions ? versions.versions.length + 1 : 1;

  return (
    <>
      <Paper sx={{ p: 2, height: '100%', overflow: 'auto' }}>
        <Stack spacing={2}>
          {/* Header */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Saved Versions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Annotator {annotatorId} › {domainNames[domain] || domain}
            </Typography>
          </Box>

          <Divider />

          {/* Radio group for versions */}
          <RadioGroup
            value={activeFilename === null ? 'base' : activeFilename}
            onChange={handleSelectVersion}
          >
            {allVersions.map((version) => {
              const isBase = version.type === 'base';
              const value = isBase ? 'base' : version.filename;
              const isActive = version.is_active;

              return (
                <Box
                  key={value}
                  sx={{
                    border: 2,
                    borderColor: isActive ? 'success.main' : 'divider',
                    borderRadius: 1,
                    p: 1.5,
                    mb: 1,
                    bgcolor: isActive ? 'success.light' : 'background.paper',
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: isActive ? 'success.light' : 'action.hover',
                    },
                  }}
                >
                  <Stack direction="row" alignItems="flex-start" spacing={1}>
                    <FormControlLabel
                      value={value}
                      control={<Radio />}
                      label={
                        <Box>
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <Typography variant="body1" fontWeight={isActive ? 600 : 400}>
                              {isBase ? 'Base Prompt (Default)' : version.display_name}
                            </Typography>
                            {isActive && (
                              <Chip label="Active" color="success" size="small" />
                            )}
                            {isBase && <Chip label="Default" color="info" size="small" />}
                          </Stack>
                          <Typography variant="caption" color="text.secondary">
                            {version.character_count?.toLocaleString()} characters
                          </Typography>
                          {!isBase && version.timestamp && (
                            <>
                              <br />
                              <Typography variant="caption" color="text.secondary">
                                Saved: {formatTimestamp(version.timestamp)}
                              </Typography>
                            </>
                          )}
                          {!isBase && version.last_modified && (
                            <>
                              <br />
                              <Typography variant="caption" color="text.secondary">
                                Modified: {formatTimestamp(version.last_modified)}
                              </Typography>
                            </>
                          )}
                          {!isBase && version.description && (
                            <>
                              <br />
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                fontStyle="italic"
                              >
                                "{version.description}"
                              </Typography>
                            </>
                          )}
                        </Box>
                      }
                      sx={{ flex: 1, m: 0 }}
                    />
                    <Stack direction="row" spacing={0.5}>
                      <IconButton
                        size="small"
                        onClick={() => onPreviewVersion(value)}
                        title="Preview"
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                      {!isBase && (
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteClick(version)}
                          title="Delete"
                          disabled={isActive}
                          color={isActive ? 'default' : 'error'}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      )}
                    </Stack>
                  </Stack>
                </Box>
              );
            })}
          </RadioGroup>

          <Divider />

          {/* Footer */}
          <Box>
            <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
              <InfoIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {totalVersions} version{totalVersions !== 1 ? 's' : ''} total
              </Typography>
            </Stack>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={onRefresh}
              size="small"
            >
              Refresh List
            </Button>
          </Box>
        </Stack>
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleCancelDelete}>
        <DialogTitle>Delete Version?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete version "{versionToDelete?.display_name}"?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete}>Cancel</Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default PromptVersionsPanel;

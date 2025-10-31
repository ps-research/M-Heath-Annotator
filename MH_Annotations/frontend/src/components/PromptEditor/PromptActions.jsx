import React, { useState } from 'react';
import {
  Stack,
  Button,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Box,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';

const SAMPLE_TEXTS = [
  "I've been feeling really down lately and can't seem to find motivation to do anything.",
  "I'm having trouble sleeping at night and my anxiety is getting worse.",
  "Sometimes I feel like nobody understands what I'm going through.",
  "I need help managing my stress levels, it's affecting my daily life.",
  "I've been having dark thoughts and I'm not sure who to talk to.",
];

const PromptActions = ({
  isOverride,
  hasChanges,
  isValid,
  saving,
  onSave,
  onResetToBase,
  promptContent,
}) => {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [sampleIndex] = useState(Math.floor(Math.random() * SAMPLE_TEXTS.length));

  const handlePreview = () => {
    setPreviewOpen(true);
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
  };

  const getRenderedPrompt = () => {
    return promptContent.replace('{text}', SAMPLE_TEXTS[sampleIndex]);
  };

  return (
    <>
      <Stack direction="row" spacing={2} justifyContent="flex-end" sx={{ mb: 2 }}>
        {isOverride && (
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={onResetToBase}
            disabled={saving}
          >
            Reset to Base
          </Button>
        )}

        <Button
          variant="outlined"
          startIcon={<VisibilityIcon />}
          onClick={handlePreview}
          disabled={!promptContent || !isValid}
        >
          Preview
        </Button>

        <Button
          variant="contained"
          startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
          onClick={onSave}
          disabled={!hasChanges || !isValid || saving}
        >
          Save Changes
        </Button>
      </Stack>

      {/* Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={handleClosePreview}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Prompt Preview</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Sample user message:
            </Typography>
            <Box
              sx={{
                p: 2,
                bgcolor: 'action.hover',
                borderRadius: 1,
                mb: 2,
              }}
            >
              <Typography variant="body2" fontStyle="italic">
                "{SAMPLE_TEXTS[sampleIndex]}"
              </Typography>
            </Box>
          </Box>

          <Typography variant="caption" color="text.secondary" gutterBottom>
            Rendered prompt with sample text:
          </Typography>
          <Box
            sx={{
              p: 2,
              bgcolor: 'background.paper',
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              maxHeight: '60vh',
              overflow: 'auto',
            }}
          >
            {getRenderedPrompt()}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePreview}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default PromptActions;

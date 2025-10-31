import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Paper,
} from '@mui/material';
import Editor from '@monaco-editor/react';

const PreviewDialog = ({ open, onClose, content, title, metadata }) => {
  const characterCount = content?.length || 0;
  const lineCount = content ? content.split('\n').length : 0;
  const wordCount = content ? content.trim().split(/\s+/).length : 0;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{title || 'Preview Prompt Version'}</DialogTitle>
      <DialogContent>
        <Box sx={{ height: '60vh', mb: 2 }}>
          <Editor
            height="100%"
            defaultLanguage="markdown"
            value={content || ''}
            theme="vs-dark"
            options={{
              readOnly: true,
              minimap: { enabled: false },
              lineNumbers: 'on',
              wordWrap: 'on',
              scrollBeyondLastLine: false,
              fontSize: 13,
              fontFamily: '"Fira Code", "Cascadia Code", Consolas, monospace',
            }}
          />
        </Box>

        <Paper sx={{ p: 2, bgcolor: 'grey.100' }} variant="outlined">
          <Typography variant="body2" color="text.secondary">
            {characterCount.toLocaleString()} characters | {lineCount.toLocaleString()} lines |{' '}
            {wordCount.toLocaleString()} words
          </Typography>
          {metadata && (
            <Box sx={{ mt: 1 }}>
              {metadata.version_number && (
                <Typography variant="body2" color="text.secondary">
                  Version: {metadata.version_number}
                </Typography>
              )}
              {metadata.timestamp && (
                <Typography variant="body2" color="text.secondary">
                  Saved: {metadata.timestamp}
                </Typography>
              )}
            </Box>
          )}
        </Paper>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PreviewDialog;

import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Box, Typography, Alert, Grid, Snackbar, Stack, Button } from '@mui/material';
import {
  fetchPrompts,
  fetchPrompt,
  updatePrompt,
  deletePrompt,
  savePromptVersion,
  fetchPromptVersions,
  setActiveVersion,
  deletePromptVersion,
  fetchVersionContent,
  selectPrompts,
  selectIsLoading,
  selectErrors,
  selectPromptVersions,
  selectActiveVersionFilename,
  selectPromptVersionsLoading,
  selectSavingVersion,
} from '../../store/slices/configSlice';
import { LoadingSpinner } from '../Common';
import PromptSelector from './PromptSelector';
import PromptMonacoEditor from './PromptMonacoEditor';
import PromptMetadata from './PromptMetadata';
import PromptActions from './PromptActions';
import PromptVersionsPanel from './PromptVersionsPanel';
import SaveVersionDialog from './SaveVersionDialog';
import PreviewDialog from './PreviewDialog';

const PromptEditorPanel = () => {
  const dispatch = useDispatch();
  const prompts = useSelector(selectPrompts);
  const loading = useSelector(selectIsLoading);
  const errors = useSelector(selectErrors);

  const [selectedAnnotator, setSelectedAnnotator] = useState(1);
  const [selectedDomain, setSelectedDomain] = useState('urgency');
  const [currentPrompt, setCurrentPrompt] = useState('');
  const [originalPrompt, setOriginalPrompt] = useState('');
  const [isOverride, setIsOverride] = useState(false);
  const [lastModified, setLastModified] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);

  // Version management state
  const [currentVersions, setCurrentVersions] = useState(null);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [previewTitle, setPreviewTitle] = useState('');
  const [previewMetadata, setPreviewMetadata] = useState(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Version selectors
  const versionsLoading = useSelector(selectPromptVersionsLoading);
  const savingVersion = useSelector(selectSavingVersion);
  const activeVersionFilename = useSelector((state) =>
    selectActiveVersionFilename(selectedAnnotator, selectedDomain)(state)
  );

  // Auto-save draft key
  const getDraftKey = () =>
    `prompt_draft_${selectedAnnotator}_${selectedDomain}`;

  // Load all prompts on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        await dispatch(fetchPrompts()).unwrap();
        setInitialLoadComplete(true);
      } catch (error) {
        setInitialLoadComplete(true);
      }
    };

    loadData();
  }, [dispatch]);

  // Load specific prompt when selection changes
  useEffect(() => {
    const loadPrompt = async () => {
      try {
        const result = await dispatch(
          fetchPrompt({ annotatorId: selectedAnnotator, domain: selectedDomain })
        ).unwrap();

        const promptContent = result.content || '';
        setCurrentPrompt(promptContent);
        setOriginalPrompt(promptContent);
        setIsOverride(result.is_override || false);
        setLastModified(result.last_modified || null);

        // Try to restore draft from localStorage
        const draftKey = getDraftKey();
        const savedDraft = localStorage.getItem(draftKey);
        if (savedDraft && savedDraft !== promptContent) {
          // Ask user if they want to restore draft
          if (
            window.confirm(
              'Found an unsaved draft for this prompt. Do you want to restore it?'
            )
          ) {
            setCurrentPrompt(savedDraft);
          } else {
            localStorage.removeItem(draftKey);
          }
        }
      } catch (error) {
        // Error handled by Redux state
      }
    };

    if (initialLoadComplete) {
      loadPrompt();
    }
  }, [selectedAnnotator, selectedDomain, dispatch, initialLoadComplete]);

  // Check for unsaved changes
  useEffect(() => {
    setHasChanges(currentPrompt !== originalPrompt);
  }, [currentPrompt, originalPrompt]);

  // Auto-save to localStorage every 30 seconds
  useEffect(() => {
    if (hasChanges) {
      const autoSaveInterval = setInterval(() => {
        const draftKey = getDraftKey();
        localStorage.setItem(draftKey, currentPrompt);
      }, 30000); // 30 seconds

      return () => clearInterval(autoSaveInterval);
    }
  }, [currentPrompt, hasChanges]);

  // Warn before navigating away with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasChanges]);

  // Load versions when annotator/domain changes
  useEffect(() => {
    const loadVersions = async () => {
      if (initialLoadComplete && selectedAnnotator && selectedDomain) {
        try {
          const result = await dispatch(
            fetchPromptVersions({
              annotatorId: selectedAnnotator,
              domain: selectedDomain,
            })
          ).unwrap();
          setCurrentVersions(result);
        } catch (error) {
          console.error('Failed to load versions:', error);
        }
      }
    };

    loadVersions();
  }, [selectedAnnotator, selectedDomain, dispatch, initialLoadComplete]);

  // Version Management Handlers
  const handleOpenSaveDialog = () => {
    setSaveDialogOpen(true);
  };

  const handleSaveVersion = async (versionName, description) => {
    try {
      await dispatch(
        savePromptVersion({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
          versionName,
          content: currentPrompt,
          description,
        })
      ).unwrap();

      // Refresh versions list
      const result = await dispatch(
        fetchPromptVersions({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
        })
      ).unwrap();

      setCurrentVersions(result);
      setSaveDialogOpen(false);

      // Update original prompt to reflect saved state
      setOriginalPrompt(currentPrompt);

      // Show success message
      setSnackbarMessage('Version saved successfully!');
      setSnackbarOpen(true);
    } catch (error) {
      alert(`Failed to save version: ${error}`);
    }
  };

  const handleSelectVersion = async (filename) => {
    if (
      hasChanges &&
      !window.confirm('Switch to this version? Any unsaved changes will be lost.')
    ) {
      return;
    }

    try {
      await dispatch(
        setActiveVersion({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
          filename: filename,
        })
      ).unwrap();

      // Reload prompt content
      const result = await dispatch(
        fetchPrompt({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
        })
      ).unwrap();

      setCurrentPrompt(result.content);
      setOriginalPrompt(result.content);
      setIsOverride(result.is_override || false);
      setLastModified(result.last_modified);

      // Refresh versions list
      const versionsResult = await dispatch(
        fetchPromptVersions({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
        })
      ).unwrap();

      setCurrentVersions(versionsResult);

      // Show success message
      setSnackbarMessage('Active version switched successfully!');
      setSnackbarOpen(true);
    } catch (error) {
      alert(`Failed to switch version: ${error}`);
    }
  };

  const handleDeleteVersion = async (filename) => {
    try {
      await dispatch(
        deletePromptVersion({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
          filename,
        })
      ).unwrap();

      // Refresh versions list
      const result = await dispatch(
        fetchPromptVersions({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
        })
      ).unwrap();

      setCurrentVersions(result);

      // Show success message
      setSnackbarMessage('Version deleted successfully!');
      setSnackbarOpen(true);
    } catch (error) {
      alert(`Failed to delete version: ${error}`);
    }
  };

  const handlePreviewVersion = async (filename) => {
    try {
      if (filename === 'base') {
        // Load base prompt
        const result = await dispatch(
          fetchPrompt({
            annotatorId: selectedAnnotator,
            domain: selectedDomain,
          })
        ).unwrap();
        setPreviewContent(result.content);
        setPreviewTitle('Base Prompt (Default)');
        setPreviewMetadata(null);
      } else {
        // Load version content
        const result = await dispatch(
          fetchVersionContent({
            annotatorId: selectedAnnotator,
            domain: selectedDomain,
            filename,
          })
        ).unwrap();
        setPreviewContent(result.content);
        setPreviewTitle(`Version: ${result.metadata?.version_name || filename}`);
        setPreviewMetadata(result.metadata);
      }

      setPreviewDialogOpen(true);
    } catch (error) {
      alert(`Failed to load version content: ${error}`);
    }
  };

  const handleRefreshVersions = async () => {
    try {
      const result = await dispatch(
        fetchPromptVersions({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
        })
      ).unwrap();

      setCurrentVersions(result);
      setSnackbarMessage('Versions refreshed!');
      setSnackbarOpen(true);
    } catch (error) {
      alert(`Failed to refresh versions: ${error}`);
    }
  };

  const handleAnnotatorChange = (annotatorId) => {
    if (hasChanges) {
      if (!window.confirm('You have unsaved changes. Continue?')) {
        return;
      }
    }
    setSelectedAnnotator(annotatorId);
  };

  const handleDomainChange = (domain) => {
    if (hasChanges) {
      if (!window.confirm('You have unsaved changes. Continue?')) {
        return;
      }
    }
    setSelectedDomain(domain);
  };

  const handleEditorChange = (newValue) => {
    setCurrentPrompt(newValue || '');
  };

  const handleSave = async () => {
    try {
      await dispatch(
        updatePrompt({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
          content: currentPrompt,
        })
      ).unwrap();

      // Clear draft from localStorage
      const draftKey = getDraftKey();
      localStorage.removeItem(draftKey);

      // Update original prompt to reflect saved state
      setOriginalPrompt(currentPrompt);
      setIsOverride(true);

      // Refresh prompt metadata
      await dispatch(
        fetchPrompt({ annotatorId: selectedAnnotator, domain: selectedDomain })
      );
    } catch (error) {
      // Error handled by Redux state
    }
  };

  const handleResetToBase = async () => {
    if (
      !window.confirm(
        'This will delete the custom override and revert to the base prompt. Continue?'
      )
    ) {
      return;
    }

    try {
      await dispatch(
        deletePrompt({
          annotatorId: selectedAnnotator,
          domain: selectedDomain,
        })
      ).unwrap();

      // Clear draft from localStorage
      const draftKey = getDraftKey();
      localStorage.removeItem(draftKey);

      // Reload the base prompt
      const result = await dispatch(
        fetchPrompt({ annotatorId: selectedAnnotator, domain: selectedDomain })
      ).unwrap();

      const promptContent = result.content || '';
      setCurrentPrompt(promptContent);
      setOriginalPrompt(promptContent);
      setIsOverride(false);
      setLastModified(null);
    } catch (error) {
      // Error handled by Redux state
    }
  };

  const isValid = currentPrompt && currentPrompt.includes('{text}');

  if (!initialLoadComplete && loading.prompts) {
    return <LoadingSpinner message="Loading prompts..." />;
  }

  const nextVersionNumber = currentVersions?.versions
    ? currentVersions.versions.length + 1
    : 1;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Prompt Editor
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Edit and customize prompts for each annotator-domain combination. Save versions to track changes over time.
      </Typography>

      {errors.prompts && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errors.prompts}
        </Alert>
      )}

      {errors.promptVersions && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errors.promptVersions}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Left Panel - Editor */}
        <Grid item xs={12} md={8}>
          <Stack spacing={2}>
            <PromptSelector
              selectedAnnotator={selectedAnnotator}
              selectedDomain={selectedDomain}
              onAnnotatorChange={handleAnnotatorChange}
              onDomainChange={handleDomainChange}
              isOverride={isOverride}
              lastModified={lastModified}
              loading={loading.prompts}
            />

            <PromptMonacoEditor
              value={currentPrompt}
              onChange={handleEditorChange}
              readOnly={loading.saving || savingVersion}
            />

            <PromptMetadata content={currentPrompt} />

            <Box>
              <Button
                variant="contained"
                color="primary"
                disabled={!hasChanges || !isValid || savingVersion}
                onClick={handleOpenSaveDialog}
                fullWidth
              >
                💾 Save As New Version
              </Button>
            </Box>

            {hasChanges && (
              <Alert severity="warning">
                You have unsaved changes. Save as a new version to preserve your work!
              </Alert>
            )}
          </Stack>
        </Grid>

        {/* Right Panel - Versions */}
        <Grid item xs={12} md={4}>
          <PromptVersionsPanel
            annotatorId={selectedAnnotator}
            domain={selectedDomain}
            versions={currentVersions}
            activeFilename={activeVersionFilename}
            onSelectVersion={handleSelectVersion}
            onDeleteVersion={handleDeleteVersion}
            onPreviewVersion={handlePreviewVersion}
            loading={versionsLoading}
            onRefresh={handleRefreshVersions}
          />
        </Grid>
      </Grid>

      {/* Save Version Dialog */}
      <SaveVersionDialog
        open={saveDialogOpen}
        onClose={() => setSaveDialogOpen(false)}
        onSave={handleSaveVersion}
        saving={savingVersion}
        annotatorId={selectedAnnotator}
        domain={selectedDomain}
        nextVersionNumber={nextVersionNumber}
      />

      {/* Preview Dialog */}
      <PreviewDialog
        open={previewDialogOpen}
        onClose={() => setPreviewDialogOpen(false)}
        content={previewContent}
        title={previewTitle}
        metadata={previewMetadata}
      />

      {/* Success Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default PromptEditorPanel;

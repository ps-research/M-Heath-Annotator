import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Box, Typography, Alert } from '@mui/material';
import {
  fetchPrompts,
  fetchPrompt,
  updatePrompt,
  deletePrompt,
  selectPrompts,
  selectIsLoading,
  selectErrors,
} from '../../store/slices/configSlice';
import { LoadingSpinner } from '../Common';
import PromptSelector from './PromptSelector';
import PromptMonacoEditor from './PromptMonacoEditor';
import PromptMetadata from './PromptMetadata';
import PromptActions from './PromptActions';

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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Prompt Editor
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Edit and customize prompts for each annotator-domain combination
      </Typography>

      {errors.prompts && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errors.prompts}
        </Alert>
      )}

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
        readOnly={loading.saving}
      />

      <PromptMetadata content={currentPrompt} />

      <PromptActions
        isOverride={isOverride}
        hasChanges={hasChanges}
        isValid={isValid}
        saving={loading.saving}
        onSave={handleSave}
        onResetToBase={handleResetToBase}
        promptContent={currentPrompt}
      />

      {hasChanges && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          You have unsaved changes. Don't forget to save!
        </Alert>
      )}
    </Box>
  );
};

export default PromptEditorPanel;

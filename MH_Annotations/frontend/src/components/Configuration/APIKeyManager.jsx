import React, { useState, useEffect, useRef} from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Card,
  CardContent,
  Typography,
  TextField,
  IconButton,
  Button,
  Chip,
  CircularProgress,
  Tooltip,
  Stack,
  Box,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  CheckCircle,
  Error as ErrorIcon,
  Save as SaveIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import {
  fetchAPIKeys,
  updateAPIKey,
  selectAPIKeys,
  selectIsLoading,
  selectErrors,
} from '../../store/slices/configSlice';
import { ANNOTATOR_IDS } from '../../utils/constants';

const APIKeyManager = () => {
  const dispatch = useDispatch();
  const apiKeys = useSelector(selectAPIKeys);
  const loading = useSelector(selectIsLoading);
  const errors = useSelector(selectErrors);

  // Local state for each key input
  const [localKeys, setLocalKeys] = useState({});
  const [visibility, setVisibility] = useState({});
  const [validation, setValidation] = useState({});
  const [testing, setTesting] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  // Add this new ref to track initial load
  const initialLoadDone = useRef(false);
  
  // Load API keys from backend on mount (only once)
  useEffect(() => {
    const loadKeys = async () => {
      await dispatch(fetchAPIKeys()).unwrap();
      initialLoadDone.current = true;
    };
    
    if (!initialLoadDone.current) {
      loadKeys();
    }
  }, [dispatch]);

  // Initialize local state ONLY on first load from Redux
  useEffect(() => {
    // Only sync from Redux if this is the initial load
    if (initialLoadDone.current && Object.keys(localKeys).length === 0) {
      const newLocalKeys = {};
      ANNOTATOR_IDS.forEach((id) => {
        const key = apiKeys[`annotator_${id}`] || '';
        newLocalKeys[id] = key;
      });
      setLocalKeys(newLocalKeys);
    }
  }, [apiKeys, localKeys]);

  // Check for unsaved changes
  useEffect(() => {
    const changed = ANNOTATOR_IDS.some((id) => {
      const reduxKey = apiKeys[`annotator_${id}`] || '';
      const localKey = localKeys[id] || '';
      return reduxKey !== localKey;
    });
    setHasChanges(changed);
  }, [localKeys, apiKeys]);

  const handleKeyChange = (annotatorId, value) => {
    setLocalKeys((prev) => ({
      ...prev,
      [annotatorId]: value,
    }));

    // Real-time validation
    validateKey(annotatorId, value);
  };

  const validateKey = (annotatorId, value) => {
    if (!value || value.length < 20) {
      setValidation((prev) => ({
        ...prev,
        [annotatorId]: {
          valid: false,
          message: value.length === 0 ? 'API key cannot be empty' : 'API key must be at least 20 characters',
        },
      }));
      return false;
    }

    setValidation((prev) => ({
      ...prev,
      [annotatorId]: { valid: true, message: '' },
    }));
    return true;
  };

  const toggleVisibility = (annotatorId) => {
    setVisibility((prev) => ({
      ...prev,
      [annotatorId]: !prev[annotatorId],
    }));
  };

  const testAPIKey = async (annotatorId) => {
    const key = localKeys[annotatorId];
    if (!key || key.length < 20) {
      setValidation((prev) => ({
        ...prev,
        [annotatorId]: { valid: false, message: 'Invalid API key format' },
      }));
      return;
    }

    setTesting((prev) => ({ ...prev, [annotatorId]: true }));

    // Simulate API test - in production, this would call a backend endpoint
    // that tests the key against Google Gemini API
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // For now, we just validate format
      // In production: await configAPI.testAPIKey(annotatorId, key);
      setValidation((prev) => ({
        ...prev,
        [annotatorId]: { valid: true, message: 'API key format valid' },
      }));
    } catch (error) {
      setValidation((prev) => ({
        ...prev,
        [annotatorId]: { valid: false, message: error.message || 'Test failed' },
      }));
    } finally {
      setTesting((prev) => ({ ...prev, [annotatorId]: false }));
    }
  };

  const handleSaveAll = async () => {
    // Validate all keys first
    let allValid = true;
    ANNOTATOR_IDS.forEach((id) => {
      if (localKeys[id] && !validateKey(id, localKeys[id])) {
        allValid = false;
      }
    });

    if (!allValid) {
      return;
    }

    // Save only changed keys
    const promises = [];
    ANNOTATOR_IDS.forEach((id) => {
      const reduxKey = apiKeys[`annotator_${id}`] || '';
      const localKey = localKeys[id] || '';
      if (reduxKey !== localKey && localKey) {
        promises.push(
          dispatch(updateAPIKey({ annotatorId: id, apiKey: localKey }))
        );
      }
    });

    try {
      await Promise.all(promises);
      // Success - keep local keys as-is (don't reload from backend)
      // This preserves the full unmasked keys in local state
      setHasChanges(false);
    } catch (error) {
      // Error is handled by Redux error state
    }
  };
  const handleDeleteKey = async (annotatorId) => {
    if (!window.confirm(`Delete API key for Annotator ${annotatorId}?`)) {
      return;
    }

    try {
      // Update with empty key to delete
      await dispatch(updateAPIKey({ annotatorId, apiKey: '' })).unwrap();
      
      // Clear from local state
      setLocalKeys((prev) => ({
        ...prev,
        [annotatorId]: '',
      }));
      
      // Clear validation
      setValidation((prev) => ({
        ...prev,
        [annotatorId]: null,
      }));
    } catch (error) {
      // Error is handled by Redux error state
    }
  };

  const maskKey = (key) => {
    if (!key || key.length < 12) return key;
    return `${key.substring(0, 8)}...${key.substring(key.length - 4)}`;
  };

  const anyInvalid = ANNOTATOR_IDS.some(
    (id) => localKeys[id] && validation[id] && !validation[id].valid
  );

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          API Key Management
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Configure Google Gemini API keys for each annotator
        </Typography>

        <Stack spacing={2}>
          {ANNOTATOR_IDS.map((id) => (
            <Box key={id}>
              <Typography variant="subtitle2" gutterBottom>
                Annotator {id}
              </Typography>



              <Stack direction="row" spacing={1} alignItems="center">
                <TextField
                  fullWidth
                  size="small"
                  type={visibility[id] ? 'text' : 'password'}
                  value={localKeys[id] || ''}
                  onChange={(e) => handleKeyChange(id, e.target.value)}
                  placeholder={`Enter API key for Annotator ${id}`}
                  error={validation[id] && !validation[id].valid}
                  helperText={validation[id]?.message || ''}
                  autoComplete="new-password"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                />
                <Tooltip title={visibility[id] ? 'Hide' : 'Show'}>
                  <IconButton
                    size="small"
                    onClick={() => toggleVisibility(id)}
                    disabled={!localKeys[id]}
                  >
                    {visibility[id] ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete Key">
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteKey(id)}
                    disabled={!localKeys[id]}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => testAPIKey(id)}
                  disabled={!localKeys[id] || testing[id]}
                  startIcon={
                    testing[id] ? (
                      <CircularProgress size={16} />
                    ) : null
                  }
                >
                  Test
                </Button>
                {validation[id] && (
                  <Chip
                    size="small"
                    icon={
                      validation[id].valid ? (
                        <CheckCircle />
                      ) : (
                        <ErrorIcon />
                      )
                    }
                    label={validation[id].valid ? 'Valid' : 'Invalid'}
                    color={validation[id].valid ? 'success' : 'error'}
                  />
                )}
              </Stack>
            </Box>
          ))}
        </Stack>

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={
              loading.saving ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />
            }
            onClick={handleSaveAll}
            disabled={!hasChanges || anyInvalid || loading.saving}
          >
            Save All Changes
          </Button>
        </Box>

        {errors.apiKeys && (
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            Error: {errors.apiKeys}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default APIKeyManager;

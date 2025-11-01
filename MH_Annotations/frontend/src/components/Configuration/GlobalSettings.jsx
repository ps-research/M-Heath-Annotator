import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Card,
  CardContent,
  Typography,
  Select,
  MenuItem,
  Slider,
  Button,
  Stack,
  Box,
  FormControl,
  InputLabel,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import {
  fetchSettings,
  updateSettings,
  selectGlobalSettings,
  selectIsLoading,
  selectErrors,
} from '../../store/slices/configSlice';
import { MODEL_OPTIONS } from '../../utils/constants';

const DEFAULT_SETTINGS = {
  model_name: 'gemma-3-27b-it',
  request_delay_seconds: 1,
  max_retries: 3,
  crash_detection_minutes: 5,
  control_check_iterations: 5,
  control_check_seconds: 10,
};

const MODEL_DESCRIPTIONS = {
  'gemma-3-27b-it': 'Gemma 3 27B IT - Instruction-tuned model for annotation tasks',
};

const GlobalSettings = () => {
  const dispatch = useDispatch();
  const globalSettings = useSelector(selectGlobalSettings);
  const loading = useSelector(selectIsLoading);
  const errors = useSelector(selectErrors);

  const [localSettings, setLocalSettings] = useState(DEFAULT_SETTINGS);
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize local state when Redux state changes
  useEffect(() => {
    if (globalSettings) {
      setLocalSettings(globalSettings);
    }
  }, [globalSettings]);

  // Check for unsaved changes
  useEffect(() => {
    // Guard clause: don't check changes if globalSettings hasn't loaded yet
    if (!globalSettings) {
      return;
    }
    const changed = Object.keys(localSettings).some(
      (key) => localSettings[key] !== globalSettings[key]
    );
    setHasChanges(changed);
  }, [localSettings, globalSettings]);

  const handleChange = (field, value) => {
    setLocalSettings((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleResetToDefaults = () => {
    if (window.confirm('Reset all settings to default values?')) {
      setLocalSettings(DEFAULT_SETTINGS);
    }
  };

  const handleSave = async () => {
    try {
      // Send flat object with individual fields, not wrapped in { global: ... }
      await dispatch(updateSettings(localSettings)).unwrap();
    } catch (error) {
      // Error handled by Redux state
    }
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Global Settings
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Configure system-wide parameters for all annotators
        </Typography>

        <Stack spacing={3}>
          {/* Model Name Selector */}
          <FormControl fullWidth>
            <InputLabel id="model-select-label">Model Name</InputLabel>
            <Select
              labelId="model-select-label"
              value={localSettings.model_name}
              onChange={(e) => handleChange('model_name', e.target.value)}
              label="Model Name"
            >
              {MODEL_OPTIONS.map((model) => (
                <MenuItem key={model} value={model}>
                  <Box>
                    <Typography variant="body1">{model}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {MODEL_DESCRIPTIONS[model]}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Request Delay Slider */}
          <Box>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <Typography variant="body2">Request Delay (seconds)</Typography>
              <Tooltip title="Delay between API requests to avoid rate limits">
                <Typography variant="caption" color="text.secondary" sx={{ cursor: 'help' }}>
                  ⓘ
                </Typography>
              </Tooltip>
            </Stack>
            <Stack direction="row" spacing={2} alignItems="center">
              <Slider
                value={localSettings.request_delay_seconds}
                onChange={(e, value) => handleChange('request_delay_seconds', value)}
                min={0}
                max={60}
                step={0.1}
                marks={[
                  { value: 0, label: '0' },
                  { value: 15, label: '15' },
                  { value: 30, label: '30' },
                  { value: 45, label: '45' },
                  { value: 60, label: '60' },
                ]}
                valueLabelDisplay="auto"
              />
              <Typography variant="body2" sx={{ minWidth: 40 }}>
                {localSettings.request_delay_seconds}s
              </Typography>
            </Stack>
          </Box>

          {/* Max Retries Slider */}
          <Box>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <Typography variant="body2">Max Retries</Typography>
              <Tooltip title="Number of retry attempts for failed requests">
                <Typography variant="caption" color="text.secondary" sx={{ cursor: 'help' }}>
                  ⓘ
                </Typography>
              </Tooltip>
            </Stack>
            <Stack direction="row" spacing={2} alignItems="center">
              <Slider
                value={localSettings.max_retries}
                onChange={(e, value) => handleChange('max_retries', value)}
                min={0}
                max={10}
                step={1}
                marks={[
                  { value: 0, label: '0' },
                  { value: 3, label: '3' },
                  { value: 5, label: '5' },
                  { value: 10, label: '10' },
                ]}
                valueLabelDisplay="auto"
              />
              <Typography variant="body2" sx={{ minWidth: 40 }}>
                {localSettings.max_retries}
              </Typography>
            </Stack>
          </Box>

          {/* Crash Detection Slider */}
          <Box>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <Typography variant="body2">Crash Detection (minutes)</Typography>
              <Tooltip title="Minutes of inactivity before marking worker as crashed">
                <Typography variant="caption" color="text.secondary" sx={{ cursor: 'help' }}>
                  ⓘ
                </Typography>
              </Tooltip>
            </Stack>
            <Stack direction="row" spacing={2} alignItems="center">
              <Slider
                value={localSettings.crash_detection_minutes}
                onChange={(e, value) => handleChange('crash_detection_minutes', value)}
                min={1}
                max={60}
                step={1}
                marks={[
                  { value: 1, label: '1' },
                  { value: 15, label: '15' },
                  { value: 30, label: '30' },
                  { value: 60, label: '60' },
                ]}
                valueLabelDisplay="auto"
              />
              <Typography variant="body2" sx={{ minWidth: 40 }}>
                {localSettings.crash_detection_minutes}m
              </Typography>
            </Stack>
          </Box>

          {/* Control Check Iterations Slider */}
          <Box>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <Typography variant="body2">Control Check Iterations</Typography>
              <Tooltip title="Number of control samples to check">
                <Typography variant="caption" color="text.secondary" sx={{ cursor: 'help' }}>
                  ⓘ
                </Typography>
              </Tooltip>
            </Stack>
            <Stack direction="row" spacing={2} alignItems="center">
              <Slider
                value={localSettings.control_check_iterations}
                onChange={(e, value) => handleChange('control_check_iterations', value)}
                min={1}
                max={20}
                step={1}
                marks={[
                  { value: 1, label: '1' },
                  { value: 5, label: '5' },
                  { value: 10, label: '10' },
                  { value: 20, label: '20' },
                ]}
                valueLabelDisplay="auto"
              />
              <Typography variant="body2" sx={{ minWidth: 40 }}>
                {localSettings.control_check_iterations}
              </Typography>
            </Stack>
          </Box>

          {/* Control Check Seconds Slider */}
          <Box>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <Typography variant="body2">Control Check Seconds</Typography>
              <Tooltip title="Seconds between control checks">
                <Typography variant="caption" color="text.secondary" sx={{ cursor: 'help' }}>
                  ⓘ
                </Typography>
              </Tooltip>
            </Stack>
            <Stack direction="row" spacing={2} alignItems="center">
              <Slider
                value={localSettings.control_check_seconds}
                onChange={(e, value) => handleChange('control_check_seconds', value)}
                min={1}
                max={60}
                step={1}
                marks={[
                  { value: 1, label: '1' },
                  { value: 10, label: '10' },
                  { value: 30, label: '30' },
                  { value: 60, label: '60' },
                ]}
                valueLabelDisplay="auto"
              />
              <Typography variant="body2" sx={{ minWidth: 40 }}>
                {localSettings.control_check_seconds}s
              </Typography>
            </Stack>
          </Box>
        </Stack>

        {/* Action Buttons */}
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleResetToDefaults}
            disabled={loading.saving}
          >
            Reset to Defaults
          </Button>
          <Button
            variant="contained"
            startIcon={
              loading.saving ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />
            }
            onClick={handleSave}
            disabled={!hasChanges || loading.saving}
          >
            Save Settings
          </Button>
        </Box>

        {errors.settings && (
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            Error: {errors.settings}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default GlobalSettings;

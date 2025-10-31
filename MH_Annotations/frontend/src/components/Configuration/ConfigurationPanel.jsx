import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Box, Typography, Paper, Button } from '@mui/material';
import {
  fetchSettings,
  fetchAPIKeys,
  selectSettings,
  selectAPIKeys,
  selectIsLoading,
} from '../../store/slices/configSlice';
import { LoadingSpinner } from '../Common';

const ConfigurationPanel = () => {
  const dispatch = useDispatch();
  const settings = useSelector(selectSettings);
  const apiKeys = useSelector(selectAPIKeys);
  const loading = useSelector(selectIsLoading);

  useEffect(() => {
    dispatch(fetchSettings());
    dispatch(fetchAPIKeys());
  }, [dispatch]);

  if (loading.settings) {
    return <LoadingSpinner message="Loading configuration..." />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Configuration
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Global Settings
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Model: {settings.global?.model_name || 'N/A'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Request Delay: {settings.global?.request_delay_seconds || 0} seconds
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Max Retries: {settings.global?.max_retries || 0}
        </Typography>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          API Keys
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {Object.keys(apiKeys).length} API keys configured
        </Typography>
      </Paper>
    </Box>
  );
};

export default ConfigurationPanel;

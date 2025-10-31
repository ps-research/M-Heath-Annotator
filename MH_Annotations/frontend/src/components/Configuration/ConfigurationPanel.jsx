import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Box, Typography, Button, Stack } from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import {
  fetchSettings,
  fetchAPIKeys,
  selectIsLoading,
} from '../../store/slices/configSlice';
import { LoadingSpinner, ErrorAlert } from '../Common';
import APIKeyManager from './APIKeyManager';
import GlobalSettings from './GlobalSettings';
import SampleLimitSliders from './SampleLimitSliders';

const ConfigurationPanel = () => {
  const dispatch = useDispatch();
  const loading = useSelector(selectIsLoading);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        await Promise.all([
          dispatch(fetchSettings()),
          dispatch(fetchAPIKeys()),
        ]);
        setInitialLoadComplete(true);
      } catch (error) {
        setInitialLoadComplete(true);
      }
    };

    loadData();
  }, [dispatch]);

  // Show loading spinner on initial load
  if (!initialLoadComplete && loading.settings) {
    return <LoadingSpinner message="Loading configuration..." />;
  }

  return (
    <Box>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 3 }}
      >
        <Typography variant="h4">Configuration</Typography>
      </Stack>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Manage API keys, sample limits, and global system settings
      </Typography>

      {/* API Key Management */}
      <APIKeyManager />

      {/* Sample Limit Configuration */}
      <SampleLimitSliders />

      {/* Global Settings */}
      <GlobalSettings />
    </Box>
  );
};

export default ConfigurationPanel;

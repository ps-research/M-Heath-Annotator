import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Box, Typography, Paper, Alert } from '@mui/material';
import {
  fetchHealth,
  selectHealth,
  selectIsLoading,
} from '../../store/slices/monitoringSlice';
import { LoadingSpinner } from '../Common';

const CrashMonitorPanel = () => {
  const dispatch = useDispatch();
  const health = useSelector(selectHealth);
  const loading = useSelector(selectIsLoading);

  useEffect(() => {
    dispatch(fetchHealth());

    const interval = setInterval(() => {
      dispatch(fetchHealth());
    }, 10000);

    return () => clearInterval(interval);
  }, [dispatch]);

  if (loading.health) {
    return <LoadingSpinner message="Loading health data..." />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Crash Monitor & System Health
      </Typography>

      {health.crashed?.length > 0 ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          {health.crashed.length} crashed worker(s) detected!
        </Alert>
      ) : (
        <Alert severity="success" sx={{ mb: 3 }}>
          All systems operational
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Crashed Workers
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {health.crashed?.length || 0} crashed workers
        </Typography>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Stalled Workers
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {health.stalled?.length || 0} stalled workers
        </Typography>
      </Paper>
    </Box>
  );
};

export default CrashMonitorPanel;

import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Box, Typography, Paper, Button, Stack } from '@mui/material';
import { PlayArrow, Stop, Pause } from '@mui/icons-material';
import {
  fetchWorkers,
  startAll,
  stopAll,
  pauseAll,
  selectAllWorkers,
  selectIsLoading,
} from '../../store/slices/workersSlice';
import { LoadingSpinner } from '../Common';

const ControlCenterPanel = () => {
  const dispatch = useDispatch();
  const workers = useSelector(selectAllWorkers);
  const loading = useSelector(selectIsLoading);

  useEffect(() => {
    dispatch(fetchWorkers());
  }, [dispatch]);

  const handleStartAll = () => {
    dispatch(startAll());
  };

  const handleStopAll = () => {
    dispatch(stopAll());
  };

  const handlePauseAll = () => {
    dispatch(pauseAll());
  };

  if (loading.fetch) {
    return <LoadingSpinner message="Loading workers..." />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Control Center
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Master Controls
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            color="success"
            startIcon={<PlayArrow />}
            onClick={handleStartAll}
            disabled={loading.start}
          >
            Start All
          </Button>
          <Button
            variant="contained"
            color="warning"
            startIcon={<Pause />}
            onClick={handlePauseAll}
            disabled={loading.pause}
          >
            Pause All
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={<Stop />}
            onClick={handleStopAll}
            disabled={loading.stop}
          >
            Stop All
          </Button>
        </Stack>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Workers
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {workers.length} workers configured
        </Typography>
      </Paper>
    </Box>
  );
};

export default ControlCenterPanel;

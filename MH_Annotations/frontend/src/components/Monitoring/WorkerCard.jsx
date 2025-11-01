import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Stack,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Visibility as EyeIcon,
  Stop as StopIcon,
} from '@mui/icons-material';
import { controlAPI } from '../../services/api';

const WorkerCard = ({ worker, onViewAnnotations }) => {
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handlePause = async () => {
    try {
      setLoading(true);
      await controlAPI.pauseWorker(worker.annotator_id, worker.domain);
      showSnackbar('Worker paused', 'success');
    } catch (error) {
      showSnackbar('Failed to pause worker: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async () => {
    try {
      setLoading(true);
      await controlAPI.resumeWorker(worker.annotator_id, worker.domain);
      showSnackbar('Worker resumed', 'success');
    } catch (error) {
      showSnackbar('Failed to resume worker: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      setLoading(true);
      await controlAPI.stopWorker(worker.annotator_id, worker.domain);
      showSnackbar('Worker stopped', 'success');
    } catch (error) {
      showSnackbar('Failed to stop worker: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Calculate progress percentage
  const progress = worker.progress || {};
  const completed = progress.completed || 0;
  const target = progress.target || 0;
  const percentage = target > 0 ? (completed / target) * 100 : 0;

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'paused':
        return 'warning';
      case 'completed':
        return 'info';
      case 'crashed':
        return 'error';
      case 'stopped':
        return 'default';
      default:
        return 'default';
    }
  };

  // Format domain name
  const formatDomain = (domain) => {
    return domain.charAt(0).toUpperCase() + domain.slice(1);
  };

  return (
    <>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1 }}>
          {/* Header */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6" component="div">
              Annotator {worker.annotator_id}
            </Typography>
            <Chip
              label={worker.status || 'unknown'}
              color={getStatusColor(worker.status)}
              size="small"
            />
          </Box>

          {/* Domain */}
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {formatDomain(worker.domain)}
          </Typography>

          {/* Progress */}
          <Box mt={2} mb={1}>
            <Box display="flex" justifyContent="space-between" mb={0.5}>
              <Typography variant="body2">
                {completed} / {target}
              </Typography>
              <Typography variant="body2">{percentage.toFixed(1)}%</Typography>
            </Box>
            <LinearProgress variant="determinate" value={Math.min(percentage, 100)} />
          </Box>

          {/* Stats */}
          <Stack spacing={0.5} mt={2}>
            {progress.speed > 0 && (
              <Typography variant="caption" color="text.secondary">
                Speed: {progress.speed.toFixed(2)} samples/min
              </Typography>
            )}
            {progress.malformed > 0 && (
              <Typography variant="caption" color="warning.main">
                Malformed: {progress.malformed}
              </Typography>
            )}
            {worker.pid && (
              <Typography variant="caption" color="text.secondary">
                PID: {worker.pid}
              </Typography>
            )}
          </Stack>

          {/* Controls */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
            <Box>
              {worker.status === 'running' && (
                <>
                  <Tooltip title="Pause">
                    <IconButton
                      size="small"
                      onClick={handlePause}
                      disabled={loading}
                      color="warning"
                    >
                      <PauseIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Stop">
                    <IconButton
                      size="small"
                      onClick={handleStop}
                      disabled={loading}
                      color="error"
                    >
                      <StopIcon />
                    </IconButton>
                  </Tooltip>
                </>
              )}
              {worker.status === 'paused' && (
                <>
                  <Tooltip title="Resume">
                    <IconButton
                      size="small"
                      onClick={handleResume}
                      disabled={loading}
                      color="success"
                    >
                      <PlayIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Stop">
                    <IconButton
                      size="small"
                      onClick={handleStop}
                      disabled={loading}
                      color="error"
                    >
                      <StopIcon />
                    </IconButton>
                  </Tooltip>
                </>
              )}
            </Box>

            {/* View Annotations Button */}
            {completed > 0 && (
              <Tooltip title="View Annotations">
                <IconButton
                  size="small"
                  onClick={() => onViewAnnotations(worker)}
                  color="primary"
                >
                  <EyeIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default WorkerCard;

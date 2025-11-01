import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Button,
  Stack,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Pause as PauseIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';

/**
 * Get status color and icon
 */
const getStatusInfo = (status) => {
  switch (status) {
    case 'running':
      return { color: 'success', label: 'Running', icon: <PlayIcon /> };
    case 'paused':
      return { color: 'warning', label: 'Paused', icon: <PauseIcon /> };
    case 'stopped':
      return { color: 'default', label: 'Stopped', icon: <StopIcon /> };
    case 'completed':
      return { color: 'info', label: 'Completed', icon: <CheckIcon /> };
    case 'crashed':
      return { color: 'error', label: 'Crashed', icon: <ErrorIcon /> };
    default:
      return { color: 'default', label: 'Not Started', icon: null };
  }
};

/**
 * Format seconds to human readable time
 */
const formatETA = (seconds) => {
  if (!seconds || seconds <= 0) return 'N/A';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
};

/**
 * Worker Card Component
 */
const WorkerCard = ({ worker, onPauseResume, onTerminate, loading }) => {
  const statusInfo = getStatusInfo(worker.status);

  const isPaused = worker.status === 'paused';
  const isRunning = worker.status === 'running';
  const canPauseResume = isRunning || isPaused;
  const canTerminate = isRunning || isPaused;

  const handlePauseResume = () => {
    onPauseResume(worker.annotator_id, worker.domain, isPaused);
  };

  const handleTerminate = () => {
    onTerminate(worker.annotator_id, worker.domain);
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        // Pulsing animation for running workers
        ...(isRunning && {
          animation: 'pulse 2s ease-in-out infinite',
          '@keyframes pulse': {
            '0%, 100%': {
              boxShadow: '0 0 0 0 rgba(76, 175, 80, 0.7)',
            },
            '50%': {
              boxShadow: '0 0 0 10px rgba(76, 175, 80, 0)',
            },
          },
        }),
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        {/* Header */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Annotator {worker.annotator_id}
          </Typography>
          <Chip
            label={statusInfo.label}
            color={statusInfo.color}
            size="small"
            icon={statusInfo.icon}
          />
        </Stack>

        {/* Domain */}
        <Typography variant="body2" color="text.secondary" mb={2}>
          Domain: <strong>{worker.domain}</strong>
        </Typography>

        {/* Progress Bar */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" mb={0.5}>
            <Typography variant="body2">Progress</Typography>
            <Typography variant="body2" color="text.secondary">
              {worker.progress_percentage}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={worker.progress_percentage}
            color={statusInfo.color}
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography variant="caption" color="text.secondary" mt={0.5}>
            {worker.completed_count} / {worker.target_count} samples
          </Typography>
        </Box>

        {/* Stats */}
        <Stack spacing={1} mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <SpeedIcon fontSize="small" color="action" />
            <Typography variant="body2">
              Speed: <strong>{worker.speed}</strong> samples/min
            </Typography>
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            <TimerIcon fontSize="small" color="action" />
            <Typography variant="body2">
              ETA: <strong>{formatETA(worker.eta_seconds)}</strong>
            </Typography>
          </Box>

          {worker.malformed_count > 0 && (
            <Typography variant="body2" color="warning.main">
              Malformed: {worker.malformed_count}
            </Typography>
          )}

          {worker.is_stale && (
            <Typography variant="body2" color="error">
              ⚠️ Worker may be stalled
            </Typography>
          )}
        </Stack>

        {/* Controls */}
        <Stack direction="row" spacing={1}>
          <Tooltip title={isPaused ? 'Resume worker' : 'Pause worker'}>
            <span style={{ flexGrow: 1 }}>
              <Button
                variant="outlined"
                fullWidth
                size="small"
                startIcon={isPaused ? <PlayIcon /> : <PauseIcon />}
                onClick={handlePauseResume}
                disabled={!canPauseResume || loading}
                color={isPaused ? 'success' : 'warning'}
              >
                {isPaused ? 'Resume' : 'Pause'}
              </Button>
            </span>
          </Tooltip>

          <Tooltip title="Stop this worker">
            <span style={{ flexGrow: 1 }}>
              <Button
                variant="outlined"
                fullWidth
                size="small"
                startIcon={<StopIcon />}
                onClick={handleTerminate}
                disabled={!canTerminate || loading}
                color="error"
              >
                Terminate
              </Button>
            </span>
          </Tooltip>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default WorkerCard;

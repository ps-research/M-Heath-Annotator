import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Button,
  LinearProgress,
  Chip,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassIcon,
} from '@mui/icons-material';

const WorkerGrid = ({ workers, onPause, onResume, onTerminate, loading }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'paused':
        return 'warning';
      case 'stopped':
      case 'crashed':
        return 'error';
      case 'completed':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <PlayIcon />;
      case 'paused':
        return <PauseIcon />;
      case 'completed':
        return <CheckCircleIcon />;
      case 'crashed':
        return <ErrorIcon />;
      default:
        return <HourglassIcon />;
    }
  };

  const calculateProgress = (worker) => {
    if (!worker.progress?.target_count || worker.progress.target_count === 0) {
      return 0;
    }
    const completed = worker.progress?.completed_ids?.length || 0;
    return Math.min((completed / worker.progress.target_count) * 100, 100);
  };

  return (
    <Grid container spacing={2}>
      {workers.map((worker) => {
        const progress = calculateProgress(worker);
        const completed = worker.progress?.completed_ids?.length || 0;
        const target = worker.progress?.target_count || 0;
        const speed = worker.progress?.stats?.samples_per_min || 0;
        const isRunning = worker.running && worker.status === 'running';
        const isPaused = worker.status === 'paused';

        return (
          <Grid item xs={12} sm={6} md={4} lg={3} key={`${worker.annotator_id}-${worker.domain}`}>
            <Card
              elevation={3}
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',
                border: '2px solid',
                borderColor: isRunning
                  ? 'success.main'
                  : isPaused
                  ? 'warning.main'
                  : 'grey.300',
                transition: 'all 0.3s',
                '&:hover': {
                  boxShadow: 6,
                },
              }}
            >
              {/* Status Badge */}
              <Box
                sx={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  zIndex: 1,
                }}
              >
                <Chip
                  icon={getStatusIcon(worker.status)}
                  label={worker.status?.toUpperCase() || 'UNKNOWN'}
                  color={getStatusColor(worker.status)}
                  size="small"
                />
              </Box>

              <CardContent sx={{ flexGrow: 1, pt: 5 }}>
                {/* Worker Info */}
                <Typography variant="h6" gutterBottom>
                  Annotator {worker.annotator_id}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Domain:{' '}
                  <strong>
                    {worker.domain.charAt(0).toUpperCase() + worker.domain.slice(1)}
                  </strong>
                </Typography>

                <Divider sx={{ my: 2 }} />

                {/* Progress */}
                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="caption" color="text.secondary">
                      Progress
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {completed} / {target}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={progress}
                    sx={{
                      height: 8,
                      borderRadius: 1,
                      bgcolor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 1,
                        bgcolor: isRunning
                          ? 'success.main'
                          : isPaused
                          ? 'warning.main'
                          : 'grey.400',
                      },
                    }}
                  />
                  <Typography variant="caption" color="text.secondary" align="center" display="block" mt={0.5}>
                    {progress.toFixed(1)}%
                  </Typography>
                </Box>

                {/* Speed */}
                {isRunning && (
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <SpeedIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      {speed.toFixed(2)} samples/min
                    </Typography>
                  </Box>
                )}

                {/* Last Updated */}
                {worker.last_updated && (
                  <Typography variant="caption" color="text.secondary">
                    Updated: {new Date(worker.last_updated).toLocaleTimeString()}
                  </Typography>
                )}
              </CardContent>

              <CardActions sx={{ p: 2, pt: 0 }}>
                <Box display="flex" gap={1} width="100%">
                  {isRunning ? (
                    <Tooltip title="Pause Worker">
                      <span style={{ flex: 1 }}>
                        <Button
                          fullWidth
                          size="small"
                          variant="outlined"
                          color="warning"
                          startIcon={<PauseIcon />}
                          onClick={() =>
                            onPause(worker.annotator_id, worker.domain)
                          }
                          disabled={loading}
                        >
                          Pause
                        </Button>
                      </span>
                    </Tooltip>
                  ) : isPaused ? (
                    <Tooltip title="Resume Worker">
                      <span style={{ flex: 1 }}>
                        <Button
                          fullWidth
                          size="small"
                          variant="outlined"
                          color="success"
                          startIcon={<PlayIcon />}
                          onClick={() =>
                            onResume(worker.annotator_id, worker.domain)
                          }
                          disabled={loading}
                        >
                          Resume
                        </Button>
                      </span>
                    </Tooltip>
                  ) : null}

                  <Tooltip title="Terminate Worker">
                    <span style={{ flex: 1 }}>
                      <Button
                        fullWidth
                        size="small"
                        variant="outlined"
                        color="error"
                        startIcon={<StopIcon />}
                        onClick={() =>
                          onTerminate(worker.annotator_id, worker.domain)
                        }
                        disabled={loading}
                      >
                        Terminate
                      </Button>
                    </span>
                  </Tooltip>
                </Box>
              </CardActions>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );
};

export default WorkerGrid;

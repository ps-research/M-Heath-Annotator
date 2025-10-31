import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  Group as GroupIcon,
  PlayArrow as PlayArrowIcon,
  Speed as SpeedIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';
import {
  fetchOverview,
  fetchHealth,
  selectOverview,
  selectHealth,
  selectIsLoading,
} from '../../store/slices/monitoringSlice';
import { LoadingSpinner, ErrorAlert } from '../Common';
import { formatSpeed, formatDurationSeconds, formatNumber } from '../../utils/formatters';

/**
 * Overview card component
 */
const OverviewCard = ({ title, value, icon, color = 'primary' }) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="text.secondary" gutterBottom variant="body2">
            {title}
          </Typography>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
        </Box>
        <Box
          sx={{
            backgroundColor: `${color}.light`,
            color: `${color}.main`,
            p: 1.5,
            borderRadius: 2,
          }}
        >
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

/**
 * Monitoring Panel component
 */
const MonitoringPanel = () => {
  const dispatch = useDispatch();
  const overview = useSelector(selectOverview);
  const health = useSelector(selectHealth);
  const loading = useSelector(selectIsLoading);

  useEffect(() => {
    // Fetch initial data
    dispatch(fetchOverview());
    dispatch(fetchHealth());

    // Set up polling
    const interval = setInterval(() => {
      dispatch(fetchOverview());
      dispatch(fetchHealth());
    }, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [dispatch]);

  if (loading.overview) {
    return <LoadingSpinner message="Loading monitoring data..." />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Monitoring Dashboard
      </Typography>

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <OverviewCard
            title="Total Workers"
            value={overview.total_workers || 0}
            icon={<GroupIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <OverviewCard
            title="Running Workers"
            value={overview.running_workers || 0}
            icon={<PlayArrowIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <OverviewCard
            title="Avg Speed"
            value={formatSpeed(overview.avg_speed || 0)}
            icon={<SpeedIcon />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <OverviewCard
            title="ETA"
            value={
              overview.estimated_time_remaining
                ? formatDurationSeconds(overview.estimated_time_remaining)
                : 'N/A'
            }
            icon={<TimerIcon />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Progress Overview */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Overall Progress
        </Typography>
        <Typography variant="body1">
          Completed: {formatNumber(overview.total_progress?.completed || 0)} /{' '}
          {formatNumber(overview.total_progress?.target || 0)} (
          {(overview.total_progress?.percentage || 0).toFixed(1)}%)
        </Typography>
      </Paper>

      {/* Health Status */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          System Health
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Typography color="success.main">
              Healthy: {health.healthy || 0}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography color="warning.main">
              Stalled: {health.stalled?.length || 0}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography color="error.main">
              Crashed: {health.crashed?.length || 0}
            </Typography>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default MonitoringPanel;

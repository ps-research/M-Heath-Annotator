import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
} from '@mui/material';
import { monitoringAPI } from '../../services/api';
import { LoadingSpinner } from '../Common';
import WorkerCard from './WorkerCard';
import AnnotationsViewerDialog from './AnnotationsViewerDialog';

const MonitoringPanel = () => {
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterAnnotator, setFilterAnnotator] = useState('all');
  const [pollingInterval, setPollingInterval] = useState(null);
  const [selectedWorker, setSelectedWorker] = useState(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  // Load workers on mount
  useEffect(() => {
    loadWorkers();
    startPolling();

    return () => {
      stopPolling();
    };
  }, []);

  const loadWorkers = async () => {
    try {
      setLoading(true);
      const data = await monitoringAPI.getWorkers();
      setWorkers(data || []);
    } catch (error) {
      console.error('Failed to load workers:', error);
    } finally {
      setLoading(false);
    }
  };

  const startPolling = () => {
    // Poll every 2 seconds
    const interval = setInterval(() => {
      loadWorkersQuiet();
    }, 2000);
    setPollingInterval(interval);
  };

  const loadWorkersQuiet = async () => {
    try {
      const data = await monitoringAPI.getWorkers();
      setWorkers(data || []);
    } catch (error) {
      console.error('Failed to poll workers:', error);
    }
  };

  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  };

  const handleViewAnnotations = (worker) => {
    setSelectedWorker(worker);
    setViewerOpen(true);
  };

  const handleCloseViewer = () => {
    setViewerOpen(false);
    setSelectedWorker(null);
  };

  // Filter workers
  const filteredWorkers = workers.filter((worker) => {
    if (filterStatus !== 'all' && worker.status !== filterStatus) {
      return false;
    }
    if (filterAnnotator !== 'all' && worker.annotator_id !== parseInt(filterAnnotator)) {
      return false;
    }
    return true;
  });

  // Calculate statistics
  const stats = {
    total: workers.length,
    running: workers.filter((w) => w.running).length,
    paused: workers.filter((w) => w.status === 'paused').length,
    completed: workers.filter((w) => w.status === 'completed').length,
    crashed: workers.filter((w) => w.status === 'crashed' || w.stale).length,
  };

  if (loading) {
    return <LoadingSpinner message="Loading monitoring data..." />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Worker Monitoring
      </Typography>

      {/* Statistics Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={2}>
            <Typography variant="h6">Total Workers</Typography>
            <Typography variant="h4">{stats.total}</Typography>
          </Grid>
          <Grid item xs={6} md={2}>
            <Chip label={`Running: ${stats.running}`} color="success" sx={{ width: '100%' }} />
          </Grid>
          <Grid item xs={6} md={2}>
            <Chip label={`Paused: ${stats.paused}`} color="warning" sx={{ width: '100%' }} />
          </Grid>
          <Grid item xs={6} md={2}>
            <Chip label={`Completed: ${stats.completed}`} color="info" sx={{ width: '100%' }} />
          </Grid>
          <Grid item xs={6} md={2}>
            <Chip label={`Crashed: ${stats.crashed}`} color="error" sx={{ width: '100%' }} />
          </Grid>
        </Grid>
      </Paper>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Filter by Status</InputLabel>
              <Select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                label="Filter by Status"
              >
                <MenuItem value="all">All Statuses</MenuItem>
                <MenuItem value="not_started">Not Started</MenuItem>
                <MenuItem value="running">Running</MenuItem>
                <MenuItem value="paused">Paused</MenuItem>
                <MenuItem value="stopped">Stopped</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="crashed">Crashed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Filter by Annotator</InputLabel>
              <Select
                value={filterAnnotator}
                onChange={(e) => setFilterAnnotator(e.target.value)}
                label="Filter by Annotator"
              >
                <MenuItem value="all">All Annotators</MenuItem>
                <MenuItem value="1">Annotator 1</MenuItem>
                <MenuItem value="2">Annotator 2</MenuItem>
                <MenuItem value="3">Annotator 3</MenuItem>
                <MenuItem value="4">Annotator 4</MenuItem>
                <MenuItem value="5">Annotator 5</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Worker Grid */}
      {filteredWorkers.length === 0 ? (
        <Alert severity="info">No workers match the selected filters</Alert>
      ) : (
        <Grid container spacing={2}>
          {filteredWorkers.map((worker) => (
            <Grid
              item
              xs={12}
              sm={6}
              md={4}
              lg={3}
              key={`${worker.annotator_id}-${worker.domain}`}
            >
              <WorkerCard worker={worker} onViewAnnotations={handleViewAnnotations} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Annotations Viewer Dialog */}
      {selectedWorker && (
        <AnnotationsViewerDialog
          open={viewerOpen}
          onClose={handleCloseViewer}
          worker={selectedWorker}
        />
      )}
    </Box>
  );
};

export default MonitoringPanel;

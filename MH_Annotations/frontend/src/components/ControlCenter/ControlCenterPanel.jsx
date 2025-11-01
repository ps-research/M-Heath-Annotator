import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Typography,
  Button,
  Grid,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  CircularProgress,
  Paper,
  Divider,
  Snackbar,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  DeleteForever as DeleteForeverIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Pause as PauseIcon,
} from '@mui/icons-material';
import { controlAPI, monitoringAPI } from '../../services/api';
import {
  fetchWorkers,
  pauseWorker,
  resumeWorker,
  stopWorker,
} from '../../store/slices/workersSlice';
import { LoadingSpinner } from '../Common';
import AnnotatorCard from './AnnotatorCard';
import WorkerGrid from './WorkerGrid';

const ControlCenterPanel = () => {
  const dispatch = useDispatch();

  // State
  const [view, setView] = useState('initial'); // 'initial' | 'running'
  const [annotatorSummaries, setAnnotatorSummaries] = useState([]);
  const [activeWorkers, setActiveWorkers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pollingInterval, setPollingInterval] = useState(null);

  // Dialogs
  const [factoryResetDialog, setFactoryResetDialog] = useState(false);
  const [resetDialog, setResetDialog] = useState(false);
  const [terminateAllDialog, setTerminateAllDialog] = useState(false);
  const [confirmation, setConfirmation] = useState('');

  // Notifications
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Load annotator summaries on mount and check for active workers
  useEffect(() => {
    const initialize = async () => {
      await loadAnnotatorSummaries();
      await checkForActiveWorkers();
    };
    initialize();

    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, []);

  const loadAnnotatorSummaries = async () => {
    try {
      setLoading(true);
      const summaries = await controlAPI.getAnnotatorSummaries();
      setAnnotatorSummaries(summaries || []);
    } catch (error) {
      showSnackbar('Failed to load annotator summaries: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadActiveWorkers = async () => {
    try {
      // Get all workers without status filter, then filter on frontend
      const allWorkers = await monitoringAPI.getWorkers();
      const activeWorkers = (allWorkers || []).filter(
        worker => worker.status === 'running' || worker.status === 'paused'
      );
      setActiveWorkers(activeWorkers);
      return activeWorkers;
    } catch (error) {
      console.error('Failed to load active workers:', error);
      return [];
    }
  };

  const checkForActiveWorkers = async () => {
    try {
      const workers = await loadActiveWorkers();
      // If there are active workers, switch to running view and start polling
      if (workers && workers.length > 0) {
        setView('running');
        startPolling();
      }
    } catch (error) {
      console.error('Failed to check for active workers:', error);
    }
  };

  const startPolling = () => {
    // Poll every 2 seconds
    const interval = setInterval(() => {
      loadActiveWorkers();
    }, 2000);
    setPollingInterval(interval);
  };

  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  };

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // RUN button handler
  const handleRun = async () => {
    try {
      setLoading(true);

      // Check if there are enabled workers
      if (annotatorSummaries.length === 0) {
        showSnackbar('No annotators with enabled domains found. Please configure in the Configuration Panel.', 'warning');
        return;
      }

      // Check if all annotators have API keys
      const missingKeys = annotatorSummaries.filter(ann => !ann.has_api_key);
      if (missingKeys.length > 0) {
        showSnackbar(
          `Missing API keys for annotators: ${missingKeys.map(a => a.annotator_id).join(', ')}`,
          'error'
        );
        return;
      }

      // Start all enabled workers
      await controlAPI.startAll();

      showSnackbar('Run started successfully!', 'success');

      // Switch to running view
      setView('running');

      // Load active workers and start polling
      await loadActiveWorkers();
      startPolling();
    } catch (error) {
      showSnackbar('Failed to start run: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Factory Reset handler
  const handleFactoryReset = async () => {
    if (confirmation !== 'FACTORY_RESET') {
      showSnackbar('Please type FACTORY_RESET to confirm', 'error');
      return;
    }

    try {
      setLoading(true);
      stopPolling();

      await controlAPI.factoryReset('FACTORY_RESET');

      showSnackbar('Factory reset completed. All data has been deleted.', 'success');
      setFactoryResetDialog(false);
      setConfirmation('');

      // Reset to initial view
      setView('initial');
      setActiveWorkers([]);
      await loadAnnotatorSummaries();
    } catch (error) {
      showSnackbar('Factory reset failed: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Reset handler (current run only)
  const handleReset = async () => {
    if (confirmation !== 'DELETE') {
      showSnackbar('Please type DELETE to confirm', 'error');
      return;
    }

    try {
      setLoading(true);
      stopPolling();

      // Stop all workers first
      await controlAPI.stopAll();

      // Then reset data
      await controlAPI.resetAll('DELETE');

      showSnackbar('Reset completed. All current run data has been deleted.', 'success');
      setResetDialog(false);
      setConfirmation('');

      // Reset to initial view
      setView('initial');
      setActiveWorkers([]);
      await loadAnnotatorSummaries();
    } catch (error) {
      showSnackbar('Reset failed: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Terminate All handler
  const handleTerminateAll = async () => {
    try {
      setLoading(true);

      await controlAPI.stopAll();

      showSnackbar('All workers terminated', 'success');
      setTerminateAllDialog(false);

      // Reload workers
      const workers = await loadActiveWorkers();

      // If no more active workers, go back to initial view
      if (!workers || workers.length === 0) {
        stopPolling();
        setView('initial');
      }
    } catch (error) {
      showSnackbar('Failed to terminate all workers: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Pause All handler
  const handlePauseAll = async () => {
    try {
      setLoading(true);

      await controlAPI.pauseAll();

      showSnackbar('All workers paused', 'success');

      // Reload workers
      await loadActiveWorkers();
    } catch (error) {
      showSnackbar('Failed to pause all workers: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Resume All handler
  const handleResumeAll = async () => {
    try {
      setLoading(true);

      await controlAPI.resumeAll();

      showSnackbar('All workers resumed', 'success');

      // Reload workers
      await loadActiveWorkers();
    } catch (error) {
      showSnackbar('Failed to resume all workers: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Individual worker controls
  const handlePauseWorker = async (annotatorId, domain) => {
    try {
      await dispatch(pauseWorker({ annotatorId, domain })).unwrap();
      showSnackbar(`Worker ${annotatorId}-${domain} paused`, 'success');
      await loadActiveWorkers();
    } catch (error) {
      showSnackbar('Failed to pause worker: ' + error.message, 'error');
    }
  };

  const handleResumeWorker = async (annotatorId, domain) => {
    try {
      await dispatch(resumeWorker({ annotatorId, domain })).unwrap();
      showSnackbar(`Worker ${annotatorId}-${domain} resumed`, 'success');
      await loadActiveWorkers();
    } catch (error) {
      showSnackbar('Failed to resume worker: ' + error.message, 'error');
    }
  };

  const handleTerminateWorker = async (annotatorId, domain) => {
    try {
      await dispatch(stopWorker({ annotatorId, domain })).unwrap();
      showSnackbar(`Worker ${annotatorId}-${domain} terminated`, 'success');
      await loadActiveWorkers();
    } catch (error) {
      showSnackbar('Failed to terminate worker: ' + error.message, 'error');
    }
  };

  // Back to initial view
  const handleBackToInitial = () => {
    stopPolling();
    setView('initial');
    setActiveWorkers([]);
    loadAnnotatorSummaries();
  };

  if (loading && view === 'initial') {
    return <LoadingSpinner message="Loading Control Center..." />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Control Center
      </Typography>

      {/* Initial View */}
      {view === 'initial' && (
        <>
          {/* Big Action Buttons */}
          <Paper sx={{ p: 4, mb: 4, bgcolor: 'grey.50' }}>
            <Grid container spacing={3} justifyContent="center">
              <Grid item xs={12} md={5}>
                <Button
                  fullWidth
                  variant="contained"
                  color="success"
                  size="large"
                  startIcon={<PlayArrowIcon />}
                  onClick={handleRun}
                  disabled={loading || annotatorSummaries.length === 0}
                  sx={{
                    py: 3,
                    fontSize: '1.5rem',
                    fontWeight: 'bold',
                    boxShadow: 3,
                    '&:hover': {
                      boxShadow: 6,
                    },
                  }}
                >
                  RUN
                </Button>
              </Grid>
              <Grid item xs={12} md={5}>
                <Button
                  fullWidth
                  variant="outlined"
                  color="error"
                  size="large"
                  startIcon={<DeleteForeverIcon />}
                  onClick={() => setFactoryResetDialog(true)}
                  disabled={loading}
                  sx={{
                    py: 3,
                    fontSize: '1.25rem',
                    fontWeight: 'bold',
                    borderWidth: 2,
                    '&:hover': {
                      borderWidth: 2,
                      boxShadow: 3,
                    },
                  }}
                >
                  Factory Reset
                </Button>
              </Grid>
            </Grid>

            {annotatorSummaries.length === 0 && (
              <Alert severity="warning" sx={{ mt: 3 }}>
                No annotators with enabled domains found. Please configure domains in the Configuration Panel.
              </Alert>
            )}
          </Paper>

          {/* Annotator Cards */}
          <Box>
            <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
              Configured Annotators ({annotatorSummaries.length})
            </Typography>

            <Grid container spacing={2}>
              {annotatorSummaries.map((summary) => (
                <Grid item xs={12} md={6} lg={4} key={summary.annotator_id}>
                  <AnnotatorCard annotatorSummary={summary} />
                </Grid>
              ))}
            </Grid>
          </Box>
        </>
      )}

      {/* Running View */}
      {view === 'running' && (
        <>
          {/* Status Bar */}
          <Paper sx={{ p: 2, mb: 3, bgcolor: 'success.light' }}>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box display="flex" alignItems="center" gap={2}>
                <CircularProgress size={24} sx={{ color: 'white' }} />
                <Typography variant="h6" color="white">
                  Run in Progress
                </Typography>
                <Typography variant="body2" color="white">
                  {activeWorkers.length} active workers
                </Typography>
              </Box>
              <Button
                variant="outlined"
                color="inherit"
                onClick={handleBackToInitial}
                sx={{ color: 'white', borderColor: 'white' }}
              >
                Back to Overview
              </Button>
            </Box>
          </Paper>

          {/* Worker Grid */}
          <Box mb={3}>
            <Typography variant="h5" gutterBottom>
              Active Workers
            </Typography>
            {activeWorkers.length > 0 ? (
              <WorkerGrid
                workers={activeWorkers}
                onPause={handlePauseWorker}
                onResume={handleResumeWorker}
                onTerminate={handleTerminateWorker}
                loading={loading}
              />
            ) : (
              <Alert severity="info">No active workers found</Alert>
            )}
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Control Buttons */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Batch Controls
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <Button
                  fullWidth
                  variant="contained"
                  color="warning"
                  startIcon={<PauseIcon />}
                  onClick={handlePauseAll}
                  disabled={loading || activeWorkers.length === 0}
                >
                  Pause All
                </Button>
              </Grid>
              <Grid item xs={12} md={3}>
                <Button
                  fullWidth
                  variant="contained"
                  color="error"
                  startIcon={<StopIcon />}
                  onClick={() => setTerminateAllDialog(true)}
                  disabled={loading || activeWorkers.length === 0}
                >
                  Terminate All
                </Button>
              </Grid>
              <Grid item xs={12} md={3}>
                <Button
                  fullWidth
                  variant="contained"
                  color="warning"
                  startIcon={<RefreshIcon />}
                  onClick={() => setResetDialog(true)}
                  disabled={loading}
                  sx={{ bgcolor: 'warning.dark' }}
                >
                  Reset
                </Button>
              </Grid>
              <Grid item xs={12} md={3}>
                <Button
                  fullWidth
                  variant="contained"
                  color="error"
                  startIcon={<DeleteForeverIcon />}
                  onClick={() => setFactoryResetDialog(true)}
                  disabled={loading}
                  sx={{ bgcolor: 'error.dark' }}
                >
                  Factory Reset
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </>
      )}

      {/* Factory Reset Dialog */}
      <Dialog
        open={factoryResetDialog}
        onClose={() => {
          setFactoryResetDialog(false);
          setConfirmation('');
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <WarningIcon color="error" />
            <span>Factory Reset - DANGER!</span>
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will <strong>DELETE ALL DATA</strong> including:
            <ul>
              <li>All annotations from all runs</li>
              <li>All progress tracking</li>
              <li>All logs</li>
              <li>All control files</li>
            </ul>
            <strong>This action cannot be undone!</strong>
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label='Type "FACTORY_RESET" to confirm'
            fullWidth
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            error={confirmation !== '' && confirmation !== 'FACTORY_RESET'}
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setFactoryResetDialog(false);
              setConfirmation('');
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleFactoryReset}
            color="error"
            variant="contained"
            disabled={confirmation !== 'FACTORY_RESET' || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Factory Reset'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reset Dialog */}
      <Dialog
        open={resetDialog}
        onClose={() => {
          setResetDialog(false);
          setConfirmation('');
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <WarningIcon color="warning" />
            <span>Reset Current Run</span>
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will stop all workers and delete all data from the current run, including:
            <ul>
              <li>All annotations from this run</li>
              <li>All progress tracking</li>
              <li>All control files</li>
            </ul>
            <strong>This action cannot be undone!</strong>
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label='Type "DELETE" to confirm'
            fullWidth
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            error={confirmation !== '' && confirmation !== 'DELETE'}
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setResetDialog(false);
              setConfirmation('');
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleReset}
            color="warning"
            variant="contained"
            disabled={confirmation !== 'DELETE' || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Reset'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Terminate All Dialog */}
      <Dialog
        open={terminateAllDialog}
        onClose={() => setTerminateAllDialog(false)}
      >
        <DialogTitle>Terminate All Workers?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will stop all running workers. Progress will be saved and can be resumed later.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTerminateAllDialog(false)}>Cancel</Button>
          <Button
            onClick={handleTerminateAll}
            color="error"
            variant="contained"
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Terminate All'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ControlCenterPanel;

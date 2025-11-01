import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Typography,
  Button,
  Stack,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Alert,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Paper,
  Divider,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  DeleteForever as DeleteIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

import {
  validateRunStart,
  startRun,
  resetCurrentRun,
  factoryReset,
  fetchGridStatus,
  pauseWorker,
  resumeWorker,
  stopWorker,
  stopAll,
  selectViewMode,
  selectGridWorkers,
  selectRunValidation,
  selectIsLoading,
  selectErrors,
} from '../../store/slices/workersSlice';

import { LoadingSpinner, ErrorAlert } from '../Common';
import WorkerCard from './WorkerCard';

/**
 * Control Center Panel - Complete Implementation
 */
const ControlCenterPanel = () => {
  const dispatch = useDispatch();

  // Redux state
  const viewMode = useSelector(selectViewMode);
  const gridWorkers = useSelector(selectGridWorkers);
  const validation = useSelector(selectRunValidation);
  const loading = useSelector(selectIsLoading);
  const errors = useSelector(selectErrors);

  // Local state for dialogs
  const [terminateAllDialog, setTerminateAllDialog] = useState(false);
  const [resetDialog, setResetDialog] = useState(false);
  const [factoryResetDialog, setFactoryResetDialog] = useState(false);
  const [factoryResetConfirmText, setFactoryResetConfirmText] = useState('');
  const [validationDialog, setValidationDialog] = useState(false);

  // Poll for grid updates when in grid view
  useEffect(() => {
    if (viewMode === 'grid') {
      // Initial fetch
      dispatch(fetchGridStatus());

      // Poll every 5 seconds
      const interval = setInterval(() => {
        dispatch(fetchGridStatus());
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [viewMode, dispatch]);

  // ===== Event Handlers =====

  const handleRunClick = async () => {
    // Validate first
    const result = await dispatch(validateRunStart()).unwrap();

    if (!result.data.valid) {
      // Show validation errors
      setValidationDialog(true);
    } else {
      // Start the run
      await dispatch(startRun(false));
    }
  };

  const handlePauseResume = async (annotatorId, domain, isPaused) => {
    if (isPaused) {
      await dispatch(resumeWorker({ annotatorId, domain }));
    } else {
      await dispatch(pauseWorker({ annotatorId, domain }));
    }

    // Refresh grid
    dispatch(fetchGridStatus());
  };

  const handleTerminate = async (annotatorId, domain) => {
    if (window.confirm(`Terminate worker for Annotator ${annotatorId}, Domain ${domain}?`)) {
      await dispatch(stopWorker({ annotatorId, domain }));

      // Refresh grid
      dispatch(fetchGridStatus());
    }
  };

  const handleTerminateAll = async () => {
    await dispatch(stopAll());
    setTerminateAllDialog(false);

    // Refresh grid
    dispatch(fetchGridStatus());
  };

  const handleReset = async () => {
    await dispatch(resetCurrentRun());
    setResetDialog(false);
  };

  const handleFactoryReset = async () => {
    if (factoryResetConfirmText === 'DELETE EVERYTHING') {
      await dispatch(factoryReset(factoryResetConfirmText));
      setFactoryResetDialog(false);
      setFactoryResetConfirmText('');
    }
  };

  // ===== Render Views =====

  // Initial View - Big RUN Button
  if (viewMode === 'initial') {
    return (
      <Box
        sx={{
          height: 'calc(100vh - 200px)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Typography variant="h3" gutterBottom>
          Control Center
        </Typography>

        <Typography variant="body1" color="text.secondary" mb={4}>
          Start your annotation experiment
        </Typography>

        <Button
          variant="contained"
          size="large"
          startIcon={<PlayIcon />}
          onClick={handleRunClick}
          disabled={loading.validate || loading.start}
          sx={{
            fontSize: '1.5rem',
            padding: '20px 60px',
            borderRadius: '50px',
            background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
            boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1976D2 30%, #1CB5E0 90%)',
              boxShadow: '0 6px 10px 4px rgba(33, 203, 243, .3)',
            },
          }}
        >
          {loading.validate || loading.start ? (
            <>
              <CircularProgress size={24} sx={{ mr: 2 }} />
              {loading.validate ? 'Validating...' : 'Starting...'}
            </>
          ) : (
            'RUN EXPERIMENT'
          )}
        </Button>

        {errors.validate && (
          <Alert severity="error" sx={{ mt: 3, maxWidth: 600 }}>
            {errors.validate}
          </Alert>
        )}

        {errors.start && (
          <Alert severity="error" sx={{ mt: 3, maxWidth: 600 }}>
            {errors.start}
          </Alert>
        )}

        {/* Validation Error Dialog */}
        <Dialog
          open={validationDialog}
          onClose={() => setValidationDialog(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon color="error" />
            Validation Failed
          </DialogTitle>
          <DialogContent>
            <DialogContentText mb={2}>
              The following issues must be resolved before starting:
            </DialogContentText>

            {validation?.data?.errors && validation.data.errors.length > 0 && (
              <>
                <Typography variant="subtitle2" color="error" gutterBottom>
                  Errors:
                </Typography>
                <List dense>
                  {validation.data.errors.map((error, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={`• ${error}`} />
                    </ListItem>
                  ))}
                </List>
              </>
            )}

            {validation?.data?.warnings && validation.data.warnings.length > 0 && (
              <>
                <Typography variant="subtitle2" color="warning.main" gutterBottom mt={2}>
                  Warnings:
                </Typography>
                <List dense>
                  {validation.data.warnings.map((warning, idx) => (
                    <ListItem key={idx}>
                      <ListItemText primary={`• ${warning}`} />
                    </ListItem>
                  ))}
                </List>
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setValidationDialog(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Box>
    );
  }

  // Loading View
  if (viewMode === 'loading') {
    return <LoadingSpinner message="Starting workers..." />;
  }

  // Grid View - Worker Cards
  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Control Center - Active Run</Typography>

        <Button
          startIcon={<RefreshIcon />}
          onClick={() => dispatch(fetchGridStatus())}
          disabled={loading.grid}
        >
          Refresh
        </Button>
      </Stack>

      {/* Worker Grid */}
      {gridWorkers.length === 0 ? (
        <Alert severity="info">
          No enabled workers found. Configure workers in the Configuration panel.
        </Alert>
      ) : (
        <Grid container spacing={3} mb={4}>
          {gridWorkers.map((worker) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={`${worker.annotator_id}-${worker.domain}`}>
              <WorkerCard
                worker={worker}
                onPauseResume={handlePauseResume}
                onTerminate={handleTerminate}
                loading={loading.pause || loading.resume || loading.stop}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Global Controls */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Global Controls
        </Typography>

        <Divider sx={{ my: 2 }} />

        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<StopIcon />}
            onClick={() => setTerminateAllDialog(true)}
            disabled={loading.stop}
          >
            Terminate All
          </Button>

          <Button
            variant="outlined"
            color="warning"
            startIcon={<DeleteIcon />}
            onClick={() => setResetDialog(true)}
            disabled={loading.reset}
          >
            Reset Current Run
          </Button>

          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setFactoryResetDialog(true)}
            disabled={loading.reset}
            sx={{ marginLeft: 'auto' }}
          >
            Factory Reset
          </Button>
        </Stack>
      </Paper>

      {/* Terminate All Dialog */}
      <Dialog open={terminateAllDialog} onClose={() => setTerminateAllDialog(false)}>
        <DialogTitle>Terminate All Workers?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will stop all running workers. Progress will be saved and workers can be
            restarted later.
          </DialogContentText>
          <DialogContentText mt={2}>
            <strong>
              {gridWorkers.filter((w) => w.is_running).length} workers will be stopped.
            </strong>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTerminateAllDialog(false)}>Cancel</Button>
          <Button onClick={handleTerminateAll} color="error" variant="contained">
            Terminate All
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reset Current Run Dialog */}
      <Dialog open={resetDialog} onClose={() => setResetDialog(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon color="warning" />
          Reset Current Run?
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will stop all workers and delete:
          </DialogContentText>
          <List dense>
            <ListItem>
              <ListItemText primary="• All annotations from this run" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• All progress logs" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• All control files" />
            </ListItem>
          </List>
          <DialogContentText color="error" mt={2}>
            <strong>This action cannot be undone!</strong>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialog(false)}>Cancel</Button>
          <Button onClick={handleReset} color="warning" variant="contained">
            Reset Current Run
          </Button>
        </DialogActions>
      </Dialog>

      {/* Factory Reset Dialog */}
      <Dialog open={factoryResetDialog} onClose={() => setFactoryResetDialog(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DeleteIcon color="error" />
          Factory Reset - DELETE EVERYTHING?
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will stop all workers and delete ALL data from ALL runs FOREVER:
          </DialogContentText>
          <List dense>
            <ListItem>
              <ListItemText primary="• All annotations from all runs" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• All progress logs" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• All control files" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• All exported data" />
            </ListItem>
          </List>
          <DialogContentText color="error" mt={2} mb={2}>
            <strong>THIS ACTION CANNOT BE UNDONE!</strong>
          </DialogContentText>
          <DialogContentText mb={2}>
            Type <strong>DELETE EVERYTHING</strong> to confirm:
          </DialogContentText>
          <TextField
            fullWidth
            value={factoryResetConfirmText}
            onChange={(e) => setFactoryResetConfirmText(e.target.value)}
            placeholder="DELETE EVERYTHING"
            error={factoryResetConfirmText && factoryResetConfirmText !== 'DELETE EVERYTHING'}
            helperText={
              factoryResetConfirmText && factoryResetConfirmText !== 'DELETE EVERYTHING'
                ? 'Text must match exactly'
                : ''
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setFactoryResetDialog(false);
            setFactoryResetConfirmText('');
          }}>
            Cancel
          </Button>
          <Button
            onClick={handleFactoryReset}
            color="error"
            variant="contained"
            disabled={factoryResetConfirmText !== 'DELETE EVERYTHING'}
          >
            Factory Reset
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ControlCenterPanel;

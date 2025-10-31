import { useEffect, useState, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { getWebSocketInstance } from '../services/websocket';
import {
  updateWorker,
  updateMultipleWorkers,
} from '../store/slices/workersSlice';
import {
  updateFromWebSocket,
  appendLog,
} from '../store/slices/monitoringSlice';
import { showSnackbar } from '../store/slices/uiSlice';

/**
 * Custom hook for WebSocket connection
 */
export const useWebSocket = () => {
  const dispatch = useDispatch();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [error, setError] = useState(null);

  const handleConnection = useCallback((data) => {
    const { status, error: connError } = data;
    setConnectionStatus(status);
    setIsConnected(status === 'connected');

    if (connError) {
      setError(connError);
      dispatch(
        showSnackbar({
          message: `WebSocket error: ${connError}`,
          severity: 'error',
        })
      );
    } else if (status === 'connected') {
      setError(null);
      dispatch(
        showSnackbar({
          message: 'Connected to server',
          severity: 'success',
        })
      );
    } else if (status === 'reconnecting') {
      dispatch(
        showSnackbar({
          message: 'Reconnecting to server...',
          severity: 'info',
        })
      );
    }
  }, [dispatch]);

  const handleMessage = useCallback((message) => {
    const { type, data } = message;

    // Dispatch to monitoring slice for processing
    dispatch(updateFromWebSocket({ type, data }));

    // Handle specific message types
    switch (type) {
      case 'full_state':
        // Full state update - update workers
        if (data.workers) {
          dispatch(updateMultipleWorkers(data.workers));
        }
        break;

      case 'progress_update':
        // Single worker progress update
        if (data.worker) {
          dispatch(updateWorker(data.worker));
        }
        break;

      case 'status_change':
        // Worker status changed
        if (data.worker) {
          dispatch(updateWorker(data.worker));
        }
        if (data.message) {
          dispatch(
            showSnackbar({
              message: data.message,
              severity: 'info',
            })
          );
        }
        break;

      case 'error':
        // Error occurred
        if (data.log) {
          dispatch(appendLog(data.log));
        }
        if (data.message) {
          dispatch(
            showSnackbar({
              message: data.message,
              severity: 'error',
            })
          );
        }
        break;

      case 'crash_detected':
        // Worker crashed
        if (data.message) {
          dispatch(
            showSnackbar({
              message: data.message,
              severity: 'warning',
            })
          );
        }
        if (data.worker) {
          dispatch(updateWorker(data.worker));
        }
        break;

      default:
        // Unknown message type
        if (import.meta.env.DEV) {
          console.log('[WebSocket Hook] Unknown message type:', type);
        }
        break;
    }
  }, [dispatch]);

  const handleError = useCallback((data) => {
    console.error('[WebSocket Hook] Error:', data.error);
    setError('WebSocket error occurred');
  }, []);

  useEffect(() => {
    // Get WebSocket instance
    const ws = getWebSocketInstance();

    // Register event listeners
    ws.on('connection', handleConnection);
    ws.on('message', handleMessage);
    ws.on('error', handleError);

    // Connect
    ws.connect();

    // Cleanup on unmount
    return () => {
      ws.off('connection', handleConnection);
      ws.off('message', handleMessage);
      ws.off('error', handleError);
      ws.disconnect();
    };
  }, [handleConnection, handleMessage, handleError]);

  return {
    isConnected,
    connectionStatus,
    error,
  };
};

export default useWebSocket;

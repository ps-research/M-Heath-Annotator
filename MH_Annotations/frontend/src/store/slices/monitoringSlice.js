import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { monitoringAPI } from '../../services/api';

// Initial state
const initialState = {
  overview: {
    total_workers: 0,
    enabled_workers: 0,
    running_workers: 0,
    paused_workers: 0,
    completed_workers: 0,
    crashed_workers: 0,
    total_progress: {
      completed: 0,
      target: 0,
      percentage: 0,
    },
    avg_speed: 0,
    estimated_time_remaining: null,
  },
  health: {
    crashed: [],
    stalled: [],
    healthy: 0,
  },
  quota: {}, // { annotator_1: {requests_today, quota_limit, ...}, ... }
  logs: [],
  loading: {
    overview: false,
    health: false,
    quota: false,
    logs: false,
  },
  errors: {
    overview: null,
    health: null,
    quota: null,
    logs: null,
  },
  lastUpdate: null,
};

// Async thunks
export const fetchOverview = createAsyncThunk(
  'monitoring/fetchOverview',
  async (_, { rejectWithValue }) => {
    try {
      const data = await monitoringAPI.getOverview();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchHealth = createAsyncThunk(
  'monitoring/fetchHealth',
  async (_, { rejectWithValue }) => {
    try {
      const data = await monitoringAPI.getHealth();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchQuota = createAsyncThunk(
  'monitoring/fetchQuota',
  async (_, { rejectWithValue }) => {
    try {
      const data = await monitoringAPI.getQuota();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchLogs = createAsyncThunk(
  'monitoring/fetchLogs',
  async (params = {}, { rejectWithValue }) => {
    try {
      const data = await monitoringAPI.getLogs(params);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Slice
const monitoringSlice = createSlice({
  name: 'monitoring',
  initialState,
  reducers: {
    setOverview: (state, action) => {
      state.overview = action.payload;
      state.lastUpdate = new Date().toISOString();
    },
    setHealth: (state, action) => {
      state.health = action.payload;
    },
    setQuota: (state, action) => {
      state.quota = action.payload;
    },
    setLogs: (state, action) => {
      state.logs = action.payload;
    },
    appendLog: (state, action) => {
      state.logs.unshift(action.payload); // Add to beginning
      // Keep only last 100 logs
      if (state.logs.length > 100) {
        state.logs = state.logs.slice(0, 100);
      }
    },
    updateFromWebSocket: (state, action) => {
      // Update state from WebSocket event
      const { type, data } = action.payload;

      switch (type) {
        case 'full_state':
          if (data.overview) {
            state.overview = data.overview;
          }
          if (data.health) {
            state.health = data.health;
          }
          if (data.quota) {
            state.quota = data.quota;
          }
          state.lastUpdate = new Date().toISOString();
          break;

        case 'progress_update':
          // Overview stats may change with progress
          if (data.overview) {
            state.overview = { ...state.overview, ...data.overview };
          }
          state.lastUpdate = new Date().toISOString();
          break;

        case 'crash_detected':
          // Add to crashed workers
          if (data.worker) {
            state.health.crashed.push(data.worker);
            state.overview.crashed_workers += 1;
          }
          break;

        case 'error':
          // Add to logs
          if (data.log) {
            state.logs.unshift(data.log);
            if (state.logs.length > 100) {
              state.logs = state.logs.slice(0, 100);
            }
          }
          break;

        default:
          break;
      }
    },
    clearError: (state, action) => {
      const errorType = action.payload;
      if (state.errors[errorType] !== undefined) {
        state.errors[errorType] = null;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch Overview
    builder
      .addCase(fetchOverview.pending, (state) => {
        state.loading.overview = true;
        state.errors.overview = null;
      })
      .addCase(fetchOverview.fulfilled, (state, action) => {
        state.loading.overview = false;
        state.overview = action.payload;
        state.lastUpdate = new Date().toISOString();
      })
      .addCase(fetchOverview.rejected, (state, action) => {
        state.loading.overview = false;
        state.errors.overview = action.payload;
      });

    // Fetch Health
    builder
      .addCase(fetchHealth.pending, (state) => {
        state.loading.health = true;
        state.errors.health = null;
      })
      .addCase(fetchHealth.fulfilled, (state, action) => {
        state.loading.health = false;
        state.health = action.payload;
      })
      .addCase(fetchHealth.rejected, (state, action) => {
        state.loading.health = false;
        state.errors.health = action.payload;
      });

    // Fetch Quota
    builder
      .addCase(fetchQuota.pending, (state) => {
        state.loading.quota = true;
        state.errors.quota = null;
      })
      .addCase(fetchQuota.fulfilled, (state, action) => {
        state.loading.quota = false;
        state.quota = action.payload;
      })
      .addCase(fetchQuota.rejected, (state, action) => {
        state.loading.quota = false;
        state.errors.quota = action.payload;
      });

    // Fetch Logs
    builder
      .addCase(fetchLogs.pending, (state) => {
        state.loading.logs = true;
        state.errors.logs = null;
      })
      .addCase(fetchLogs.fulfilled, (state, action) => {
        state.loading.logs = false;
        state.logs = action.payload;
      })
      .addCase(fetchLogs.rejected, (state, action) => {
        state.loading.logs = false;
        state.errors.logs = action.payload;
      });
  },
});

export const {
  setOverview,
  setHealth,
  setQuota,
  setLogs,
  appendLog,
  updateFromWebSocket,
  clearError,
} = monitoringSlice.actions;

// Selectors
export const selectOverview = (state) => state.monitoring.overview;
export const selectHealth = (state) => state.monitoring.health;
export const selectQuota = (state) => state.monitoring.quota;
export const selectLogs = (state) => state.monitoring.logs;
export const selectCrashedWorkers = (state) => state.monitoring.health.crashed;
export const selectStalledWorkers = (state) => state.monitoring.health.stalled;
export const selectIsLoading = (state) => state.monitoring.loading;
export const selectErrors = (state) => state.monitoring.errors;
export const selectLastUpdate = (state) => state.monitoring.lastUpdate;

export default monitoringSlice.reducer;

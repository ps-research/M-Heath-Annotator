import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { controlAPI, monitoringAPI } from '../../services/api';

// Initial state
const initialState = {
  workers: [], // Array of worker status objects
  gridWorkers: [], // For grid view
  selectedWorkers: [], // Array of {annotator_id, domain} for bulk operations
  runValidation: null, // Validation result
  viewMode: 'initial', // 'initial' | 'grid' | 'loading'
  loading: {
    start: false,
    stop: false,
    pause: false,
    resume: false,
    reset: false,
    restart: false,
    fetch: false,
    validate: false,
    grid: false,
  },
  errors: {
    start: null,
    stop: null,
    pause: null,
    resume: null,
    reset: null,
    restart: null,
    fetch: null,
    validate: null,
  },
};

// Async thunks for worker control
export const fetchWorkers = createAsyncThunk(
  'workers/fetchWorkers',
  async (filters = {}, { rejectWithValue }) => {
    try {
      const data = await monitoringAPI.getWorkers(filters);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchWorker = createAsyncThunk(
  'workers/fetchWorker',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      const data = await monitoringAPI.getWorker(annotatorId, domain);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const startWorker = createAsyncThunk(
  'workers/startWorker',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      const data = await controlAPI.startWorker(annotatorId, domain);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const stopWorker = createAsyncThunk(
  'workers/stopWorker',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      const data = await controlAPI.stopWorker(annotatorId, domain);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const pauseWorker = createAsyncThunk(
  'workers/pauseWorker',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      const data = await controlAPI.pauseWorker(annotatorId, domain);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const resumeWorker = createAsyncThunk(
  'workers/resumeWorker',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      const data = await controlAPI.resumeWorker(annotatorId, domain);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const startAll = createAsyncThunk(
  'workers/startAll',
  async (_, { rejectWithValue }) => {
    try {
      const data = await controlAPI.startAll();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const stopAll = createAsyncThunk(
  'workers/stopAll',
  async (_, { rejectWithValue }) => {
    try {
      const data = await controlAPI.stopAll();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const pauseAll = createAsyncThunk(
  'workers/pauseAll',
  async (_, { rejectWithValue }) => {
    try {
      const data = await controlAPI.pauseAll();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const resumeAll = createAsyncThunk(
  'workers/resumeAll',
  async (_, { rejectWithValue }) => {
    try {
      const data = await controlAPI.resumeAll();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const resetWorker = createAsyncThunk(
  'workers/resetWorker',
  async ({ annotatorId, domain, confirmation }, { rejectWithValue }) => {
    try {
      const data = await controlAPI.resetWorker(annotatorId, domain, confirmation);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const resetAll = createAsyncThunk(
  'workers/resetAll',
  async (confirmation, { rejectWithValue }) => {
    try {
      const data = await controlAPI.resetAll(confirmation);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const restartWorker = createAsyncThunk(
  'workers/restartWorker',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      const data = await controlAPI.restartWorker(annotatorId, domain);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Run management thunks
export const validateRunStart = createAsyncThunk(
  'workers/validateRunStart',
  async (_, { rejectWithValue }) => {
    try {
      const data = await controlAPI.validateRunStart();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const startRun = createAsyncThunk(
  'workers/startRun',
  async (validateOnly = false, { rejectWithValue }) => {
    try {
      const data = await controlAPI.startRun(validateOnly);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const resetCurrentRun = createAsyncThunk(
  'workers/resetCurrentRun',
  async (_, { rejectWithValue }) => {
    try {
      const data = await controlAPI.resetCurrentRun();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const factoryReset = createAsyncThunk(
  'workers/factoryReset',
  async (confirmationText, { rejectWithValue }) => {
    try {
      const data = await controlAPI.factoryReset(confirmationText);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchGridStatus = createAsyncThunk(
  'workers/fetchGridStatus',
  async (_, { rejectWithValue }) => {
    try {
      const data = await controlAPI.getWorkersGridStatus();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Slice
const workersSlice = createSlice({
  name: 'workers',
  initialState,
  reducers: {
    setWorkers: (state, action) => {
      state.workers = action.payload;
    },
    updateWorker: (state, action) => {
      const updatedWorker = action.payload;
      const index = state.workers.findIndex(
        (w) =>
          w.annotator_id === updatedWorker.annotator_id &&
          w.domain === updatedWorker.domain
      );
      if (index !== -1) {
        state.workers[index] = { ...state.workers[index], ...updatedWorker };
      } else {
        state.workers.push(updatedWorker);
      }
    },
    updateMultipleWorkers: (state, action) => {
      const workers = action.payload;
      workers.forEach((updatedWorker) => {
        const index = state.workers.findIndex(
          (w) =>
            w.annotator_id === updatedWorker.annotator_id &&
            w.domain === updatedWorker.domain
        );
        if (index !== -1) {
          state.workers[index] = { ...state.workers[index], ...updatedWorker };
        } else {
          state.workers.push(updatedWorker);
        }
      });
    },
    toggleWorkerSelection: (state, action) => {
      const { annotatorId, domain } = action.payload;
      const index = state.selectedWorkers.findIndex(
        (w) => w.annotator_id === annotatorId && w.domain === domain
      );
      if (index !== -1) {
        state.selectedWorkers.splice(index, 1);
      } else {
        state.selectedWorkers.push({ annotator_id: annotatorId, domain });
      }
    },
    clearSelection: (state) => {
      state.selectedWorkers = [];
    },
    selectAllWorkers: (state) => {
      state.selectedWorkers = state.workers.map((w) => ({
        annotator_id: w.annotator_id,
        domain: w.domain,
      }));
    },
    clearError: (state, action) => {
      const errorType = action.payload;
      if (state.errors[errorType] !== undefined) {
        state.errors[errorType] = null;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch Workers
    builder
      .addCase(fetchWorkers.pending, (state) => {
        state.loading.fetch = true;
        state.errors.fetch = null;
      })
      .addCase(fetchWorkers.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.workers = action.payload;
      })
      .addCase(fetchWorkers.rejected, (state, action) => {
        state.loading.fetch = false;
        state.errors.fetch = action.payload;
      });

    // Start Worker
    builder
      .addCase(startWorker.pending, (state) => {
        state.loading.start = true;
        state.errors.start = null;
      })
      .addCase(startWorker.fulfilled, (state) => {
        state.loading.start = false;
      })
      .addCase(startWorker.rejected, (state, action) => {
        state.loading.start = false;
        state.errors.start = action.payload;
      });

    // Stop Worker
    builder
      .addCase(stopWorker.pending, (state) => {
        state.loading.stop = true;
        state.errors.stop = null;
      })
      .addCase(stopWorker.fulfilled, (state) => {
        state.loading.stop = false;
      })
      .addCase(stopWorker.rejected, (state, action) => {
        state.loading.stop = false;
        state.errors.stop = action.payload;
      });

    // Pause Worker
    builder
      .addCase(pauseWorker.pending, (state) => {
        state.loading.pause = true;
        state.errors.pause = null;
      })
      .addCase(pauseWorker.fulfilled, (state) => {
        state.loading.pause = false;
      })
      .addCase(pauseWorker.rejected, (state, action) => {
        state.loading.pause = false;
        state.errors.pause = action.payload;
      });

    // Resume Worker
    builder
      .addCase(resumeWorker.pending, (state) => {
        state.loading.resume = true;
        state.errors.resume = null;
      })
      .addCase(resumeWorker.fulfilled, (state) => {
        state.loading.resume = false;
      })
      .addCase(resumeWorker.rejected, (state, action) => {
        state.loading.resume = false;
        state.errors.resume = action.payload;
      });

    // Reset Worker
    builder
      .addCase(resetWorker.pending, (state) => {
        state.loading.reset = true;
        state.errors.reset = null;
      })
      .addCase(resetWorker.fulfilled, (state) => {
        state.loading.reset = false;
      })
      .addCase(resetWorker.rejected, (state, action) => {
        state.loading.reset = false;
        state.errors.reset = action.payload;
      });

    // Restart Worker
    builder
      .addCase(restartWorker.pending, (state) => {
        state.loading.restart = true;
        state.errors.restart = null;
      })
      .addCase(restartWorker.fulfilled, (state) => {
        state.loading.restart = false;
      })
      .addCase(restartWorker.rejected, (state, action) => {
        state.loading.restart = false;
        state.errors.restart = action.payload;
      });

    // Validate Run Start
    builder
      .addCase(validateRunStart.pending, (state) => {
        state.loading.validate = true;
        state.errors.validate = null;
      })
      .addCase(validateRunStart.fulfilled, (state, action) => {
        state.loading.validate = false;
        state.runValidation = action.payload;
      })
      .addCase(validateRunStart.rejected, (state, action) => {
        state.loading.validate = false;
        state.errors.validate = action.payload;
      });

    // Start Run
    builder
      .addCase(startRun.pending, (state) => {
        state.loading.start = true;
        state.errors.start = null;
        state.viewMode = 'loading';
      })
      .addCase(startRun.fulfilled, (state, action) => {
        state.loading.start = false;
        state.viewMode = 'grid';
        state.runValidation = action.payload.data?.validation;
      })
      .addCase(startRun.rejected, (state, action) => {
        state.loading.start = false;
        state.errors.start = action.payload;
        state.viewMode = 'initial';
      });

    // Reset Current Run
    builder
      .addCase(resetCurrentRun.pending, (state) => {
        state.loading.reset = true;
        state.errors.reset = null;
      })
      .addCase(resetCurrentRun.fulfilled, (state) => {
        state.loading.reset = false;
        state.viewMode = 'initial';
        state.gridWorkers = [];
      })
      .addCase(resetCurrentRun.rejected, (state, action) => {
        state.loading.reset = false;
        state.errors.reset = action.payload;
      });

    // Factory Reset
    builder
      .addCase(factoryReset.pending, (state) => {
        state.loading.reset = true;
        state.errors.reset = null;
      })
      .addCase(factoryReset.fulfilled, (state) => {
        state.loading.reset = false;
        state.viewMode = 'initial';
        state.gridWorkers = [];
      })
      .addCase(factoryReset.rejected, (state, action) => {
        state.loading.reset = false;
        state.errors.reset = action.payload;
      });

    // Fetch Grid Status
    builder
      .addCase(fetchGridStatus.pending, (state) => {
        state.loading.grid = true;
      })
      .addCase(fetchGridStatus.fulfilled, (state, action) => {
        state.loading.grid = false;
        state.gridWorkers = action.payload;
      })
      .addCase(fetchGridStatus.rejected, (state, action) => {
        state.loading.grid = false;
        state.errors.fetch = action.payload;
      });
  },
});

export const {
  setWorkers,
  updateWorker,
  updateMultipleWorkers,
  toggleWorkerSelection,
  clearSelection,
  selectAllWorkers: selectAllWorkersAction,
  clearError,
} = workersSlice.actions;

// Selectors
export const selectAllWorkers = (state) => state.workers.workers;
export const selectWorker = (annotatorId, domain) => (state) =>
  state.workers.workers.find(
    (w) => w.annotator_id === annotatorId && w.domain === domain
  );
export const selectWorkersByAnnotator = (annotatorId) => (state) =>
  state.workers.workers.filter((w) => w.annotator_id === annotatorId);
export const selectWorkersByDomain = (domain) => (state) =>
  state.workers.workers.filter((w) => w.domain === domain);
export const selectWorkersByStatus = (status) => (state) =>
  state.workers.workers.filter((w) => w.status === status);
export const selectRunningWorkers = (state) =>
  state.workers.workers.filter((w) => w.running);
export const selectCrashedWorkers = (state) =>
  state.workers.workers.filter((w) => w.stale || w.status === 'crashed');
export const selectSelectedWorkers = (state) => state.workers.selectedWorkers;
export const selectIsLoading = (state) => state.workers.loading;
export const selectErrors = (state) => state.workers.errors;

// New selectors for Control Center
export const selectViewMode = (state) => state.workers.viewMode;
export const selectGridWorkers = (state) => state.workers.gridWorkers;
export const selectRunValidation = (state) => state.workers.runValidation;

export default workersSlice.reducer;

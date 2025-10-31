import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { dataAPI, exportAPI } from '../../services/api';
import { PAGINATION } from '../../utils/constants';

// Initial state
const initialState = {
  annotations: {
    items: [],
    total: 0,
    page: 1,
    page_size: PAGINATION.DEFAULT_PAGE_SIZE,
    total_pages: 0,
    has_next: false,
    has_prev: false,
  },
  filters: {
    annotator_ids: [],
    domains: [],
    malformed_only: false,
    completed_only: false,
    search_text: '',
    date_from: null,
    date_to: null,
    page: PAGINATION.DEFAULT_PAGE,
    page_size: PAGINATION.DEFAULT_PAGE_SIZE,
  },
  selectedAnnotation: null,
  statistics: {
    total_annotations: 0,
    malformed_count: 0,
    completed_count: 0,
    by_annotator: {},
    by_domain: {},
  },
  loading: {
    annotations: false,
    annotation: false,
    statistics: false,
    retry: false,
    export: false,
  },
  errors: {
    annotations: null,
    annotation: null,
    statistics: null,
    retry: null,
    export: null,
  },
};

// Async thunks
export const fetchAnnotations = createAsyncThunk(
  'data/fetchAnnotations',
  async (filters = {}, { rejectWithValue }) => {
    try {
      const data = await dataAPI.getAnnotations(filters);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchAnnotation = createAsyncThunk(
  'data/fetchAnnotation',
  async ({ annotatorId, domain, sampleId }, { rejectWithValue }) => {
    try {
      const data = await dataAPI.getAnnotation(annotatorId, domain, sampleId);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchStatistics = createAsyncThunk(
  'data/fetchStatistics',
  async (filters = {}, { rejectWithValue }) => {
    try {
      const data = await dataAPI.getStatistics(filters);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const retryAnnotation = createAsyncThunk(
  'data/retryAnnotation',
  async ({ annotatorId, domain, sampleId }, { rejectWithValue }) => {
    try {
      const data = await dataAPI.retryAnnotation(annotatorId, domain, sampleId);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const exportData = createAsyncThunk(
  'data/exportData',
  async (exportRequest, { rejectWithValue }) => {
    try {
      const blob = await exportAPI.exportData(exportRequest);
      return blob;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Slice
const dataSlice = createSlice({
  name: 'data',
  initialState,
  reducers: {
    setAnnotations: (state, action) => {
      state.annotations = action.payload;
    },
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    updateFilter: (state, action) => {
      const { key, value } = action.payload;
      state.filters[key] = value;
    },
    resetFilters: (state) => {
      state.filters = initialState.filters;
    },
    setSelectedAnnotation: (state, action) => {
      state.selectedAnnotation = action.payload;
    },
    setStatistics: (state, action) => {
      state.statistics = action.payload;
    },
    setPage: (state, action) => {
      state.filters.page = action.payload;
      state.annotations.page = action.payload;
    },
    setPageSize: (state, action) => {
      state.filters.page_size = action.payload;
      state.annotations.page_size = action.payload;
      state.filters.page = 1; // Reset to first page when changing page size
      state.annotations.page = 1;
    },
    clearError: (state, action) => {
      const errorType = action.payload;
      if (state.errors[errorType] !== undefined) {
        state.errors[errorType] = null;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch Annotations
    builder
      .addCase(fetchAnnotations.pending, (state) => {
        state.loading.annotations = true;
        state.errors.annotations = null;
      })
      .addCase(fetchAnnotations.fulfilled, (state, action) => {
        state.loading.annotations = false;
        state.annotations = action.payload;
      })
      .addCase(fetchAnnotations.rejected, (state, action) => {
        state.loading.annotations = false;
        state.errors.annotations = action.payload;
      });

    // Fetch Annotation
    builder
      .addCase(fetchAnnotation.pending, (state) => {
        state.loading.annotation = true;
        state.errors.annotation = null;
      })
      .addCase(fetchAnnotation.fulfilled, (state, action) => {
        state.loading.annotation = false;
        state.selectedAnnotation = action.payload;
      })
      .addCase(fetchAnnotation.rejected, (state, action) => {
        state.loading.annotation = false;
        state.errors.annotation = action.payload;
      });

    // Fetch Statistics
    builder
      .addCase(fetchStatistics.pending, (state) => {
        state.loading.statistics = true;
        state.errors.statistics = null;
      })
      .addCase(fetchStatistics.fulfilled, (state, action) => {
        state.loading.statistics = false;
        state.statistics = action.payload;
      })
      .addCase(fetchStatistics.rejected, (state, action) => {
        state.loading.statistics = false;
        state.errors.statistics = action.payload;
      });

    // Retry Annotation
    builder
      .addCase(retryAnnotation.pending, (state) => {
        state.loading.retry = true;
        state.errors.retry = null;
      })
      .addCase(retryAnnotation.fulfilled, (state) => {
        state.loading.retry = false;
      })
      .addCase(retryAnnotation.rejected, (state, action) => {
        state.loading.retry = false;
        state.errors.retry = action.payload;
      });

    // Export Data
    builder
      .addCase(exportData.pending, (state) => {
        state.loading.export = true;
        state.errors.export = null;
      })
      .addCase(exportData.fulfilled, (state) => {
        state.loading.export = false;
      })
      .addCase(exportData.rejected, (state, action) => {
        state.loading.export = false;
        state.errors.export = action.payload;
      });
  },
});

export const {
  setAnnotations,
  setFilters,
  updateFilter,
  resetFilters,
  setSelectedAnnotation,
  setStatistics,
  setPage,
  setPageSize,
  clearError,
} = dataSlice.actions;

// Selectors
export const selectAnnotations = (state) => state.data.annotations;
export const selectAnnotationItems = (state) => state.data.annotations.items;
export const selectFilters = (state) => state.data.filters;
export const selectSelectedAnnotation = (state) => state.data.selectedAnnotation;
export const selectStatistics = (state) => state.data.statistics;
export const selectCurrentPage = (state) => state.data.annotations.page;
export const selectPageSize = (state) => state.data.annotations.page_size;
export const selectTotalPages = (state) => state.data.annotations.total_pages;
export const selectHasNext = (state) => state.data.annotations.has_next;
export const selectHasPrev = (state) => state.data.annotations.has_prev;
export const selectIsLoading = (state) => state.data.loading;
export const selectErrors = (state) => state.data.errors;

export default dataSlice.reducer;

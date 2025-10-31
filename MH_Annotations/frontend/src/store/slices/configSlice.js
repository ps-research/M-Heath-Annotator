import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { configAPI } from '../../services/api';

// Initial state
const initialState = {
  settings: {
    global: {
      model_name: 'gemma-3-27b-it',
      request_delay_seconds: 1,
      max_retries: 3,
      crash_detection_minutes: 5,
      control_check_iterations: 5,
      control_check_seconds: 10,
    },
    annotators: {}, // { 1: { urgency: {enabled, target_count}, ... }, ...}
  },
  apiKeys: {}, // { annotator_1: 'key', ... }
  prompts: {
    base: {}, // { urgency: {...}, ... }
    overrides: {}, // { annotator_1: { urgency: {...} } }
  },
  promptVersions: {
    loading: false,
    error: null,
    data: {}, // Structure: [annotator_id_domain] = {base, versions[]}
  },
  activeVersions: {}, // {annotator_1: {urgency: "v2_...", ...}, ...}
  loading: {
    settings: false,
    apiKeys: false,
    prompts: false,
    saving: false,
    promptVersions: false,
    savingVersion: false,
  },
  errors: {
    settings: null,
    apiKeys: null,
    prompts: null,
    promptVersions: null,
  },
};

// Async thunks
export const fetchSettings = createAsyncThunk(
  'config/fetchSettings',
  async (_, { rejectWithValue }) => {
    try {
      const data = await configAPI.getSettings();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateSettings = createAsyncThunk(
  'config/updateSettings',
  async (updates, { rejectWithValue }) => {
    try {
      const data = await configAPI.updateSettings(updates);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchAPIKeys = createAsyncThunk(
  'config/fetchAPIKeys',
  async (_, { rejectWithValue }) => {
    try {
      const data = await configAPI.getAPIKeys();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateAPIKey = createAsyncThunk(
  'config/updateAPIKey',
  async ({ annotatorId, apiKey }, { rejectWithValue }) => {
    try {
      await configAPI.updateAPIKey(annotatorId, apiKey);
      return { annotatorId, apiKey };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchPrompts = createAsyncThunk(
  'config/fetchPrompts',
  async (_, { rejectWithValue }) => {
    try {
      const data = await configAPI.getPrompts();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchPrompt = createAsyncThunk(
  'config/fetchPrompt',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      const data = await configAPI.getPrompt(annotatorId, domain);
      return { annotatorId, domain, ...data };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updatePrompt = createAsyncThunk(
  'config/updatePrompt',
  async ({ annotatorId, domain, content }, { rejectWithValue }) => {
    try {
      const data = await configAPI.updatePrompt(annotatorId, domain, content);
      return { annotatorId, domain, content, ...data };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const deletePrompt = createAsyncThunk(
  'config/deletePrompt',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      await configAPI.deletePrompt(annotatorId, domain);
      return { annotatorId, domain };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchDomainConfig = createAsyncThunk(
  'config/fetchDomainConfig',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      const data = await configAPI.getDomainConfig(annotatorId, domain);
      return { annotatorId, domain, config: data };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateDomainConfig = createAsyncThunk(
  'config/updateDomainConfig',
  async ({ annotatorId, domain, config }, { rejectWithValue }) => {
    try {
      const data = await configAPI.updateDomainConfig(annotatorId, domain, config);
      return { annotatorId, domain, config: data };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Phase 3 - Version Management Thunks
export const savePromptVersion = createAsyncThunk(
  'config/savePromptVersion',
  async ({ annotatorId, domain, versionName, content, description }, { rejectWithValue }) => {
    try {
      const data = await configAPI.savePromptVersion(
        annotatorId,
        domain,
        versionName,
        content,
        description
      );
      return { annotatorId, domain, ...data };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchPromptVersions = createAsyncThunk(
  'config/fetchPromptVersions',
  async ({ annotatorId, domain }, { rejectWithValue }) => {
    try {
      const data = await configAPI.getPromptVersions(annotatorId, domain);
      return { annotatorId, domain, ...data };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const setActiveVersion = createAsyncThunk(
  'config/setActiveVersion',
  async ({ annotatorId, domain, filename }, { rejectWithValue }) => {
    try {
      const data = await configAPI.setActiveVersion(annotatorId, domain, filename);
      return { annotatorId, domain, filename };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const deletePromptVersion = createAsyncThunk(
  'config/deletePromptVersion',
  async ({ annotatorId, domain, filename }, { rejectWithValue }) => {
    try {
      await configAPI.deletePromptVersion(annotatorId, domain, filename);
      return { annotatorId, domain, filename };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchVersionContent = createAsyncThunk(
  'config/fetchVersionContent',
  async ({ annotatorId, domain, filename }, { rejectWithValue }) => {
    try {
      const data = await configAPI.getVersionContent(annotatorId, domain, filename);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Slice
const configSlice = createSlice({
  name: 'config',
  initialState,
  reducers: {
    setSettings: (state, action) => {
      state.settings = action.payload;
    },
    setAPIKeys: (state, action) => {
      state.apiKeys = action.payload;
    },
    setPrompts: (state, action) => {
      state.prompts = action.payload;
    },
    updateSingleAPIKey: (state, action) => {
      const { annotatorId, apiKey } = action.payload;
      state.apiKeys[`annotator_${annotatorId}`] = apiKey;
    },
    updateSingleDomainConfig: (state, action) => {
      const { annotatorId, domain, config } = action.payload;
      if (!state.settings.annotators[annotatorId]) {
        state.settings.annotators[annotatorId] = {};
      }
      state.settings.annotators[annotatorId][domain] = config;
    },
    clearError: (state, action) => {
      const errorType = action.payload;
      if (state.errors[errorType] !== undefined) {
        state.errors[errorType] = null;
      }
    },
    clearAllErrors: (state) => {
      state.errors = initialState.errors;
    },
  },
  extraReducers: (builder) => {
    // Fetch Settings
    builder
      .addCase(fetchSettings.pending, (state) => {
        state.loading.settings = true;
        state.errors.settings = null;
      })
      .addCase(fetchSettings.fulfilled, (state, action) => {
        state.loading.settings = false;
        state.settings = action.payload;
      })
      .addCase(fetchSettings.rejected, (state, action) => {
        state.loading.settings = false;
        state.errors.settings = action.payload;
      });

    // Update Settings
    builder
      .addCase(updateSettings.pending, (state) => {
        state.loading.saving = true;
        state.errors.settings = null;
      })
      .addCase(updateSettings.fulfilled, (state, action) => {
        state.loading.saving = false;
        state.settings = action.payload;
      })
      .addCase(updateSettings.rejected, (state, action) => {
        state.loading.saving = false;
        state.errors.settings = action.payload;
      });

    // Fetch API Keys
    builder
      .addCase(fetchAPIKeys.pending, (state) => {
        state.loading.apiKeys = true;
        state.errors.apiKeys = null;
      })
      .addCase(fetchAPIKeys.fulfilled, (state, action) => {
        state.loading.apiKeys = false;
        state.apiKeys = action.payload?.data || action.payload; ;
      })
      .addCase(fetchAPIKeys.rejected, (state, action) => {
        state.loading.apiKeys = false;
        state.errors.apiKeys = action.payload;
      });

    // Update API Key
    builder
      .addCase(updateAPIKey.pending, (state) => {
        state.loading.saving = true;
      })
      .addCase(updateAPIKey.fulfilled, (state, action) => {
        state.loading.saving = false;
        const { annotatorId, apiKey } = action.payload;
        state.apiKeys[`annotator_${annotatorId}`] = apiKey;
      })
      .addCase(updateAPIKey.rejected, (state, action) => {
        state.loading.saving = false;
        state.errors.apiKeys = action.payload;
      });

    // Fetch Prompts
    builder
      .addCase(fetchPrompts.pending, (state) => {
        state.loading.prompts = true;
        state.errors.prompts = null;
      })
      .addCase(fetchPrompts.fulfilled, (state, action) => {
        state.loading.prompts = false;
        state.prompts = action.payload;
      })
      .addCase(fetchPrompts.rejected, (state, action) => {
        state.loading.prompts = false;
        state.errors.prompts = action.payload;
      });

    // Update Domain Config
    builder
      .addCase(updateDomainConfig.fulfilled, (state, action) => {
        const { annotatorId, domain, config } = action.payload;
        if (!state.settings.annotators[annotatorId]) {
          state.settings.annotators[annotatorId] = {};
        }
        state.settings.annotators[annotatorId][domain] = config;
      });

    // Save Prompt Version
    builder
      .addCase(savePromptVersion.pending, (state) => {
        state.loading.savingVersion = true;
        state.errors.promptVersions = null;
      })
      .addCase(savePromptVersion.fulfilled, (state, action) => {
        state.loading.savingVersion = false;
        // Optionally update the versions data if it's already loaded
        const { annotatorId, domain } = action.payload;
        const key = `${annotatorId}_${domain}`;
        if (state.promptVersions.data[key]) {
          // Trigger refresh by clearing the data
          delete state.promptVersions.data[key];
        }
      })
      .addCase(savePromptVersion.rejected, (state, action) => {
        state.loading.savingVersion = false;
        state.errors.promptVersions = action.payload;
      });

    // Fetch Prompt Versions
    builder
      .addCase(fetchPromptVersions.pending, (state) => {
        state.promptVersions.loading = true;
        state.promptVersions.error = null;
      })
      .addCase(fetchPromptVersions.fulfilled, (state, action) => {
        state.promptVersions.loading = false;
        const { annotatorId, domain, ...versionsData } = action.payload;
        const key = `${annotatorId}_${domain}`;
        state.promptVersions.data[key] = versionsData;
      })
      .addCase(fetchPromptVersions.rejected, (state, action) => {
        state.promptVersions.loading = false;
        state.promptVersions.error = action.payload;
      });

    // Set Active Version
    builder
      .addCase(setActiveVersion.pending, (state) => {
        state.loading.saving = true;
      })
      .addCase(setActiveVersion.fulfilled, (state, action) => {
        state.loading.saving = false;
        const { annotatorId, domain, filename } = action.payload;
        const annotatorKey = `annotator_${annotatorId}`;
        if (!state.activeVersions[annotatorKey]) {
          state.activeVersions[annotatorKey] = {};
        }
        state.activeVersions[annotatorKey][domain] = filename;

        // Update the versions data to reflect the new active version
        const key = `${annotatorId}_${domain}`;
        if (state.promptVersions.data[key]) {
          // Mark all versions as not active
          if (state.promptVersions.data[key].base) {
            state.promptVersions.data[key].base.is_active = filename === null;
          }
          if (state.promptVersions.data[key].versions) {
            state.promptVersions.data[key].versions = state.promptVersions.data[
              key
            ].versions.map((v) => ({
              ...v,
              is_active: v.filename === filename,
            }));
          }
        }
      })
      .addCase(setActiveVersion.rejected, (state, action) => {
        state.loading.saving = false;
        state.errors.promptVersions = action.payload;
      });

    // Delete Prompt Version
    builder
      .addCase(deletePromptVersion.pending, (state) => {
        state.loading.saving = true;
      })
      .addCase(deletePromptVersion.fulfilled, (state, action) => {
        state.loading.saving = false;
        const { annotatorId, domain, filename } = action.payload;
        const key = `${annotatorId}_${domain}`;
        // Remove from versions data
        if (state.promptVersions.data[key]?.versions) {
          state.promptVersions.data[key].versions = state.promptVersions.data[
            key
          ].versions.filter((v) => v.filename !== filename);
        }
      })
      .addCase(deletePromptVersion.rejected, (state, action) => {
        state.loading.saving = false;
        state.errors.promptVersions = action.payload;
      });
  },
});

export const {
  setSettings,
  setAPIKeys,
  setPrompts,
  updateSingleAPIKey,
  updateSingleDomainConfig,
  clearError,
  clearAllErrors,
} = configSlice.actions;

// Selectors
export const selectSettings = (state) => state.config.settings;
export const selectGlobalSettings = (state) => state.config.settings.global;
export const selectAnnotatorSettings = (state) => state.config.settings.annotators;
export const selectAPIKeys = (state) => state.config.apiKeys;
export const selectAPIKey = (annotatorId) => (state) =>
  state.config.apiKeys[`annotator_${annotatorId}`];
export const selectPrompts = (state) => state.config.prompts;
export const selectDomainConfig = (annotatorId, domain) => (state) =>
  state.config.settings.annotators[annotatorId]?.[domain];
export const selectIsLoading = (state) => state.config.loading;
export const selectErrors = (state) => state.config.errors;

// Phase 3 - Version Management Selectors
export const selectPromptVersions = (annotatorId, domain) => (state) =>
  state.config.promptVersions.data[`${annotatorId}_${domain}`] || null;
export const selectActiveVersionFilename = (annotatorId, domain) => (state) =>
  state.config.activeVersions[`annotator_${annotatorId}`]?.[domain] || null;
export const selectPromptVersionsLoading = (state) => state.config.promptVersions.loading;
export const selectSavingVersion = (state) => state.config.loading.savingVersion;

export default configSlice.reducer;

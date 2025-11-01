import axios from 'axios';

// Create Axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add timestamp for logging
    config.metadata = { startTime: new Date() };

    // Log in development
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Calculate response time
    if (response.config.metadata) {
      const endTime = new Date();
      const duration = endTime - response.config.metadata.startTime;

      if (import.meta.env.DEV) {
        console.log(
          `[API Response] ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`
        );
      }
    }

    // Extract data from APIResponse wrapper if present
    // Backend returns: { success: bool, data: any, message: string }
    // We want to return just the 'data' field
    if (response.data && typeof response.data === 'object' && 'data' in response.data) {
      return response.data.data;
    }

    return response.data;
  },
  (error) => {
    // Handle errors
    let errorMessage = 'An error occurred';

    if (error.response) {
      // Server responded with error status
      if (error.response.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response.status === 404) {
        errorMessage = 'Resource not found';
      } else if (error.response.status === 500) {
        errorMessage = 'Server error occurred';
      } else if (error.response.status >= 400 && error.response.status < 500) {
        errorMessage = `Client error: ${error.response.statusText}`;
      }
    } else if (error.request) {
      // Request made but no response
      errorMessage = 'No response from server';
    } else if (error.code === 'ECONNABORTED') {
      errorMessage = 'Request timeout';
    } else {
      errorMessage = error.message || 'Network error';
    }

    if (import.meta.env.DEV) {
      console.error('[API Error]', errorMessage, error);
    }

    return Promise.reject(new Error(errorMessage));
  }
);

// Configuration API
export const configAPI = {
  getSettings: () => api.get('/api/config/settings'),
  updateSettings: (updates) => api.put('/api/config/settings', updates),

  getAPIKeys: () => api.get('/api/config/api-keys'),
  updateAPIKey: (annotatorId, apiKey) =>
    api.put(`/api/config/api-keys/${annotatorId}`, { api_key: apiKey }),
  testAPIKey: (annotatorId, apiKey) =>
    api.post(`/api/config/test-api-key/${annotatorId}`, { api_key: apiKey }),

  getPrompts: () => api.get('/api/config/prompts'),
  getPrompt: (annotatorId, domain) =>
    api.get(`/api/config/prompts/${annotatorId}/${domain}`),
  updatePrompt: (annotatorId, domain, content) =>
    api.put(`/api/config/prompts/${annotatorId}/${domain}`, { content }),
  deletePrompt: (annotatorId, domain) =>
    api.delete(`/api/config/prompts/${annotatorId}/${domain}`),

  getDomainConfig: (annotatorId, domain) =>
    api.get(`/api/config/annotators/${annotatorId}/${domain}`),
  updateDomainConfig: (annotatorId, domain, config) =>
    api.put(`/api/config/annotators/${annotatorId}/${domain}`, config),

  // Phase 3 - Version Management
  savePromptVersion: (annotatorId, domain, versionName, content, description) =>
    api.post(`/api/config/prompts/${annotatorId}/${domain}/versions`, {
      version_name: versionName,
      content,
      description,
    }),
  getPromptVersions: (annotatorId, domain) =>
    api.get(`/api/config/prompts/${annotatorId}/${domain}/versions`),
  setActiveVersion: (annotatorId, domain, filename) =>
    api.put(`/api/config/prompts/${annotatorId}/${domain}/active-version`, {
      filename,
    }),
  deletePromptVersion: (annotatorId, domain, filename) =>
    api.delete(`/api/config/prompts/${annotatorId}/${domain}/versions/${filename}`),
  getVersionContent: (annotatorId, domain, filename) =>
    api.get(`/api/config/prompts/${annotatorId}/${domain}/versions/${filename}`),

  // Dataset Info
  getDatasetInfo: () => api.get('/api/config/dataset/info'),
};

// Control API
export const controlAPI = {
  startWorker: (annotatorId, domain) =>
    api.post('/api/control/start', { annotator_id: annotatorId, domain }),
  stopWorker: (annotatorId, domain) =>
    api.post('/api/control/stop', { annotator_id: annotatorId, domain }),
  pauseWorker: (annotatorId, domain) =>
    api.post('/api/control/pause', { annotator_id: annotatorId, domain }),
  resumeWorker: (annotatorId, domain) =>
    api.post('/api/control/resume', { annotator_id: annotatorId, domain }),

  startAll: () => api.post('/api/control/start'),
  stopAll: () => api.post('/api/control/stop'),
  pauseAll: () => api.post('/api/control/pause'),
  resumeAll: () => api.post('/api/control/resume'),

  resetWorker: (annotatorId, domain, confirmation) =>
    api.post('/api/control/reset', {
      annotator_id: annotatorId,
      domain,
      confirmation,
    }),
  resetAll: (confirmation) =>
    api.post('/api/control/reset', { confirmation }),

  restartWorker: (annotatorId, domain) =>
    api.post(`/api/control/restart/${annotatorId}/${domain}`),
};

// Monitoring API
export const monitoringAPI = {
  getOverview: () => api.get('/api/monitoring/overview'),

  getWorkers: (filters = {}) => api.get('/api/monitoring/workers', { params: filters }),
  getWorker: (annotatorId, domain) =>
    api.get(`/api/monitoring/workers/${annotatorId}/${domain}`),

  getHealth: () => api.get('/api/monitoring/health'),
  getQuota: () => api.get('/api/monitoring/quota'),

  getLogs: (params = {}) => api.get('/api/monitoring/logs', { params }),
};

// Data API
export const dataAPI = {
  getAnnotations: (filters = {}) =>
    api.get('/api/data/annotations', { params: filters }),
  getAnnotation: (annotatorId, domain, sampleId) =>
    api.get(`/api/data/annotations/${annotatorId}/${domain}/${sampleId}`),

  getStatistics: (filters = {}) =>
    api.get('/api/data/statistics', { params: filters }),

  retryAnnotation: (annotatorId, domain, sampleId) =>
    api.post(`/api/data/retry/${annotatorId}/${domain}/${sampleId}`),
};

// Export API
export const exportAPI = {
  exportData: (exportRequest) =>
    api.post('/api/export', exportRequest, {
      responseType: 'blob',
    }),
  previewExport: (exportRequest) =>
    api.get('/api/export/preview', { params: exportRequest }),
};

export default api;

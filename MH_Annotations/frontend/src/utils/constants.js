// Annotation domains
export const DOMAINS = [
  'urgency',
  'therapeutic',
  'intensity',
  'adjunct',
  'modality',
  'redressal',
];

// Annotator IDs
export const ANNOTATOR_IDS = [1, 2, 3, 4, 5];

// Worker statuses
export const WORKER_STATUS = {
  STOPPED: 'stopped',
  RUNNING: 'running',
  PAUSED: 'paused',
  COMPLETED: 'completed',
  CRASHED: 'crashed',
};

// Panel names
export const PANELS = {
  CONFIGURATION: 'configuration',
  PROMPTS: 'prompts',
  CONTROL: 'control',
  MONITORING: 'monitoring',
  DATA: 'data',
  EXPORT: 'export',
  CRASH: 'crash',
};

// Export formats
export const EXPORT_FORMATS = {
  EXCEL: 'excel',
  JSON: 'json',
};

// Log levels
export const LOG_LEVELS = {
  ERROR: 'ERROR',
  WARNING: 'WARNING',
  INFO: 'INFO',
  DEBUG: 'DEBUG',
};

// WebSocket event types
export const WS_EVENTS = {
  FULL_STATE: 'full_state',
  PROGRESS_UPDATE: 'progress_update',
  STATUS_CHANGE: 'status_change',
  ERROR: 'error',
  CRASH_DETECTED: 'crash_detected',
  HEARTBEAT: 'heartbeat',
};

// Model options
export const MODEL_OPTIONS = [
  'gemini-2.0-flash-exp',
  'gemini-1.5-flash',
  'gemini-1.5-pro',
];

// Sample limit constraints
export const SAMPLE_LIMIT = {
  MIN: 0,
  MAX: 2000,
  STEP: 5,
  DEFAULT: 0,
};

// Pagination defaults
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 50,
  PAGE_SIZE_OPTIONS: [10, 25, 50, 100, 500],
};

// Refresh intervals (ms)
export const REFRESH_INTERVALS = {
  FAST: 5000,    // 5 seconds
  MEDIUM: 10000, // 10 seconds
  SLOW: 30000,   // 30 seconds
  MANUAL: 60000, // 60 seconds
};

// Confirmation text for dangerous operations
export const CONFIRMATION_TEXT = 'DELETE';

// API timeouts (ms)
export const API_TIMEOUT = 30000; // 30 seconds

// WebSocket config
export const WS_CONFIG = {
  RECONNECT_DELAY: 3000,
  MAX_RECONNECT_ATTEMPTS: 5,
  HEARTBEAT_INTERVAL: 30000,
};

// Domain display names
export const DOMAIN_NAMES = {
  urgency: 'Urgency',
  therapeutic: 'Therapeutic',
  intensity: 'Intensity',
  adjunct: 'Adjunct',
  modality: 'Modality',
  redressal: 'Redressal',
};

// Status colors
export const STATUS_COLORS = {
  running: 'success',
  paused: 'warning',
  stopped: 'default',
  completed: 'info',
  crashed: 'error',
};

// Icons for panels
export const PANEL_ICONS = {
  configuration: 'Settings',
  prompts: 'Edit',
  control: 'PlayArrow',
  monitoring: 'Dashboard',
  data: 'TableChart',
  export: 'FileDownload',
  crash: 'Warning',
};

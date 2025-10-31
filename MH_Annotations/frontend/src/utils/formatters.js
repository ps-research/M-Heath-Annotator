import { formatDistanceToNow, format, formatDuration, intervalToDuration } from 'date-fns';

/**
 * Format a date string or Date object to a readable format
 */
export const formatDate = (date) => {
  if (!date) return 'N/A';
  try {
    return format(new Date(date), 'MMM dd, yyyy HH:mm:ss');
  } catch (error) {
    return 'Invalid date';
  }
};

/**
 * Format a date to relative time (e.g., "2 minutes ago")
 */
export const formatRelativeTime = (date) => {
  if (!date) return 'N/A';
  try {
    return formatDistanceToNow(new Date(date), { addSuffix: true });
  } catch (error) {
    return 'Invalid date';
  }
};

/**
 * Format time in HH:MM:SS format
 */
export const formatTime = (date) => {
  if (!date) return 'N/A';
  try {
    return format(new Date(date), 'HH:mm:ss');
  } catch (error) {
    return 'Invalid time';
  }
};

/**
 * Format a number as percentage
 */
export const formatPercentage = (value, decimals = 1) => {
  if (value === null || value === undefined) return '0%';
  return `${Number(value).toFixed(decimals)}%`;
};

/**
 * Format progress ratio (completed/total) as percentage
 */
export const formatProgress = (completed, total) => {
  if (!total || total === 0) return '0%';
  const percentage = (completed / total) * 100;
  return formatPercentage(percentage);
};

/**
 * Format speed (samples per minute)
 */
export const formatSpeed = (speed) => {
  if (speed === null || speed === undefined) return '0/min';
  return `${Number(speed).toFixed(1)}/min`;
};

/**
 * Format duration in seconds to readable format
 */
export const formatDurationSeconds = (seconds) => {
  if (!seconds || seconds <= 0) return 'N/A';

  try {
    const duration = intervalToDuration({ start: 0, end: seconds * 1000 });
    const parts = [];

    if (duration.days) parts.push(`${duration.days}d`);
    if (duration.hours) parts.push(`${duration.hours}h`);
    if (duration.minutes) parts.push(`${duration.minutes}m`);
    if (duration.seconds && !duration.hours && !duration.days) {
      parts.push(`${duration.seconds}s`);
    }

    return parts.join(' ') || '0s';
  } catch (error) {
    return 'N/A';
  }
};

/**
 * Format file size in bytes to readable format
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * Format number with thousand separators
 */
export const formatNumber = (value) => {
  if (value === null || value === undefined) return '0';
  return Number(value).toLocaleString();
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text, maxLength = 50) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Mask API key (show first 8 and last 4 characters)
 */
export const maskAPIKey = (apiKey) => {
  if (!apiKey || apiKey.length < 12) return '***';
  return `${apiKey.substring(0, 8)}...${apiKey.substring(apiKey.length - 4)}`;
};

/**
 * Format worker ID (annotator-domain)
 */
export const formatWorkerID = (annotatorId, domain) => {
  return `${annotatorId}-${domain}`;
};

/**
 * Format annotator name
 */
export const formatAnnotatorName = (annotatorId) => {
  return `Annotator ${annotatorId}`;
};

/**
 * Format domain name (capitalize first letter)
 */
export const formatDomainName = (domain) => {
  if (!domain) return '';
  return domain.charAt(0).toUpperCase() + domain.slice(1);
};

/**
 * Format error message (extract meaningful part)
 */
export const formatErrorMessage = (error) => {
  if (!error) return 'Unknown error';

  if (typeof error === 'string') return error;

  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }

  if (error.message) return error.message;

  return 'An error occurred';
};

/**
 * Format sample ID
 */
export const formatSampleID = (sampleId) => {
  if (!sampleId) return 'N/A';
  return String(sampleId);
};

/**
 * Get status display text
 */
export const getStatusText = (status) => {
  const statusMap = {
    running: 'Running',
    paused: 'Paused',
    stopped: 'Stopped',
    completed: 'Completed',
    crashed: 'Crashed',
  };
  return statusMap[status] || status;
};

/**
 * Get log level color
 */
export const getLogLevelColor = (level) => {
  const colors = {
    ERROR: '#f44336',
    WARNING: '#ff9800',
    INFO: '#2196f3',
    DEBUG: '#9e9e9e',
  };
  return colors[level] || colors.INFO;
};

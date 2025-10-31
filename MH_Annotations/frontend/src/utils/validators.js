import { SAMPLE_LIMIT, DOMAINS, ANNOTATOR_IDS } from './constants';

/**
 * Validate API key format
 */
export const validateAPIKey = (apiKey) => {
  if (!apiKey || typeof apiKey !== 'string') {
    return { valid: false, error: 'API key is required' };
  }

  if (apiKey.trim().length === 0) {
    return { valid: false, error: 'API key cannot be empty' };
  }

  // Basic length check (Google API keys are typically 39 characters)
  if (apiKey.length < 20) {
    return { valid: false, error: 'API key appears to be too short' };
  }

  return { valid: true, error: null };
};

/**
 * Validate sample limit
 */
export const validateSampleLimit = (limit) => {
  const numLimit = Number(limit);

  if (isNaN(numLimit)) {
    return { valid: false, error: 'Sample limit must be a number' };
  }

  if (numLimit < SAMPLE_LIMIT.MIN) {
    return { valid: false, error: `Sample limit cannot be less than ${SAMPLE_LIMIT.MIN}` };
  }

  if (numLimit > SAMPLE_LIMIT.MAX) {
    return { valid: false, error: `Sample limit cannot exceed ${SAMPLE_LIMIT.MAX}` };
  }

  if (numLimit % SAMPLE_LIMIT.STEP !== 0) {
    return { valid: false, error: `Sample limit must be a multiple of ${SAMPLE_LIMIT.STEP}` };
  }

  return { valid: true, error: null };
};

/**
 * Validate annotator ID
 */
export const validateAnnotatorID = (annotatorId) => {
  const numId = Number(annotatorId);

  if (isNaN(numId)) {
    return { valid: false, error: 'Annotator ID must be a number' };
  }

  if (!ANNOTATOR_IDS.includes(numId)) {
    return { valid: false, error: `Annotator ID must be one of: ${ANNOTATOR_IDS.join(', ')}` };
  }

  return { valid: true, error: null };
};

/**
 * Validate domain name
 */
export const validateDomain = (domain) => {
  if (!domain || typeof domain !== 'string') {
    return { valid: false, error: 'Domain is required' };
  }

  if (!DOMAINS.includes(domain.toLowerCase())) {
    return { valid: false, error: `Domain must be one of: ${DOMAINS.join(', ')}` };
  }

  return { valid: true, error: null };
};

/**
 * Validate prompt content
 */
export const validatePrompt = (content) => {
  if (!content || typeof content !== 'string') {
    return { valid: false, error: 'Prompt content is required' };
  }

  if (content.trim().length === 0) {
    return { valid: false, error: 'Prompt cannot be empty' };
  }

  // Check for {text} placeholder
  if (!content.includes('{text}')) {
    return { valid: false, error: 'Prompt must contain {text} placeholder' };
  }

  return { valid: true, error: null };
};

/**
 * Validate request delay
 */
export const validateRequestDelay = (delay) => {
  const numDelay = Number(delay);

  if (isNaN(numDelay)) {
    return { valid: false, error: 'Request delay must be a number' };
  }

  if (numDelay < 0) {
    return { valid: false, error: 'Request delay cannot be negative' };
  }

  if (numDelay > 60) {
    return { valid: false, error: 'Request delay cannot exceed 60 seconds' };
  }

  return { valid: true, error: null };
};

/**
 * Validate max retries
 */
export const validateMaxRetries = (retries) => {
  const numRetries = Number(retries);

  if (isNaN(numRetries)) {
    return { valid: false, error: 'Max retries must be a number' };
  }

  if (numRetries < 0) {
    return { valid: false, error: 'Max retries cannot be negative' };
  }

  if (numRetries > 10) {
    return { valid: false, error: 'Max retries cannot exceed 10' };
  }

  return { valid: true, error: null };
};

/**
 * Validate crash detection minutes
 */
export const validateCrashDetection = (minutes) => {
  const numMinutes = Number(minutes);

  if (isNaN(numMinutes)) {
    return { valid: false, error: 'Crash detection must be a number' };
  }

  if (numMinutes < 1) {
    return { valid: false, error: 'Crash detection cannot be less than 1 minute' };
  }

  if (numMinutes > 60) {
    return { valid: false, error: 'Crash detection cannot exceed 60 minutes' };
  }

  return { valid: true, error: null };
};

/**
 * Validate email format (for future use)
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!email || typeof email !== 'string') {
    return { valid: false, error: 'Email is required' };
  }

  if (!emailRegex.test(email)) {
    return { valid: false, error: 'Invalid email format' };
  }

  return { valid: true, error: null };
};

/**
 * Validate confirmation text for dangerous operations
 */
export const validateConfirmation = (input, expectedText) => {
  if (!input || typeof input !== 'string') {
    return { valid: false, error: 'Confirmation text is required' };
  }

  if (input !== expectedText) {
    return { valid: false, error: `Please type "${expectedText}" to confirm` };
  }

  return { valid: true, error: null };
};

/**
 * Validate date range
 */
export const validateDateRange = (startDate, endDate) => {
  if (!startDate || !endDate) {
    return { valid: true, error: null }; // Optional
  }

  const start = new Date(startDate);
  const end = new Date(endDate);

  if (isNaN(start.getTime()) || isNaN(end.getTime())) {
    return { valid: false, error: 'Invalid date format' };
  }

  if (start > end) {
    return { valid: false, error: 'Start date must be before end date' };
  }

  return { valid: true, error: null };
};

/**
 * Validate page number
 */
export const validatePage = (page, totalPages) => {
  const numPage = Number(page);

  if (isNaN(numPage)) {
    return { valid: false, error: 'Page must be a number' };
  }

  if (numPage < 1) {
    return { valid: false, error: 'Page must be at least 1' };
  }

  if (totalPages && numPage > totalPages) {
    return { valid: false, error: `Page cannot exceed ${totalPages}` };
  }

  return { valid: true, error: null };
};

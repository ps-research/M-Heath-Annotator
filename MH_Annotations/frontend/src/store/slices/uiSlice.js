import { createSlice } from '@reduxjs/toolkit';
import { PANELS } from '../../utils/constants';

const initialState = {
  currentPanel: PANELS.MONITORING,
  sidebarOpen: true,
  dialogs: {
    resetConfirm: {
      open: false,
      scope: null, // 'single' | 'all'
      annotator_id: null,
      domain: null,
    },
    workerDetail: {
      open: false,
      annotator_id: null,
      domain: null,
    },
    annotationDetail: {
      open: false,
      annotation: null,
    },
    promptEditor: {
      open: false,
      annotator_id: null,
      domain: null,
    },
  },
  snackbar: {
    open: false,
    message: '',
    severity: 'info', // 'success' | 'error' | 'warning' | 'info'
  },
  theme: 'light', // 'light' | 'dark'
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setCurrentPanel: (state, action) => {
      state.currentPanel = action.payload;
    },
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action) => {
      state.sidebarOpen = action.payload;
    },
    openDialog: (state, action) => {
      const { dialog, data } = action.payload;
      if (state.dialogs[dialog]) {
        state.dialogs[dialog] = {
          open: true,
          ...data,
        };
      }
    },
    closeDialog: (state, action) => {
      const dialog = action.payload;
      if (state.dialogs[dialog]) {
        state.dialogs[dialog] = initialState.dialogs[dialog];
      }
    },
    closeAllDialogs: (state) => {
      state.dialogs = initialState.dialogs;
    },
    showSnackbar: (state, action) => {
      const { message, severity = 'info' } = action.payload;
      state.snackbar = {
        open: true,
        message,
        severity,
      };
    },
    hideSnackbar: (state) => {
      state.snackbar.open = false;
    },
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
    },
    setTheme: (state, action) => {
      state.theme = action.payload;
    },
  },
});

export const {
  setCurrentPanel,
  toggleSidebar,
  setSidebarOpen,
  openDialog,
  closeDialog,
  closeAllDialogs,
  showSnackbar,
  hideSnackbar,
  toggleTheme,
  setTheme,
} = uiSlice.actions;

// Selectors
export const selectCurrentPanel = (state) => state.ui.currentPanel;
export const selectSidebarOpen = (state) => state.ui.sidebarOpen;
export const selectDialogs = (state) => state.ui.dialogs;
export const selectDialog = (dialog) => (state) => state.ui.dialogs[dialog];
export const selectSnackbar = (state) => state.ui.snackbar;
export const selectTheme = (state) => state.ui.theme;

export default uiSlice.reducer;

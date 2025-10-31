import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Box, Snackbar, Alert } from '@mui/material';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { hideSnackbar, selectSnackbar } from '../../store/slices/uiSlice';

const SIDEBAR_WIDTH = 240;
const TOOLBAR_HEIGHT = 64;

/**
 * Main layout component
 */
const MainLayout = ({ children }) => {
  const dispatch = useDispatch();
  const snackbar = useSelector(selectSnackbar);

  const handleCloseSnackbar = () => {
    dispatch(hideSnackbar());
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Top Bar */}
      <TopBar />

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          ml: `${SIDEBAR_WIDTH}px`,
          mt: `${TOOLBAR_HEIGHT}px`,
          backgroundColor: 'background.default',
          minHeight: `calc(100vh - ${TOOLBAR_HEIGHT}px)`,
        }}
      >
        {children}
      </Box>

      {/* Global Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MainLayout;

import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Tooltip,
  Box,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
} from '@mui/icons-material';
import { toggleSidebar, toggleTheme, selectTheme } from '../../store/slices/uiSlice';
import { useWebSocket } from '../../hooks/useWebSocket';

/**
 * Top app bar component
 */
const TopBar = () => {
  const dispatch = useDispatch();
  const theme = useSelector(selectTheme);
  const { isConnected, connectionStatus } = useWebSocket();

  const handleToggleSidebar = () => {
    dispatch(toggleSidebar());
  };

  const handleToggleTheme = () => {
    dispatch(toggleTheme());
  };

  const getConnectionColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'success';
      case 'connecting':
      case 'reconnecting':
        return 'warning';
      case 'disconnected':
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getConnectionLabel = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'reconnecting':
        return 'Reconnecting...';
      case 'disconnected':
        return 'Disconnected';
      case 'failed':
        return 'Connection Failed';
      default:
        return 'Unknown';
    }
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>
        {/* Menu Button */}
        <IconButton
          color="inherit"
          edge="start"
          onClick={handleToggleSidebar}
          sx={{ mr: 2, display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>

        {/* Title */}
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Mental Health Annotation Dashboard
        </Typography>

        {/* WebSocket Status */}
        <Box sx={{ mr: 2 }}>
          <Tooltip title={getConnectionLabel()}>
            <Chip
              label={getConnectionLabel()}
              color={getConnectionColor()}
              size="small"
              variant="outlined"
              sx={{
                color: 'white',
                borderColor: 'white',
              }}
            />
          </Tooltip>
        </Box>

        {/* Theme Toggle */}
        <Tooltip title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
          <IconButton color="inherit" onClick={handleToggleTheme}>
            {theme === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
};

export default TopBar;

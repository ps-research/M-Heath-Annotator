import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Badge,
  Divider,
  Typography,
  Box,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Edit as EditIcon,
  PlayArrow as PlayArrowIcon,
  Dashboard as DashboardIcon,
  TableChart as TableChartIcon,
  FileDownload as FileDownloadIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { setCurrentPanel, selectCurrentPanel, selectSidebarOpen } from '../../store/slices/uiSlice';
import { selectCrashedWorkers } from '../../store/slices/monitoringSlice';
import { PANELS } from '../../utils/constants';

const SIDEBAR_WIDTH = 240;

/**
 * Navigation sidebar component
 */
const Sidebar = () => {
  const dispatch = useDispatch();
  const currentPanel = useSelector(selectCurrentPanel);
  const sidebarOpen = useSelector(selectSidebarOpen);
  const crashedWorkers = useSelector(selectCrashedWorkers);

  const menuItems = [
    {
      id: PANELS.CONFIGURATION,
      label: 'Configuration',
      icon: <SettingsIcon />,
      badge: null,
    },
    {
      id: PANELS.PROMPTS,
      label: 'Prompt Editor',
      icon: <EditIcon />,
      badge: null,
    },
    {
      id: PANELS.CONTROL,
      label: 'Control Center',
      icon: <PlayArrowIcon />,
      badge: null,
    },
    {
      id: PANELS.MONITORING,
      label: 'Monitoring',
      icon: <DashboardIcon />,
      badge: null,
    },
    {
      id: PANELS.DATA,
      label: 'Data Viewer',
      icon: <TableChartIcon />,
      badge: null,
    },
    {
      id: PANELS.EXPORT,
      label: 'Export',
      icon: <FileDownloadIcon />,
      badge: null,
    },
    {
      id: PANELS.CRASH,
      label: 'Crash Monitor',
      icon: <WarningIcon />,
      badge: crashedWorkers.length > 0 ? crashedWorkers.length : null,
    },
  ];

  const handlePanelChange = (panelId) => {
    dispatch(setCurrentPanel(panelId));
  };

  return (
    <Drawer
      variant="permanent"
      open={sidebarOpen}
      sx={{
        width: SIDEBAR_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: SIDEBAR_WIDTH,
          boxSizing: 'border-box',
          borderRight: 'none',
        },
      }}
    >
      {/* Logo/Title */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Typography variant="h6" component="div" noWrap fontWeight="bold">
          MH Annotator
        </Typography>
      </Box>

      <Divider />

      {/* Navigation Menu */}
      <List sx={{ pt: 2 }}>
        {menuItems.map((item) => (
          <ListItemButton
            key={item.id}
            selected={currentPanel === item.id}
            onClick={() => handlePanelChange(item.id)}
            sx={{
              mx: 1,
              borderRadius: 1,
              mb: 0.5,
              '&.Mui-selected': {
                backgroundColor: 'primary.main',
                color: 'primary.contrastText',
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
                '& .MuiListItemIcon-root': {
                  color: 'primary.contrastText',
                },
              },
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 40,
                color: currentPanel === item.id ? 'inherit' : 'action.active',
              }}
            >
              {item.badge !== null ? (
                <Badge badgeContent={item.badge} color="error">
                  {item.icon}
                </Badge>
              ) : (
                item.icon
              )}
            </ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar;

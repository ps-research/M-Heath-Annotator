import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainLayout } from './components/Layout';
import { MonitoringPanel } from './components/Monitoring';
import { ConfigurationPanel } from './components/Configuration';
import { PromptEditorPanel } from './components/PromptEditor';
import { ControlCenterPanel } from './components/ControlCenter';
import { DataViewerPanel } from './components/DataViewer';
import { ExportPanel } from './components/Export';
import { CrashMonitorPanel } from './components/CrashMonitor';
import { selectCurrentPanel, selectTheme } from './store/slices/uiSlice';
import { getTheme } from './theme';
import { PANELS } from './utils/constants';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30 seconds
      cacheTime: 300000, // 5 minutes
    },
  },
});

function App() {
  const currentPanel = useSelector(selectCurrentPanel);
  const themeMode = useSelector(selectTheme);

  // Create MUI theme based on current mode
  const theme = useMemo(() => getTheme(themeMode), [themeMode]);

  // Render the appropriate panel based on currentPanel
  const renderPanel = () => {
    switch (currentPanel) {
      case PANELS.CONFIGURATION:
        return <ConfigurationPanel />;
      case PANELS.PROMPTS:
        return <PromptEditorPanel />;
      case PANELS.CONTROL:
        return <ControlCenterPanel />;
      case PANELS.MONITORING:
        return <MonitoringPanel />;
      case PANELS.DATA:
        return <DataViewerPanel />;
      case PANELS.EXPORT:
        return <ExportPanel />;
      case PANELS.CRASH:
        return <CrashMonitorPanel />;
      default:
        return <MonitoringPanel />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <MainLayout>
          {renderPanel()}
        </MainLayout>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;

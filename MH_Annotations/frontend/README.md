# Mental Health Annotation Dashboard - Frontend

React-based dashboard for managing the Mental Health Annotation System (Phase 3).

## Features

- **7 Specialized Panels:**
  - Configuration: Manage API keys and settings
  - Prompt Editor: Edit annotation prompts
  - Control Center: Start/stop workers
  - Monitoring: Real-time system dashboard
  - Data Viewer: Browse annotation data
  - Export: Export data in various formats
  - Crash Monitor: Monitor system health

- **Real-time Updates:** WebSocket integration for live data
- **Material-UI Components:** Professional, accessible UI
- **Redux State Management:** Centralized application state
- **Dark/Light Theme:** User-selectable themes

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

### Build

```bash
npm run build
```

### Production

```bash
npm run preview
```

## Technology Stack

- React 18
- Material-UI v5
- Redux Toolkit
- React Query
- Axios
- Monaco Editor
- Recharts
- WebSocket

## Project Structure

```
src/
├── components/       # React components
│   ├── Layout/      # Layout components (Sidebar, TopBar, MainLayout)
│   ├── Common/      # Reusable components
│   └── [Panels]/    # Panel-specific components
├── services/        # API and WebSocket services
├── store/           # Redux store and slices
├── hooks/           # Custom React hooks
├── utils/           # Utility functions
└── theme/           # Material-UI theme configuration
```

## Configuration

Edit `.env` to configure API endpoints:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/ws
```

## License

MIT

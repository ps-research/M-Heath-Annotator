import { configureStore } from '@reduxjs/toolkit';
import configReducer from './slices/configSlice';
import workersReducer from './slices/workersSlice';
import monitoringReducer from './slices/monitoringSlice';
import dataReducer from './slices/dataSlice';
import uiReducer from './slices/uiSlice';

const store = configureStore({
  reducer: {
    config: configReducer,
    workers: workersReducer,
    monitoring: monitoringReducer,
    data: dataReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: ['data/exportData/fulfilled'],
        // Ignore these field paths in all actions
        ignoredActionPaths: ['payload.blob'],
        // Ignore these paths in the state
        ignoredPaths: ['data.annotations.items'],
      },
    }),
  devTools: import.meta.env.DEV,
});

export { store };
export default store;

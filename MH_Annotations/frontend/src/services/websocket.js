import { WS_CONFIG } from '../utils/constants';

/**
 * WebSocket Manager for real-time updates
 */
class WebSocketManager {
  constructor(url) {
    this.url = url || import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws';
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = WS_CONFIG.MAX_RECONNECT_ATTEMPTS;
    this.reconnectDelay = WS_CONFIG.RECONNECT_DELAY;
    this.listeners = new Map();
    this.isConnected = false;
    this.heartbeatInterval = null;
    this.lastPong = null;
    this.shouldReconnect = true;
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    try {
      console.log('[WebSocket] Connecting to:', this.url);

      this.socket = new WebSocket(this.url);

      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
      this.socket.onerror = this.handleError.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      this.handleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    console.log('[WebSocket] Disconnecting...');
    this.shouldReconnect = false;

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.isConnected = false;
    this.reconnectAttempts = 0;
  }

  /**
   * Handle connection open
   */
  handleOpen() {
    console.log('[WebSocket] Connected');
    this.isConnected = true;
    this.reconnectAttempts = 0;

    // Dispatch connection event
    this.dispatch('connection', { status: 'connected' });

    // Start heartbeat
    this.startHeartbeat();

    // Request full state
    this.send({ type: 'request_full_state' });
  }

  /**
   * Handle incoming message
   */
  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);

      if (import.meta.env.DEV) {
        console.log('[WebSocket] Message:', message);
      }

      // Handle heartbeat response
      if (message.type === 'pong') {
        this.lastPong = new Date();
        return;
      }

      // Dispatch to registered listeners
      this.dispatch(message.type, message.data);
      this.dispatch('message', message);
    } catch (error) {
      console.error('[WebSocket] Message parse error:', error);
    }
  }

  /**
   * Handle WebSocket error
   */
  handleError(error) {
    console.error('[WebSocket] Error:', error);
    this.dispatch('error', { error });
  }

  /**
   * Handle connection close
   */
  handleClose(event) {
    console.log('[WebSocket] Closed:', event.code, event.reason);
    this.isConnected = false;

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    this.dispatch('connection', { status: 'disconnected' });

    // Attempt reconnection if not manual close
    if (this.shouldReconnect && event.code !== 1000) {
      this.handleReconnect();
    }
  }

  /**
   * Handle reconnection with exponential backoff
   */
  handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.dispatch('connection', {
        status: 'failed',
        error: 'Max reconnection attempts reached',
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    this.dispatch('connection', {
      status: 'reconnecting',
      attempt: this.reconnectAttempts,
    });

    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect();
      }
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    this.lastPong = new Date();

    this.heartbeatInterval = setInterval(() => {
      if (!this.isConnected) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
        return;
      }

      // Check if we received a pong recently
      if (this.lastPong) {
        const timeSinceLastPong = new Date() - this.lastPong;
        if (timeSinceLastPong > WS_CONFIG.HEARTBEAT_INTERVAL * 2) {
          console.warn('[WebSocket] No pong received, reconnecting...');
          this.socket.close();
          return;
        }
      }

      // Send ping
      this.send({ type: 'ping' });
    }, WS_CONFIG.HEARTBEAT_INTERVAL);
  }

  /**
   * Send message to server
   */
  send(message) {
    if (!this.isConnected || !this.socket) {
      console.warn('[WebSocket] Not connected, cannot send message');
      return false;
    }

    try {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      this.socket.send(data);
      return true;
    } catch (error) {
      console.error('[WebSocket] Send error:', error);
      return false;
    }
  }

  /**
   * Register event listener
   */
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  /**
   * Unregister event listener
   */
  off(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      return;
    }

    const listeners = this.listeners.get(eventType);
    const index = listeners.indexOf(callback);
    if (index !== -1) {
      listeners.splice(index, 1);
    }
  }

  /**
   * Dispatch event to all registered listeners
   */
  dispatch(eventType, data) {
    if (!this.listeners.has(eventType)) {
      return;
    }

    const listeners = this.listeners.get(eventType);
    listeners.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[WebSocket] Listener error for ${eventType}:`, error);
      }
    });
  }

  /**
   * Get connection status
   */
  getStatus() {
    if (!this.socket) {
      return 'disconnected';
    }

    switch (this.socket.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'unknown';
    }
  }
}

// Create singleton instance
let wsInstance = null;

export const getWebSocketInstance = () => {
  if (!wsInstance) {
    wsInstance = new WebSocketManager();
  }
  return wsInstance;
};

export const connectWebSocket = () => {
  const ws = getWebSocketInstance();
  ws.connect();
  return ws;
};

export const disconnectWebSocket = () => {
  if (wsInstance) {
    wsInstance.disconnect();
  }
};

export default WebSocketManager;

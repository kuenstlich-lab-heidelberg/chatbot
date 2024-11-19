class MessageManager {
    static websocket = null;
    static token = null;
    static wsUrl = null;
    static reconnectAttempts = 0;
    static maxReconnectAttempts = 10;
    static callbacks = {};
    static defaultCallback = null;
    static initialized = false;

    static async initialize(options = {}) {
        if (MessageManager.initialized) {
            console.warn("MessageManager is already initialized.");
            return;
        }
        MessageManager.initialized = true;

        MessageManager.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        MessageManager.defaultCallback = options.defaultCallback || function() {};
        MessageManager.callbacks = {};

        // Fetch the websocket token
        await MessageManager._fetchToken();

        if (!MessageManager.token) {
            console.error("MessageManager: Failed to obtain token.");
            MessageManager.callbacks["token.error"]?.()
            return;
        }

        const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        MessageManager.wsUrl = `${wsProtocol}${window.location.host}/websocket/${MessageManager.token}`;

        MessageManager._connectWebSocket();
    }



    static on(messageType, callback) {
        MessageManager.callbacks[messageType] = callback;
    }

    static off(messageType) {
        delete MessageManager.callbacks[messageType];
    }

    static send(message) {
        if (MessageManager.websocket && MessageManager.websocket.readyState === WebSocket.OPEN) {
            MessageManager.websocket.send(JSON.stringify(message));
        } else {
            console.error("WebSocket is not open. Cannot send message.");
        }
    }

    static async _fetchToken() {
        try {
            const response = await fetch("/websocket/connect", {
                credentials: "include"
            });
            const data = await response.json();
            MessageManager.token = data.token;
        } catch (error) {
            console.error("Error fetching token:", error);
            MessageManager.token = null;
        }
    }

    static _connectWebSocket() {
        try {
            // Close existing WebSocket if necessary
            if (MessageManager.websocket && MessageManager.websocket.readyState !== WebSocket.CLOSED) {
                MessageManager.websocket.close();
            }

            MessageManager.websocket = new WebSocket(MessageManager.wsUrl);

            MessageManager.websocket.onopen = () => {
                MessageManager.reconnectAttempts = 0;
                console.log("WebSocket connected.");
                MessageManager.callbacks["connection.open"]?.()
            };

            MessageManager.websocket.onmessage = async (event) => {
                if (typeof event.data === "string") {
                    try {
                        const message = JSON.parse(event.data);
                        if (message.function && MessageManager.callbacks[message.function]) {
                            MessageManager.callbacks[message.function](message);
                        } else if (MessageManager.defaultCallback) {
                            MessageManager.defaultCallback(message);
                        }
                    } catch (error) {
                        console.error("Error parsing text message:", error);
                    }
                } else if (event.data instanceof Blob) {
                    const arrayBuffer = await event.data.arrayBuffer();
                    MessageManager.callbacks["binary"]?.(arrayBuffer);
                }
            };

            MessageManager.websocket.onerror = (error) => {
                console.error("WebSocket error:", error);
                MessageManager.callbacks["connection.error"]?.(error);
            };

            MessageManager.websocket.onclose = MessageManager._reconnectWebSocket;

        } catch (error) {
            console.error("Error connecting WebSocket:", error);
        }
    }

    static _reconnectWebSocket() {
        if (MessageManager.reconnectAttempts < MessageManager.maxReconnectAttempts) {
            setTimeout(() => {
                MessageManager.reconnectAttempts++;
                console.log(`Attempting to reconnect WebSocket (Attempt ${MessageManager.reconnectAttempts})`);
                MessageManager._connectWebSocket();
            }, 5000);
        } else {
            console.error("Unable to reconnect WebSocket after maximum attempts.");
            if (MessageManager.callbacks["connection.lost"]) {
                MessageManager.callbacks["connection.lost"]();
            }
        }
    }

}

// ttsManager.js

class TTSManager {
    // Configurable parameters and callbacks
    static playbackRate = 0.92;
    static onStart = function() {};
    static onEnd = function() {};
    static onPlaybackComplete = function(duration) {};
    static onError = function(error) {};

    // Internal variables
    static audioContext = null;
    static currentSource = null;
    static isPlaying = false;
    static accumulatedChunks = [];
    static measurementStartTime = null;
    static measurementInProgress = false;
    static measurementValid = false;

    static async initialize(options = {}) {
        // Assign configurable parameters and callbacks
        TTSManager.playbackRate = options.playbackRate || TTSManager.playbackRate;
        TTSManager.onStart = options.onStart || TTSManager.onStart;
        TTSManager.onEnd = options.onEnd || TTSManager.onEnd;
        TTSManager.onPlaybackComplete = options.onPlaybackComplete || TTSManager.onPlaybackComplete;
        TTSManager.onError = options.onError || TTSManager.onError;

        if (TTSManager.audioContext === null) {
            TTSManager.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
    }

    static enqueue(arrayBuffer) {
        const wasAccumulatedEmpty = TTSManager.accumulatedChunks.length === 0;
        TTSManager.accumulatedChunks.push(new Int16Array(arrayBuffer));

        if (!TTSManager.isPlaying) {
            if (wasAccumulatedEmpty) {
                // Start measurement
                TTSManager.measurementStartTime = performance.now();
                TTSManager.measurementInProgress = true;
                TTSManager.measurementValid = true;

                // Call the onStart callback
                TTSManager.onStart();
            }
            TTSManager._playNextInQueue();
        }
    }

    static stop() {
        // Invalidate measurement if in progress
        if (TTSManager.measurementInProgress) {
            TTSManager.measurementValid = false;
        }

        TTSManager.accumulatedChunks = [];
        TTSManager.isPlaying = false;
        TTSManager.measurementStartTime = null;
        TTSManager.measurementInProgress = false;

        if (TTSManager.currentSource) {
            TTSManager.currentSource.onended = null;
            TTSManager.currentSource.stop();
            TTSManager.currentSource = null;
        }
    }

    static _playNextInQueue() {
        if (TTSManager.accumulatedChunks.length === 0) {
            TTSManager.isPlaying = false;
            if (TTSManager.measurementInProgress) {
                if (TTSManager.measurementValid) {
                    const measurementEndTime = performance.now();
                    const totalDuration = (measurementEndTime - TTSManager.measurementStartTime) / 1000; // in seconds

                    // Call the onPlaybackComplete callback
                    TTSManager.onPlaybackComplete(totalDuration);
                }
                // Reset measurement variables
                TTSManager.measurementStartTime = null;
                TTSManager.measurementInProgress = false;
                TTSManager.measurementValid = false;
            }
            // Call the onEnd callback
            TTSManager.onEnd();
            return;
        }

        const totalLength = TTSManager.accumulatedChunks.reduce((acc, chunk) => acc + chunk.length, 0);
        const concatenatedData = new Int16Array(totalLength);
        let offset = 0;
        for (const chunk of TTSManager.accumulatedChunks) {
            concatenatedData.set(chunk, offset);
            offset += chunk.length;
        }

        TTSManager.accumulatedChunks = [];

        const sampleRate = 24000;
        const audioBuffer = TTSManager.audioContext.createBuffer(1, concatenatedData.length, sampleRate);
        const channelData = audioBuffer.getChannelData(0);
        for (let i = 0; i < concatenatedData.length; i++) {
            channelData[i] = concatenatedData[i] / 32768;
        }

        const source = TTSManager.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(TTSManager.audioContext.destination);

        source.playbackRate.value = TTSManager.playbackRate;
        source.onended = () => {
            TTSManager._playNextInQueue();
        };

        try {
            source.start();
        } catch (error) {
            TTSManager.onError(error);
        }

        TTSManager.currentSource = source;
        TTSManager.isPlaying = true;
    }
}

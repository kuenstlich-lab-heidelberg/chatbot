// sttManager.js

class STTManager {
    static commitIdleTime = 800; // Default to 800ms
    static lang = 'de-DE';
    static onFinalResult = function(text) {};
    static onInterimResult = function(text) {};
    static onStart = function() {};
    static onEnd = function() {};
    static onError = function(error) {};

    // Internal variables
    static finalTranscript = '';
    static recognizing = false;
    static shouldRestart = false;
    static recognition = null;
    static inactivityTimeout = null; // Timer for inactivity

    static micButton = null; // Will be assigned in initialize

    static async initialize(options = {}) {
        // Assign micButton after DOM is loaded
        STTManager.micButton = document.getElementById("micButton");

        // Configurable parameters
        STTManager.commitIdleTime = options.commitIdleTime || STTManager.commitIdleTime;
        STTManager.lang = options.lang || STTManager.lang;
        STTManager.onFinalResult = options.onFinalResult || STTManager.onFinalResult;
        STTManager.onInterimResult = options.onInterimResult || STTManager.onInterimResult;
        STTManager.onStart = options.onStart || STTManager.onStart;
        STTManager.onEnd = options.onEnd || STTManager.onEnd;
        STTManager.onError = options.onError || STTManager.onError;

        if (!('webkitSpeechRecognition' in window)) {
            alert("Web Speech API is not supported by this browser. Please use Chrome.");
        } else {
            STTManager.recognition = new webkitSpeechRecognition();
            STTManager.recognition.continuous = true;
            STTManager.recognition.interimResults = true;
            STTManager.recognition.lang = STTManager.lang;

            STTManager.recognition.onstart = STTManager._onStart.bind(this);
            STTManager.recognition.onerror = STTManager._onError.bind(this);
            STTManager.recognition.onend = STTManager._onEnd.bind(this);
            STTManager.recognition.onresult = STTManager._onResult.bind(this);
        }
    }

    static start() {
        if (STTManager.recognition && !STTManager.recognizing) {
            STTManager.finalTranscript = '';
            STTManager.recognition.start();
            STTManager.shouldRestart = true;
        }
    }

    static stop() {
        if (STTManager.recognition && STTManager.recognizing) {
            STTManager.shouldRestart = false;
            STTManager.recognition.stop();
        }
    }

    static toggle() {
        if (STTManager.recognizing) {
            STTManager.stop();
        } else {
            STTManager.start();
        }
    }

    static _onStart() {
        STTManager.recognizing = true;
        STTManager.micButton.classList.add("active"); // Set mic button to active state
        STTManager.onStart();
    }

    static _onError(event) {
        if (event.error === 'no-speech') {
            console.warn("No speech detected. Trying again.");
        } else if (event.error === 'audio-capture') {
            alert("No microphone found. Please check microphone settings.");
        } else if (event.error === 'not-allowed') {
            alert("Microphone access denied.");
            STTManager.shouldRestart = false;
        }
        STTManager.onError(event.error);
    }

    static _onEnd() {
        STTManager.recognizing = false;
        STTManager.micButton.classList.remove("active"); // Remove active state from mic button
        if (STTManager.shouldRestart) {
            STTManager.recognition.start();
        }
        STTManager.onEnd();
    }

    static _onResult(event) {
        clearTimeout(STTManager.inactivityTimeout); // Reset inactivity timer
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                STTManager.finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }

        // Update the input field or any other UI element if needed
        const questionInput = document.getElementById("question");
        questionInput.value = STTManager.finalTranscript + " " + interimTranscript;

        // Call the onInterimResult callback with the current transcript
        const combinedTranscript = STTManager.finalTranscript + " " + interimTranscript;
        STTManager.onInterimResult(combinedTranscript.trim());

        STTManager.inactivityTimeout = setTimeout(() => {
            if (STTManager.finalTranscript || interimTranscript) {
                STTManager._finalizeSpeech();
            }
        }, STTManager.commitIdleTime);
    }

    static _finalizeSpeech() {
        const finalText = STTManager.finalTranscript.trim();
        // Reset transcript for the next speech segment
        STTManager.finalTranscript = '';
        STTManager.recognition.stop();
        // Call the callback with the final result
        STTManager.onFinalResult(finalText);
    }
}

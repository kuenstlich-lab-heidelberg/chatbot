let gameStarted = false;

const introContainer = document.getElementById("intro")
const conversationContainer = document.getElementById("conversation")

const chatContainer = document.getElementById("chatContainer")
const inputArea = document.getElementById("inputArea")
const startButton = document.getElementById("startButton")
const questionInput = document.getElementById("question")
const micButton = document.getElementById("micButton")

let thinkingIndicator = null;
let lastReceivedText = ""

async function startGame() {
    try {
        // Initialize the Text To Speech Manager
        await TTSManager.initialize({
            playbackRate: 0.92,
            onPlaybackComplete: (duration) => {
                // Actions to perform when playback is complete and duration is valid
                MessageManager.send({"function": "speak.statistic", "duration": duration, "characters": lastReceivedText.length})
                console.log(`Total playback duration: ${duration.toFixed(2)} seconds`);
                console.log(`Total characters: ${lastReceivedText.length}`);
                console.log(`Playback characters/second: ${lastReceivedText.length/duration.toFixed(2)} character/seconds`);
            }
        });

        // Initialize the SpeechToText Manager
        await STTManager.initialize({
            commitIdleTime: 400,
            lang: 'de-DE',
            onInterimResult: (text) => {
                questionInput.value = text;
            },
            onFinalResult: (text) => {
                questionInput.value = text;
                sendUserMessage();
            },
            onStart: () => {
                //MessageManager.send({ "function": "speak.stop"})
            }
        });

        // Initialize the MessageManager
        await MessageManager.initialize({defaultCallback: (message)=>{
            console.log(message)
        }});
        MessageManager.on("speak.stop", TTSManager.stop);
        MessageManager.on("binary", TTSManager.enqueue);
        MessageManager.on("tag_event", (message)=>{
            const platoImage = document.getElementById("plato");
            let srcValue = platoImage.getAttribute("src");
            const updatedSrc = srcValue.replace(/\/([^/]+)\.png$/, `/${message.tag}.png`);
            platoImage.setAttribute("src", updatedSrc);
            console.log("Aktualisiertes src-Attribut:", platoImage.getAttribute("src"));
        })

        // Start the game and toggle the UI
        if (!gameStarted) {
            gameStarted = true;
            conversationContainer.style.display = "flex";
            introContainer.style.display = "none";
            questionInput.focus();

            // Send "start" message to initialize the game
            showThinkingIndicator();
            const data = await sendMessage("start");
            removeThinkingIndicator();
            addMessage(data.response, "bot");
        }

    } catch (error) {
        console.error("Error starting game:", error);
        addMessage("An error occurred while starting the game.", "bot");
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendUserMessage();
    }
}

async function sendUserMessage() {
    text = questionInput.value.trim();
    questionInput.value = "";

    if (text) {
        try {
            addMessage(text, "user");
            showThinkingIndicator();

            const data = await sendMessage(text);
            addMessage(data.response, "bot");
        } catch (error) {
            addMessage("Error connecting to server.", "bot");
        }
        finally{
            removeThinkingIndicator();
        }
    }
}

async function sendMessage(text) {
    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ text: text })
        });
        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error sending message:", error);
        throw error;
    }
}


function showThinkingIndicator() {
    if (!thinkingIndicator) {
        thinkingIndicator = document.createElement("div");
        thinkingIndicator.classList.add("typing-indicator");

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement("div");
            dot.classList.add("dot");
            thinkingIndicator.appendChild(dot);
        }
        chatContainer.insertBefore(thinkingIndicator, chatContainer.firstChild);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function removeThinkingIndicator() {
    if (thinkingIndicator) {
        chatContainer.removeChild(thinkingIndicator);
        thinkingIndicator = null;
    }
}

function addMessage(text, sender) {
    const messageBubble = document.createElement("div");
    messageBubble.classList.add("message", sender);
    messageBubble.textContent = text;
    chatContainer.insertBefore(messageBubble, chatContainer.firstChild);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if( sender == "bot"){
        lastReceivedText = text
    }
}


document.addEventListener('DOMContentLoaded', () => {
    startButton.addEventListener('click', startGame);
    questionInput.addEventListener('keypress', handleKeyPress);
    micButton.addEventListener('click',  STTManager.toggle);
});

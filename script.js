const OPENROUTER_API_KEY = prompt("Enter your OpenRouter API key:");
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const modelSearch = document.getElementById('model-search');
const modelList = document.getElementById('model-list');

let models = [];
let selectedModel = '';

// Fetch models from OpenRouter
async function getModels() {
    try {
        const response = await fetch("https://openrouter.ai/api/v1/models");
        const data = await response.json();
        models = data.data;
        displayModels(models);
    } catch (error) {
        console.error("Error fetching models:", error);
    }
}

// Display models in the list
function displayModels(filteredModels) {
    modelList.innerHTML = '';
    filteredModels.forEach(model => {
        const modelElement = document.createElement('div');
        modelElement.textContent = model.name;
        modelElement.dataset.modelId = model.id;
        modelElement.addEventListener('click', () => {
            selectedModel = model.id;
            modelSearch.value = model.name;
            modelList.style.display = 'none';
        });
        modelList.appendChild(modelElement);
    });
}

// Filter models based on search input
modelSearch.addEventListener('input', () => {
    const searchTerm = modelSearch.value.toLowerCase();
    const filteredModels = models.filter(model => model.name.toLowerCase().includes(searchTerm));
    displayModels(filteredModels);
    modelList.style.display = 'block';
});

// Hide model list when clicking outside
document.addEventListener('click', (event) => {
    if (!modelSearch.contains(event.target)) {
        modelList.style.display = 'none';
    }
});


// Send message to the API
async function sendMessage() {
    const message = messageInput.value;
    if (!message || !selectedModel) {
        alert("Please select a model and type a message.");
        return;
    }

    appendMessage(message, 'user-message');
    messageInput.value = '';

    try {
        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: selectedModel,
                messages: [{ role: 'user', content: message }]
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`API Error: ${response.status} - ${errorData.error.message}`);
        }

        const data = await response.json();
        const assistantMessage = data.choices[0].message.content;
        appendMessage(assistantMessage, 'assistant-message');

    } catch (error) {
        console.error("Error sending message:", error);
        appendMessage(`Error: ${error.message}`, 'assistant-message');
    }
}

// Append message to the chat window
function appendMessage(message, className) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', className);
    messageElement.textContent = message;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initial load
getModels();
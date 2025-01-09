import { getToken } from './authentication.js';
import { apiAddress, loadGame } from './script.js'
import { getUserData } from './profile.js';
import { playMessageSound } from './sound.js';

let chatSocket = null;
let username
let userId

async function getUser() {
	try {
		const token = getToken();
		const response = await fetch(apiAddress + '/api/users/', {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${token}`,
			}
		});

		if (!response.ok) {
			console.error(`Bad response from /api/users/: ${response.status} ${response.statusText}`);
			throw new Error(response.statusText);
		}

		const data = await response.json();
		username = data.username;
		userId = data.id;
		return { username, userId };
	} catch (error) {
		console.error(`Error: failed to fetch user data: ${error.message}`);
		throw error;
	}
}


function saveMessageToStorage(message) {
	let chatHistory = JSON.parse(localStorage.getItem("chatHistory")) || [];
	chatHistory.push(message);
	localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
}

function loadMessagesFromStorage() {
	let chatHistory = JSON.parse(localStorage.getItem("chatHistory")) || [];
	const chatLog = document.getElementById("chat-log");

	chatHistory.forEach((data) => {
		const messageElement = document.createElement("p");
		const userElement = document.createElement("strong");

		userElement.textContent = data.user + ": ";

		if (data.user === "PongChat") {
			messageElement.innerHTML = data.message;
		} else {
			messageElement.textContent = data.message;
		}

		messageElement.prepend(userElement);
		chatLog.appendChild(messageElement);
	});
}

function chatNavFlash() {
	const button = document.getElementsByClassName('chat-nav')[0];

	if (!button) return;
	button.classList.add('hover-effect');
	button.focus();
	setTimeout(() => {
		button.classList.remove('hover-effect');
		button.blur();
	}, 500);
}

export async function initChat() {
	// Initialize chat content
	const content = document.getElementById('content');
	content.innerHTML = `
		<h2>Chat Room</h2>
		<h4>type /help to see chat instructions</h4>
		<div id="chat-log">
			<!-- Messages will appear here -->
		</div>
		<input id="chat-message-input" type="text" placeholder="Type your message here..." style="width: 80%;" />
		<button id="chat-message-submit">&lt;send&gt;</button>
	`;

	loadMessagesFromStorage();

	document.getElementById("chat-message-submit").onclick = function () {
		const messageInput = document.getElementById("chat-message-input");
		const message = messageInput.value;
		chatSocket.send(JSON.stringify({ message: message }));
		messageInput.value = "";
	};

	document.getElementById("chat-message-input").onkeyup = function (e) {
		if (e.key === "Enter") {
			document.getElementById("chat-message-submit").click();
		}
	};

	// Event delegation to handle dynamically added game links
	document.getElementById("chat-log").addEventListener("click", async (event) => {
		// Check if the clicked element is a game link
		const target = event.target;
		if (target.tagName === "A" && target.id.startsWith("join-game-")) {
			event.preventDefault();

			// Extract the game_id from the link's ID
			const game_id = target.id.split("join-game-")[1];

			loadGame(game_id, userId);
		}
		else if (target.tagName === "A" && target.id.startsWith("profile-")) {
			event.preventDefault();

			const profile_id = target.id.split("profile-")[1];
			getUserData(profile_id)
		}
	});

	scrollToBottom();
};

export function closeChatSocket(){
	if (chatSocket) {
		chatSocket.close()
	}
	chatSocket = null;
};
export async function openChatSocket() {
	try {
		await getUser();

		if (!chatSocket) {
			const host = window.location.hostname;
			const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
			const port = window.location.port || (protocol === 'wss' ? '443' : '80');
			const wsChatAddress = `${protocol}://${host}:${port}/ws/chat/?username=${username}`;

			chatSocket = new WebSocket(wsChatAddress);
			handleSocketMessages();
		}
	} catch (error) {
		console.error("Failed to open chat socket:", error);
	}
}


function handleSocketMessages() {
	chatSocket.onopen = function () {
	};

	chatSocket.onclose = function () {
	};


	chatSocket.onmessage = function (e) {
		const data = JSON.parse(e.data);
		const chatLog = document.getElementById("chat-log");
		if (!chatLog) {
			chatNavFlash();
			playMessageSound();
			saveMessageToStorage({ user: data.user, message: data.message });
			return;
		}

		// Create elements for the username and message
		const messageElement = document.createElement("p");
		const userElement = document.createElement("strong");

		// Set content for username and message
		userElement.textContent = data.user + ": ";
		if (data.user === "PongChat") {
			// Use innerHTML for server-generated messages (safe for pre-formatted commands)
			messageElement.innerHTML = data.message;
		} else {
			// Use textContent for user messages to prevent injection
			messageElement.textContent = data.message;
		}

		// Append username and message to the chat log
		messageElement.prepend(userElement);
		chatLog.appendChild(messageElement);

		// Scroll to the latest message
		chatLog.scrollTop = chatLog.scrollHeight;

		// Save message to local storage
		saveMessageToStorage({ user: data.user, message: data.message });
	};
}

function scrollToBottom() {
	const chatLog = document.getElementById('chat-log');
	chatLog.scrollTop = chatLog.scrollHeight;
}
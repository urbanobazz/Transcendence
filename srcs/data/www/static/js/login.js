// login.js

// Handles logic for login page

import { apiAddress, router } from './script.js'
import { checkAndRefreshToken, authCheck } from './authentication.js';
import { closeTournamentSocket } from './tournament.js';
import { closeChatSocket, openChatSocket } from './chat.js';

let tokenInterval;

/**
 * Inject login form html and add event listeners.
 *
 * @returns void.
 */
export function loadLogin() {
	const content = document.getElementById('content');
	content.innerHTML = `
		<h2>login</h2>
		<a href="/42-login" id="42-login" data-link>&lt;login with 42 account&gt;</a>
		<br>
		<form id="login-form">
			<label for="username">Username:</label>
			<input type="text" id="username" name="username" required>
			<br>
			<label for="password">Password:</label>
			<input type="password" id="password" name="password" required>
			<br>
			<div class="horizontal-align" style="flex-direction: column; align-items: flex-end;">
				<button id="login" type="submit">&lt;login&gt</button>
			</div>
		</form>
		<div id="error-login"></div>
		<br><br>
		<div class="form-group horizontal-align">
			<h2>or register</h2>
			<a href="/register" id="register" data-link>&lt;register&gt;</a>
		</div>
	`;

	const form = document.getElementById('login-form');
	form.addEventListener('submit', handleLoginSubmit);
}

/**
 * Change default behaviour of form, call login()
 * function instead.
 *
 * @param event  form submit event
 * @returns void.
 */
function handleLoginSubmit(event) {
	event.preventDefault();

	const form = event.target;
	const username = form.username.value;
	const password = form.password.value;

	login(username, password);
}

/**
 * Authentiactes the user through the backend API.
 *
 * @param username  users username.
 * @param password  users password.
 * @returns void.
 */
export function login(username, password) {
	fetch(apiAddress + '/api/login/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ username, password })
	})
	.then(response => {
		if (!response.ok) {
			return response.json().then(data => {
				throw new Error('failed to login XD');
			});
		}
		return response.json();
	})
	.then(data => {
		if (data.access) {
			document.getElementById('error-message').innerHTML = '';
			localStorage.setItem('token', data.access);
			authCheck();
			openChatSocket();
			setTokenInterval();
			history.pushState({}, "", "/chat");
			router("/chat");
		} else {
			throw new Error('Failed to obtain token');
		}
	})
	.catch((error) => {
		console.error('Error:', error);
		const errorMessageContainer = document.getElementById('error-login');
		errorMessageContainer.innerHTML = `<h2>${error.message}</h2>`;
	});
}

export function logout() {

	fetch(apiAddress + '/api/logout/', {
		method: 'POST',
		credentials: 'include'
	})
	.then(response => response.json())
	.then(data => {
		localStorage.clear();
		closeTournamentSocket();
		authCheck();
		closeChatSocket();
		if (tokenInterval) {
			clearInterval(tokenInterval);
			tokenInterval = null;
		}
	})
	.catch(error => {
		console.error('Error logging out:', error);
	});
}

export function setTokenInterval() {
	tokenInterval = setInterval(checkAndRefreshToken, 60000 * 5); // check JWT token every 5 minutes
}
// register.js

// Handles logic for register page
import { apiAddress } from './script.js'
import { login } from './login.js';

const content = document.getElementById('content');

/**
 * Injects the register form in the html and
 * adds event listeners.
 *
 * @returns void.
 */
export function loadRegister() {
	content.innerHTML = `
		<h2>Register</h2>
		<form id="registerForm" class="form-horizontal">
			<div class="form-group">
				<label for="username" class="form-label">Username:</label>
				<input type="text" id="username" name="username" required>
			</div>
			<div class="form-group">
				<label for="password" class="form-label">Password:</label>
				<input type="password" id="password" name="password" required>
			</div>
			<div class="form-group">
				<label for="password-confirm" class="form-label">Confirm Password:</label>
				<input type="password" id="password-confirm" name="password-confirm" required>
			</div>
			<div class="center-container">
				<button id=register class="form-btn" type="submit">&lt;register&gt;</button>
			</div>
		</form>
	`;

	const form = document.getElementById('registerForm');
	form.addEventListener('submit', handleRegisterSubmit);
}

/**
 * Prevents default form behaviour, checks
 * if password is equal to confirmed password
 * and registers user through register() function.
 *
 * @param event submit form event
 * @returns void.
 */
function handleRegisterSubmit(event) {
	event.preventDefault();

	const form = event.target;
	const username = form.username.value;
	const password = form.password.value;
	const passwordConfirm = form['password-confirm'].value;

	const errorMessageContainer = document.getElementById('error-message');
	errorMessageContainer.innerHTML = '';

	if (password != passwordConfirm) {
		console.error('passwords do not match');
		errorMessageContainer.innerHTML = `<h2>passwords do not match...</h2>`;
	}
	else {
		register(username, password);
	}
}

/**
 * Registers user through bakend API.
 *
 * @param username
 * @param password
 * @returns void.
 */
function register(username, password) {
	fetch(apiAddress + '/api/register/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ username, password})
	})
	.then(response => {
		if (!response.ok) {
			return response.json().then(data => {
				throw new Error(data.message || 'Failed to register');
			});
		}
		return response.json();
	})
	.then(data => {
		login(username, password);
	})
	.catch((error) => {
		console.error('Error:', error);
		document.getElementById('error-message').innerHTML = `<h2>${error.message}</h2>`;
	});
}

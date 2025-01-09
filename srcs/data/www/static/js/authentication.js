import { apiAddress, loadTemplate } from './script.js'
import { logout } from './login.js';
import { openChatSocket } from './chat.js';

export function getToken() {
	const loginButton = document.getElementById('loginButton');
	const profileButton = document.getElementById('profileButton');
	const homeButton = document.getElementById('homeButton');

	const token = localStorage.getItem('token');

	if (!token) {
		if (profileButton)
			profileButton.remove();
		loginButton.innerText = '<login>';
		loginButton.setAttribute('href', '/login');
		homeButton.innerText = '<home>';
		homeButton.setAttribute('href', '/');
		history.pushState({}, "", '/');
		loadTemplate('homeTemplate');
		return null;
	} else {
		return token;
	}
}

/**
 * Adapts the page if user is authenticated,
 * adds 'my profile' and replaces 'login' to 'logout' button.
 *
 * @returns void.
 */
export function authCheck() {
	const loginButton = document.getElementById('loginButton');
	const profileButton = document.getElementById('profileButton');
	const homeButton = document.getElementById('homeButton');
	const navbar = document.getElementById('nav');

	const token = getToken();

	fetch(apiAddress + '/api/users/', {
		method: 'HEAD',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
	})
	.then(response => {
		if (response.ok) {
			loginButton.innerText = '<logout>';
			loginButton.setAttribute('href', '/logout');

			homeButton.innerText = '<chat>';
			homeButton.setAttribute('href', '/chat');
			homeButton.setAttribute('class', 'chat-nav');

			if (!profileButton) {
				const profile = document.createElement('a');
				profile.id = "profileButton";
				profile.innerText = "<my profile>";
				profile.setAttribute('href', '/profile');
				profile.setAttribute('data-link', ''); // SPA routing
				navbar.appendChild(profile);
			}
			openChatSocket();
		} else {
			localStorage.removeItem('token');
			loginButton.innerText = '<login>';
			loginButton.setAttribute('href', '/login');
			homeButton.innerText = '<home>';
			homeButton.setAttribute('href', '/');
			history.pushState({}, "", '/');
			loadTemplate('homeTemplate');
			return;
		}
	})
	.catch((error) => {
		history.pushState({}, "", '/');
		loadTemplate('homeTemplate');
	});
}


export function checkAndRefreshToken() {
	const token = getToken();

	//const expirationTime = getExpirationTimeFromToken(token);
	const expirationTime = jwt_decode(token).exp;
	const currentTime = Math.floor(Date.now() / 1000);
	const timeLeft = expirationTime - currentTime;

	// Refresh if expires in next 5 minutes (300 seconds)
	if (timeLeft <= 300) {
		refreshAccessToken();
	}
}

function refreshAccessToken() {
	// Call the backend API to refresh the token (using the HttpOnly cookie automatically)
	fetch(apiAddress + '/api/token/refresh/', {
		method: 'POST',
		credentials: 'include',  // To send the HttpOnly cookie with the request
	})
	.then(response => {
		if (!response.ok) {
			logout();
			return;
		}
		return response.json();
	})
	.then(data => {
		localStorage.setItem('token', data.access);  // Store new access token
	})
	.catch(error => {
		console.error('Error refreshing access token:', error);
	});
}

// script.js
//  Main script with router to all other pages
import { redirectToOAuth, handleOAuthCallback, OAuthProcessing } from './remoteAuth.js';
import { editProfile, editAvatar, editUsername, editPassword } from './editProfile.js';
import { setupLobby, multiLobby, tournamentLobby } from './lobby.js';
import { initializeGame, loop, cleanupGame, waitingForGame, deleteGame } from './game.js';
import { authCheck } from './authentication.js';
import { loadLogin, logout } from './login.js';
import { getUserData } from './profile.js';
import { loadRegister } from './register.js';
import { searchUsers } from './users.js';
import { initChat } from './chat.js';

export const apiAddress = window.location.origin

const routes = {
	'/': () => loadTemplate('homeTemplate'),
	'/profile': () => getUserData(),
	'/profile/:userId': (userId) => getUserData(userId),
	'/login': () => loadLogin(),
	'/42-login': () => redirectToOAuth(),
	'/oauth-callback': () => handleOAuthCallback(),
	'/logout': () => logout(),
	'/register': () => loadRegister(),
	'/play': () => setupLobby(),
	'/single-player': () => setupGame('single'),
	'/multi-player': () => multiLobby(),
	'/local-multi': () => setupGame('local-multi'),
	'/tournament': () => tournamentLobby(),
	'/users': () => searchUsers("users"),
	'/friends': () => searchUsers("friends"),
	'/edit-profile': () => editProfile(),
	'/edit-avatar': () => editAvatar(),
	'/edit-username': () => editUsername(),
	'/edit-password': () => editPassword(),
	'/chat': () => initChat(),
};

export function router(path) {
	try {
		const profileRegex = /^\/profile\/(U-\w+|AI-\w+)$/;
		const match = path.match(profileRegex);
		if (match) {
			const userId = match[1];
			routes['/profile/:userId'](userId);
			return;
		}

		const route = routes[path];
		cleanupGame();

		if (route) {
			route();
		} else {
			loadTemplate('errorTemplate');
		}
	} catch (error) {
		console.error('Error: ', error);
	}
}

// Initialize SPA: Setup click event listeners and route based on URL
function initSPA() {
	document.addEventListener("click", (event) => {
		if (event.target.matches("[data-link]")) {
			event.preventDefault();
			if (waitingForGame == true ) {
				alert("Game will be deleted");
				deleteGame();
			}
			const path = event.target.getAttribute("href");
			history.pushState({}, "", path);
			document.getElementById('error-message').innerHTML = '';
			router(path); // Load content based on the route
		}
	});

	// Handle browser back/forward buttons
	window.addEventListener("popstate", () => {
		router(window.location.pathname);
	});

	// Load the initial path on page load
	router(window.location.pathname);
}


/**
 * Loads a predefined template from index.html.
 *
 * @param templateid  id of the html template.
 * @returns void.
 */
export function loadTemplate(templateId) {
	const template = document.getElementById(templateId);
	const content = document.getElementById('content');
	content.innerHTML = '';
	content.appendChild(template.content.cloneNode(true));
}

function setupGame(type) {
	const errorMessageContainer = document.getElementById('error-message');
	errorMessageContainer.innerHTML = '';

	document.getElementById('content').innerHTML = `
		<h2 id="title">choose game settings</h2>
		<div class="form-group horizontal-align">
			<label for="game-speed" style="font-size: large;">game speed:</label>
			<select id="game-speed" class="form-control mb-2">
				<option value="0.5">slow</option>
				<option value="1" selected>medium</option>
				<option value="1.5">fast</option>
			</select>
			<label for="power-ups" style="font-size: large; margin: 0px 10px;">power-ups:</label>
			<input type="checkbox" id="power-ups" class="form-control mb-2" checked>
		</div>
		<button id="start-game" class="btn btn-primary">&lt;start game&gt;</button>
	`;

	document.getElementById('start-game').addEventListener('click', async () => {
		const gameSpeed = document.getElementById('game-speed').value;
    	const powerUps = document.getElementById('power-ups').checked;
		if (type == 'single')
			loadGame("GAI-" + self.crypto.randomUUID().replace(/-/g, ''), "U-1000", null, gameSpeed, powerUps);
		else if (type == 'local-multi')
			loadGame("LG-" + self.crypto.randomUUID().replace(/-/g, ''), "U-1000", null, gameSpeed, powerUps);
	});
}

/**
 * Loads a game based on ID. Will create the websocket
 * connection and start the game loop.
 *
 * @param   gameId  id of the game object in the database.
 * @param   playerId  id of the user loading the game.
 * @param   tournamentId  id of the tournament if game belongs to one, default is null.
 * @returns void.
 */
export function loadGame(gameId, playerId, tournamentId=null, gameSpeed=null, powerUps=null) {
	initializeGame(gameId, playerId, tournamentId, gameSpeed, powerUps);
	requestAnimationFrame(loop);
}

// Initialize user session state and SPA routing
document.addEventListener("DOMContentLoaded", () => {
	initSPA();
	if (!OAuthProcessing)
		authCheck();
});

//setInterval(checkAndRefreshToken, 60000 * 5); // check JWT token every 5 minutes


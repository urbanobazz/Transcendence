// loby.js

// Puts user in lobby before game

import { loadGame, apiAddress } from './script.js'
import { setupTournament } from './tournament.js';
import { getToken } from './authentication.js';

const content = document.getElementById('content');

/**
 * Injects html dependend on user authentication.
 * Not authenticated users only get singleplayer
 * and authenticated users can choose muliplayer and tournaments.
 *
 * @returns void.
 */
export function setupLobby() {
	const token = !!getToken();

	content.innerHTML = `
		<h2>Okayyy letsgooo</h2>
		<a href="/single-player" id="single-player" data-link>&lt;single-training&gt;</a> <br>
		<a href="/local-multi" id="local-multi" data-link>&lt;multi-training&gt;</a> <br>
		${token ? '<a href="/multi-player" id="multi-player" data-link>&lt;multi-player&gt;</a><br>' : ''}
		${token ? '<a href="/tournament" id="tournament" data-link>&lt;tournament&gt;</a><br>' : ''}
	`;
}

/**
 * Sets up html for a list of muli-player games or
 * creating a new game. Then calls function to
 * fetch games from API.
 *
 * @returns void.
 */
export function multiLobby() {
	content.innerHTML = `
		<h2 id="title"></h2>
		<input type="text" id="search-input" placeholder="search games" class="form-control mb-2">
		<div id="scroll-list">
		</div>
		<br>
		<input type="text" id="game-name" placeholder="enter game name" class="form-control mb-2">
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
		<button id="createGameButton" class="btn btn-primary">&lt;create new game&gt;</button>
	`;

	document.getElementById('createGameButton').addEventListener('click', async () => {
		const gameName = document.getElementById('game-name').value;
		const gameSpeed = document.getElementById('game-speed').value;
    	const powerUps = document.getElementById('power-ups').checked;
		if (gameName) {
			createGame('multi/', gameName, gameSpeed, powerUps);
		} else {
			alert('Please enter a game name.');
		}
	});

	document.getElementById('search-input').addEventListener('input', (event) => {
		filterList('game-list', event);
	});

	fetchGames('multi/');
}

/**
 * Sets up html for a list of tournaments or
 * creating a new tournament. Then calls function to
 * fetch tournaments from API.
 *
 * @returns void.
 */
export function tournamentLobby() {
	content.innerHTML = `
		<h2 id="title"></h2>
		<input type="text" id="search-input" placeholder="search tournaments" class="form-control mb-2">
		<div id="scroll-list">
		</div>
		<br>
		<input type="text" id="game-name" placeholder="enter tournament name" class="form-control mb-2">
		<div class="form-group horizontal-align">
			<label for="num-players" style="font-size: large;">How many players?</label>
			<select id="num-players" class="form-control mb-2">
				<option value="4">4</option>
				<option value="6">6</option>
				<option value="8">8</option>
			</select>
		</div>
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
		<button id="createGameButton" class="btn btn-primary">&lt;create new tournament&gt;</button>
	`;

	document.getElementById('createGameButton').addEventListener('click', async () => {
		const gameName = document.getElementById('game-name').value;
		const numPlayers = document.getElementById('num-players').value;
		const gameSpeed = document.getElementById('game-speed').value;
    	const powerUps = document.getElementById('power-ups').checked;

		if (gameName) {
			createGame('tournaments/', gameName, gameSpeed, powerUps, numPlayers);
		} else {
			alert('Please enter a tournament name.');
		}
	});

	document.getElementById('search-input').addEventListener('input', (event) => {
		filterList('game-list', event);
	});

	fetchGames('tournaments/');
}


export function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

/**
 * Fetch list of games of "type".
 * If type is "tournaments/" tournaments will be fetched,
 * if type is "mulit/" mulitplayer games will be fetched.
 *
 * @param type	type of games to be fetched ("multi/", "tournaments/")
 * @returns void.
 */
function fetchGames(type) {

	const token = getToken();

	fetch(apiAddress + '/api/' + type, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
	})
		.then(response => {
			if (!response.ok) {
				return response.json().then(data => {
					throw new Error('Bad Response: ' + data.error);
				});
			}
			return response.json();
		})
		.then(data => {
			if (data && Array.isArray(data.games) && data.games.length > 0) {
				let user_id = data.user_id;

				document.getElementById('title').innerText = "join other games!";
				const container = document.getElementById('scroll-list');
				//container.classList.add('overflow-auto');
				// Create game list
				const gameList = document.createElement('ul');
				gameList.id = 'game-list';
				container.appendChild(gameList)
				// loop over games and add to list
				data.games.forEach(game => {
					let name = game.name ? game.name : "game";
					const listItem = document.createElement('li');
					listItem.innerHTML = `
					${name} (${game.id})
					<a href="#" id="join-game-${game.id}">&lt;join game&gt;</a>
				`;
					gameList.appendChild(listItem);
					// add join button
					document.getElementById(`join-game-${game.id}`).addEventListener('click', async (event) => {
						event.preventDefault();
						joinGame(type, game.id, user_id);
						document.getElementById('error-message').innerHTML = '';
					});
				});
			} else {
				document.getElementById('search-input').remove();
				document.getElementById('scroll-list').remove();
				const errorMessageContainer = document.getElementById('title');
				errorMessageContainer.innerHTML = `No running games found`;
			}
		})
		.catch((error) => {
			console.error('Error:', error);
		});
}

async function joinGame(type, gameId, userId) {
	try {
		const token = getToken();
		const response = await fetch(apiAddress + `/api/${type}join/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${token}`,
			},
			body: JSON.stringify({ game_id: gameId })
		});

		if (!response.ok) {
			throw new Error(`Failed to join game: ${response.statusText}`);
		}

		await sleep(500);

		if (type == 'tournaments/')
			setupTournament(gameId, userId);
		else
			loadGame(gameId, userId);

	} catch (error) {
		document.getElementById('error-message').innerText = `Error: ${error.message}`;
		console.error("Error joining game:", error);
	}
}

/**
 * Creates game of "type".
 * If type is "tournaments/" tournament will be created,
 * if type is "mulit/" mulitplayer game will be created.
 *
 * @param type	type of game to be created ("multi/", "tournaments/")
 * @returns void.
 */
export function createGame(type, gameName=null, gameSpeed='1', powerUps=true, numPlayers=2) {
	const token = getToken();

	fetch(apiAddress + '/api/' + type + 'create/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: JSON.stringify({game_name: gameName, n_players: numPlayers, game_speed: gameSpeed, power_ups: powerUps}),
	})
	.then(response => {
		if (!response.ok) {
			if (response.status === 409) {
				// Handle 409 error specifically
				let error = document.getElementById('error-message');
				error.innerHTML = "<h2>You are already enrolled in another tournament</h2>";
				document.getElementById('createGameButton').remove();
				return;
			} else {
				// For other errors, read the response body and throw an error
				return response.json().then(data => {
					throw new Error('Error: ' + data.error);
				});
			}
		}
		return response.json();
	})
	.then(data => {
		if (data) {
			if (type == 'tournaments/')
				setupTournament(data.game.id, data.user_id);
			else
				loadGame(data.game.id, data.user_id);
		} else {
			throw new Error('Failed to create game: ' + data.error);
		}
	})
	.catch((error) => {
			console.error('Error:', error);
	});
}

export function filterList(listId) {
	const searchInput = document.getElementById('search-input').value.toLowerCase();
	const games = document.querySelectorAll(`#${listId} li`);

	games.forEach(game => {
		const gameName = game.textContent.toLowerCase();
		if (gameName.includes(searchInput)) {
			game.style.display = '';
		} else {
			game.style.display = 'none';
		}
	});
}

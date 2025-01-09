// profile.js

// Handles logic for profile page

import { apiAddress, router } from './script.js'
import { setFriend, setBlocked } from './blockFriends.js'
import { getToken } from './authentication.js';

/**
 * Injects the html and eventlisteners for the
 * profile page of a user. If username was not passed,
 * the authenticated users profile will be loaded. If username is passed,
 * the profile of username will be loaded.
 *
 * @param	 username
 * @param	 authenticated true if user is auithenticated and requesting their own profile
 * @returns void.
 */
function setupProfile(data, authenticated) {
	const content = document.getElementById('content');
	if (authenticated) {
		content.innerHTML = `
			<h2>Welcome to your profile!</h2>

			<div class="profile-container">
				<div class="left-column">
					<img id="avatar" alt="Avatar">
					<h1 id="username"></h1>
					<a href="/friends" id="friends" data-link>&lt;friends&gt;</a>
					<a href="/users" id="users" data-link>&lt;search users&gt;</a>
					<a href="/edit-profile" id="edit-profile" data-link>&lt;edit profile&gt;</a>
				</div>

				<div id="stats-square">
				</div>
			</div>
		`;
	} else {
		content.innerHTML = `
			<h2>Welcome to ${data.username}'s profile!</h2>

			<div class="profile-container">
				<div class="left-column">
					<img id="avatar" alt="Avatar" width="100%">
					<h1 id="username"></h1>
					<a href="/friend" id="friend"></a>
					<a href="/block" id="block"></a>
					<a href="/chat" id="chat" data-link>&lt;chat&gt</a>
				</div>

				<div id="stats-square">
				</div>
			</div>
		`;

		// Initial button states based on the data
		updateFriendButton(data.is_friend, data.username);
		updateBlockButton(data.is_blocked, data.username);
	}
}

/**
 * Fetches user data from the backend API of
 * a user. If user_id is non existent
 * the authenticated user will be fetched. If the parameter
 * does exist, the user with user_id will be fetched.
 *
 * @param	user_id  user id of requested user
 * @returns void.
 */
export function getUserData(user_id) {
	let method;
	let authenticated = false;
	let body = null;
	const token = getToken()

	if (!user_id) {
		method = 'GET';
		authenticated = true;
	}
	else {
		method = 'POST';
		body = JSON.stringify({ user_id });
	}

	fetch(apiAddress + '/api/users/', {
		method: method,
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: body
	})
	.then(response => {
		if (!response.ok) {
			console.error(`Bad response from /api/users/ ${response.status} ${response.message}`);
			throw new Error(response.message);
		}
		return response.json();
	})
	.then(data => {
		// Display user data from API
		setupProfile(data, authenticated);
		fillStats(data);
		document.getElementById('username').innerText = `Username: ${data.username}`;
		document.getElementById('avatar').src = `${data.avatar}`;
	})
	.catch((error) => {
		console.error(`Error: failed to fetch user data: ${error.message}`);
	});
}

function fillStats(data) {
	const statSquare = document.getElementById('stats-square');
	statSquare.innerHTML = ''; // Clear previous content

	// Display wins and losses
	const wins = document.createElement('h2');
	wins.innerText = `Wins: ${data.stats.wins}`;
	const losses = document.createElement('h2');
	losses.innerText = `Losses: ${data.stats.losses}`;
	statSquare.appendChild(wins);
	statSquare.appendChild(losses);

	// Display games played
	const gamesTitle = document.createElement('h2');
	gamesTitle.innerText = 'Games Played:';
	statSquare.appendChild(gamesTitle);

	if (data.stats.games_played.length > 0) {
		const gamesTable = document.createElement('table');
		const tableHead = document.createElement('thead');
		const tableBody = document.createElement('tbody');
	
		// Create table headers
		const headerRow = document.createElement('tr');
		const headers = ['Player 1', 'Score', 'Player 2'];
		headers.forEach(headerText => {
			const header = document.createElement('th');
			header.innerText = headerText;
			headerRow.appendChild(header);
		});
		tableHead.appendChild(headerRow);
		gamesTable.appendChild(tableHead);
	
		// Create table rows for each game
		data.stats.games_played.forEach(game => {
			const row = document.createElement('tr');
	
			const player1Cell = document.createElement('td');
			player1Cell.innerText = game.p1;
			row.appendChild(player1Cell);
	
			const scoreCell = document.createElement('td');
			scoreCell.innerText = `${game.p1_score} - ${game.p2_score}`;
			row.appendChild(scoreCell);
	
			const player2Cell = document.createElement('td');
			player2Cell.innerText = game.p2;
			row.appendChild(player2Cell);
	
			tableBody.appendChild(row);
		});
		gamesTable.appendChild(tableBody);
		statSquare.appendChild(gamesTable);
	} else {
		const noGames = document.createElement('h2');
		noGames.innerText = 'No games played yet.';
		statSquare.appendChild(noGames);
	}
}



// Function to update friend button state
function updateFriendButton(isFriend, username) {
	let friendButton = document.getElementById('friend');

	if (isFriend) {
		friendButton.innerText = "<remove friend>";
		friendButton.onclick = async function (event) {
			event.preventDefault();
			await setFriend(username, 'DELETE');
			updateFriendButton(false, username); // Update button state to "become friends"
		};
	} else {
		friendButton.innerText = "<become friends>";
		friendButton.onclick = async function (event) {
			event.preventDefault();
			await setFriend(username, 'POST');
			updateFriendButton(true, username); // Update button state to "remove friend"
		};
	}
}

// Function to update block button state
function updateBlockButton(isBlocked, username) {
	const blockButton = document.getElementById('block');

	if (isBlocked) {
		blockButton.innerText = "<unblock>";
		blockButton.onclick = async function (event) {
			event.preventDefault();
			await setBlocked(username, 'DELETE');
			updateBlockButton(false, username); // Update button state to "block user"
		};
	} else {
		blockButton.innerText = "<block user>";
		blockButton.onclick = async function (event) {
			event.preventDefault();
			await setBlocked(username, 'POST');
			updateBlockButton(true, username); // Update button state to "unblock"
		};
	}
}

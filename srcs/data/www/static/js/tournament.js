import { getToken } from './authentication.js';
import { loadGame, apiAddress, router } from './script.js'

let tournamentSocket = null;
let tournamentIntervalId;
const content = document.getElementById('content');

export function setupTournament(tournamentId, userId) {
	if (tournamentIntervalId) {
		clearInterval(tournamentIntervalId);
	}

	content.innerHTML = `
		<h1>get ready for the tournament!</h1>
		<h2 id="n-players"></h2>
		<a href="/leave-tournament" id="leave-tournament">&lt;leave tournament&gt;</a>
		<a href="/start-tournament" id="start-tournament" style="display: none;">&lt;start tournament&gt;</a>
	`;
	getTournamentInfo(tournamentId);
	initWebSocket(tournamentId, userId);


	document.getElementById(`leave-tournament`).addEventListener('click', async (event) => {
		event.preventDefault();
		leaveTournament(tournamentId);
		closeTournamentSocket();
	});

	document.getElementById(`start-tournament`).addEventListener('click', async (event) => {
		event.preventDefault();
		document.getElementById(`start-tournament`).innerText = "<waiting for others>";
		userReady(tournamentId);
	});

	tournamentIntervalId = setInterval(() => getTournamentInfo(tournamentId), 1000);
}

export function clearTournamentInterval() {
	if (tournamentIntervalId) {
		clearInterval(tournamentIntervalId);
		tournamentIntervalId = null;
	}
}


async function getTournamentInfo(tournamentId) {
	const token = getToken();

	await fetch(apiAddress + '/api/tournaments/info/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: JSON.stringify({ tournament_id: tournamentId }),
	})
	.then(response => response.json())
	.then(data => {
		document.getElementById('n-players').innerText = `${data.joined}/${data.n_players} players joined`;
		if (data.joined == data.n_players) {
			alert(`tournament "${data.name}" ready to start, enough players joined`);
			document.getElementById('leave-tournament').style.display = 'none';
			document.getElementById(`start-tournament`).style.display = 'inline';
			clearTournamentInterval();
			return true;
		}
		return false;
	})
	.catch((error) => {
		console.error(`Failed to fetch tournament info: ${error.message}`);
		return false;
	});
}

export function userReady(tournamentId) {
	console.log("user ready for tournament: ", tournamentId);
	const message = {
		action: 'userReady',
	};
	tournamentSocket.send(JSON.stringify(message));

}

function initWebSocket(tournamentId, userId) {
	// Initialize WebSocket
	const host = window.location.hostname;
	const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
	const port = window.location.port || (protocol === 'wss' ? '443' : '80');
	let wsAddress = `${protocol}://${host}:${port}/ws/pong/${tournamentId}/?user_id=${userId}`;
	tournamentSocket = new WebSocket(wsAddress);

	// Handle messages received from the server
	tournamentSocket.onmessage = (event) => {
		const data = JSON.parse(event.data);
		if (data.action === 'tournamentStarted') {
			clearTournamentInterval();
			startCountdown(() => loadGame(data.game_id, userId, tournamentId), data);
		}
		else if (data.action === 'waiting') {
		}
		else if (data.action === 'finished') {
			setupRanking(tournamentId, data)
			closeTournamentSocket();
		}
	};
}

function startCountdown(callback, data) {
	const countdownContainer = document.createElement('div');
	countdownContainer.id = 'countdown-container';
	countdownContainer.style.textAlign = 'center';
	countdownContainer.style.fontSize = '2em';
	content.innerHTML = `<h1>You're plaing against ${data.opponent_name}</h1>`;
	content.appendChild(countdownContainer);

	let countdown = 4;
	countdownContainer.innerText = `Get ready: ${countdown}`;

	const countdownInterval = setInterval(() => {
		countdown -= 1;
		if (countdown > 0) {
			countdownContainer.innerText = `Get ready: ${countdown}`;
		} else {
			clearInterval(countdownInterval);
			content.innerHTML = '';
			callback();
		}
	}, 1000);
}

function setupRanking(tournamentId, data) {
	const token = getToken();

	fetch(apiAddress + '/api/tournaments/rank/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: JSON.stringify({ tournament_id: tournamentId }),
	})
	.then(response => response.json())
	.then(rankData => {
		// DISPLAY RANKING
		content.innerHTML = `
			<h1>user ${data.winner} won tournament ${data.name}!!</h1>
			<div id="scroll-list">
				<ul id="user-rank" class="no-bullets">
				</ul>
			</div>
		`;
		const rankList = document.getElementById("user-rank");
		let rank = 1;
		rankData.ranking.forEach(player => {
			const listItem = document.createElement('li');
			listItem.innerHTML = `
				${rank} - ${player.username}, wins: ${player.wins}
			`;
			rankList.appendChild(listItem);
			rank++;
		});
	})
	.catch((error) => {
		console.error(`Failed to fetch tournament ranking: ${error.message}`);
	});
}

function leaveTournament(tournamentId) {
	const token = getToken();
	fetch(apiAddress + '/api/tournaments/leave/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: JSON.stringify({ tournament_id: tournamentId }),
	})
	.then(response =>  {
		if (response.ok) {
			history.pushState({}, "", "/tournament");
			router("/tournament");
		}
	})
	.catch((error) => {
		console.error(`Failed to leave tournament: ${error.message}`);
	});
}

export function closeTournamentSocket() {
	clearTournamentInterval();
	if (tournamentSocket)
		tournamentSocket.close();
}

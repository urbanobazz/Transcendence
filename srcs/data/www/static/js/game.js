import { userReady } from './tournament.js';
import { apiAddress, router } from './script.js';
import { getToken } from './authentication.js';

// Global variables
let gs = null;  // Game state
let websock;  // WebSocket instance
let tournamentId = null;
let userId = null;
let g_gameId = null;
export let waitingForGame = false;
const keyStates = {
    ArrowUp: false,
    ArrowDown: false,
    w: false,
    s: false,
    space: false
};

/**
 * Initializes all parameters to set up the WebSocket.
 *
 * @param gameId  id of the game to start
 * @param playerId  player id
 * @param tournamentCheck  checks if tournament mode is on
 * @returns void
 */
export async function initializeGame(gameId, playerId, tournamentCheck, gameSpeed, powerUps) {
    userId = playerId;
    g_gameId = gameId;

    const host = window.location.hostname;
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const port = window.location.port || (protocol === 'wss' ? '443' : '80');
    let wsAddress = `${protocol}://${host}:${port}/ws/pong/${gameId}/?` +
					`player_id=${playerId}&` +
					`game_speed=${gameSpeed}&` +
					`power_ups=${powerUps}`;

    if (tournamentCheck) tournamentId = tournamentCheck;

    await setupWebsocket(playerId, wsAddress);
    setupCanvas();
}

/**
 * Handles WebSocket errors.
 *
 * @returns void
 */
function handleWebSocketError(event) {
    console.error("WebSocket error:", event);
}

/**
 * Sets up the WebSocket connection and sends init message.
 *
 * @param playerId  id of the player
 * @param wsAddress  url of the WebSocket
 * @returns void
 */
async function setupWebsocket(playerId, wsAddress) {
	websock = new WebSocket(wsAddress);

	websock.onopen = function () {
		websock.send(JSON.stringify({
			message: "init",
			player_id: playerId
		}));
	};

	websock.onerror = function (error) {
		console.error('WebSocket error: ', error);
		document.getElementById('content').innerHTML = `
			<h2>sorry, could not load game</h2>
			<a href="/play" data-link>&lt;play another game&gt;</a>
		`;
		return;
	};

	setupEventListeners();
}

/**
 * Closes WebSocket connection.
 *
 * @returns void
 */
function handleWebSocketClose(event) {
    console.warn("WebSocket closed:", event);
}

/**
 * Handles key events and updates key states.
 *
 * @param event key event
 * @returns void
 */
function handleKeyEvent(event) {
    const validKeys = ['ArrowUp', 'ArrowDown', 'w', 's', ' '];
    if (event.key === ' ') event.key = 'space';
    if (validKeys.includes(event.key)) {
        event.preventDefault();  // Prevent default actions for certain keys
        keyStates[event.key] = event.type === 'keydown';
    }
}

/**
 * Sends the current key states to the server via WebSocket.
 *
 * @returns void
 */
function sendKeyStates() {
    if (websock && websock.readyState === WebSocket.OPEN) {
        websock.send(JSON.stringify({ message: 'input', input: keyStates }));
    } else {
        console.error("WebSocket is not open.");
    }
}

/**
 * Sets up event listeners for the keys.
 *
 * @returns void
 */
function setupEventListeners() {
    document.addEventListener('keydown', handleKeyEvent);
    document.addEventListener('keyup', handleKeyEvent);

    websock.addEventListener('message', handleWebSocketMessage);
    websock.addEventListener('close', handleWebSocketClose);
    websock.addEventListener('error', handleWebSocketError);
}

/**
 * Handles the message received from
 * the WebSocket and responds accordingly.
 *
 * @param data JSON data received from WebSocket
 * @returns void
 */
function handleWebSocketMessage({ data }) {
    try {
        const json_data = JSON.parse(data);

        const { message, gs: gameState } = json_data;
        gs = gameState;  // Update the game state with new data
        if (gs)
            gs.update = performance.now();
        // Process the game state update and send input states back
        if (['update', 'init', 'left', 'right'].includes(message)) {
            updateScores();
            sendKeyStates();  // Send the current key states after receiving the update
        } else if (message === 'waiting_for_player') {
            waiting();  // Show waiting message if waiting for another player
        } else if (message == "start_game") {
            try {
                const canvas = document.getElementById('game');
                canvas.setAttribute('height', '450px');
                if (json_data.p1.username && json_data.p2.username) {
                    document.getElementById('player1-name').textContent = json_data.p1.username;
                    document.getElementById('player2-name').textContent = json_data.p2.username;
                }
                document.getElementById('cancel-button').remove();
            } catch (error) {}

            waitingForGame = false;
        } else if (message === 'r_win' || message === 'l_win') {
            const winner = message === 'r_win' ? 'Player 2' : 'Player 1';
            endGame(winner);
        } else if (message.startsWith('U-') || message.startsWith('AI-')) {
            const winner = message;
            endGame(winner);
        } else if (message === 'cancelled') {
            const winner = userId;
            endGame(winner);
        } else {
            console.error("Received an unknown message:", message);
        }
    } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
    }
}

/**
 * Set up waiting room for players to wait for their opponent.
 *
 * @returns void
 */
function waiting() {
    waitingForGame = true;
    const canvas = document.getElementById('game');
    if (!canvas) {
        return;
    }
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = 'black';
    context.fillRect(0, 0, canvas.width, canvas.height);

    context.fillStyle = '#a4ff48';
    context.font = '30px monospace';
    context.textAlign = 'center';
    context.fillText('Waiting for another player...', canvas.width / 2, canvas.height / 2);

    let cancelButton = document.getElementById('cancel-button');
    if (!cancelButton) {
        const cancelButton = document.createElement('button');
        cancelButton.innerText = '<cancel>';
        cancelButton.id = 'cancel-button';
    
        // Append the button to the div with id="content"
        const contentDiv = document.getElementById('content');
        contentDiv.appendChild(cancelButton);
    
        // Add event listener for the cancel button
        cancelButton.addEventListener('click', () => deleteGame());
    }
}

/**
 * Updates the player scores in the DOM.
 *
 * @returns void
 */
function updateScores() {
    document.getElementById('player1-score').textContent = gs.lpad.score || 0;
    document.getElementById('player2-score').textContent = gs.rpad.score || 0;
}

/**
 * Injects HTML for the game canvas
 *
 * @returns void
 */
function setupCanvas() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div id="score" width="100%" height="5%" font-family="monospace" class="center-container">
            <span id="player1-name">player 1 </span> - <span id="player2-name"> player 2</span>
        </div>
		<div id="score" width="100%" height="5%" font-family="monospace" class="center-container">
            <span id="player1-score">0</span> - <span id="player2-score">0</span>
        </div>
        <canvas width="800px" height="250px" id="game"></canvas>
    `;
}

/**
 * Cleans up event listeners from the game.
 *
 * @returns void
 */
export function cleanupGame() {
    document.removeEventListener('keydown', handleKeyEvent);
    document.removeEventListener('keyup', handleKeyEvent);
    tournamentId = null;

    if (websock) {
        websock.removeEventListener('message', handleWebSocketMessage);
        websock.removeEventListener('close', handleWebSocketClose);
        websock.removeEventListener('error', handleWebSocketError);
        websock.close();
        websock = null;
    }
}

function predictBallPosition() {
    const now = performance.now();
    const diff = (now - gs.update) / 1000;
    const predictedX = gs.ball.x + gs.ball.dx * diff;
    const predictedY = gs.ball.y + gs.ball.dy * diff;
    gs.ball.x = predictedX
    gs.ball.y = predictedY
}

/**
 * Game loop.
 *
 * @returns void
 */
export function loop() {
    if (!gs) {
        requestAnimationFrame(loop);
        return;
    }

    const canvas = document.getElementById('game');
    if (!canvas) {
        cleanupGame();
        return;
    }

    const context = canvas.getContext('2d');
    if (!context) {
        console.error("Failed to get canvas context.");
        requestAnimationFrame(loop);
        return;
    }

    predictBallPosition();
    renderGame(context, canvas);
    requestAnimationFrame(loop);
}

/**
 * Renders the game elements on the canvas.
 *
 * @param context context of the canvas element
 * @param canvas HTML ID of the canvas element
 * @returns void
 */
function renderGame(context, canvas) {
    const grid = 15;
    context.fillStyle = 'black';
    context.fillRect(0, 0, canvas.width, canvas.height);

    context.fillStyle = '#a4ff48';
    context.fillRect(gs.lpad.x, gs.lpad.y, gs.lpad.width, gs.lpad.height);
    context.fillRect(gs.rpad.x, gs.rpad.y, gs.rpad.width, gs.rpad.height);

    context.fillRect(gs.ball.x, gs.ball.y, gs.ball.width, gs.ball.height);

    context.fillStyle = '#a4ff48';
    context.fillRect(0, 0, canvas.width, grid);
    context.fillRect(0, canvas.height - grid, canvas.width, grid);

    for (let i = grid; i < canvas.height - grid; i += grid * 2) {
        context.fillRect(canvas.width / 2 - grid / 2, i, grid, grid);
    }

    // Draw the status bar
    if (gs.powerups.type != 'off') {renderStatusBar(context, canvas)};
}

/**
 * Renders the status bar based on the game state.
 *
 * @param context context of the canvas element
 * @param canvas HTML ID of the canvas element
 * @returns void
 */
function renderStatusBar(context, canvas) {
    const statusValue = gs.powerups.bar || 0; // Default to 0 if not provided
    const barWidth = canvas.width * 0.8; // Bar spans 80% of canvas width - should this be larger?
    const barHeight = 10;
    const barX = (canvas.width - barWidth) / 2;
    const barY = 5;

    const progress = (statusValue + 100) / 200; // Normalize to range [0, 1]
    const filledWidth = barWidth * progress;

    context.fillStyle = 'red';
    context.fillRect(barX, barY, barWidth, barHeight);

    context.fillStyle = 'blue';
    context.fillRect(barX, barY, filledWidth, barHeight);

    if (gs.powerups && gs.powerups.type) {
        const textX = barX + filledWidth;
        const textY = barY + barHeight / 2 + 5;

        let powerupText = '';
        if (gs.powerups.type === 'plarge') {
            powerupText = '<->';
        } else if (gs.powerups.type === 'psmall') {
            powerupText = '>-<';
        } else if (gs.powerups.type === 'invers') {
            powerupText = '±±±';
        }

        if (powerupText) {
            context.font = '20px monospace';
            context.textAlign = 'center';
            
            const textMetrics = context.measureText(powerupText);
            const textWidth = textMetrics.width;
            const textHeight = 20; // Approximate height based on font size
            
            const rectX = textX - textWidth / 2 - 5;
            const rectY = textY - textHeight / 2 - 9;
            const rectWidth = textWidth + 10;
            const rectHeight = textHeight; 
            
            context.fillStyle = '#a4ff48'; 
            context.fillRect(rectX, rectY, rectWidth, rectHeight);
            
            context.fillStyle = 'black';
            context.fillText(powerupText, textX, textY);
        }
    }
}


function endGame(winner) {
    const content = document.getElementById('content');
    content.innerHTML = `
        <h1 id="winner"></h1>
        <h2>Final score: ${gs.lpad.score} - ${gs.rpad.score}</h2>
        <h2 id="n-players"></h2>
        <a id="play-next"></a>
        <h3 id="waiting"></h3>
    `;

    // Set the winner message based on the winner ID
    if (winner === userId) {
        document.getElementById('winner').innerText = "You won!! <3333 :P";
    } else if (winner === 'Player 1' || winner === 'Player 2') {
        document.getElementById('winner').innerText = `${winner} won the game!`;
    } else {
        document.getElementById('winner').innerText = "You lost... better luck next time XD";
    }

    // Set up the play-next button for either a tournament or a replay option
    const playNextButton = document.getElementById('play-next');
    if (tournamentId && winner === userId) {
        playNextButton.innerText = "<continue>";
        playNextButton.addEventListener('click', async (event) => {
            event.preventDefault();
            userReady(tournamentId);
            playNextButton.remove();
            document.getElementById('waiting').innerText = "waiting for others...";
        });
    } else {
        playNextButton.innerText = "<play again>";
        playNextButton.setAttribute('href', '/play');
        playNextButton.setAttribute('data-link', '');
    }

    // Clean up game event listeners and WebSocket connection
    cleanupGame();
}

export function deleteGame() {
    waitingForGame = false;
    cleanupGame();
    const token = getToken();
    fetch(apiAddress + '/api/multi/', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({game_id: g_gameId}),
    })
    .catch((error) => {
        console.error('Error:', error);
    });
    history.pushState({}, "", "/play");
    router("/play");
}
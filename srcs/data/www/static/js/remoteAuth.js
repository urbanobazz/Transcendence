import { apiAddress, router } from "./script.js";
import { authCheck, getToken, checkAndRefreshToken } from "./authentication.js";
import { openChatSocket } from "./chat.js";
import { setTokenInterval } from "./login.js";

export let OAuthProcessing = false;

export function redirectToOAuth() {
	const clientId = 'u-s4t2ud-675e1b9dc23d0feb7d67b1982d00b6a2eec2abcde10ff5f2991e2944aae80b51';
	const redirectUri = `${apiAddress}/oauth-callback`; // Frontend's callback
	const authUrl = `https://api.intra.42.fr/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code`;
	window.location.href = authUrl;
}

export function handleOAuthCallback() {
	const urlParams = new URLSearchParams(window.location.search);
	const authorizationCode = urlParams.get('code');
	const redirectUri = `${apiAddress}/oauth-callback`;

	if (authorizationCode) {
		OAuthProcessing = true;
		content.innerHTML = `<h2>loading...</h2>`;
		fetch(apiAddress + '/api/auth/oauth-callback/', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ code: authorizationCode , redirect_uri: redirectUri})
		})
		.then(response => response.json())
		.then( data => {
			if (data.access) {
				localStorage.setItem('token', data.access);
				uploadAvatar(data);
				authCheck();
				openChatSocket();
				setTokenInterval();
				history.pushState({}, "", "/chat");
				router("/chat");
				OAuthProcessing = false;
			} else {
				console.error('Authentication failed.');
			}
		})
		.catch((error) => {
			console.error('Error during OAuth callback handling:', error);
		});
	}
}

function uploadAvatar(data) {
	let token = getToken();

	fetch(apiAddress + '/api/auth/avatar/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: JSON.stringify(data)
	})
	.then(response => response.json())
	.catch((error) => {
		console.error('Error during OAuth avatar upload:', error);
	});
}

import { getToken } from './authentication.js';
import { apiAddress } from './script.js'

/**
 * Sets friend relation between authenticated user and requested username.
 * Method should be POST to add a friend and DELETE to remove a friend.
 *
 * @param username  user that should be befriended/unfriended.
 * @param method  'POST' to befriend, 'DELETE' to unfriend.
 * @returns void.
 */
export function setFriend(username, method) {
	const token = getToken();

	fetch(apiAddress + '/api/friends/', {
		method: method,
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: JSON.stringify({ friend_username: username })
	})
		.then(response => {
			if (!response.ok) {
				throw new Error(`Failed to ${method} friends`);
			}
			return response.json();
		})
		.catch(error => {
			console.error('Error:', error);
		});
}


/**
 * Sets blocked relation between authenticated user and requested username.
 * Method should be POST to block username and DELETE to unblock username.
 *
 * @param username  user that should be blocked/unblocked.
 * @param method  'POST' to block, 'DELETE' to unblock.
 * @returns void.
 */
export function setBlocked(username, method) {
	const token = getToken();

	fetch(apiAddress + '/api/users/block/', {
		method: method,
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: JSON.stringify({ blocked_username: username })
	})
		.then(response => {
			if (!response.ok) {
				throw new Error(`Failed to ${method} block`);
			}
			return response.json();
		})
		.catch(error => {
			console.error('Error:', error);
		});
}

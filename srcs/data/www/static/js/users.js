// search.js

// Fetches all users

import { apiAddress } from './script.js'
import { filterList } from './lobby.js';
import { getToken } from './authentication.js';

/**
 * Injects empty user list in html and
 * adds event listener to go back to profile
 * of authenticated user.
 *
 * @returns void.
 */
function setupList(type) {
	const content = document.getElementById('content');
	content.innerHTML = `
		<h2 id=title></h2>
		<input type="text" id="search-input" placeholder="search users" class="form-control mb-2">
		<div id="scroll-list" class="form-horizontal">
		</div>
		<a href="/profile" id="profile" data-link>&lt;back to profile&gt;</a>
	`;

	document.getElementById('search-input').addEventListener('input', (event) => {
		filterList('user-list', event);
	});
}

/**
 * Fetches a list of users or friends from the backend API.
 * If type = "friends", a list of friends from the authenticated user
 * will be listed. If friends = "users" all users from the platform
 * will be listed.
 *
 * @param   type tupe of users to fetch ("friends", "users")
 * @returns void.
 */
export function searchUsers(type) {
	let url;

	const token = getToken();

	setupList(type);

	if (type == "users")
		url = "search";
	else
		url = type;

	fetch(apiAddress + `/api/${url}/`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
	})
		.then(response => {
			if (!response.ok) {
				console.error(`Bad response from /api/${url}/ ${response.status} ${response.message}`);
				throw new Error(response.message);
			}
			return response.json();
		})
		.then(data => {
			if (data && Array.isArray(data) && data.length > 0) {
				document.getElementById('title').innerText = `Search ${type}`;
				const container = document.getElementById('scroll-list');
				const userList = document.createElement('ul'); // Create user list
				userList.id = 'user-list';
				container.appendChild(userList)

				data.forEach(user => {
					const listItem = document.createElement('li');
					listItem.className = 'user-list-item';
					listItem.innerHTML = `
						<span class="username">${user.username}</span>
						<a href="/profile/${user.id}" id="profile-${user.id}" class="profile-link" data-link>&lt;see profile&gt;</a>
					`;
					userList.appendChild(listItem);

				});
			} else {
				console.error('No users found: ' + type);
				document.getElementById('search-input').remove();
				document.getElementById('scroll-list').remove();
				const title = document.getElementById('title');
				title.innerText = `No ${type} found`;
			}
		})
		.catch((error) => {
			console.error(`Error: failed to fetch user list: ${error.message}`);
		});
}

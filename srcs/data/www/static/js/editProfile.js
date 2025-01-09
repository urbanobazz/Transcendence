import { getToken } from "./authentication.js";
import { apiAddress, router } from './script.js'


/**
 * Function to edit profile
 *
 * @returns void.
 */
export function editProfile() {
	const content = document.getElementById('content');
	content.innerHTML = `
		<h2>edit your profile!</h2>
		<a href="/edit-avatar" id="edit-avatar" data-link>&lt;edit avatar&gt;</a>
		<a href="/edit-username" id="edit-username" data-link>&lt;edit username&gt;</a>
		<a href="/edit-password" id="edit-password" data-link>&lt;edit password&gt;</a>
	`;
}

export function editAvatar() {
	const content = document.getElementById('content');
	content.innerHTML = `
		<h2>edit your avatar</h2>
		<form id="edit-profile-form" enctype="multipart/form-data" class="form-horizontal">
			<div class="form-group">
				<label for="profile-picture" class="form-label">Upload a profile picture:</label>
				<input type="file" id="profile-picture" name="profile-picture" accept="image/*" class="file-input">
			</div>
			<div class="center-container">
				<button class="form-btn" type="submit">submit</button>
			</div>
		</form>
	`;

	const form = document.getElementById('edit-profile-form');
	form.addEventListener('submit', handleAvatarSubmit);
}

export function editUsername() {
	const content = document.getElementById('content');
	content.innerHTML = `
		<h2>edit your username</h2>
		<form id="change-username-form" class="form-horizontal">
			<div class="form-group">
				<label for="new-username" class="form-label">change username:</label>
				<input type="text" id="new-username" name="new-username" placeholder="Enter new username">
			</div>
			<div class="center-container">
				<button type="submit" class="form-btn">&lt;change username&gt;</button>
			</div>
		</form>
	`;

	const form = document.getElementById('change-username-form');
	form.addEventListener('submit', handleUsernameSubmit);
}

export function editPassword() {
	const content = document.getElementById('content');
	content.innerHTML = `
		<h2>edit your password</h2>
		<form id="change-password-form" class="form-horizontal">
			<div class="form-group">
				<label for="current-password" class="form-label">current password:</label>
				<input type="password" id="current-password" name="current-password" placeholder="enter current password" class="form-input">
			</div>
			<div class="form-group">
				<label for="new-password" class="form-label">new password:</label>
				<input type="password" id="new-password" name="new-password" placeholder="enter new password" class="form-input">
			</div>
			<div class="form-group">
				<label for="new-password-confirm" class="form-label">confirm new password:</label>
				<input type="password" id="new-password-confirm" name="new-password-confirm" placeholder="confirm new password" class="form-input">
			</div>
			<div class="center-container">
				<button type="submit" class="form-btn">&lt;change password&gt;</button>
			</div>
		</form>
	`;

	const form = document.getElementById('change-password-form');
	form.addEventListener('submit', handlePasswordSubmit);
}

function handleAvatarSubmit(event) {
	event.preventDefault();

	const form = event.target;
	const formData = new FormData(form);

	const token = getToken();

	fetch(apiAddress + '/api/users/avatar/', {
		method: 'POST',
		headers: {
			'Authorization': `Bearer ${token}`,
		},
		body: formData,
	})
	.then(response => {
		if (!response.ok) {
			throw new Error('Failed to upload profile picture');
		}
		return response.json();
	})
	.then(data => {
		history.pushState({}, "", "/profile");
		router("/profile");
	})
	.catch(error => {
		console.error('Error:', error);
	});
}

function handleUsernameSubmit(event) {
	event.preventDefault();

	const form = event.target;
	const newUsername = form['new-username'].value;

	const token = getToken();

	fetch(apiAddress + '/api/users/', {
		method: 'PUT',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: JSON.stringify({ newUsername })
	})
	.then(response => {
		if (!response.ok) {
			return response.json().then(data => {
				throw new Error(data.message || 'Failed to update username');
			});
		}
		return response.json();
	})
	.then(data => {
		history.pushState({}, "", "/profile");
		router("/profile");
	})
	.catch((error) => {
		console.error('Error:', error);
		document.getElementById('error-message').innerHTML = `<h2>${error.message}</h2>`;
	});
}

function handlePasswordSubmit(event) {
	event.preventDefault();

	const form = event.target;
	const oldPassword = form['current-password'].value;
	const newPassword = form['new-password'].value;
	const newPasswordConfirm = form['new-password-confirm'].value;

	const errorMessageContainer = document.getElementById('error-message');
	errorMessageContainer.innerHTML = '';

	if (newPassword != newPasswordConfirm) {
		console.error('new passwords do not match');
		errorMessageContainer.innerHTML = `<h2>new passwords do not match...</h2>`;
		return;
	}

	const token = getToken();

	fetch(apiAddress + '/api/users/', {
		method: 'PUT',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`,
		},
		body: JSON.stringify({ oldPassword, newPassword})
	})
	.then(response => {
		if (!response.ok) {
			return response.json().then(data => {
				throw new Error(data.message || 'Failed to update password');
			});
		}
		return response.json();
	})
	.then(data => {
		history.pushState({}, "", "/profile");
		router("/profile");
	})
	.catch((error) => {
		console.error('Error:', error);
		document.getElementById('error-message').innerHTML = `<h2>${error.message}</h2>`;
	});
}

export function playMessageSound() {
	const audio = document.getElementById('message-sound');
	if (audio) {
		audio.currentTime = 0;
		audio.play().catch((error) => {
			console.error("Failed to play sound:", error);
		});
	}
}

// Clicking the computer in the room image opens the menu of this room's exercises and quiz.
const hotspot = document.getElementById('computer-hotspot');
const menu = document.getElementById('computer-popup');

if (hotspot && menu) {
  const openMenu = () => menu.showModal();
  hotspot.addEventListener('click', openMenu);
  hotspot.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openMenu();
    }
  });

  // exercise_popup.js and quiz.js open their own popups for these buttons;
  // close the menu so only the chosen popup stays on screen.
  menu.addEventListener('click', (event) => {
    if (event.target.closest('.exercise-button, #quiz-button')) menu.close();
  });
}

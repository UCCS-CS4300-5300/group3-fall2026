    const selectSound = document.getElementById('select');

    document.querySelectorAll('.hotspot').forEach((hotspot) => {
      hotspot.addEventListener('mouseenter', () => {
        selectSound.currentTime = 0;
        selectSound.play().catch((error) => {
          console.error('Could not play hotspot sound:', error);
        });
      });
    });
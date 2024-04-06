document.addEventListener('DOMContentLoaded', function() {
    const vessels = document.querySelectorAll('.vessel');
    const overlay = document.querySelector('.overlay');
    const vesselImages = document.querySelectorAll('.vessel img');
  
    vesselImages.forEach(function(vesselImage) {
      vesselImage.addEventListener('click', function() {
        overlay.style.display = 'none'; // This will hide the overlay
      });
    });
  
    vessels.forEach(vessel => {
      const typewriterText = vessel.nextElementSibling;
      const text = typewriterText.getAttribute('data-text');
      let typewriterEffect;
  
      vessel.addEventListener('mouseenter', () => {
        clearInterval(typewriterEffect);
  
        let index = 0;
        typewriterText.textContent = '|'; 
        typewriterText.style.visibility = 'visible'; // Make  text visible
  
        typewriterEffect = setInterval(() => {
          if (index < text.length) {
            typewriterText.textContent = text.slice(0, index + 1) + '|';
            index++;
          } else {
            typewriterText.textContent = text; 
            clearInterval(typewriterEffect); 
          }
        }, 100); // Typing speed in milliseconds
      });
  
      vessel.addEventListener('mouseleave', () => {
        clearInterval(typewriterEffect); 
        typewriterText.textContent = ''; 
        typewriterText.style.visibility = 'hidden'; 
      });
  });
});

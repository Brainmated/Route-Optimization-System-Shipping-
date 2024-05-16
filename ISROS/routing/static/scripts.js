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
      }, 10); // Typing speed in milliseconds
    });
  
    vessel.addEventListener('mouseleave', () => {
      clearInterval(typewriterEffect); 
      typewriterText.textContent = ''; 
      typewriterText.style.visibility = 'hidden'; 
    });
  });
  // Slider for weight percentage
  const weightSlider = document.getElementById('weight');
  const weightDisplay = document.getElementById('weightDisplay');
  weightSlider.oninput = function() {
      weightDisplay.textContent = this.value + '%';
  };

  // Slider for propeller condition
  const propellerSlider = document.getElementById('propellerCondition');
  const propellerDisplay = document.getElementById('propellerDisplay');
  propellerSlider.oninput = function() {
      propellerDisplay.textContent = this.value;
  };

  const loadingOverlay = document.getElementById('loadingOverlay');
  const vesselForm = document.getElementById('vesselForm');

  vesselForm.addEventListener('submit', function(event) {
    const locationA = document.getElementById('locationA').value;
    const locationB = document.getElementById('locationB').value;
    const gasPrice = document.getElementById('currentGasPrice').value;
    
    if (locationA === "" || locationB === "" || gasPrice === "") {
      event.preventDefault(); // Prevent form submission
      alert('Please fill in all required fields: Location A, Location B, and Current Gas Price.');
    } else {
      loadingOverlay.style.display = 'flex'; // Only display the overlay if form validation passes
    }
  });
});

// ====== Navbar Toggle (Your Original Code) ======
const menuToggle = document.getElementById('mobile-menu');
const navList = document.getElementById('nav-list');

menuToggle.addEventListener('click', () => {
    navList.classList.toggle('active');
});

// === Prevent page scroll on form submit ===
document.addEventListener('DOMContentLoaded', () => {
  const analyzeForm = document.querySelector('.analyze-form');

  if (analyzeForm) {
    analyzeForm.addEventListener('submit', (e) => {
      e.preventDefault(); // stop auto page reload/scroll

      // Send data manually using fetch (AJAX style)
      const formData = new FormData(analyzeForm);
      fetch(analyzeForm.action, {
        method: 'POST',
        body: formData
      })
      // ✅ Check if Flask-Login redirected (unauthenticated user)
      .then(response => {
        if (response.redirected) {
          window.location.href = response.url; // go to login page
          return;
        }
        return response.text();
      })
      .then(html => {
        if (!html) return; // stop if redirected above
        // Replace only the analyze section content, not full page
        const parser = new DOMParser();
        const newDoc = parser.parseFromString(html, 'text/html');
        const newAnalyzeSection = newDoc.querySelector('#analyze');
        document.querySelector('#analyze').innerHTML = newAnalyzeSection.innerHTML;
      })
      .catch(error => console.error('Error:', error));
    });
  }
});

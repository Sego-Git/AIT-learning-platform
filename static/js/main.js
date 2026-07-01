async function postJson(path, data) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}

function showMessage(container, message, isError = false) {
  if (!container) return;
  container.textContent = message;
  container.style.color = isError ? '#dc2626' : '#15803d';
}

async function handleForm(formId, messageId, apiPath, successRedirect) {
  const form = document.getElementById(formId);
  if (!form) return;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = document.getElementById(messageId);
    const formData = new FormData(form);
    const payload = {};

    for (const [key, value] of formData.entries()) {
      payload[key] = value;
    }

    const result = await postJson(apiPath, payload);
    if (result.error) {
      showMessage(message, result.error, true);
      return;
    }

    showMessage(message, result.message || 'Success!', false);
    if (successRedirect) {
      window.location.href = successRedirect;
    }
  });
}

async function loadProfile() {
  const profileContainer = document.getElementById('profile-content');
  if (!profileContainer) return;

  const response = await fetch('/api/profile');
  const result = await response.json();
  if (result.error) {
    profileContainer.innerHTML = `<p class="form-message">${result.error}</p>`;
    return;
  }

  const user = result.user;
  const courses = result.courses;

  const userHtml = `
    <div class="section">
      <h2>Account information</h2>
      <p><strong>Name:</strong> ${user.full_name}</p>
      <p><strong>Email:</strong> ${user.email}</p>
      <p><strong>Role:</strong> ${user.role}</p>
    </div>
  `;

  const coursesHtml = courses.length
    ? courses.map(course => `
      <div class="admin-card">
        <h3>${course.title}</h3>
        <p>${course.summary || course.description}</p>
        <p><strong>Progress:</strong> ${course.percentage}%</p>
      </div>
    `).join('')
    : '<p>You have not enrolled in any courses yet.</p>';

  profileContainer.innerHTML = `
    ${userHtml}
    <div class="section">
      <h2>Enrolled courses</h2>
      ${coursesHtml}
    </div>
  `;
}

window.addEventListener('DOMContentLoaded', () => {
  handleForm('login-form', 'login-message', '/api/login', '/profile.html');
  handleForm('register-form', 'register-message', '/api/register', '/login.html');
  loadProfile();
});

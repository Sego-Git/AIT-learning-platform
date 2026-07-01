async function fetchJson(path) {
  const response = await fetch(path);
  return response.json();
}

async function postJson(path, data) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}

function renderAdminList(items, container, emptyText, type) {
  if (!container) return;
  container.innerHTML = items.length
    ? items.map(item => `
        <div class="admin-card">
          <h3>${item.title}</h3>
          <p>${item.description || item.summary || 'No description provided.'}</p>
          ${item.detail ? `<small>${item.detail}</small>` : ''}
        </div>
      `).join('')
    : `<p>${emptyText}</p>`;
}

async function loadAdminData() {
  const courseList = document.getElementById('course-list');
  const eventList = document.getElementById('event-list');
  const courses = await fetchJson('/api/admin/courses');
  const events = await fetchJson('/api/admin/events');
  renderAdminList(courses.courses || [], courseList, 'No courses added yet.', 'course');
  renderAdminList(events.events || [], eventList, 'No events added yet.', 'event');
}

window.addEventListener('DOMContentLoaded', () => {
  const courseForm = document.getElementById('course-form');
  const eventForm = document.getElementById('event-form');

  const messageArea = (text) => {
    const container = document.querySelector('.form-message') || document.createElement('div');
    container.className = 'form-message';
    container.textContent = text;
    if (!document.querySelector('.form-message')) {
      courseForm.prepend(container);
    }
  };

  if (courseForm) {
    courseForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const payload = {
        title: document.getElementById('course-title').value.trim(),
        summary: document.getElementById('course-summary').value.trim(),
        description: document.getElementById('course-description').value.trim(),
        price: document.getElementById('course-price').value.trim(),
      };
      const result = await postJson('/api/admin/courses', payload);
      if (result.error) {
        messageArea(result.error);
        return;
      }
      messageArea('Course added successfully.');
      courseForm.reset();
      loadAdminData();
    });
  }

  if (eventForm) {
    eventForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const payload = {
        title: document.getElementById('event-title').value.trim(),
        event_date: document.getElementById('event-date').value,
        location: document.getElementById('event-location').value.trim(),
        description: document.getElementById('event-description').value.trim(),
      };
      const result = await postJson('/api/admin/events', payload);
      if (result.error) {
        messageArea(result.error);
        return;
      }
      messageArea('Event added successfully.');
      eventForm.reset();
      loadAdminData();
    });
  }

  loadAdminData();
});

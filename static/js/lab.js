require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });

let editor;
let currentExercise = null;

require(['vs/editor/editor.main'], function() {
  editor = monaco.editor.create(document.getElementById('editor'), {
    value: '# Write your Python code here\nprint("Hello, World!")',
    language: 'python',
    theme: 'vs-light',
    fontSize: 14,
    automaticLayout: true,
    minimap: { enabled: true },
  });

  // Load exercise from URL params
  const params = new URLSearchParams(window.location.search);
  const exerciseId = params.get('exercise_id');
  if (exerciseId) {
    loadExercise(exerciseId);
  }
});

async function loadExercise(exerciseId) {
  try {
    const response = await fetch(`/api/exercises/${exerciseId}`, {
      credentials: 'include',
    });
    if (!response.ok) {
      showOutput('Error loading exercise', 'error');
      return;
    }
    currentExercise = await response.json();
    document.getElementById('exercise-title').textContent = currentExercise.title;
    document.getElementById('exercise-description').textContent = currentExercise.description;
    
    if (currentExercise.starter_code) {
      editor.setValue(currentExercise.starter_code);
    }

    // Show test cases
    if (currentExercise.test_cases && typeof currentExercise.test_cases === 'string') {
      try {
        currentExercise.test_cases = JSON.parse(currentExercise.test_cases);
      } catch (e) {
        currentExercise.test_cases = [];
      }
    }

    document.getElementById('lesson-content').innerHTML = `
      <h2>${currentExercise.title}</h2>
      <p>${currentExercise.description}</p>
      <div class="code-example">
        <strong>Starter Code:</strong>
        <pre>${escapeHtml(currentExercise.starter_code || '')}</pre>
      </div>
      ${currentExercise.test_cases && currentExercise.test_cases.length ? `
        <div>
          <h3>Test Cases</h3>
          <ul>
            ${currentExercise.test_cases.map(tc => `<li><code>${escapeHtml(tc)}</code></li>`).join('')}
          </ul>
        </div>
      ` : ''}
    `;
  } catch (error) {
    showOutput(`Error: ${error.message}`, 'error');
  }
}

document.getElementById('run-btn').addEventListener('click', async () => {
  const code = editor.getValue();
  const output = document.getElementById('output');
  output.innerHTML = ''; // Clear output first
  
  showOutput('Executing code...', 'success');
  
  try {
    const response = await fetch('/api/execute-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Include session cookies
      body: JSON.stringify({ code }),
    });
    
    const result = await response.json();
    output.innerHTML = ''; // Clear the "Executing..." message
    
    console.log('Response status:', response.status);
    console.log('Result:', result);
    
    // Check if response status is not OK
    if (!response.ok) {
      showOutput(`Error (${response.status}): ${result.error || 'Failed to execute code'}`, 'error');
      return;
    }
    
    // Display any errors from execution
    if (result.error && result.error.trim()) {
      showOutput(result.error, 'error');
    }
    
    if (result.output && result.output.trim()) {
      showOutput(result.output, 'success');
    }
    
    if (!result.error && !result.output) {
      showOutput('Code executed successfully (no output)', 'success');
    }
  } catch (error) {
    output.innerHTML = '';
    showOutput(`Network error: ${error.message}`, 'error');
    console.error('Fetch error:', error);
  }
});

document.getElementById('submit-btn').addEventListener('click', async () => {
  if (!currentExercise) {
    showOutput('No exercise loaded', 'error');
    return;
  }
  const code = editor.getValue();
  try {
    const response = await fetch(`/api/exercises/${currentExercise.id}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ code }),
    });
    const result = await response.json();
    const output = document.getElementById('output');
    output.innerHTML = '';
    if (result.test_results) {
      // Show test case results
      result.test_results.forEach((tr, idx) => {
        const line = document.createElement('div');
        line.className = `output-line output-${tr.passed ? 'success' : 'error'}`;
        line.innerHTML = `<strong>Test ${idx + 1}:</strong> Expected: <code>${escapeHtml(tr.expected)}</code> | Got: <code>${escapeHtml(tr.actual)}</code> ${tr.passed ? '✓' : '✗'}`;
        output.appendChild(line);
      });
      if (result.passed) {
        showOutput('✓ All test cases passed! Great job!', 'success');
      } else {
        showOutput('✗ Some test cases failed. See above.', 'error');
      }
    } else if (result.passed) {
      showOutput('✓ Exercise passed! Great job!', 'success');
    } else {
      showOutput(`✗ Exercise failed: ${result.error || 'Unknown error'}`, 'error');
    }
  } catch (error) {
    showOutput(`Error: ${error.message}`, 'error');
  }
});

document.getElementById('reset-btn').addEventListener('click', () => {
  if (currentExercise && currentExercise.starter_code) {
    editor.setValue(currentExercise.starter_code);
    document.getElementById('output').innerHTML = '';
  }
});

function showOutput(text, type = 'success') {
  const output = document.getElementById('output');
  
  // Split text into lines for better display
  const lines = text.split('\n').filter(line => line || line === '');
  
  lines.forEach(line => {
    const lineEl = document.createElement('div');
    lineEl.className = `output-line output-${type}`;
    lineEl.textContent = line || ' '; // Show space for empty lines
    output.appendChild(lineEl);
  });
  
  // Auto-scroll to bottom
  output.scrollTop = output.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

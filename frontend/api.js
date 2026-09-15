const API_BASE = window.location.origin;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}.`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch {
      // Keep the HTTP status message when the server did not return JSON.
    }
    throw new Error(detail);
  }

  return response.json();
}

export function fetchState() {
  return request('/state');
}

export function addMember(name) {
  return request('/members', {
    method: 'POST',
    body: JSON.stringify({ name })
  });
}

export function addExpense({ desc, amount, date, participants, payer }) {
  return request('/expenses', {
    method: 'POST',
    body: JSON.stringify({ desc, amount: Number(amount), date, participants, payer })
  });
}

export function recordSettlement({ from, to, amount, date, notes }) {
  return request('/settlements', {
    method: 'POST',
    body: JSON.stringify({ from, to, amount: Number(amount), date, notes })
  });
}

export function closeGroup() {
  return request('/group/close', { method: 'POST' });
}

export function reopenGroup() {
  return request('/group/reopen', { method: 'POST' });
}

export function computeBalances() {
  return request('/balances');
}

export default {
  fetchState,
  addMember,
  addExpense,
  recordSettlement,
  closeGroup,
  reopenGroup,
  computeBalances
};

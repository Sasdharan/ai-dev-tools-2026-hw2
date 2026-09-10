import api from './api.js';

const qs = s=>document.querySelector(s);

async function refresh(){
  const state = await api.fetchState();
  renderGroup(state.group);
  renderMembers(state.members);
  renderParticipants(state.members);
  renderExpenses(state.expenses);
  renderBalances(await api.computeBalances(), state.members);
  renderSettlements(state.settlements, state.members);
}

function renderGroup(group){
  qs('#group-info').textContent = `${group.name} (${group.closed? 'Closed':'Open'})`;
  qs('#close-group-btn').disabled = group.closed;
  qs('#reopen-group-btn').disabled = !group.closed;
}

function renderMembers(members){
  const el = qs('#members-list'); el.innerHTML='';
  members.forEach(m=>{
    const d = document.createElement('div'); d.className='member'; d.textContent = m.name; d.dataset.id=m.id;
    el.appendChild(d);
  });
  // populate settlement selects
  const from = qs('#settle-from'); const to = qs('#settle-to');
  from.innerHTML=''; to.innerHTML='';
  members.forEach(m=>{ from.appendChild(new Option(m.name,m.id)); to.appendChild(new Option(m.name,m.id)); });
}

function renderParticipants(members){
  const list = qs('#participant-list'); list.innerHTML='';
  members.forEach(m=>{
    const id = `p_${m.id}`;
    const lbl = document.createElement('label');
    lbl.innerHTML = `<input type="checkbox" value="${m.id}" checked /> ${m.name}`;
    list.appendChild(lbl);
  });
}

function renderExpenses(expenses){
  const el = qs('#expenses-list'); el.innerHTML='';
  expenses.forEach(e=>{
    const d = document.createElement('div'); d.className='expense';
    d.innerHTML = `<b>${e.desc}</b> $${e.amount.toFixed(2)} — ${e.date} — participants: ${e.participants.length}`;
    el.appendChild(d);
  });
}

function renderBalances(balances, members){
  const el = qs('#balances'); el.innerHTML='';
  members.forEach(m=>{
    const v = balances[m.id]||0; const row = document.createElement('div');
    row.textContent = `${m.name}: ${v>=0? '$'+v.toFixed(2) : '-$'+Math.abs(v).toFixed(2)}`;
    el.appendChild(row);
  });
}

function renderSettlements(settlements, members){
  const el = qs('#settlements-list'); el.innerHTML='';
  settlements.forEach(s=>{
    const from = members.find(m=>m.id===s.from)?.name||s.from;
    const to = members.find(m=>m.id===s.to)?.name||s.to;
    const d = document.createElement('div'); d.textContent = `${s.date || ''} ${from} → ${to}: $${s.amount.toFixed(2)}`;
    el.appendChild(d);
  });
}

// Handlers
qs('#add-member-btn').addEventListener('click', async ()=>{
  const name = qs('#member-name').value.trim(); if(!name) return;
  await api.addMember(name); qs('#member-name').value=''; await refresh();
});

qs('#expense-form').addEventListener('submit', async e=>{
  e.preventDefault();
  const desc = qs('#expense-desc').value; const amount = qs('#expense-amt').value; const date = qs('#expense-date').value || new Date().toISOString().slice(0,10);
  const mode = document.querySelector('input[name=mode]:checked').value;
  const checked = Array.from(qs('#participant-list').querySelectorAll('input[type=checkbox]:checked')).map(i=>i.value);
  const participants = mode==='everyone' ? (await api.fetchState()).members.map(m=>m.id) : checked;
  if(participants.length===0) { alert('Select participants'); return; }
  await api.addExpense({desc, amount, date, participants});
  qs('#expense-desc').value=''; qs('#expense-amt').value=''; await refresh();
});

qs('#record-settlement-btn').addEventListener('click', async ()=>{
  const from = qs('#settle-from').value; const to = qs('#settle-to').value; const amount = qs('#settle-amt').value;
  if(!from || !to || !amount) { alert('Select from/to and amount'); return; }
  await api.recordSettlement({from,to,amount,date:new Date().toISOString().slice(0,10)});
  qs('#settle-amt').value=''; await refresh();
});

qs('#close-group-btn').addEventListener('click', async ()=>{ await api.closeGroup(); await refresh(); });
qs('#reopen-group-btn').addEventListener('click', async ()=>{ await api.reopenGroup(); await refresh(); });

window.addEventListener('load', ()=>{ refresh(); });

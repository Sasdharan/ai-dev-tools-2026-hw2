import api from './api.js';

const qs = s=>document.querySelector(s);

async function refresh(){
  const state = await api.fetchState();
  renderGroup(state.group);
  renderMembers(state.members);
  renderParticipants(state.members);
  renderPayerOptions(state.members);
  renderExpenses(state.expenses);
  renderBalances(await api.computeBalances(), state.members);
  renderSettlements(state.settlements, state.members);
}

function renderGroup(group){
  qs('#group-info').textContent = `${group.name} (${group.closed? 'Closed':'Open'})`;
  qs('#close-group-btn').disabled = group.closed;
  qs('#reopen-group-btn').disabled = !group.closed;
  // enable/disable settlement UI depending on closed state
  qs('#record-settlement-btn').disabled = !group.closed;
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
  const everyone = qs('input[name=mode]:checked').value === 'everyone';
  members.forEach(m=>{
    const lbl = document.createElement('label');
    lbl.innerHTML = `<input type="checkbox" value="${m.id}"${everyone ? ' checked' : ''} /> ${m.name}`;
    list.appendChild(lbl);
  });
}

function renderPayerOptions(members){
  const sel = qs('#expense-payer'); sel.innerHTML='';
  members.forEach(m=> sel.appendChild(new Option(m.name,m.id)));
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
  // show numeric balances
  members.forEach(m=>{
    const v = balances[m.id]||0; const row = document.createElement('div');
    row.textContent = `${m.name}: ${v>=0? '$'+v.toFixed(2) : '-$'+Math.abs(v).toFixed(2)}`;
    el.appendChild(row);
  });

  renderSuggestedSettlements(balances, members);
}

function renderSuggestedSettlements(balances, members){
  const el = qs('#suggested-settlements'); el.innerHTML='';
  const sug = document.createElement('div');
  const creditors = members.map(m=>({id:m.id,name:m.name,bal:balances[m.id]||0})).filter(x=>x.bal>0).sort((a,b)=>b.bal-a.bal);
  const debtors = members.map(m=>({id:m.id,name:m.name,bal:balances[m.id]||0})).filter(x=>x.bal<0).sort((a,b)=>a.bal-b.bal);
  if(creditors.length || debtors.length){
    let i=0,j=0;
    while(i<debtors.length && j<creditors.length){
      const d = debtors[i]; const c = creditors[j];
      const take = Math.min(-d.bal, c.bal);
      const line = document.createElement('div');
      line.textContent = `${d.name} → ${c.name}: $${take.toFixed(2)}`;
      sug.appendChild(line);
      d.bal += take; c.bal -= take;
      if(Math.abs(d.bal) < 0.005) i++; if(c.bal < 0.005) j++;
    }
    el.appendChild(sug);
  }
  qs('#suggested-settlements-heading').hidden = !(creditors.length || debtors.length);
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
  const payer = qs('#expense-payer').value || participants[0];
  if(!participants.length) { alert('Select participants'); return; }
  await api.addExpense({desc, amount, date, participants, payer});
  qs('#expense-desc').value=''; qs('#expense-amt').value=''; await refresh();
});

qs('#record-settlement-btn').addEventListener('click', async ()=>{
  const from = qs('#settle-from').value; const to = qs('#settle-to').value; const amount = qs('#settle-amt').value;
  const state = await api.fetchState();
  if(!state.group.closed){ alert('Group must be closed to record settlements'); return; }
  if(!from || !to || !amount) { alert('Select from/to and amount'); return; }
  await api.recordSettlement({from,to,amount,date:new Date().toISOString().slice(0,10)});
  qs('#settle-amt').value=''; await refresh();
});

qs('#close-group-btn').addEventListener('click', async ()=>{ await api.closeGroup(); await refresh(); });
qs('#reopen-group-btn').addEventListener('click', async ()=>{ await api.reopenGroup(); await refresh(); });

window.addEventListener('load', ()=>{ refresh(); });

// Prevent future dates and manage mode switching default checks
const dateInput = qs('#expense-date');
dateInput.max = new Date().toISOString().slice(0,10);

document.querySelectorAll('input[name=mode]').forEach(r=> r.addEventListener('change', e=>{
  const mode = e.target.value;
  const checks = qs('#participant-list').querySelectorAll('input[type=checkbox]');
  if(mode === 'everyone'){
    checks.forEach(c=>c.checked = true);
  } else {
    checks.forEach(c=>c.checked = false);
  }
}));

// Centralized mocked backend API
let state = {
  group: { id: 'g1', name: 'Trip', closed: false },
  members: [ { id: 'm1', name: 'Alice' }, { id: 'm2', name: 'Bob' } ],
  expenses: [],
  settlements: []
};

function uid(prefix='id'){
  return prefix+Math.random().toString(36).slice(2,9);
}

export async function fetchState(){
  return structuredClone(state);
}

export async function addMember(name){
  const m = { id: uid('m'), name };
  state.members.push(m);
  return m;
}

export async function addExpense({desc, amount, date, participants}){
  const e = { id: uid('e'), desc, amount: Number(amount), date, participants, locked:false };
  state.expenses.push(e);
  return e;
}

export async function recordSettlement({from,to,amount,date,notes}){
  const s = { id: uid('s'), from, to, amount: Number(amount), date, notes };
  state.settlements.push(s);
  // apply to balances by creating adjustment expense (simplified)
  return s;
}

export async function closeGroup(){ state.group.closed = true; return state.group; }
export async function reopenGroup(){ state.group.closed = false; return state.group; }

export async function computeBalances(){
  // simple balance computation: for each expense, split equally among participants
  const balances = {};
  state.members.forEach(m=>balances[m.id]=0);
  state.expenses.forEach(e=>{
    const share = e.amount / e.participants.length;
    e.participants.forEach(pid=>{
      if(pid===e.payer) return; // payer field optional
      balances[pid] += share;
    });
    // assume first participant paid if no payer
    const payer = e.payer || e.participants[0];
    balances[payer] -= e.amount - (e.participants.includes(payer)? (e.amount / e.participants.length):0);
  });
  // apply settlements
  state.settlements.forEach(s=>{
    balances[s.from] += s.amount;
    balances[s.to] -= s.amount;
  });
  return balances;
}

export default { fetchState, addMember, addExpense, recordSettlement, closeGroup, reopenGroup, computeBalances };

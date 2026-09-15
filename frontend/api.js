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
  const e = { id: uid('e'), desc, amount: Number(amount), date, participants, payer: participants[0], locked:false };
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
  // compute balances: positive = credit (should receive), negative = owes
  const balances = {};
  state.members.forEach(m=>balances[m.id]=0);
  state.expenses.forEach(e=>{
    const payer = e.payer || e.participants[0];
    const share = e.amount / e.participants.length;
    // each participant owes their share
    e.participants.forEach(pid=>{
      balances[pid] -= share;
    });
    // payer paid full amount, so credit payer
    balances[payer] += e.amount;
  });
  // apply settlements: from pays amount to to
  state.settlements.forEach(s=>{
    balances[s.from] += s.amount * 1; // payer gets credit reduction
    balances[s.to] -= s.amount * 1;
  });
  return balances;
}

export default { fetchState, addMember, addExpense, recordSettlement, closeGroup, reopenGroup, computeBalances };

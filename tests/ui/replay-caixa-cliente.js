// Teste de navegador (requer Playwright): reproduz um banco real e alterna a caixa "Enviar ao dono do negócio" várias vezes.
// Uso: node tests/ui/replay-caixa-cliente.js caminho/para/.spec/entrevista.html
const { chromium } = require('playwright');
const REAL={clientes:{
 "D-01":{ativa:true,em:"2026-11-14T16:20:21Z",opcoes:[],texto:"Hoje você guarda a lista de clientes..."},
 "N-03":{ativa:true,em:"2026-11-14T16:20:21Z",opcoes:[],texto:"Como você vai saber..."},
 "N-04":{ativa:false,dispensada:true,em:"2026-11-14T18:26:48Z"},
 "N-05":{ativa:false,dispensada:true,em:"2026-11-14T18:26:12Z"},
 "N-06":{arquivo:false,ativa:true,em:"2026-11-14T17:46:36Z",opcoes:["Até R$ 100 por mês"],texto:"Quanto você pretende gastar por mês?"},
 "U-01":{ativa:true,em:"2026-11-14T16:20:21Z",opcoes:[],texto:"Quem vai usar o sistema?"},
 "U-05":{arquivo:false,ativa:true,em:"2026-11-14T18:26:34Z",opcoes:[],texto:"Quantas pessoas vão usar o sistema e quantos clientes você atende por mês?"},
 "X-01":{arquivo:false,ativa:true,em:"2026-11-14T17:49:15Z",opcoes:["Até 50 por mês"],texto:"Hoje, quantos pedidos?"},
 "X-02":{ativa:true,em:"2026-11-14T16:35:05Z",opcoes:[],texto:"Seus gerentes de loja..."},
 "X-03":{ativa:true,em:"2026-11-14T16:35:05Z",opcoes:[],texto:"Sua planilha..."}},
 answers:{
 "N-04":{em:"2026-11-14T18:26:00Z",indices:[1],texto:"",tipo:"opcao"},
 "U-05":{em:"2026-11-14T18:26:31Z",tipo:"reaberta"},
 "N-06":{arquivo:false,em:"2026-11-14T17:46:36Z",opcoes:["Até R$ 100 por mês"],texto:"Quanto...",tipo:"cliente"},
 "X-01":{arquivo:false,em:"2026-11-14T17:49:15Z",opcoes:["Até 50 por mês"],texto:"Hoje...",tipo:"cliente"},
 "X-02":{ativa:true,em:"2026-11-14T16:35:05Z",opcoes:[],texto:"Seus gerentes...",tipo:"cliente"},
 "X-03":{ativa:true,em:"2026-11-14T16:35:05Z",opcoes:[],texto:"Sua planilha...",tipo:"cliente"},
 "U-06":{em:"2026-11-14T17:36:22Z",texto:"",tipo:"bypass"}}};
(async()=>{const b=await chromium.launch();const ctx=await b.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});const p=await ctx.newPage();
const logs=[];p.on('pageerror',e=>logs.push('PAGEERROR '+e.message));
await p.addInitScript(real=>{
  const K='__mockdb';if(!localStorage.getItem(K))localStorage.setItem(K,JSON.stringify(real));
  const st=JSON.parse(localStorage.getItem(K));window.__st=st;const subs={answers:[],clientes:[]};
  const snap=(col,cache)=>({docs:Object.entries(st[col]).map(([id,d])=>({id,exists:true,data:()=>d})),metadata:{fromCache:!!cache}});
  const save=()=>localStorage.setItem(K,JSON.stringify(st));
  window.claude={use:async n=>n==='db'?{doc:path=>({set:async d=>{const [col,id]=path.split('/');st[col][id]=JSON.parse(JSON.stringify(d));save();setTimeout(()=>subs[col].forEach(f=>f(snap(col))),15);}}),
    collection:col=>({onSnapshot:cb=>{subs[col].push(cb);setTimeout(()=>cb(snap(col,true)),5);setTimeout(()=>cb(snap(col,false)),60);return()=>{}}})}:null};},REAL);
const url='file://'+process.argv[2];
await p.goto(url);await p.waitForTimeout(500);
const chip=async()=>{const t=await p.evaluate(()=>{const c=document.querySelector('.pinchip');return c?c.textContent.replace(/\s+/g,' '):'(sem chip)'});return t;};
const irPara=async id=>{ // navega até o bloco que contém a pergunta
  for(const nome of ['Negócio','Usuários']){await p.tap('.chip:has-text("'+nome+'")').catch(()=>{});await p.waitForTimeout(100);
    if(await p.evaluate(a=>!!document.querySelector('[data-card="'+a+'"]'),id))return true;}return false;};
const ligado=async id=>{await irPara(id);return p.evaluate(a=>document.querySelector('[data-card="'+a+'"] input[data-cli]').checked,id);};
const ids=['N-04','N-05','U-05'];
const estado=async()=>{const o={};for(const i of ids)o[i]=await ligado(i);return JSON.stringify(o);};
console.log('0) situação REAL em que você ficou:',await estado(),'|',await chip(),'  (N-04 e N-05 desligadas, U-05 ligada)');
// desmarcar/remarcar N-05 várias vezes, sem esperar (até no mesmo segundo)
await irPara('N-05');
const sel='[data-card="N-05"] input[data-cli]';
for(let k=1;k<=6;k++){await p.tap(sel);await p.waitForTimeout(k%2?30:250);}
await p.waitForTimeout(400);
console.log('1) alternei N-05 seis vezes (algumas no mesmo segundo):',await estado(),'| banco N-05 ativa:',await p.evaluate(()=>window.__st.clientes['N-05'].ativa));
console.log('   N-04 e U-05 intactas? ',(await estado())===JSON.stringify({'N-04':false,'N-05':false,'U-05':true}));
// ligar N-05 e conferir que só ela mudou
await irPara('N-05');await p.tap(sel);await p.waitForTimeout(400);
console.log('2) liguei N-05:',await estado(),'|',await chip());
// recarregar: tudo persiste
await p.reload();await p.waitForTimeout(600);
console.log('3) após recarregar:',await estado(),'|',await chip());
// desligar U-05, ligar N-04: troca independente
await irPara('U-05');await p.tap('[data-card="U-05"] input[data-cli]');await p.waitForTimeout(250);
await irPara('N-04');await p.tap('[data-card="N-04"] input[data-cli]');await p.waitForTimeout(350);
console.log('4) desliguei U-05 e liguei N-04:',await estado(),'|',await chip());
// ordem real dos carimbos: sempre crescente por pergunta
const ems=await p.evaluate(()=>['N-04','N-05','U-05'].map(i=>window.__st.clientes[i].em));
console.log('   carimbos finais:',ems.join(' | '));
console.log('erros JS:',logs.join('|')||'nenhum');await b.close();})();

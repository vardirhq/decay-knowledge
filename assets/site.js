const docs=[
{title:'Your first script',kind:'Learn',text:'scripts export update dt gameplay behaviour',href:'#first-script'},
{title:'Variables & types',kind:'Learn',text:'let var f32 bool string types vectors',href:'#learn'},
{title:'Entities & scripts',kind:'Learn',text:'entity scripts behaviour component relationship',href:'#learn'},
{title:'Script communication',kind:'Learn',text:'typed script references messages communicate another script',href:'#learn'},
{title:'Events',kind:'Language reference',text:'event emit on broadcast project wide typed event',href:'#reference'},
{title:'Shared state',kind:'Language reference',text:'state global variable shared project game score',href:'#reference'},
{title:'Vec2',kind:'Language reference',text:'vector position direction normalized distance lerp',href:'#reference'},
{title:'Move an entity',kind:'Cookbook',text:'movement input transform position speed delta time dt',href:'#cookbook'},
{title:'Input',kind:'Sindri API',text:'keyboard gamepad controller actions axis player input',href:'#reference'},
{title:'Physics',kind:'Sindri API',text:'collision collider impulse velocity rigid body',href:'#reference'},
{title:'Choosing messages, events and state',kind:'Concept',text:'communication message event state global specific script architecture',href:'#concepts'},
{title:'Make a game',kind:'Tutorial',text:'complete game arena enemies health score audio weave export',href:'#game'}
];
const dialog=document.querySelector('#searchDialog');const input=document.querySelector('#searchInput');const results=document.querySelector('#searchResults');
function render(q=''){const words=q.toLowerCase().trim().split(/\s+/).filter(Boolean);const found=docs.filter(d=>!words.length||words.every(w=>(d.title+' '+d.kind+' '+d.text).toLowerCase().includes(w))).slice(0,9);results.innerHTML=found.length?found.map(d=>`<a class="search-result" href="${d.href}" data-close><strong>${d.title}</strong><span>${d.kind}</span></a>`).join(''):'<div class="empty">No results. Either the docs are missing it or you have discovered a new spelling of “velocity”.</div>';results.querySelectorAll('[data-close]').forEach(a=>a.addEventListener('click',()=>dialog.close()))}
function openSearch(){render('');dialog.showModal();setTimeout(()=>input.focus(),20)}
document.querySelector('#searchTrigger').addEventListener('click',openSearch);input.addEventListener('input',()=>render(input.value));document.addEventListener('keydown',e=>{if(e.key==='/'&&!dialog.open&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();openSearch()}if(e.key==='Escape'&&dialog.open)dialog.close()});
document.querySelectorAll('[data-copy]').forEach(btn=>btn.addEventListener('click',async()=>{const el=document.getElementById(btn.dataset.copy);try{await navigator.clipboard.writeText(el.innerText);btn.textContent='Copied';setTimeout(()=>btn.textContent='Copy',1200)}catch{btn.textContent='Select & copy'}}));
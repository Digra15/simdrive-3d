import{a as o,i as s,o as c,r as l,t as u}from"./types-PM6GkcTL.js";
/* License client milik sendiri. Utama: /api/license/* (serve.py). Cadangan: window.SimDriveLicense (static/offline). */
const API=`/api/license`;
const M={"/check":`check`,"/verify":`verify`,"/activate":`activate`,"/deactivate":`deactivate`,"/identify":`identify`,"/bind":`bind`,"/session":`session`};
function L(e,t){let g=window.SimDriveLicense;if(g&&typeof g[M[e]]===`function`)return g[M[e]](t);throw Error(`Mesin lisensi tidak tersedia`)}
async function R(e,t){try{let n=await fetch(API+e,{method:`POST`,headers:{"content-type":`application/json`},body:JSON.stringify(t||{})});if(!n.ok)throw Error(`status ${n.status}`);return await n.json()}catch{return await L(e,t)}}
function K(e){return async(...t)=>{let n=t[0]&&t[0].data||{};return await R(e,n)}}
function f(e){return e}
var p=12e4,m=c().regex(/^[a-zA-Z0-9_-]{8,100}$/),h=s({licensed:u(),trialLeftMs:l().finite().min(0).max(p),trialUsed:u(),expiresAt:c().nullable().optional()});
function g(e,t=Date.now()){let n=h.parse(e);if(n.licensed){if(!n.trialUsed||n.trialLeftMs!==0||n.expiresAt===void 0)throw Error(`Respons lisensi tidak valid`);if(n.expiresAt===null)return{...n,status:`lifetime_active`};let e=Date.parse(n.expiresAt);if(!Number.isFinite(e))throw Error(`Tanggal lisensi tidak valid`);return e>t?{...n,status:`licensed_active`}:{licensed:!1,trialUsed:!0,trialLeftMs:0,status:`expired`}}if(n.expiresAt!=null||!n.trialUsed&&n.trialLeftMs!==12e4)throw Error(`Respons trial tidak valid`);return{...n,status:n.trialUsed?n.trialLeftMs>0?`trial_active`:`expired`:`unverified`}}
var _=K(`/check`),v=K(`/verify`),y=K(`/activate`),b=K(`/deactivate`),x=K(`/identify`),S=K(`/bind`),C=K(`/session`);
export{C as a,m as c,S as i,g as l,x as n,_ as o,b as r,v as s,y as t,f as u};
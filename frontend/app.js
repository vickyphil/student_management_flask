
const app=document.getElementById("app");
const toastEl=document.getElementById("toast");
let me=null, catalog=null;

const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const money=n=>"₦"+Number(n||0).toLocaleString("en-NG",{minimumFractionDigits:0,maximumFractionDigits:2});
const fullName=s=>[s?.first_name,s?.middle_name,s?.last_name].filter(Boolean).join(" ");
const badge=s=>{
 const cls=s==="Active"||s==="Paid"||s==="Cleared"||s==="Completed"?"badge-green":s==="Suspended"||s==="Overdue"||s==="Not Cleared"?"badge-red":s==="Registered"?"badge-blue":"badge-gray";
 return `<span class="badge ${cls}">${esc(s||"—")}</span>`;
};
function toast(msg){toastEl.textContent=msg;toastEl.classList.add("show");setTimeout(()=>toastEl.classList.remove("show"),2800)}
async function api(url,opts={}){
 const r=await fetch(url,{credentials:"same-origin",headers:{"Content-Type":"application/json",...(opts.headers||{})},...opts});
 let d={}; try{d=await r.json()}catch{}
 if(r.status===401){me=null;if(location.pathname!="/") renderLogin();throw new Error(d.error||"Authentication required")}
 if(!r.ok) throw new Error(d.error||"Request failed");
 return d;
}
async function loadMe(){try{const d=await api("/api/auth/me");me=d.authenticated?d.user:null}catch{me=null}}

function authShell(title,body,footer=""){
 return `<main class="auth-shell"><section class="auth-card">
 <h1>${title}</h1><p>Veritas University</p>${body}<div class="auth-footer">${footer}</div></section></main>`;
}
function renderLogin(){
 app.innerHTML=authShell("Welcome back",`<form id="login-form" class="form-stack">
 <label>Email<input id="email" type="email" required autocomplete="email"></label>
 <label>Password<input id="password" type="password" required autocomplete="current-password"></label>
 <div id="auth-error" class="error-box hidden"></div><button class="btn btn-primary" type="submit">Log in</button>
 <a class="auth-link" href="#forgot">Forgot password?</a></form>`,
 `Don't have an account? <a class="auth-link" href="#register">Create one</a>`);
 document.getElementById("login-form").onsubmit=async e=>{
  e.preventDefault();const err=document.getElementById("auth-error");
  try{await api("/api/auth/login",{method:"POST",body:JSON.stringify({email:email.value,password:password.value})});location.hash="#/";route()}
  catch(x){err.textContent=x.message;err.classList.remove("hidden")}
 };
}
function renderRegister(){
 app.innerHTML=authShell("Create your account",`<form id="register-form" class="form-stack">
 <label>Full name<input id="name" required></label><label>Email<input id="email" type="email" required></label>
 <label>Password<input id="password" type="password" minlength="8" required></label>
 <label>Confirm password<input id="confirm" type="password" minlength="8" required></label>
 <div id="auth-error" class="error-box hidden"></div><button class="btn btn-primary">Create account</button></form>`,
 `Already have an account? <a class="auth-link" href="#login">Log in</a>`);
 document.getElementById("register-form").onsubmit=async e=>{
  e.preventDefault();const err=document.getElementById("auth-error");
  if(password.value!==confirm.value){err.textContent="Passwords do not match.";err.classList.remove("hidden");return}
  try{const d=await api("/api/auth/register",{method:"POST",body:JSON.stringify({email:email.value,password:password.value,full_name:name.value})});
   app.innerHTML=authShell("Verify your email",`<form id="verify-form" class="form-stack">
   <p>${esc(d.message)}</p>${d.development_otp?`<div class="success-box">Development code: <strong>${esc(d.development_otp)}</strong></div>`:""}
   <label>6-digit code<input id="otp" inputmode="numeric" maxlength="6" required></label>
   <div id="verify-error" class="error-box hidden"></div><button class="btn btn-primary">Verify</button></form>`,`<a class="auth-link" href="#login">Back to login</a>`);
   document.getElementById("verify-form").onsubmit=async ev=>{ev.preventDefault();const er=document.getElementById("verify-error");try{await api("/api/auth/verify",{method:"POST",body:JSON.stringify({email:email.value,otp:otp.value})});await loadMe();location.hash="#/";route()}catch(x){er.textContent=x.message;er.classList.remove("hidden")}};
  }catch(x){err.textContent=x.message;err.classList.remove("hidden")}
 };
}
function renderForgot(){
 app.innerHTML=authShell("Reset password",`<form id="forgot-form" class="form-stack">
 <label>Email<input id="email" type="email" required></label><div id="auth-error" class="success-box hidden"></div>
 <button class="btn btn-primary">Send reset link</button></form>`,`<a class="auth-link" href="#login">Back to login</a>`);
 document.getElementById("forgot-form").onsubmit=async e=>{e.preventDefault();const box=document.getElementById("auth-error");try{const d=await api("/api/auth/forgot",{method:"POST",body:JSON.stringify({email:email.value})});box.textContent=d.message;box.classList.remove("hidden")}catch(x){box.textContent=x.message;box.className="error-box"}};
}

function shell(content){
 const initials=(me?.full_name||me?.email||"U").split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase();
 app.innerHTML=`<div class="app-shell"><aside class="sidebar"><div class="brand"><span class="brand-mark">V</span><span><strong>VERITAS</strong><small>Veritas University</small></span></div><nav class="nav">
 <a href="#/" data-nav><span class="nav-icon">▦</span>Dashboard</a><a href="#/students" data-nav><span class="nav-icon">♧</span>Students</a><a href="#/courses" data-nav><span class="nav-icon">▤</span>Courses</a><a href="#/results" data-nav><span class="nav-icon">⌁</span>Results</a><a href="#/finance" data-nav><span class="nav-icon">₦</span>Finance</a><a href="#/analytics" data-nav><span class="nav-icon">⌁</span>Analytics</a><a href="#/audit" data-nav><span class="nav-icon">▣</span>Audit Logs</a>
 </nav><div class="session-card"><span>ACTIVE SESSION</span><strong>2024/2025 · 1st Sem</strong></div></aside><div class="main"><header class="topbar"><strong class="topbar-title">Dashboard</strong><div class="topbar-search">⌕ <span>Search students, reg number, email...</span></div><div class="topbar-user"><span class="notification">♧<i></i></span><span class="user-avatar">${initials}</span><span><strong>${esc(me?.full_name||me?.email||"User")}</strong><small>${esc(me?.role||"user").replace(/^./,x=>x.toUpperCase())}</small></span><button id="logout" class="btn btn-secondary">Log out</button></div></header><main class="content">${content}</main></div></div>`;
 document.getElementById("logout").onclick=async()=>{await api("/api/auth/logout",{method:"POST"});me=null;location.hash="#login";route()};
 document.querySelectorAll("[data-nav]").forEach(a=>a.classList.toggle("active",a.getAttribute("href")===location.hash||(!location.hash&&a.getAttribute("href")==="#/")));
}

async function dashboard(){
 const d=await api("/api/dashboard");
 shell(`<div class="page-head"><h1>Admin Dashboard</h1><p>University-wide overview · Session 2024/2025</p></div>
 <div class="grid grid-4">
 ${stat("Total Students",d.total,"accent-blue","♧")}${stat("Active",d.active,"accent-green","♧")}${stat("Graduated",d.graduated,"accent-blue","⌁")}${stat("Suspended",d.suspended,"accent-red","♧")}
 ${stat("Faculties",d.faculties,"","▣")}${stat("Departments",d.departments,"","▣")}${stat("Programmes",d.programmes,"","▣")}${stat("Hostel Occupancy",d.hostel_allocated,"accent-blue","⌂")}
 </div>
 <div class="grid grid-2 fee-row">${stat("Total Fees Collected",money(d.collected),"accent-green","↗")}${stat("Outstanding Fees",money(d.outstanding),"accent-red","!")}</div>
 <div class="grid grid-2 dashboard-lower"><section class="card chart-card"><h3>Student Status Distribution</h3>${statusBar(d)}<div class="chart-legend"><span class="legend-green">■ Active</span><span class="legend-blue">■ Graduated</span><span class="legend-red">■ Suspended</span></div></section>
 <section class="card chart-card"><h3>Fee Collection (₦)</h3><div class="fee-chart"><span style="height:${Math.max(8,Math.min(100,(d.collected/(Number(d.collected)+Number(d.outstanding||1))*100)))}%"></span><span style="height:${Math.max(8,Math.min(100,(d.outstanding/(Number(d.collected)+Number(d.outstanding||1))*100)))}%"></span></div><div class="chart-labels"><span>Collected</span><span>Outstanding</span></div></section></div>
 <section class="card recent-card"><div class="section-heading"><h3>Recent Students</h3><a href="#/students">View all →</a></div><div class="list">${(d.students||[]).map(s=>`<a class="kpi-row" href="#/students/${s.id}" style="text-decoration:none;color:inherit"><span class="student-row"><span class="mini-avatar">${esc((s.first_name||"?")[0]+(s.last_name||"")[0])}</span><span><strong>${esc(fullName(s))}</strong><br><small class="muted">${esc(s.registration_number)}</small></span></span>${badge(s.student_status)}</a>`).join("")||'<div class="empty">No students yet.</div>'}</div></section>`);
}
function stat(label,value,cls="",icon=""){return `<section class="card stat-card"><span class="stat-icon ${cls}">${icon}</span><div><div class="stat-label">${label}</div><div class="stat-value ${cls}">${esc(value)}</div></div></section>`}
function statusBar(d){
 const vals=[["Active",d.active,"var(--green)"],["Graduated",d.graduated,"var(--primary)"],["Suspended",d.suspended,"var(--red)"],["Inactive",d.inactive,"#94a3b8"]];
 const total=Math.max(d.total,1);return vals.map(x=>`<div style="margin:12px 0"><div class="kpi-row"><span>${x[0]}</span><strong>${x[1]}</strong></div><div class="bar"><span style="width:${Math.min(100,x[1]/total*100)}%;background:${x[2]}"></span></div></div>`).join("")
}

async function students(){
 const params=new URLSearchParams();const q=window._studentQ||"";const st=window._studentStatus||"All";if(q)params.set("q",q);if(st!="All")params.set("status",st);
 const rows=await api("/api/students?"+params);
 shell(`<div class="page-head"><h1>Students</h1><p>${rows.length} student(s) found</p></div>
 <section class="card"><div class="toolbar"><input id="student-search" class="search input" placeholder="Search by name or registration number..." value="${esc(q)}"><select id="student-status" class="select" style="width:auto"><option>All</option>${["Active","Inactive","Suspended","Graduated","Withdrawn"].map(x=>`<option ${x===st?"selected":""}>${x}</option>`).join("")}</select>${me.role==="admin"?'<button id="add-student" class="btn btn-primary">Add student</button>':""}</div></section>
 <section class="card" style="margin-top:16px"><div class="table-wrap"><table class="table"><thead><tr><th>Student</th><th>Reg. Number</th><th>Level</th><th>Status</th><th></th></tr></thead><tbody>${rows.map(s=>`<tr><td><strong>${esc(fullName(s))}</strong></td><td>${esc(s.registration_number)}</td><td>${s.level} Level</td><td>${badge(s.student_status)}</td><td><a class="auth-link" href="#/students/${s.id}">View →</a></td></tr>`).join("")||'<tr><td colspan="5" class="empty">No students match your search.</td></tr>'}</tbody></table></div></section>`);
 document.getElementById("student-search").oninput=e=>{window._studentQ=e.target.value;clearTimeout(window._t);window._t=setTimeout(students,250)};
 document.getElementById("student-status").onchange=e=>{window._studentStatus=e.target.value;students()};
 document.getElementById("add-student")?.addEventListener("click",()=>studentModal());
}
async function studentModal(existing=null){
 if(!catalog) catalog=await api("/api/catalog");
 const s=existing||{};
 const opts=(arr,key,label)=>`<option value="">Select</option>`+(arr||[]).map(x=>`<option value="${x.id}" ${String(x.id)===String(s[key])?"selected":""}>${esc(x[label]||x.name||x.session_name)}</option>`).join("");
 const overlay=document.createElement("div");overlay.className="modal-backdrop";overlay.innerHTML=`<div class="modal"><div class="modal-head"><h2>${existing?"Edit":"Add"} Student</h2><button class="close">×</button></div>
 <form id="student-form" class="form-grid">
 <label>Registration number<input name="registration_number" value="${esc(s.registration_number)}" ${existing?"readonly":""} required></label>
 <label>First name<input name="first_name" value="${esc(s.first_name)}" required></label><label>Middle name<input name="middle_name" value="${esc(s.middle_name)}"></label><label>Last name<input name="last_name" value="${esc(s.last_name)}" required></label>
 <label>Gender<select name="gender"><option value="">Select</option><option ${s.gender==="Male"?"selected":""}>Male</option><option ${s.gender==="Female"?"selected":""}>Female</option></select></label>
 <label>Date of birth<input name="date_of_birth" type="date" value="${esc(s.date_of_birth)}"></label>
 <label>Level<select name="level">${[100,200,300,400,500,600].map(x=>`<option ${x==s.level?"selected":""}>${x}</option>`).join("")}</select></label>
 <label>Status<select name="student_status">${["Active","Inactive","Suspended","Graduated","Withdrawn"].map(x=>`<option ${x===s.student_status?"selected":""}>${x}</option>`).join("")}</select></label>
 <label>University<select name="university_id">${opts(catalog.universities,"university_id","name")}</select></label>
 <label>Faculty<select name="faculty_id">${opts(catalog.faculties,"faculty_id","name")}</select></label>
 <label>Department<select name="department_id">${opts(catalog.departments,"department_id","name")}</select></label>
 <label>Programme<select name="programme_id">${opts(catalog.programmes,"programme_id","name")}</select></label>
 <label>Academic session<select name="academic_session_id">${opts(catalog.sessions,"academic_session_id","session_name")}</select></label>
 <label class="full">Photo URL<input name="photo_url" value="${esc(s.photo_url)}"></label>
 <div class="full actions"><button type="submit" class="btn btn-primary">${existing?"Save changes":"Create student"}</button><button type="button" class="btn btn-secondary cancel">Cancel</button></div>
 <div id="modal-error" class="full error-box hidden"></div></form></div>`;
 document.body.appendChild(overlay);overlay.querySelector(".close").onclick=()=>overlay.remove();overlay.querySelector(".cancel").onclick=()=>overlay.remove();
 overlay.querySelector("form").onsubmit=async e=>{e.preventDefault();const fd=new FormData(e.target),data=Object.fromEntries(fd.entries());for(const k of ["university_id","faculty_id","department_id","programme_id","academic_session_id"])if(!data[k])data[k]=null;
 try{if(existing)await api("/api/students/"+existing.id,{method:"PUT",body:JSON.stringify(data)});else await api("/api/students",{method:"POST",body:JSON.stringify(data)});overlay.remove();toast("Student saved.");students()}catch(x){const er=overlay.querySelector("#modal-error");er.textContent=x.message;er.classList.remove("hidden")}}
}

async function profile(id){
 const [base,ov]=await Promise.all([api("/api/students/"+id),api("/api/students/"+id+"/overview")]);
 const s=base.student, contact=base.contact||{},adm=base.admission,acc=base.accommodation;
 shell(`<a class="auth-link" href="#/students">← Back to students</a><section class="profile-hero" style="margin-top:12px"><div class="avatar">${s.photo_url?`<img src="${esc(s.photo_url)}" alt="">`:esc((s.first_name||"?")[0]+(s.last_name||"")[0])}</div><div style="flex:1"><h1>${esc(fullName(s))}</h1><div style="color:#cbd5e1">${esc(s.registration_number)}</div><div style="color:#cbd5e1;margin-top:8px">${esc(s.programme_name||"—")} · ${s.level} Level · ${esc(s.session_name||"—")}</div></div><div>${badge(s.student_status)}</div></section>
 <div class="profile-meta"><div class="card"><span class="stat-label">Department</span><br><strong>${esc(s.department_name)}</strong></div><div class="card"><span class="stat-label">Faculty</span><br><strong>${esc(s.faculty_name)}</strong></div><div class="card"><span class="stat-label">Programme</span><br><strong>${esc(s.programme_name)}</strong></div><div class="card"><span class="stat-label">University</span><br><strong>${esc(s.university_name)}</strong></div></div>
 <div class="tabs">${["overview","personal","courses","results","attendance","fees","accommodation","admission","clearance","documents"].map((x,i)=>`<button class="tab ${i===0?"active":""}" data-tab="${x}">${x==="personal"?"Personal Info":x==="courses"?"Course Reg":x[0].toUpperCase()+x.slice(1)}</button>`).join("")}</div><div id="profile-content"></div>`);
 const renderTab=t=>{document.querySelectorAll(".tab").forEach(b=>b.classList.toggle("active",b.dataset.tab===t));document.getElementById("profile-content").innerHTML=profileTab(t,s,contact,adm,acc,ov);attachProfileActions(id,t)};
 document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>renderTab(b.dataset.tab));renderTab("overview");
}
function profileTab(t,s,c,a,acc,o){
 if(t==="overview"){
  const units=o.registrations.reduce((total,course)=>total+Number(course.credit_units||0),0);
  const feeStatus=o.balance<=0?"Paid":"Pending";
    return `<div class="grid grid-4 profile-kpis">${profileMetric("Current GPA",Number(o.gpa).toFixed(2),"accent-blue","↗")}${profileMetric("CGPA",Number(o.cgpa).toFixed(2),"accent-green","↗")}${profileMetric("Attendance",o.attendance_percentage+"%",o.attendance_percentage>=75?"accent-green":"accent-red","▣")}${profileMetric("Fee Status",feeStatus,"accent-green","₦")}</div>
  <div class="grid grid-2 profile-summaries"><section class="card summary-card"><h3>Academic Summary</h3><div class="summary-row"><span>Courses Registered</span><strong>${o.registrations.length}</strong></div><div class="summary-row"><span>Results Recorded</span><strong>${o.results.length}</strong></div><div class="summary-row"><span>Level</span><strong>${s.level} Level</strong></div><div class="summary-row"><span>Session</span><strong>${esc(s.session_name||"—")}</strong></div><div class="summary-row"><span>Programme</span><strong>${esc(s.programme_name||"—")}</strong></div></section><section class="card summary-card"><h3>Financial Summary</h3><div class="summary-row"><span>Total Due</span><strong>${money(o.total_due)}</strong></div><div class="summary-row"><span>Total Paid</span><strong>${money(o.total_paid)}</strong></div><div class="summary-row"><span>Balance</span><strong class="accent-green">${money(o.balance)}</strong></div><div class="summary-row"><span>Status</span><strong>${feeStatus}</strong></div><div class="summary-row"><span>Clearance</span><strong class="accent-red">${esc(a?.clearance_status||"—")}</strong></div></section></div>
  <section class="card registered-courses"><div class="section-heading"><h3>Registered Courses</h3><span class="muted">${o.registrations.length} course(s) registered · ${units} total credit units</span></div><div class="course-grid">${o.registrations.map(course=>`<article class="course-card"><strong>${esc(course.course_code)}</strong><span>${esc(course.course_title)}</span><small>${course.credit_units} units · ${esc(course.status||"Registered")}</small></article>`).join("")||'<div class="empty">No courses registered.</div>'}</div></section>`;
 }
 if(t==="personal")return `<section class="card"><div class="grid grid-2">${field("First Name",s.first_name)}${field("Middle Name",s.middle_name)}${field("Last Name",s.last_name)}${field("Gender",s.gender)}${field("Date of Birth",s.date_of_birth)}${field("Registration Number",s.registration_number)}${field("Email",c.email)}${field("Phone",c.phone)}${field("Residential Address",c.residential_address)}${field("State",c.state)}${field("LGA",c.lga)}${field("Emergency Contact",c.emergency_contact_name)}${field("Emergency Phone",c.emergency_contact_phone)}${field("Relationship",c.emergency_contact_relationship)}</div></section>`;
 if(t==="courses")return table(["Code","Title","Units","Level","Status"],o.registrations.map(r=>[r.course_code,r.course_title,r.credit_units,r.level,badge(r.status)]));
 if(t==="results")return table(["Course","Units","Score","Grade","GP","QP"],o.results.map(r=>{const [g,gp]=grade(r.score);return[r.course_code,r.credit_units,r.score,g,gp,gp*Number(r.credit_units)]}));
 if(t==="attendance")return table(["Course","Attended","Total","%"],o.attendance.map(r=>[r.course_code,r.classes_attended,r.total_classes,Math.round(r.classes_attended/r.total_classes*100)+"%"]));
 if(t==="fees")return table(["Fee Type","Due","Paid","Balance","Date","Status"],o.payments.map(p=>[p.fee_type,money(p.amount_due),money(p.amount_paid),money(Number(p.amount_due)-Number(p.amount_paid)),p.payment_date||"—",badge(p.payment_status)]));
 if(t==="accommodation")return `<section class="card"><h3>Accommodation</h3>${acc?`<div class="grid grid-2">${field("Hostel",acc.hostel_name)}${field("Block",acc.block)}${field("Room",acc.room_number)}${field("Bed",acc.bed_space)}${field("Allocation Date",acc.allocation_date)}${field("Status",acc.status)}</div>`:'<div class="empty">No accommodation allocated.</div>'}</section>`;
 if(t==="admission")return `<section class="card"><h3>Admission Record</h3>${a?`<div class="grid grid-2">${field("Admission Date",a.admission_date)}${field("Type",a.admission_type)}${field("Session",a.admission_session)}${field("Number",a.admission_number)}${field("Graduation Status",a.graduation_status)}${field("Clearance",a.clearance_status)}</div>`:'<div class="empty">No admission record.</div>'}</section>`;
 if(t==="clearance")return `<section class="card"><h3>Clearance</h3><p>${badge(a?.clearance_status||"—")}</p><p class="muted">Graduation status: ${esc(a?.graduation_status||"—")}</p></section>`;
 if(t==="documents")return `<section class="card"><h3>Documents</h3><p class="muted">The original app used browser print as a PDF workaround. This native version provides a print-ready profile and keeps PDF generation independent of the original platform.</p><button class="btn btn-primary no-print" onclick="window.print()">Print / Save as PDF</button></section>`;
}
function profileMetric(label,value,cls,icon){return `<section class="card profile-metric"><span class="profile-metric-icon ${cls}">${icon}</span><div><div class="stat-label">${label}</div><div class="profile-metric-value">${esc(value)}</div></div></section>`}
function field(l,v){return `<div><span class="stat-label">${esc(l)}</span><br><strong>${esc(v||"—")}</strong></div>`}
function grade(score){score=Number(score);return score>=70?["A",5]:score>=60?["B",4]:score>=50?["C",3]:score>=45?["D",2]:score>=40?["E",1]:["F",0]}
function table(headers,rows){return `<section class="card"><div class="table-wrap"><table class="table"><thead><tr>${headers.map(h=>`<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(x=>`<td>${typeof x==="string"&&x.startsWith("<span")?x:esc(x)}</td>`).join("")}</tr>`).join("")||`<tr><td colspan="${headers.length}" class="empty">No records.</td></tr>`}</tbody></table></div></section>`}
function attachProfileActions(id,t){}

async function analytics(){
 const d=await api("/api/analytics");
 shell(`<div class="page-head"><h1>Analytics</h1><p>Transparent academic-risk analysis using NumPy, Pandas and scikit-learn.</p></div>
 <div class="grid grid-4">${stat("Students",d.summary.count)}${stat("High risk",d.summary.high,"accent-red")}${stat("Medium risk",d.summary.medium)}${stat("Low risk",d.summary.low,"accent-green")}</div>
 <section class="card" style="margin-top:16px"><div class="table-wrap"><table class="table"><thead><tr><th>Student</th><th>Average score</th><th>Attendance</th><th>Fee balance ratio</th><th>Risk</th></tr></thead><tbody>${d.students.map(s=>`<tr><td>${esc(s.student_name)}<br><small class="muted">${esc(s.registration_number)}</small></td><td>${s.average_score}</td><td>${s.attendance_percentage}%</td><td>${Math.round(s.outstanding_fee_ratio*100)}%</td><td>${badge(s.risk_band)}</td></tr>`).join("")||'<tr><td colspan="5" class="empty">No student data yet.</td></tr>'}</tbody></table></div></section>`);
}
async function auditPage(){
 const rows=await api("/api/audit");shell(`<div class="page-head"><h1>Audit Logs</h1><p>Recent system actions.</p></div><section class="card"><div class="table-wrap"><table class="table"><thead><tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Details</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(new Date(r.created_at).toLocaleString())}</td><td>${esc(r.user_name)}</td><td>${badge(r.action)}</td><td>${esc(r.entity_type)} #${esc(r.entity_id)}</td><td>${esc(r.details)}</td></tr>`).join("")||'<tr><td colspan="5" class="empty">No audit records.</td></tr>'}</tbody></table></div></section>`)
}
async function coursesPage(){
 const d=await api("/api/catalog");shell(`<div class="page-head"><h1>Courses</h1><p>${d.courses.length} course(s)</p></div><section class="card"><div class="table-wrap"><table class="table"><thead><tr><th>Code</th><th>Title</th><th>Units</th><th>Level</th><th>Semester</th></tr></thead><tbody>${d.courses.map(c=>`<tr><td><strong>${esc(c.course_code)}</strong></td><td>${esc(c.course_title)}</td><td>${c.credit_units}</td><td>${c.level}</td><td>${esc(d.semesters.find(s=>s.id===c.semester_id)?.name||"—")}</td></tr>`).join("")||'<tr><td colspan="5" class="empty">No courses.</td></tr>'}</tbody></table></div></section>`)
}
function route(){
 const h=location.hash.replace(/^#\/?/,"");if(!me){if(h==="register")return renderRegister();if(h==="forgot")return renderForgot();return renderLogin()}
 const parts=h.split("/").filter(Boolean);if(parts[0]==="students"&&parts[1])return profile(parts[1]);if(parts[0]==="students")return students();if(parts[0]==="courses")return coursesPage();if(parts[0]==="analytics")return me.role==="admin"?analytics():students();if(parts[0]==="audit")return me.role==="admin"?auditPage():students();return dashboard()
}
window.addEventListener("hashchange",route);
(async()=>{await loadMe();route()})();

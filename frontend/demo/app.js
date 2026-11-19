/* WELLOOP 데모 화면 (빌드 도구 없이 동작). 화면 기준: Figma Mid-Fi A·B·C·D 묶음, API 명세서 01~05 구역.
   본 개발의 프론트 기술은 프론트 담당이 정합니다. 이 파일은 흐름 확인용이에요. */
const API = "/api/v1";
const $ = (s) => document.querySelector(s);
const view = $("#view");
const store = { get t() { try { return sessionStorage.getItem("t"); } catch { return this._t; } },
                set t(v) { this._t = v; try { v ? sessionStorage.setItem("t", v) : sessionStorage.removeItem("t"); } catch {} } };
let me = null;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const DISEASE = { HYPERTENSION: "고혈압", DIABETES: "당뇨", DYSLIPIDEMIA: "이상지질혈증" };
const LEVEL = { LOW: "낮음", WARNING: "주의", HIGH: "높음" };
const md = (iso) => iso.slice(5).replace("-", "/");

const inFlight = new Set();
async function api(path, method = "GET", body) {
  const key = method + " " + path;
  if (method !== "GET") { if (inFlight.has(key)) throw new Error("처리 중이에요. 잠시만 기다려 주세요."); inFlight.add(key); }
  try { return await send(path, method, body); } finally { inFlight.delete(key); }
}
async function send(path, method, body) {
  const res = await fetch(API + path, { method, headers: { "Content-Type": "application/json", ...(store.t ? { Authorization: "Bearer " + store.t } : {}) },
                                        body: body ? JSON.stringify(body) : undefined });
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (res.status === 401 && store.t) { store.t = null; me = null; location.hash = "#/login"; }
  if (!res.ok) throw Object.assign(new Error(data?.detail || "요청을 처리하지 못했어요"), { status: res.status, code: data?.code });
  return data;
}
const num = (id) => { const v = $("#" + id)?.value; return v === "" || v == null ? null : Number(v); };
const val = (id) => $("#" + id)?.value || null;
const chk = (id) => !!$("#" + id)?.checked;
const showErr = (e) => { const el = $("#err"); if (el) el.textContent = e.message; };
const go = (h) => { location.hash = h; };
function bars(points, key, fixedMax) {
  if (!points.length) return `<p class="sub">아직 기록이 없어요. 기록이 쌓이면 여기에 변화가 보여요.</p>`;
  const last = points.slice(-6), vals = last.map((p) => p[key]);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  // 점수(0~100)는 전체 눈금 기준, 체중·혈압 등은 기록 범위 기준으로 높이를 정해 작은 변화도 보이게 해요
  const h = (v) => fixedMax ? Math.max(4, (v / fixedMax) * 100) : hi === lo ? 55 : 30 + ((v - lo) / (hi - lo)) * 60;
  const note = last.length === 1 ? `<p class="sub">기록이 2번 이상 쌓이면 변화를 비교할 수 있어요.</p>` : "";
  return `<div class="bars">${last.map((p) => `<div><b>${p[key]}</b><i style="height:${h(p[key])}%"></i><span>${md(p.date)}</span></div>`).join("")}</div>${note}`;
}
const alertCard = (a) => `<div class="card alert ${a.level}"><h2>${esc(a.title)}</h2><p>${esc(a.message)}</p></div>`;
const alertsHtml = async () => (await api("/safety/alerts").catch(() => ({ items: [] }))).items.map(alertCard).join("");
const demoNote = (r) => r.is_demo_model ? `<div class="notice">데모용 모델이에요. 합성 데이터로 만든 것이라 <b>점수에 의미가 없습니다.</b> 화면 흐름 확인용입니다.</div>` : "";

const routes = {
  "": () => { view.innerHTML = `<p class="sub">YOUR EVERYDAY HEALTH</p><h1>내 건강을 이해하는<br>가장 다정한 시작</h1>
      <p>생활습관 문진으로 위험 신호를 살펴보고, 작은 실천을 이어 가요.</p>
      <div class="card"><h2>이렇게 진행돼요</h2><p>문진 → 위험 신호 확인 → 오늘의 미션 → 기록 → 변화 확인</p></div>
      <button class="btn" onclick="go('#/signup')">시작하기</button><button class="btn ghost" onclick="go('#/login')">이미 계정이 있어요 · 로그인</button>
      <p class="sub">의학적 진단·처방을 하지 않는 생활습관 관리 도구입니다.</p>`; },

  signup: () => { view.innerHTML = `<h1>건강한 일상,<br>함께 시작해요</h1>
      <label>이메일</label><input id="email" type="email" placeholder="example@email.com">
      <label>비밀번호 (8자 이상)</label><input id="pw" type="password">
      <label>이름</label><input id="name" type="text">
      <div class="row"><div><label>생년월일</label><input id="birth" type="date" value="1974-01-01"></div>
      <div><label>성별</label><select id="gender"><option value="FEMALE">여성</option><option value="MALE">남성</option></select></div></div>
      <label class="check"><input id="terms" type="checkbox">[필수] 서비스 이용약관 동의</label>
      <label class="check"><input id="privacy" type="checkbox">[필수] 개인정보 수집·이용 동의</label>
      <p id="err" class="error"></p><button class="btn" id="go">가입하기</button>`;
    $("#go").onclick = async () => { try {
      await api("/auth/signup", "POST", { email: val("email"), password: val("pw") || "", name: val("name") || "", birth_date: val("birth"),
                                         gender: val("gender"), terms_agreed: chk("terms"), privacy_agreed: chk("privacy") });
      const r = await api("/auth/login", "POST", { email: val("email"), password: val("pw") }); store.t = r.access_token; me = r.user; go("#/consent");
    } catch (e) { showErr(e); } }; },

  login: () => { view.innerHTML = `<h1>다시 만나 반가워요</h1><label>이메일</label><input id="email" type="email">
      <label>비밀번호</label><input id="pw" type="password"><p id="err" class="error"></p>
      <button class="btn" id="go">로그인</button><button class="btn text" onclick="go('#/signup')">이메일로 회원가입</button>`;
    $("#go").onclick = async () => { try {
      const r = await api("/auth/login", "POST", { email: val("email") || "", password: val("pw") || "" }); store.t = r.access_token; me = r.user;
      try { await api("/predictions/latest"); go("#/home"); } catch { go("#/consent"); }
    } catch (e) { showErr(e); } }; },

  consent: () => { view.innerHTML = `<h1>건강정보는<br>허락을 받고 사용할게요</h1>
      <div class="card"><h2>민감정보 수집·이용 안내</h2><p class="sub">수집 항목: 문진 응답, 체중·허리둘레·혈압 기록, 체크인</p>
      <p class="sub">이용 목적: 위험 신호 안내, 맞춤 생활습관 추천</p><p class="sub">보유 기간: 탈퇴 시 삭제</p></div>
      <label class="check"><input id="agree" type="checkbox">건강정보(민감정보) 수집·이용에 동의합니다</label>
      <p id="err" class="error"></p><button class="btn" id="go">동의하고 문진 시작</button>`;
    $("#go").onclick = async () => { if (!chk("agree")) return showErr(new Error("동의가 있어야 건강 평가를 할 수 있어요"));
      try { await api("/consents", "POST", { consent_type: "HEALTH_DATA", agreed: true }); Q.step = 1; Q.data = {}; Q.recheck = false; go("#/q"); } catch (e) { showErr(e); } }; },

  q: renderQuestionnaire,

  result: async () => { const r = await api("/predictions/latest");
    if (r.view === "MANAGEMENT") return go("#/manage");
    const al = await alertsHtml();
    view.innerHTML = `<p class="sub">예측 결과 · ${esc(r.prediction_date)}</p><h1>작은 습관부터<br>관리를 시작해 보세요</h1>${demoNote(r)}${al}
      <div class="card"><h2>대사 건강 위험 신호 점수</h2><div class="big-num">${r.overall.score} <span class="sub">/ 100</span></div>
        <p><span class="chip ${r.overall.grade}">${esc(r.overall.grade_label)}</span> <span class="sub">점수가 높을수록 위험 신호가 커요 · 입력 정보 ${r.input_count}개 반영</span></p></div>
      <div class="card"><h2>질환별 위험 신호</h2>${r.results.map((x) => `<div class="list-row"><span>${DISEASE[x.disease_type]}</span>
        ${x.is_managed ? `<span class="chip muted">관리 중</span>` : `<span class="chip ${x.risk_level}">${LEVEL[x.risk_level]}</span>`}</div>`).join("")}</div>
      <div class="card"><h2>결과에 영향을 준 정보</h2>${r.factors.length ? r.factors.map((f) => `<span class="chip ${f.is_missing ? "muted" : ""}">${esc(f.label)}</span>`).join("") : `<p class="sub">두드러진 요인이 없어요.</p>`}</div>
      ${r.managed_diseases.length ? `<div class="card"><h2>관리 중인 질환</h2><p>${r.managed_diseases.map((d) => DISEASE[d]).join(" · ")}</p>
        <button class="btn ghost" onclick="go('#/manage')">생활 관리 현황 보기</button></div>` : ""}
      <p class="sub">${esc(r.disclaimer)}</p>
      <button class="btn" onclick="go('#/home')">나에게 맞는 챌린지 보기</button>
      <button class="btn ghost" onclick="go('#/whatif')">만약 생활습관을 바꾼다면?</button>
      <button class="btn text" onclick="go('#/checkup')">검진 수치 입력하기 (선택)</button>
      <button class="btn text" onclick="go('#/history')">예측 이력 보기</button>`; },

  checkup: async () => { const last = await api("/checkups/latest").catch(() => null);
    const f = (id, label) => `<div><label>${label}</label><input id="${id}" type="number" step="0.1"></div>`;
    view.innerHTML = `<p class="sub">선택 입력</p><h1>검진 수치가 있다면<br>더 입력해 주세요</h1>
      <div class="card"><label>검진 받은 날</label><input id="checkup_date" type="date">
        <div class="row">${f("pressure_systolic", "수축기 혈압")}${f("pressure_diastolic", "이완기 혈압")}</div>
        <div class="row">${f("fasting_glucose", "공복혈당")}${f("hba1c", "당화혈색소 (%)")}</div>
        <div class="row">${f("total_cholesterol", "총콜레스테롤")}${f("ldl_cholesterol", "LDL")}</div>
        <div class="row">${f("hdl_cholesterol", "HDL")}${f("triglycerides", "중성지방")}</div>
        <p class="sub">있는 수치만 입력하세요. 검진 수치는 기준 초과 안내에만 쓰고 위험 신호 예측에는 넣지 않아요.</p>
        <p id="err" class="error"></p><button class="btn" id="go">저장하고 확인하기</button></div><div id="out">${last ? checkupCard(last) : ""}</div>
      <button class="btn text" onclick="go('#/result')">결과로 돌아가기</button>`;
    $("#go").onclick = async () => { try { const body = { checkup_date: val("checkup_date") };
      ["pressure_systolic", "pressure_diastolic", "fasting_glucose", "hba1c", "total_cholesterol", "ldl_cholesterol", "hdl_cholesterol", "triglycerides"].forEach((k) => body[k] = num(k));
      $("#out").innerHTML = checkupCard(await api("/checkups", "POST", body)); $("#err").textContent = "";
    } catch (e) { showErr(e); } }; },

  manage: async () => { let s; try { s = await api("/management/summary"); } catch { return go("#/result"); }
    view.innerHTML = `<p class="sub">관리 평가 · 진단 이력이 있는 사용자</p><h1>치료는 의료진과,<br>생활 관리는 꾸준하게</h1>
      <div class="card"><h2>이번 주 관리 현황</h2><div class="big-num">실천율 ${Math.round(s.completion.rate * 100)}%</div>
        <p class="sub">계획 ${s.completion.planned_count}회 중 ${s.completion.completed_count}회 완료</p></div>
      <div class="card"><h2>관리 중인 항목</h2>${s.managed_items.map((m) => `<p><b>${esc(m.label)}</b></p>
        ${m.latest_log ? `<p class="sub">최근 기록: 혈압 ${m.latest_log.pressure_systolic} / ${m.latest_log.pressure_diastolic} mmHg</p>` : ""}
        <p class="sub">복약 체크: 이번 주 ${m.medication_check.checked_days} / ${m.medication_check.total_days}일</p>`).join("")}</div>
      <div class="card"><h2>이번 주 제안</h2>${s.suggestions.map((x) => `<p>${esc(x)}</p>`).join("")}</div>
      <p class="sub">${esc(s.disclaimer)}</p><button class="btn" onclick="go('#/home')">오늘의 관리 계획 보기</button>
      <button class="btn text" onclick="go('#/record')">건강 수치 기록</button>`; },

  home: async () => { const [coach, today, latest] = await Promise.all([api("/coach/today"), api("/challenges/today"), api("/predictions/latest").catch(() => null)]);
    if (!latest) return go("#/consent");
    const al = await alertsHtml();
    view.innerHTML = `<h1>${esc(me.name)}님, 안녕하세요</h1>${al}
      <div class="card"><h2>오늘의 코치</h2><p>${esc(coach.content)}</p><p class="sub">${esc(coach.disclaimer)}</p></div>
      <div class="card"><h2>오늘의 미션 <span class="chip">${today.missions.filter((m) => m.completed).length} / ${today.missions.length}</span>
        ${today.streak_days ? `<span class="chip">${today.streak_days}일 연속</span>` : ""}</h2>
        ${today.missions.map((m) => `<div class="mission"><span>${m.completed ? "✅" : "⬜"}</span><div><b>${esc(m.title)}</b><p class="sub">${esc(m.category_label)}</p></div></div>`).join("")}
        <button class="btn" onclick="go('#/challenge')">체크인하기</button></div>
      <div class="card"><h2>나의 위험 신호</h2>${latest.overall ? `<p><b>${latest.overall.score}점</b> <span class="chip ${latest.overall.grade}">${esc(latest.overall.grade_label)}</span></p>` : `<p>관리 중인 질환을 꾸준히 돌보고 있어요.</p>`}
        <button class="btn ghost" onclick="go('#/result')">결과 다시 보기</button></div>`; },

  challenge: async () => { const t = await api("/challenges/today");
    view.innerHTML = `<h1>오늘의 실천을<br>체크해 주세요</h1>
      <div class="card"><h2>추천 생활습관</h2>${t.recommended_categories.map((c) => `<p><span class="chip">${esc(c.label)}</span> <span class="sub">${esc(c.reason)}</span></p>`).join("")}</div>
      <div class="card"><h2>오늘의 미션</h2>${t.missions.map((m) => `<label class="mission"><input type="checkbox" class="m" value="${m.daily_challenge_id}" ${m.completed ? "checked" : ""}>
        <div><b>${esc(m.title)}</b><p class="sub">${esc(m.description)}</p></div></label>`).join("")}</div>
      <div class="card"><h2>오늘의 컨디션 · 선택</h2><div class="row"><div><label>어젯밤 수면 (시간)</label><input id="sleep" type="number" step="0.5" min="0" max="24"></div>
        <div><label>기분</label><select id="mood"><option value="">선택</option><option value="1">나쁨</option><option value="2">조금 나쁨</option><option value="3">보통</option><option value="4">좋음</option><option value="5">아주 좋음</option></select></div></div>
        <label class="check"><input id="med" type="checkbox">오늘 약을 챙겼어요 (복용 중인 경우)</label>
        <label>오늘의 한 줄 메모 · 선택</label><input id="memo" type="text" maxlength="200" placeholder="나만 보는 메모예요"></div><div id="safety"></div>
      <p id="err" class="error"></p><button class="btn" id="go">체크인 저장</button><p class="sub">못 한 날이 있어도 괜찮아요. 다시 시작하면 됩니다.</p>`;
    $("#go").onclick = async () => { try {
      const r = await api("/checkins", "POST", { completed_daily_challenge_ids: [...document.querySelectorAll(".m:checked")].map((x) => Number(x.value)),
                                               sleep_hours: num("sleep"), mood: num("mood"), medication_taken: chk("med") ? true : null, memo: val("memo") });
      $("#safety").innerHTML = r.safety_alert ? alertCard(r.safety_alert) : "";
      $("#err").style.color = "var(--green)"; $("#err").textContent = `저장했어요. 오늘 실천율 ${Math.round(r.completion_rate * 100)}% · ${r.streak_days}일 연속`;
    } catch (e) { showErr(e); } }; },

  record: async () => { const logs = await api("/health-logs?period=3m&size=10");
    view.innerHTML = `<h1>오늘의 수치를<br>기록해 주세요</h1>
      <div class="card"><div class="row"><div><label>체중 (kg)</label><input id="w" type="number" step="0.1"></div><div><label>허리둘레 (cm)</label><input id="waist" type="number" step="0.1"></div></div>
        <div class="row"><div><label>수축기 혈압</label><input id="sys" type="number"></div><div><label>이완기 혈압</label><input id="dia" type="number"></div></div>
        <p class="sub">있는 수치만 입력해도 돼요. 값의 임상적 해석은 의료진에게 문의하세요.</p>
        <p id="err" class="error"></p><button class="btn" id="go">기록 저장</button></div>
      <div class="card"><h2>최근 기록</h2>${logs.items.length ? logs.items.map((l) => `<div class="list-row"><span>${esc(l.log_date)}<br><span class="sub">${[l.weight && l.weight + "kg", l.waist_size && "허리 " + l.waist_size + "cm", l.pressure_systolic && l.pressure_systolic + "/" + l.pressure_diastolic + "mmHg"].filter(Boolean).join(" · ")}</span></span>
        <button class="link" data-del="${l.health_log_id}">삭제</button></div>`).join("") : `<p class="sub">아직 기록이 없어요.</p>`}</div>`;
    $("#go").onclick = async () => { try {
      const r = await api("/health-logs", "POST", { weight: num("w"), waist_size: num("waist"), pressure_systolic: num("sys"), pressure_diastolic: num("dia") });
      if (r.recalculated) { alertMsg("기록을 반영해 위험 신호를 다시 계산했어요."); } routes.record();
    } catch (e) { showErr(e); } };
    document.querySelectorAll("[data-del]").forEach((b) => b.onclick = async () => { await api("/health-logs/" + b.dataset.del, "DELETE"); routes.record(); }); },

  health: async (period = "1m") => { const d = await api("/dashboard?period=" + period);
    view.innerHTML = `<h1>기록의 변화를<br>한눈에 살펴보세요</h1>
      <select id="period"><option value="1m">최근 1개월</option><option value="3m">3개월</option><option value="all">전체</option></select>
      <div class="card" style="margin-top:14px"><h2>위험 신호 점수 추이 · 0~100점</h2><p class="sub">점수가 높을수록 위험 신호가 커요</p>${bars(d.risk_score_trend.points, "score", 100)}</div>
      ${d.health_trends.map((t) => `<div class="card"><h2>${esc(t.label)} 추이 · ${esc(t.unit)}</h2>${bars(t.points, "value")}</div>`).join("")}
      <p class="sub">${esc(d.notice)}</p><button class="btn" onclick="go('#/record')">오늘의 건강 수치 기록</button>
      <button class="btn text" onclick="go('#/history')">예측 이력 보기</button>`;
    $("#period").value = period; $("#period").onchange = (e) => routes.health(e.target.value); },

  history: async () => { const h = await api("/predictions?period=all");
    view.innerHTML = `<h1>예측 이력</h1><p class="sub">전체 ${h.total}회</p>
      ${h.items.map((i, n) => `<div class="card"><b>${esc(i.prediction_date)}　${i.overall_score ?? "-"}점</b>
        <p class="sub">${n === 0 ? "최근 결과 · " : ""}${esc(i.reason_label)}</p></div>`).join("") || `<p class="sub">아직 이력이 없어요.</p>`}
      <p class="sub">입력 항목이나 모델이 바뀌면 직접 비교에 유의하세요.</p><button class="btn" onclick="go('#/health')">기록 추이·위험도 변화 보기</button>`; },

  whatif: async () => { const r = await api("/predictions/latest"); const base = (await api("/predictions/simulate", "POST", { changes: { activity_days_per_week: 0 } }).catch(() => null));
    view.innerHTML = `<h1>만약 생활습관을<br>바꾼다면?</h1><p class="sub">기준 결과: ${esc(r.prediction_date)} · ${r.overall ? r.overall.score + "점" : "-"}</p>
      <div class="card"><h2>비교할 가정 설정</h2><label>주간 운동 횟수 (일)</label><input id="act" type="number" min="0" max="7" value="4">
        <label>하루 평균 수면 (시간)</label><input id="sl" type="number" min="0" max="24" step="0.5" value="7">
        <label>허리둘레 (cm) · 선택</label><input id="wa" type="number" step="0.5">
        <p class="sub">변경한 가정은 실제 건강 기록에 저장되지 않아요.</p></div>
      <p id="err" class="error"></p><button class="btn" id="go">가정값으로 비교하기</button><div id="out"></div>`;
    if (!base) $("#err").textContent = "예측 대상 질환이 없어 비교할 수 없어요.";
    $("#go").onclick = async () => { try { const ch = { activity_days_per_week: num("act"), sleep_hours: num("sl") }; if (num("wa") != null) ch.waist_size = num("wa");
      Object.keys(ch).forEach((k) => ch[k] == null && delete ch[k]);
      const s = await api("/predictions/simulate", "POST", { changes: ch });
      $("#out").innerHTML = `<div class="card"><h2>가상 비교 미리보기</h2><div class="big-num">${s.overall.current} → ${s.overall.simulated}</div>
        ${s.changes.map((c) => `<p class="sub">${esc(c.label)}: 현재 ${c.current ?? "-"} → 가정 ${c.assumed}${esc(c.unit || "")}</p>`).join("")}<p class="sub">${esc(s.notice)}</p></div>`;
    } catch (e) { showErr(e); } }; },

  my: () => { view.innerHTML = `<h1>내 정보·설정</h1><div class="card"><div class="list-row"><span>이름</span><b>${esc(me.name)}</b></div>
      <div class="list-row"><span>이메일</span><span>${esc(me.email)}</span></div><div class="list-row"><span>생년월일</span><span>${esc(me.birth_date)}</span></div></div>
      <label class="check"><input id="big" type="checkbox" ${document.body.classList.contains("big") ? "checked" : ""}>큰 글씨 모드</label>
      <button class="btn ghost" id="re">재문진하기</button><button class="btn text" id="out">로그아웃</button>`;
    $("#big").onchange = (e) => document.body.classList.toggle("big", e.target.checked);
    $("#re").onclick = () => { Q.step = 1; Q.recheck = true; go("#/q"); };
    $("#out").onclick = () => { store.t = null; me = null; Q.data = {}; Q.step = 1; Q.recheck = false; go("#/"); }; },
};

function checkupCard(c) { return `<div class="card"><h2>검진 수치 확인</h2>${c.exceeded.length ? c.exceeded.map((e) => `<div class="list-row"><span>${esc(e.label)}</span><span class="chip WARNING">${e.value} · 기준 ${esc(e.reference)}</span></div>`).join("") + `<p>${esc(c.guide)}</p>` : `<p>기준을 넘는 수치가 없어요.</p>`}
  ${c.is_stale ? `<p class="sub">${esc(c.stale_guide)}</p>` : ""}<p class="sub">의학적 진단이 아니며 정확한 판단은 의료진과 상담하세요.</p></div>`; }
function alertMsg(text) { const n = document.createElement("div"); n.className = "notice"; n.textContent = text; view.prepend(n); }

/* ----- 문진 4단계 (B01~B04) ----- */
const Q = { step: 1, data: {}, recheck: false };
const yn3 = (id, label) => `<label>${label}</label><select id="${id}"><option value="UNKNOWN">잘 모르겠어요</option><option value="NO">없음</option><option value="YES">있음</option></select>`;
const STEPS = {
  1: () => `<h1>먼저, 기본 정보를<br>알려 주세요</h1><div class="row"><div><label>키 (cm)</label><input id="height" type="number" step="0.1"></div><div><label>몸무게 (kg)</label><input id="weight" type="number" step="0.1"></div></div>
      <label>허리둘레 (cm)</label><input id="waist_size" type="number" step="0.1"><p class="sub">배꼽 높이에서 숨을 내쉰 뒤 잰 값이에요.</p>
      <h2 style="margin-top:18px">진단받았거나 약을 먹고 있는 질환</h2>
      <label class="check"><input id="htn_diagnosed" type="checkbox">고혈압</label><label class="check"><input id="dm_diagnosed" type="checkbox">당뇨</label>
      <label class="check"><input id="dl_diagnosed" type="checkbox">이상지질혈증</label><p class="sub">해당 질환은 예측 대신 생활 관리 현황을 보여 드려요.</p>`,
  2: () => `<h1>평소 생활 습관을<br>함께 살펴볼게요</h1><label>흡연</label><select id="smoking_status"><option value="NEVER">비흡연</option><option value="FORMER">과거 흡연</option><option value="CURRENT">현재 흡연</option></select>
      <div class="row"><div><label>음주 (주 며칠)</label><input id="drinking_days_per_week" type="number" min="0" max="7"></div><div><label>1회 음주량 (잔)</label><input id="drinks_per_occasion" type="number" min="0" max="30"></div></div>
      <div class="row"><div><label>운동 (주 며칠)</label><input id="activity_days_per_week" type="number" min="0" max="7"></div><div><label>하루 운동 (분)</label><input id="activity_minutes_per_day" type="number" min="0" max="600"></div></div>
      <div class="row"><div><label>채소 (주 몇 번)</label><input id="veg_freq" type="number" min="0" max="21"></div><div><label>아침식사 (주 며칠)</label><input id="breakfast_freq" type="number" min="0" max="7"></div></div>
      <label>평균 수면 (시간)</label><input id="sleep_hours" type="number" min="0" max="24" step="0.5"><label class="check"><input id="sleep_trouble" type="checkbox">잠들기 어렵거나 자주 깨요</label>
      <p class="sub">정확하지 않아도 괜찮아요. 가장 가까운 답을 적어 주세요.</p>`,
  3: () => `<h1>건강 위험 요인을<br>확인할게요</h1>${yn3("family_htn", "가족 중 고혈압")}${yn3("family_dm", "가족 중 당뇨")}${yn3("family_dl", "가족 중 이상지질혈증")}
      <label class="check"><input id="exercise_restricted" type="checkbox">의사에게 "운동을 조심하라"는 말을 들었어요</label>
      <p class="sub">예: 심장·관절 문제로 무리한 운동을 피하라고 들은 경우예요. 체크하면 강도 높은 미션은 빼고 추천해요.</p>`,
  4: () => `<h1>마지막으로,<br>맞춤 설정이에요</h1>${me?.gender === "FEMALE" ? `<label>폐경 상태</label><select id="menopause_status"><option value="">선택 안 함</option><option value="PRE">폐경 전</option><option value="PERI">진행 중</option><option value="POST">폐경 후</option></select>` : ""}
      <label>가장 바꾸고 싶은 생활습관</label><input id="improvement_goal" type="text" maxlength="100" placeholder="예: 저녁 식사 후 걷기">
      <div class="card" style="margin-top:16px"><h2>다음 단계 안내</h2><p class="sub">입력한 내용으로 위험 신호를 살펴봅니다. 의학적 진단이 아니에요.</p></div>`,
};
function collect() { view.querySelectorAll("input,select").forEach((el) => {
  Q.data[el.id] = el.type === "checkbox" ? el.checked : el.value === "" ? null : el.type === "number" ? Number(el.value) : el.value; }); }
function renderQuestionnaire() {
  view.innerHTML = `<p class="sub">건강 문진 ${Q.step} / 4</p><div class="steps">${[1, 2, 3, 4].map((i) => `<i class="${i <= Q.step ? "on" : ""}"></i>`).join("")}</div>${STEPS[Q.step]()}
    <p id="err" class="error"></p><button class="btn" id="next">${Q.step < 4 ? "다음" : "결과 확인하기"}</button>${Q.step > 1 ? `<button class="btn text" id="prev">이전</button>` : ""}`;
  view.querySelectorAll("input,select").forEach((el) => { const v = Q.data[el.id]; if (v == null) return; el.type === "checkbox" ? (el.checked = v) : (el.value = v); });
  if ($("#prev")) $("#prev").onclick = () => { collect(); Q.step--; renderQuestionnaire(); };
  $("#next").onclick = async () => { collect();
    if (Q.step === 1 && !(Q.data.height && Q.data.weight && Q.data.waist_size)) return showErr(new Error("키·몸무게·허리둘레를 입력해 주세요"));
    if (Q.step < 4) { Q.step++; return renderQuestionnaire(); }
    try { const d = Q.data;
      const body = { ...d, htn_medication: d.htn_diagnosed, dm_medication: d.dm_diagnosed, dl_medication: d.dl_diagnosed, is_completed: true, is_recheck: Q.recheck };
      const q = await api("/questionnaires", "POST", body); await api("/predictions", "POST", { questionnaire_id: q.questionnaire_id }); go("#/result");
    } catch (e) { showErr(e); } };
}

const PUBLIC = ["", "signup", "login"], TABBED = ["home", "challenge", "record", "health", "my"];
async function render() {
  const name = location.hash.replace(/^#\/?/, "");
  if (!PUBLIC.includes(name)) { if (!store.t) return go("#/login"); if (!me) { try { me = await api("/users/me"); } catch { return; } } }
  $("#tabs").hidden = !TABBED.includes(name);
  document.querySelectorAll("#tabs a").forEach((a) => a.classList.toggle("on", a.dataset.tab === name));
  try { await (routes[name] || routes[""])(); } catch (e) { view.innerHTML = `<div class="card"><h2>화면을 불러오지 못했어요</h2><p class="sub">${esc(e.message)}</p></div>`; }
  window.scrollTo(0, 0);
}
$("#logo").onclick = (e) => { e.preventDefault(); go(store.t ? "#/home" : "#/"); if (location.hash === (store.t ? "#/home" : "#/")) render(); };
window.addEventListener("hashchange", render); window.go = go; render();

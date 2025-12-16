/* home.js */

// --- 화면 전환 ---
function toggleForms() {
  const loginBox = document.getElementById("login-box");
  const signupBox = document.getElementById("signup-box");

  if (loginBox.classList.contains("hidden")) {
    loginBox.classList.remove("hidden");
    signupBox.classList.add("hidden");
  } else {
    loginBox.classList.add("hidden");
    signupBox.classList.remove("hidden");
    // 폼 초기화
    document.getElementById("signupForm").reset();
    resetIdCheck();
    document.getElementById("pw-msg").innerText = "";
  }
}

// --- 아이디 중복 확인 ---
let isIdChecked = false;

function checkId() {
  const username = document.getElementById("su_username").value;
  const msgBox = document.getElementById("id-msg");
  const btn = document.getElementById("btn-id-check");

  if (!username) {
    alert("아이디를 입력해주세요.");
    return;
  }

  fetch("/auth/check-id", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: username }),
  }).then((res) => {
    if (res.status === 200) {
      msgBox.innerText = "사용 가능한 아이디입니다.";
      msgBox.className = "msg-text msg-success";
      isIdChecked = true;
      btn.innerText = "확인완료";
      btn.classList.add("checked");
    } else {
      msgBox.innerText = "이미 사용 중인 아이디입니다.";
      msgBox.className = "msg-text msg-error";
      isIdChecked = false;
    }
  });
}

function resetIdCheck() {
  isIdChecked = false;
  const msgBox = document.getElementById("id-msg");
  const btn = document.getElementById("btn-id-check");
  msgBox.innerText = "";
  btn.innerText = "중복확인";
  btn.classList.remove("checked");
}

// --- 비밀번호 일치 확인 ---
function checkPwMatch() {
  const pw = document.getElementById("su_password").value;
  const pwConfirm = document.getElementById("su_password_confirm").value;
  const msgBox = document.getElementById("pw-msg");

  if (pw && pwConfirm && pw !== pwConfirm) {
    msgBox.innerText = "비밀번호가 일치하지 않습니다.";
  } else {
    msgBox.innerText = "";
  }
}

// --- 전화번호 자동 하이픈 ---
function autoHyphen(target) {
  target.value = target.value
    .replace(/[^0-9]/g, "")
    .replace(/^(\d{0,3})(\d{0,4})(\d{0,4})$/g, "$1-$2-$3")
    .replace(/(\-{1,2})$/g, "");
}

// --- 최종 가입 요청 ---
function submitSignup() {
  if (!isIdChecked) {
    alert("아이디 중복 확인을 해주세요.");
    document.getElementById("su_username").focus();
    return;
  }

  const username = document.getElementById("su_username").value;
  const password = document.getElementById("su_password").value;
  const pwConfirm = document.getElementById("su_password_confirm").value;
  const birthdate = document.getElementById("su_birthdate").value;
  const gender = document.getElementById("su_gender").value;
  const phone = document.getElementById("su_phone").value;
  const email = document.getElementById("su_email").value;

  if (!username || !password || !birthdate || !gender || !phone || !email) {
    alert("모든 정보를 입력해주세요.");
    return;
  }
  if (password !== pwConfirm) {
    alert("비밀번호가 일치하지 않습니다.");
    return;
  }

  const data = {
    username: username,
    password: password,
    birthdate: birthdate,
    gender: gender,
    phone_number: phone,
    email: email,
  };

  fetch("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
    .then((response) =>
      response.json().then((body) => ({ status: response.status, body: body }))
    )
    .then((result) => {
      if (result.status === 200) {
        alert("가입을 축하합니다! 로그인해주세요.");
        toggleForms();
      } else {
        alert(result.body.detail || "가입 실패");
      }
    })
    .catch((err) => console.error(err));
}

// --- 로그인 요청 ---
function submitLoginForm(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const data = Object.fromEntries(formData.entries());

  fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
    .then((res) =>
      res.json().then((body) => ({ status: res.status, body: body }))
    )
    .then((result) => {
      if (result.status === 200) {
        window.location.href = "/";
      } else {
        alert(result.body.detail || "로그인 실패");
      }
    });
}

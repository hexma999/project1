/* chatbot.js */
document.addEventListener("DOMContentLoaded", () => {
  // [핵심 수정] 챗봇 요소들을 찾아서 변수에 할당
  const fab = document.getElementById("chatbotFab");
  const popup = document.getElementById("chatbotPopup");

  // 1. 챗봇이 다른 요소(예: sticky 헤더)의 CSS 영향을 받지 않도록
  //    HTML 구조상 body의 직속 자식으로 강제 이동시킵니다.
  if (fab && popup) {
    document.body.appendChild(fab);
    document.body.appendChild(popup);
  }

  const closeBtn = document.getElementById("chatbotClose");
  const input = document.getElementById("chatInput");
  const send = document.getElementById("chatSend");
  const body = document.getElementById("chatbotBody");

  // 요소가 로드되지 않았을 경우를 대비해 null 체크
  if (!fab || !popup || !closeBtn || !input || !send || !body) {
    console.error("Chatbot elements not found");
    return;
  }

  function togglePopup(forceOpen) {
    const open = forceOpen ?? !popup.classList.contains("open");
    popup.classList.toggle("open", open);
    popup.setAttribute("aria-hidden", String(!open));
    if (open) input.focus();
  }

  fab.addEventListener("click", () => togglePopup());
  closeBtn.addEventListener("click", () => togglePopup(false));

  // ESC로 닫기
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && popup.classList.contains("open"))
      togglePopup(false);
  });

  // 바깥 클릭으로 닫기 (팝업 영역 외)
  document.addEventListener("click", (e) => {
    if (!popup.classList.contains("open")) return;
    const clickInsidePopup = popup.contains(e.target) || fab.contains(e.target);
    if (!clickInsidePopup) togglePopup(false);
  });

  // 메시지 전송
  send.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;

    // 사용자 메시지 추가
    const userMsg = document.createElement("div");
    userMsg.className = "msg user";
    userMsg.textContent = msg;
    body.appendChild(userMsg);
    input.value = "";
    body.scrollTop = body.scrollHeight;

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();

      // 봇 응답 추가
      const botMsg = document.createElement("div");
      botMsg.className = "msg bot";
      botMsg.textContent = data.reply;
      body.appendChild(botMsg);
      body.scrollTop = body.scrollHeight;
    } catch (error) {
      console.error("Chat Error:", error);
      const errorMsg = document.createElement("div");
      errorMsg.className = "msg bot";
      errorMsg.textContent = "오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
      body.appendChild(errorMsg);
    }
  }
});

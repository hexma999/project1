/* main.js */

// 모바일 감지
function isMobile() {
  return window.matchMedia("(max-width: 680px)").matches;
}

// 말풍선 목록 토글
function toggleBubbleList(category, btn) {
  const el = document.getElementById(`bubbleList-${category}`);
  if (!el) return;

  const opening = el.style.display !== "block";
  el.style.display = opening ? "block" : "none";
  if (btn) btn.textContent = opening ? "감추기" : "모두보기";
  setupExpiryBubbles();
}

// 말풍선 닫기
function closeBubble(category) {
  const bubble = document.getElementById(
    `expiryBubble${category[0].toUpperCase() + category.slice(1)}`
  );
  if (!bubble) return;

  bubble.classList.add("is-closed");
  bubble.style.display = "none";
  setupExpiryBubbles();
}

// 모든 말풍선 위치 계산 (PC)
function positionAllBubbles() {
  const configs = [
    { bubbleId: "expiryBubbleDog", anchorId: "navDog" },
    { bubbleId: "expiryBubbleCat", anchorId: "navCat" },
    { bubbleId: "expiryBubbleBird", anchorId: "navBird" },
  ];

  const items = configs
    .map((c) => {
      const bubble = document.getElementById(c.bubbleId);
      const anchor = document.getElementById(c.anchorId);
      return { ...c, bubble, anchor };
    })
    .filter((x) => x.bubble && x.anchor && x.bubble.style.display !== "none");

  if (items.length === 0) return;

  const bottoms = items.map((x) => x.anchor.getBoundingClientRect().bottom);
  const top = Math.max(...bottoms) + 8;

  items.forEach((x) => {
    x.bubble.style.display = "block";
    x.bubble.style.position = "fixed";
    x.bubble.style.top = `${top}px`;
  });

  const vw = window.innerWidth;
  const margin = 10;

  const measured = items
    .map((x) => {
      const a = x.anchor.getBoundingClientRect();
      const w = x.bubble.getBoundingClientRect().width || 280;
      const center = a.left + a.width / 2;
      return { ...x, w, center, left: 0 };
    })
    .sort((a, b) => a.center - b.center);

  const avgW = measured.reduce((s, i) => s + i.w, 0) / measured.length;
  const gap = Math.round(Math.max(10, Math.min(24, avgW * 0.05)));

  measured.forEach((it) => {
    it.left = Math.round(it.center - it.w / 2);
    it.left = Math.max(margin, Math.min(it.left, vw - margin - it.w));
  });

  for (let i = 1; i < measured.length; i++) {
    const prev = measured[i - 1];
    const cur = measured[i];
    const minLeft = prev.left + prev.w + gap;
    if (cur.left < minLeft) cur.left = minLeft;
  }

  const last = measured[measured.length - 1];
  const overflow = last.left + last.w - (vw - margin);
  if (overflow > 0) {
    measured.forEach((it) => (it.left -= overflow));
  }

  const groupLeft = measured[0].left;
  const groupRight =
    measured[measured.length - 1].left + measured[measured.length - 1].w;
  const groupW = groupRight - groupLeft;
  const targetLeft = Math.round((vw - groupW) / 2);

  let delta = targetLeft - groupLeft;
  const minDelta = margin - groupLeft;
  const maxDelta = vw - margin - groupRight;
  delta = Math.max(minDelta, Math.min(maxDelta, delta));
  measured.forEach((it) => (it.left += delta));

  measured.forEach((it) => {
    it.bubble.style.left = `${it.left}px`;
  });
}

function shouldUseRail(visibleCount) {
  const total = visibleCount * 240 + Math.max(0, visibleCount - 1) * 12 + 24;
  return isMobile() || total > window.innerWidth;
}

function updateStickyTopHeight() {
  const sticky = document.getElementById("stickyTop");
  if (!sticky) return;
  const h = sticky.offsetHeight || 0;
  document.documentElement.style.setProperty("--stickyTopH", `${h}px`);
}

function setupExpiryBubbles() {
  updateStickyTopHeight();
  const mount = document.getElementById("expiryBubbleMount");
  const rail = document.getElementById("expiryBubbleRail");
  const bubbles = [
    document.getElementById("expiryBubbleDog"),
    document.getElementById("expiryBubbleCat"),
    document.getElementById("expiryBubbleBird"),
  ].filter(Boolean);

  const openBubbles = bubbles.filter((b) => !b.classList.contains("is-closed"));
  const useRail = shouldUseRail(openBubbles.length);

  if (useRail) {
    if (mount) mount.style.display = "none";
    if (rail) rail.style.display = "flex";
    openBubbles.forEach((b) => {
      rail.appendChild(b);
      b.classList.add("in-rail");
      b.style.position = "static";
      b.style.left = "";
      b.style.top = "";
      b.style.display = "block";
    });
  } else {
    if (mount) mount.style.display = "block";
    if (rail) rail.style.display = "none";
    bubbles.forEach((b) => {
      mount.appendChild(b);
      b.classList.remove("in-rail");
      if (b.classList.contains("is-closed")) {
        b.style.display = "none";
      } else {
        b.style.display = "block";
        b.style.position = "fixed";
      }
    });
    positionAllBubbles();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  updateStickyTopHeight();
  setTimeout(updateStickyTopHeight, 50);
  setTimeout(() => {
    updateStickyTopHeight();
    positionAllBubbles();
  }, 200);
});

window.addEventListener("load", () => {
  updateStickyTopHeight();
  setupExpiryBubbles();
});
window.addEventListener("resize", () => {
  updateStickyTopHeight();
  setupExpiryBubbles();
});

$(document).ready(function () {
  // 992px 이상(PC 화면)에서만 동작
  // 드롭다운 메뉴 영역에서 마우스가 떠나면(mouseleave), 강제로 닫힘 처리
  $(".navbar-nav .dropdown").on("mouseleave", function () {
    if (window.innerWidth >= 992) {
      $(this).removeClass("show"); // 메뉴 항목의 show 클래스 제거
      $(this).find(".dropdown-menu").removeClass("show"); // 하위 메뉴의 show 클래스 제거
    }
  });
});

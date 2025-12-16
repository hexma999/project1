/* product_detail.js */

// 1. 맨 위로 가기
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// 2. 모달 열기/닫기
function openReviewModal() {
  document.getElementById("reviewModal").style.display = "flex";
}
function closeReviewModal() {
  document.getElementById("reviewModal").style.display = "none";
}

// 3. 로그아웃 (공통함수지만 페이지 내에 정의되어 있었으므로 유지)
function logout() {
  fetch("/auth/logout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
    .then((response) => response.json())
    .then((data) => {
      window.location.reload();
    })
    .catch((error) => console.error("Error:", error));
}

// 4. 리뷰 전송
function submitReview(productId) {
  let content = document.getElementById("reviewContent").value;
  if (!content) {
    alert("내용을 입력해주세요.");
    return;
  }

  fetch("/products/" + productId + "/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: content }),
  })
    .then((res) => res.json())
    .then((data) => {
      alert(data.message || "리뷰가 등록되었습니다!");
      location.reload();
    });
}

// 5. 수량 변경 로직
document.addEventListener("DOMContentLoaded", function () {
  const minusBtn = document.getElementById("btnMinus");
  const plusBtn = document.getElementById("btnPlus");
  const quantityInput = document.getElementById("quantityInput");

  if (minusBtn && plusBtn && quantityInput) {
    minusBtn.addEventListener("click", function () {
      let currentValue = parseInt(quantityInput.value);
      if (currentValue > 1) {
        quantityInput.value = currentValue - 1;
      }
    });

    plusBtn.addEventListener("click", function () {
      let currentValue = parseInt(quantityInput.value);
      quantityInput.value = currentValue + 1;
    });
  }
});

// 6. 구매하기 로직
function buyItem(productId) {
  const quantity = document.getElementById("quantityInput").value;
  if (!confirm(quantity + "개를 구매하시겠습니까?")) return;

  fetch("/orders/buy/" + productId, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ quantity: parseInt(quantity) }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.result === "success") {
        alert(data.message);
        window.location.href = "/mypage"; // 구매 후 마이페이지로 이동
      } else {
        alert(data.message);
        if (data.message.includes("로그인")) {
          location.href = "/login";
        }
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("구매 중 오류가 발생했습니다.");
    });
}

function addToCart(productId) {
  const quantity = document.getElementById("quantityInput").value;

  fetch("/cart/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      product_id: productId,
      quantity: parseInt(quantity),
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.result === "success") {
        if (confirm("장바구니에 담았습니다. 확인하러 가시겠습니까?")) {
          location.href = "/cart";
        } else {
          // 배지 개수 업데이트 (cart_floating.html의 함수 호출)
          if (typeof updateCartCount === "function") updateCartCount();
        }
      } else {
        alert(data.message);
        if (data.message.includes("로그인")) location.href = "/login";
      }
    });
}

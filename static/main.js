// GPT応答のローディグ
const form = document.querySelector("form");
const loading = document.createElement("div");
loading.className = "loading";
loading.textContent = "送信中...";
loading.style.display = "none";
document.body.appendChild(loading);

form.addEventListener("submit", function () {
  loading.style.display = "block";
});

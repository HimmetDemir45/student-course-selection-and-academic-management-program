/**
 * Basit istemci doğrulama. Rollback: base.html script etiketini kaldırın.
 */
(function () {
  function initRegisterForm() {
    var form = document.getElementById("register-form");
    if (!form || form.method.toLowerCase() !== "post") return;
    var email = form.querySelector('input[type="email"], input[name="email"]');
    if (!email) return;
    email.setAttribute("aria-describedby", (email.getAttribute("aria-describedby") || "") + " email-hint");
    email.addEventListener("blur", function () {
      if (email.validity && email.validity.typeMismatch) {
        email.setCustomValidity("Geçerli bir e-posta girin.");
      } else {
        email.setCustomValidity("");
      }
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initRegisterForm);
  } else {
    initRegisterForm();
  }
})();

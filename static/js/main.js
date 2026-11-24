document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".menu-toggle");
    const nav = document.querySelector("#mainNav");

    if (toggle && nav) {
        toggle.addEventListener("click", () => {
            const isOpen = nav.classList.toggle("open");
            toggle.setAttribute("aria-expanded", String(isOpen));
            toggle.setAttribute("aria-label", isOpen ? "Fermer le menu" : "Ouvrir le menu");
            toggle.textContent = isOpen ? "×" : "☰";
        });
    }

    // Ajoute automatiquement les classes aux champs générés par les formulaires Django.
    document.querySelectorAll(".form-field input, .form-field textarea, .form-field select").forEach((field) => {
        field.classList.add("django-field");
    });
});

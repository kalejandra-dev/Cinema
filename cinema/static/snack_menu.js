// Snacks menu in the booking: "− n +" buttons for every product.
// Updates the number of items and the snacks total while choosing, highlights
// the chosen products, and warns if the deals include more tickets than seats.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("booking-snacks-form");
    if (!form) return;

    const MAX = 10;
    const seats = parseInt(form.dataset.seats, 10);
    const inputs = form.querySelectorAll(".qty-input");
    const countText = document.getElementById("snack-count");
    const totalText = document.getElementById("snack-total");
    const warning = document.getElementById("snack-warning");
    const submitButton = document.getElementById("snack-submit");

    function quantity(input) {
        const value = parseInt(input.value, 10);
        return Number.isNaN(value) ? 0 : Math.min(Math.max(value, 0), MAX);
    }

    function update() {
        let items = 0;
        let total = 0;
        let tickets = 0;
        inputs.forEach((input) => {
            const n = quantity(input);
            items += n;
            total += n * parseFloat(input.dataset.price);
            tickets += n * parseInt(input.dataset.tickets || "0", 10);
            // highlight the product while it has some quantity
            input.closest("[data-choice]").classList.toggle("is-selected", n > 0);
        });

        countText.textContent = items;
        totalText.textContent = `€${total.toFixed(2)}`;

        const tooManyTickets = tickets > seats;
        warning.hidden = !tooManyTickets;
        warning.textContent = `Your deals include ${tickets} tickets, but you chose ${seats} seat${seats === 1 ? "" : "s"}.`;
        submitButton.disabled = tooManyTickets;
    }

    form.querySelectorAll("[data-stepper]").forEach((stepper) => {
        const input = stepper.querySelector(".qty-input");
        stepper.querySelectorAll("[data-step]").forEach((button) => {
            button.addEventListener("click", () => {
                input.value = Math.min(Math.max(quantity(input) + Number(button.dataset.step), 0), MAX);
                update();
            });
        });
    });

    // Typing a number directly also works
    form.addEventListener("input", update);
    form.addEventListener("change", (event) => {
        if (event.target.classList.contains("qty-input")) {
            event.target.value = quantity(event.target);
            update();
        }
    });
    update();
});

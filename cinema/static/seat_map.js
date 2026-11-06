// Seat map on the booking page:
// shows which seats are selected and the tickets total, and disables
// the submit button while no seat is selected.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("booking-form");
    if (!form) return;

    const pricePerSeat = parseFloat(form.dataset.pricePerSeat);
    const selectedText = document.getElementById("selected-seats");
    const totalText = document.getElementById("seats-total");
    const submitButton = form.querySelector("button[type='submit']");

    function update() {
        const checked = form.querySelectorAll("input[name='seats']:checked");
        const labels = Array.from(checked, (input) => input.value);

        selectedText.textContent = labels.length ? labels.join(", ") : "none";
        totalText.textContent = (labels.length * pricePerSeat).toFixed(2);
        submitButton.disabled = labels.length === 0;
    }

    form.addEventListener("change", update);
    update();
});
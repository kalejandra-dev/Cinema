// Booking step 1 (seat map):
// shows the selected seats and the tickets price,
// and disables "Continue" while no seat is selected.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("seats-form");
    if (!form) return;

    const pricePerSeat = parseFloat(form.dataset.pricePerSeat);
    const selectedText = document.getElementById("selected-seats");
    const totalText = document.getElementById("seats-total");
    const continueButton = form.querySelector("button[type='submit']");

    function update() {
        const checked = form.querySelectorAll("input[name='seats']:checked");
        const labels = Array.from(checked, (input) => input.value);

        selectedText.textContent = labels.length ? labels.join(", ") : "none";
        totalText.textContent = (labels.length * pricePerSeat).toFixed(2);
        continueButton.disabled = labels.length === 0;
    }

    form.addEventListener("change", update);
    update();
});
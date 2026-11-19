// Booking page:
// shows the selected seats and the totals (tickets, food and drinks, total),
// and disables the submit button while no seat is selected.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("booking-form");
    if (!form) return;

    const pricePerSeat = parseFloat(form.dataset.pricePerSeat);
    const foodInputs = form.querySelectorAll("input[data-price]");
    const selectedText = document.getElementById("selected-seats");
    const seatsTotalText = document.getElementById("seats-total");
    const foodTotalText = document.getElementById("food-total");
    const totalText = document.getElementById("booking-total");
    const submitButton = form.querySelector("button[type='submit']");

    function update() {
        const checked = form.querySelectorAll("input[name='seats']:checked");
        const labels = Array.from(checked, (input) => input.value);
        const seatsTotal = labels.length * pricePerSeat;

        let foodTotal = 0;
        foodInputs.forEach((input) => {
            const quantity = parseInt(input.value, 10);
            if (quantity > 0) {
                foodTotal += quantity * parseFloat(input.dataset.price);
            }
        });

        selectedText.textContent = labels.length ? labels.join(", ") : "none";
        seatsTotalText.textContent = seatsTotal.toFixed(2);
        foodTotalText.textContent = foodTotal.toFixed(2);
        totalText.textContent = (seatsTotal + foodTotal).toFixed(2);
        submitButton.disabled = labels.length === 0;
    }

    form.addEventListener("input", update);   // typing in the quantity boxes
    form.addEventListener("change", update);  // clicking seats
    update();
});
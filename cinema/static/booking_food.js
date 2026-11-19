// Booking step 2 (packages and food):
// updates the totals while the user changes the quantities, and disables
// "Confirm booking" if the packages include more tickets than seats.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("food-form");
    if (!form) return;

    const pricePerSeat = parseFloat(form.dataset.pricePerSeat);
    const seats = parseInt(form.dataset.seats, 10);
    const foodInputs = form.querySelectorAll("input[data-price]");
    const packageInputs = form.querySelectorAll("input[data-package-price]");
    const seatsTotalText = document.getElementById("seats-total");
    const packagesTotalText = document.getElementById("packages-total");
    const foodTotalText = document.getElementById("food-total");
    const totalText = document.getElementById("booking-total");
    const warning = document.getElementById("package-warning");
    const confirmButton = document.getElementById("confirm-button");

    function quantity(input) {
        const value = parseInt(input.value, 10);
        return value > 0 ? value : 0;
    }

    function update() {
        let packageTickets = 0;
        let packagesTotal = 0;
        packageInputs.forEach((input) => {
            packageTickets += quantity(input) * parseInt(input.dataset.tickets, 10);
            packagesTotal += quantity(input) * parseFloat(input.dataset.packagePrice);
        });

        let foodTotal = 0;
        foodInputs.forEach((input) => {
            foodTotal += quantity(input) * parseFloat(input.dataset.price);
        });

        // Seats that are not covered by a package are paid at the normal price
        const seatsTotal = Math.max(seats - packageTickets, 0) * pricePerSeat;
        const tooManyTickets = packageTickets > seats;

        seatsTotalText.textContent = seatsTotal.toFixed(2);
        if (packagesTotalText) packagesTotalText.textContent = packagesTotal.toFixed(2);
        foodTotalText.textContent = foodTotal.toFixed(2);
        totalText.textContent = (seatsTotal + packagesTotal + foodTotal).toFixed(2);

        warning.hidden = !tooManyTickets;
        warning.textContent = `Your packages include ${packageTickets} tickets, `
            + `but you chose ${seats} seats.`;
        confirmButton.disabled = tooManyTickets;
    }

    form.addEventListener("input", update);
    update();
});
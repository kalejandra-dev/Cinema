// Booking step 1 (seat map):
// shows the selected seats and the tickets price, disables "Continue" while no
// seat is selected, and every few seconds asks the server (fetch) which seats
// are taken, so seats booked by other people turn grey without reloading.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("seats-form");
    if (!form) return;

    const REFRESH_EVERY = 5000;   // milliseconds
    const pricePerSeat = parseFloat(form.dataset.pricePerSeat);
    const seatInputs = form.querySelectorAll("input[name='seats']");
    const selectedText = document.getElementById("selected-seats");
    const totalText = document.getElementById("seats-total");
    const notice = document.getElementById("seat-notice");
    const continueButton = form.querySelector("button[type='submit']");

    function update() {
        const checked = form.querySelectorAll("input[name='seats']:checked");
        const labels = Array.from(checked, (input) => input.value);

        selectedText.textContent = labels.length ? labels.join(", ") : "none";
        totalText.textContent = (labels.length * pricePerSeat).toFixed(2);
        continueButton.disabled = labels.length === 0;
    }

    async function refreshTakenSeats() {
        if (document.hidden) return;   // the tab is not visible: don't ask the server
        try {
            const response = await fetch(form.dataset.takenUrl);
            if (!response.ok) return;
            const data = await response.json();
            const taken = new Set(data.taken);

            const lost = [];   // seats the user had chosen that someone else just booked
            seatInputs.forEach((input) => {
                const isTaken = taken.has(input.value);
                if (isTaken && input.checked) {
                    input.checked = false;
                    lost.push(input.value);
                }
                input.disabled = isTaken;
            });

            if (lost.length > 0) {
                notice.textContent = `Sorry, ${lost.join(", ")} ${lost.length === 1 ? "was" : "were"} `
                    + "just booked by someone else. Please choose another seat.";
                notice.hidden = false;
            }
            update();
        } catch (error) {
            // Network problem or the session expired: try again next time
        }
    }

    form.addEventListener("change", () => {
        notice.hidden = true;
        update();
    });
    update();
    setInterval(refreshTakenSeats, REFRESH_EVERY);
});

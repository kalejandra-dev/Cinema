// Movie detail: day tabs (Today, Tomorrow, ...).
// Clicking a day asks the server for that day's showtimes (JSON, with fetch)
// and shows them without reloading the page.
document.addEventListener("DOMContentLoaded", () => {
    const list = document.getElementById("showtime-list");
    const tabs = document.querySelectorAll(".day-tab");
    if (!list || tabs.length === 0) return;

    function showtimeItem(showtime, canBook) {
        // Built with textContent (never innerHTML), so data from the server is never run as HTML
        const item = document.createElement("li");
        item.classList.add("is-visible");          // don't wait for the scroll animation

        const info = document.createElement("div");
        const time = document.createElement("strong");
        time.className = "showtime-time";
        time.textContent = showtime.time;
        const details = document.createElement("span");
        details.className = "meta";
        details.textContent = `${showtime.screen} · ${showtime.seats_left} seats left`;
        info.append(time, details);
        item.append(info);

        if (showtime.seats_left === 0) {
            const soldOut = document.createElement("span");
            soldOut.className = "tag tag-off";
            soldOut.textContent = "Sold out";
            item.append(soldOut);
        } else if (canBook) {
            const book = document.createElement("a");
            book.className = "btn";
            book.href = showtime.booking_url;
            book.textContent = "Book";
            item.append(book);
        }
        return item;
    }

    async function showDay(tab) {
        list.classList.add("is-loading");
        try {
            const response = await fetch(`${list.dataset.url}?date=${tab.dataset.date}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();

            const items = data.showtimes.map((showtime) => showtimeItem(showtime, data.can_book));
            if (items.length === 0) {
                const empty = document.createElement("li");
                empty.className = "empty is-visible";
                empty.textContent = "No more showtimes this day.";
                items.push(empty);
            }
            list.replaceChildren(...items);

            tabs.forEach((other) => {
                other.classList.toggle("is-active", other === tab);
                other.toggleAttribute("aria-current", other === tab);
            });
            history.replaceState(null, "", tab.href);   // the URL shows the chosen day
        } catch (error) {
            window.location.href = tab.href;            // if fetch fails, just load the page
        } finally {
            list.classList.remove("is-loading");
        }
    }

    tabs.forEach((tab) => {
        tab.addEventListener("click", (event) => {
            event.preventDefault();     // don't follow the link, load the day with fetch
            showDay(tab);
        });
    });
});

// Soft animations: cards and panels fade in when they scroll into view.
// The class "js-reveal" is only added when JavaScript runs, so without JS
// everything is just visible.
(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion || !("IntersectionObserver" in window)) return;

    const items = document.querySelectorAll(
        ".movie-card, .panel, .booking-card, .showtime-list li, .form-card"
    );
    document.documentElement.classList.add("js-reveal");

    function show(item) {
        item.classList.add("is-visible");
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                show(entry.target);
                observer.unobserve(entry.target);   // animate only once
            }
        });
    }, { threshold: 0.12 });

    items.forEach((item, i) => {
        // small delay between cards of the same row, so they appear one after another
        item.style.transitionDelay = `${(i % 4) * 70}ms`;
        observer.observe(item);
    });

    // Safety net: some browsers (e.g. Firefox in the lab virtual desktop) never
    // report the items as visible, and they would stay hidden forever.
    // After a moment, show everything that is still hidden.
    window.setTimeout(() => {
        items.forEach((item) => {
            if (!item.classList.contains("is-visible")) {
                show(item);
                observer.unobserve(item);
            }
        });
    }, 1000);
})();

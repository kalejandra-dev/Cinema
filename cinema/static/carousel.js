// Carousel on the home page: shows one featured movie at a time.
// It moves by itself every few seconds, with arrows and dots to change slide,
// and it stops while the mouse (or keyboard focus) is over it.
document.addEventListener("DOMContentLoaded", () => {
    const carousel = document.querySelector(".carousel");
    if (!carousel) return;

    const slides = carousel.querySelectorAll(".slide");
    const dots = carousel.querySelectorAll(".carousel-dot");
    const prevButton = carousel.querySelector(".carousel-prev");
    const nextButton = carousel.querySelector(".carousel-next");
    if (slides.length < 2) return;

    const INTERVAL = 3000;  // milliseconds between slides
    // Don't move by itself if the user asked the system for reduced motion
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let current = 0;
    let timer = null;

    function show(index) {
        // % makes it go back to the first slide after the last one (and vice versa)
        current = (index + slides.length) % slides.length;
        slides.forEach((slide, i) => {
            const active = i === current;
            slide.classList.toggle("is-active", active);
            slide.setAttribute("aria-hidden", active ? "false" : "true");
        });
        dots.forEach((dot, i) => {
            dot.classList.toggle("is-active", i === current);
        });
    }

    function start() {
        if (reduceMotion) return;
        stop();
        timer = setInterval(() => show(current + 1), INTERVAL);
    }

    function stop() {
        clearInterval(timer);
    }

    prevButton.addEventListener("click", () => { show(current - 1); start(); });
    nextButton.addEventListener("click", () => { show(current + 1); start(); });
    dots.forEach((dot, i) => {
        dot.addEventListener("click", () => { show(i); start(); });
    });

    carousel.addEventListener("mouseenter", stop);
    carousel.addEventListener("mouseleave", start);
    carousel.addEventListener("focusin", stop);
    carousel.addEventListener("focusout", start);

    start();
});

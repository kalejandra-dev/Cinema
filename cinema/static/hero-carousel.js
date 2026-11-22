
document.addEventListener("DOMContentLoaded", () => {
    const carousel = document.querySelector("[data-promo-carousel]");
    if (!carousel) return;

    const track = carousel.querySelector("[data-promo-track]");
    const slides = [...carousel.querySelectorAll("[data-promo-slide]")];
    const dots = [...carousel.querySelectorAll(".promo-dot")];
    const previous = carousel.querySelector(".promo-prev");
    const next = carousel.querySelector(".promo-next");

    if (!track || slides.length < 2) return;

    const INTERVAL = 6000;
    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    );

    let current = 0;
    let timer = null;
    let touchStartX = null;
    let touchStartY = null;

    function showSlide(index) {
        current = (index + slides.length) % slides.length;

        // Move the entire row of slides horizontally.
        track.style.transform = `translateX(-${current * 100}%)`;

        slides.forEach((slide, i) => {
            const active = i === current;

            slide.classList.toggle("is-active", active);
            slide.setAttribute("aria-hidden", String(!active));
            slide.inert = !active;
        });

        dots.forEach((dot, i) => {
            const active = i === current;

            dot.classList.toggle("is-active", active);
            dot.setAttribute("aria-pressed", String(active));
        });
    }

    function stopAutoplay() {
        clearTimeout(timer);
        timer = null;
    }

    function startAutoplay() {
        stopAutoplay();

        if (
            reducedMotion.matches ||
            document.hidden ||
            carousel.matches(":hover") ||
            carousel.contains(document.activeElement)
        ) {
            return;
        }

        timer = setTimeout(() => {
            showSlide(current + 1);
            startAutoplay();
        }, INTERVAL);
    }

    function navigate(index) {
        showSlide(index);
        startAutoplay();
    }

    previous.addEventListener("click", () => {
        navigate(current - 1);
    });

    next.addEventListener("click", () => {
        navigate(current + 1);
    });

    dots.forEach((dot, i) => {
        dot.addEventListener("click", () => navigate(i));
    });

    // Allow arrow-key navigation while using the carousel.
    carousel.addEventListener("keydown", (event) => {
        if (event.key === "ArrowLeft") {
            event.preventDefault();
            navigate(current - 1);
        } else if (event.key === "ArrowRight") {
            event.preventDefault();
            navigate(current + 1);
        }
    });

    // Pause while the user interacts with the carousel.
    carousel.addEventListener("mouseenter", stopAutoplay);
    carousel.addEventListener("mouseleave", startAutoplay);
    carousel.addEventListener("focusin", stopAutoplay);

    carousel.addEventListener("focusout", () => {
        requestAnimationFrame(startAutoplay);
    });

    // Basic mobile swipe navigation.
    carousel.addEventListener("touchstart", (event) => {
        const touch = event.changedTouches[0];
        touchStartX = touch.clientX;
        touchStartY = touch.clientY;
        stopAutoplay();
    }, { passive: true });

    carousel.addEventListener("touchend", (event) => {
        if (touchStartX === null) return;

        const touch = event.changedTouches[0];
        const deltaX = touch.clientX - touchStartX;
        const deltaY = touch.clientY - touchStartY;

        if (
            Math.abs(deltaX) > 60 &&
            Math.abs(deltaX) > Math.abs(deltaY)
        ) {
            navigate(current + (deltaX < 0 ? 1 : -1));
        } else {
            startAutoplay();
        }

        touchStartX = null;
        touchStartY = null;
    }, { passive: true });

    document.addEventListener("visibilitychange", startAutoplay);

    if (typeof reducedMotion.addEventListener === "function") {
        reducedMotion.addEventListener("change", startAutoplay);
    }

    showSlide(0);
    startAutoplay();
});

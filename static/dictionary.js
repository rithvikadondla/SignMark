// ==========================================
// SIGNMARK DICTIONARY - COMPLETE UPGRADE
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("dictionarySearch");
    const alphabetButtons = document.querySelectorAll(".alphabet-btn");
    const letterCards = document.querySelectorAll(".letter-card");
    const noResults = document.getElementById("dictionaryNoResults");

    const dictionaryModal = document.getElementById("dictionaryModal");
    const modalSignImage = document.getElementById("modalSignImage");
    const modalSignLetter = document.getElementById("modalSignLetter");
    const closeDictionaryModal = document.getElementById("closeDictionaryModal");

    let selectedLetter = "all";


    // ==========================================
    // SEARCH + FILTER
    // ==========================================

    function filterDictionary() {

        const searchValue = searchInput
            ? searchInput.value.toUpperCase().trim()
            : "";

        let visibleCards = 0;

        letterCards.forEach(card => {

            const letter = card.dataset.letter;

            const matchesSearch = letter.includes(searchValue);

            const matchesFilter =
                selectedLetter === "all" ||
                letter === selectedLetter;

            if (matchesSearch && matchesFilter) {

                card.style.display = "";

                card.classList.add("dictionary-card-visible");

                visibleCards++;

            } else {

                card.style.display = "none";

                card.classList.remove("dictionary-card-visible");

            }

        });


        // NO RESULTS MESSAGE

        if (noResults) {

            noResults.style.display =
                visibleCards === 0 ? "block" : "none";

        }


        // UPDATE RESULT COUNT

        const resultCount =
            document.getElementById("dictionaryResultCount");

        if (resultCount) {

            resultCount.textContent =
                visibleCards + (visibleCards === 1
                    ? " letter found"
                    : " letters found");

        }

    }


    // ==========================================
    // SEARCH INPUT
    // ==========================================

    if (searchInput) {

        searchInput.addEventListener("input", filterDictionary);

    }


    // ==========================================
    // ALPHABET FILTER
    // ==========================================

    alphabetButtons.forEach(button => {

        button.addEventListener("click", function () {

            alphabetButtons.forEach(btn => {
                btn.classList.remove("active");
            });

            this.classList.add("active");

            selectedLetter = this.dataset.letter;

            filterDictionary();

        });

    });


    // ==========================================
    // DICTIONARY MODAL OPEN
    // ==========================================

    function openDictionaryModal(card) {

        if (!dictionaryModal || !modalSignImage || !modalSignLetter) {
            return;
        }

        const letter = card.dataset.letter;
        const image = card.querySelector("img");

        if (!image) return;

        modalSignImage.src = image.src;
        modalSignImage.alt = "ASL sign for letter " + letter;

        modalSignLetter.textContent = "Letter " + letter;

        dictionaryModal.style.display = "flex";

        dictionaryModal.classList.remove("modal-closing");

        document.body.style.overflow = "hidden";

    }


    // ==========================================
    // CLOSE MODAL
    // ==========================================

    function closeModal() {

        if (!dictionaryModal) return;

        dictionaryModal.style.display = "none";

        document.body.style.overflow = "";

    }


    // ==========================================
    // CARD CLICK
    // ==========================================

    letterCards.forEach(card => {

        card.addEventListener("click", function () {

            openDictionaryModal(this);

        });


        // KEYBOARD ACCESSIBILITY

        card.setAttribute("tabindex", "0");

        card.setAttribute("role", "button");

        card.setAttribute(
            "aria-label",
            "View sign for letter " + card.dataset.letter
        );


        card.addEventListener("keydown", function (event) {

            if (event.key === "Enter" || event.key === " ") {

                event.preventDefault();

                openDictionaryModal(this);

            }

        });

    });


    // ==========================================
    // CLOSE BUTTON
    // ==========================================

    if (closeDictionaryModal) {

        closeDictionaryModal.addEventListener("click", closeModal);

    }


    // ==========================================
    // CLICK OUTSIDE MODAL
    // ==========================================

    if (dictionaryModal) {

        dictionaryModal.addEventListener("click", function (event) {

            if (event.target === dictionaryModal) {

                closeModal();

            }

        });

    }


    // ==========================================
    // ESCAPE KEY
    // ==========================================

    document.addEventListener("keydown", function (event) {

        if (
            event.key === "Escape" &&
            dictionaryModal &&
            dictionaryModal.style.display === "flex"
        ) {

            closeModal();

        }

    });


    // ==========================================
    // INITIAL FILTER
    // ==========================================

    filterDictionary();

});


// ==========================================
// DICTIONARY RESET FUNCTION
// ==========================================

function resetDictionary() {

    const searchInput =
        document.getElementById("dictionarySearch");

    const alphabetButtons =
        document.querySelectorAll(".alphabet-btn");

    if (searchInput) {
        searchInput.value = "";
    }

    alphabetButtons.forEach(button => {

        button.classList.remove("active");

        if (button.dataset.letter === "all") {
            button.classList.add("active");
        }

    });

    const cards = document.querySelectorAll(".letter-card");

    cards.forEach(card => {
        card.style.display = "";
    });

}
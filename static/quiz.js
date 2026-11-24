// 🤟 SIGNMARK - ENDLESS ASL QUIZ

const questionBank = [

    // 🌱 BEGINNER LEVEL

    {
        level: "Beginner",
        question: "What does ASL stand for?",
        options: ["American Sign Language", "Advanced Speaking Language", "Active Sign Learning", "Australian Symbol Language"],
        answer: 0,
        explanation: "ASL means American Sign Language! 🤟"
    },
    {
        level: "Beginner",
        question: "How many letters are in the English alphabet?",
        options: ["24", "25", "26", "28"],
        answer: 2,
        explanation: "There are 26 letters in the English alphabet! 🔤"
    },
    {
        level: "Beginner",
        question: "Which letters involve movement in ASL?",
        options: ["A and B", "J and Z", "C and D", "E and F"],
        answer: 1,
        explanation: "J and Z involve movement! ✨"
    },
    {
        level: "Beginner",
        question: "What is fingerspelling used for?",
        options: ["Dancing", "Spelling words and names", "Drawing", "Counting money"],
        answer: 1,
        explanation: "Fingerspelling can be used to spell names and words! 💡"
    },
    {
        level: "Beginner",
        question: "Is ASL universal?",
        options: ["Yes", "No, sign languages differ", "Only in Asia", "Only in America"],
        answer: 1,
        explanation: "Sign languages differ across countries and communities! 🌍"
    },
    {
        level: "Beginner",
        question: "How many hands are generally used for the ASL alphabet?",
        options: ["One", "Three", "Four", "Always two"],
        answer: 0,
        explanation: "The ASL fingerspelling alphabet is generally one-handed! ✋"
    },
    {
        level: "Beginner",
        question: "What is sign language?",
        options: ["A secret code", "A visual language", "A written language only", "A dance"],
        answer: 1,
        explanation: "Sign languages are visual languages using hands, facial expressions and body movements! 👀"
    },
    {
        level: "Beginner",
        question: "Which is important while communicating in ASL?",
        options: ["Looking away", "Visual attention", "Closing your eyes", "Speaking loudly only"],
        answer: 1,
        explanation: "Visual attention is important during signed communication! 😊"
    },

    // 🌟 INTERMEDIATE LEVEL

    {
        level: "Intermediate",
        question: "What is handshape?",
        options: ["Hand size", "The shape of the hand and fingers", "Hand colour", "Hand temperature"],
        answer: 1,
        explanation: "Handshape describes the configuration of fingers and hand! ✋"
    },
    {
        level: "Intermediate",
        question: "What does palm orientation describe?",
        options: ["Palm direction", "Finger length", "Hand size", "Arm strength"],
        answer: 0,
        explanation: "Palm orientation describes which direction your palm faces! 👋"
    },
    {
        level: "Intermediate",
        question: "Which can affect the meaning of a sign?",
        options: ["Handshape", "Movement", "Location", "All of these"],
        answer: 3,
        explanation: "Handshape, location, movement and orientation all matter! 🎯"
    },
    {
        level: "Intermediate",
        question: "What are non-manual signals?",
        options: ["Facial expressions and body signals", "Shoes", "Written letters", "Sounds only"],
        answer: 0,
        explanation: "Facial expressions and body movements can communicate meaning and grammar! 😊"
    },
    {
        level: "Intermediate",
        question: "Why is facial expression important in ASL?",
        options: ["It is decoration", "It can express grammar and emotions", "It is never used", "It replaces the alphabet"],
        answer: 1,
        explanation: "Facial expressions can convey grammatical information and emotions! 💕"
    },
    {
        level: "Intermediate",
        question: "What is sign location?",
        options: ["Where a sign is formed", "The sign's colour", "A sign's spelling", "A person's height"],
        answer: 0,
        explanation: "Location refers to where the sign is made around the body or signing space! 📍"
    },
    {
        level: "Intermediate",
        question: "What is the purpose of movement in signing?",
        options: ["It has no meaning", "It can be part of a sign's meaning", "It is only exercise", "It replaces facial expression"],
        answer: 1,
        explanation: "Movement is an important linguistic feature of many signs! 🤟"
    },
    {
        level: "Intermediate",
        question: "Can changing hand orientation change a sign?",
        options: ["Yes", "No, never", "Only in written English", "Only while dancing"],
        answer: 0,
        explanation: "Hand orientation can distinguish signs! 🌟"
    },

    // 🔥 ADVANCED LEVEL

    {
        level: "Advanced",
        question: "Does ASL follow English grammar exactly?",
        options: ["Yes", "No, ASL has its own grammar", "ASL has no grammar", "Only sometimes"],
        answer: 1,
        explanation: "ASL has its own linguistic grammar and structure! 🧠"
    },
    {
        level: "Advanced",
        question: "What is role shifting?",
        options: ["Changing clothes", "Representing different people or viewpoints", "Changing alphabet", "Repeating a sign"],
        answer: 1,
        explanation: "Role shifting can represent different characters or perspectives! 🎭"
    },
    {
        level: "Advanced",
        question: "What is topic-comment structure?",
        options: ["A random movement", "Organizing a topic and then information about it", "A handshape", "A sign's colour"],
        answer: 1,
        explanation: "Topic-comment structure presents a topic followed by information about it! 💬"
    },
    {
        level: "Advanced",
        question: "Why is context important in ASL?",
        options: ["It removes meaning", "It helps understand intended meaning", "It changes signs into English", "It is not important"],
        answer: 1,
        explanation: "Context helps us interpret signs and communication correctly! 🌍"
    },
    {
        level: "Advanced",
        question: "What can eyebrows communicate in ASL?",
        options: ["Nothing", "Grammatical information", "Alphabet letters", "Hand size"],
        answer: 1,
        explanation: "Eyebrow movements can mark grammatical features, including some question types! 👀"
    },
    {
        level: "Advanced",
        question: "What is a classifier in ASL?",
        options: ["A type of shoe", "A linguistic handshape used in certain constructions", "An English letter", "A spelling mistake"],
        answer: 1,
        explanation: "Classifiers are handshapes used in particular linguistic constructions to represent things or describe spatial information! ✨"
    },
    {
        level: "Advanced",
        question: "Why is ASL considered a natural language?",
        options: ["It has no rules", "It developed naturally within communities", "It is only a game", "It was made only for quizzes"],
        answer: 1,
        explanation: "ASL developed naturally within Deaf communities and has its own linguistic structure! 💖"
    },

    // 🎉 FUN & TRICKY QUESTIONS

    {
        level: "Beginner",
        question: "Can sign languages be understood without learning them?",
        options: ["Always", "Not always, they need learning", "Only at night", "Only by children"],
        answer: 1,
        explanation: "Sign languages are real languages and need to be learned! 💡"
    },
    {
        level: "Beginner",
        question: "Which is important when watching someone sign?",
        options: ["Looking at their face and hands", "Looking at the floor", "Closing your eyes", "Looking away"],
        answer: 0,
        explanation: "Visual attention helps you understand signed communication! 👀"
    },
    {
        level: "Beginner",
        question: "True or False: ASL is just English words made with hands.",
        options: ["True", "False", "Sometimes", "Only for names"],
        answer: 1,
        explanation: "ASL has its own grammar and structure, not just English translated word-for-word! 🧠"
    },
    {
        level: "Intermediate",
        question: "What happens if a sign's movement changes?",
        options: ["It may change its meaning", "Nothing ever", "It becomes a letter", "It disappears"],
        answer: 0,
        explanation: "Movement can be an important part of a sign's meaning! 🤟"
    },
    {
        level: "Intermediate",
        question: "Which is NOT one of the main sign parameters?",
        options: ["Handshape", "Location", "Movement", "Shoesize"],
        answer: 3,
        explanation: "Shoe size is not a sign parameter! 😄"
    },
    {
        level: "Intermediate",
        question: "Why should you avoid distracting someone while they sign?",
        options: ["They cannot see", "Visual attention is important", "Signs disappear", "ASL stops working"],
        answer: 1,
        explanation: "Signed communication relies heavily on visual attention! 💕"
    },
    {
        level: "Advanced",
        question: "Can facial grammar change the meaning of a sentence?",
        options: ["Yes", "No", "Only in English", "Never"],
        answer: 0,
        explanation: "Non-manual grammatical signals can affect meaning in ASL! 🌟"
    },
    {
        level: "Advanced",
        question: "What is the best way to learn a sign?",
        options: ["Guess forever", "Watch, practice and get feedback", "Never practice", "Only read its name"],
        answer: 1,
        explanation: "Watching, practicing and getting feedback help build signing skills! 🎯"
    },
    {
        level: "Advanced",
        question: "Why can context help when understanding a sign?",
        options: ["It gives clues about meaning", "It hides the sign", "It removes grammar", "It makes all signs identical"],
        answer: 0,
        explanation: "Context gives clues that help interpret meaning! 🌍"
    },
    {
        level: "Beginner",
        question: "What should you do when you don't understand a sign?",
        options: ["Give up immediately", "Ask politely for repetition or clarification", "Look away", "Guess and leave"],
        answer: 1,
        explanation: "Asking politely for clarification is a good communication strategy! 💗"
    },

    // 🎮 FUN CHALLENGES & SITUATION QUESTIONS

    {
        level: "Beginner",
        question: "Challenge: If someone fingerspells a name, what should you do?",
        options: ["Watch carefully", "Look away", "Start talking loudly", "Ignore it"],
        answer: 0,
        explanation: "Watch carefully to follow the letters being signed! 👀"
    },
    {
        level: "Beginner",
        question: "Fun Quiz: Which one is a sign language?",
        options: ["ASL", "HTML", "Wi-Fi", "Bluetooth"],
        answer: 0,
        explanation: "ASL stands for American Sign Language! 🤟"
    },
    {
        level: "Beginner",
        question: "True or False: Sign languages use facial expressions too.",
        options: ["False", "True", "Only sometimes when laughing", "Never"],
        answer: 1,
        explanation: "Facial expressions are an important part of sign languages! 😊"
    },
    {
        level: "Intermediate",
        question: "Challenge: You missed a sign during a conversation. What is best?",
        options: ["Pretend you understood", "Politely ask them to repeat", "Walk away", "Change the subject"],
        answer: 1,
        explanation: "Politely asking for repetition helps communication! 💬"
    },
    {
        level: "Intermediate",
        question: "Which feature makes sign languages visual?",
        options: ["Hand movements and facial expressions", "Sounds only", "Written paragraphs", "Music"],
        answer: 0,
        explanation: "Sign languages use visual features like hand movements, facial expressions and body signals! 👋"
    },
    {
        level: "Intermediate",
        question: "Tricky Question: Are all signs just hand movements?",
        options: ["Yes, only hands matter", "No, facial expressions and body movements may matter too", "Only fingers matter", "Signs have no meaning"],
        answer: 1,
        explanation: "Signing can involve hands, face, body and space! 🧠"
    },
    {
        level: "Intermediate",
        question: "What should you focus on when learning a new sign?",
        options: ["Handshape, location and movement", "Only the sign's name", "The background colour", "Your shoes"],
        answer: 0,
        explanation: "Handshape, location and movement are useful features to observe! 🎯"
    },
    {
        level: "Advanced",
        question: "Situation: A signer's eyebrows change while signing. Should you ignore it?",
        options: ["Yes, always", "No, it may carry grammatical information", "It is only decoration", "It means they are confused"],
        answer: 1,
        explanation: "Eyebrow movements can convey grammatical information in ASL! 👀"
    },
    {
        level: "Advanced",
        question: "Tricky Question: Can two sign languages have different grammar?",
        options: ["No, all sign languages are identical", "Yes, different sign languages have their own structures", "Only alphabet signs differ", "They have no grammar"],
        answer: 1,
        explanation: "Different sign languages have their own linguistic structures! 🌍"
    },
    {
        level: "Advanced",
        question: "Challenge: Why should ASL learners practice with real signers?",
        options: ["To improve understanding and receive feedback", "To avoid learning", "Because books are forbidden", "To memorize random movements"],
        answer: 0,
        explanation: "Practicing with fluent signers can improve understanding and give helpful feedback! 💖"
    },

    // 🖼️ IMAGE GUESSING QUESTIONS

    {
        level: "Beginner",
        question: "Guess the ASL letter shown in the image!",
        image: "/static/images/A.jpg",
        options: ["A", "B", "C", "D"],
        answer: 0,
        explanation: "This is the ASL letter A! 🤟"
    },
    {
        level: "Beginner",
        question: "Which letter does this hand sign represent?",
        image: "/static/images/B.jpg",
        options: ["D", "B", "F", "L"],
        answer: 1,
        explanation: "This is the ASL letter B! ✋"
    },
    {
        level: "Beginner",
        question: "Can you identify this ASL hand sign?",
        image: "/static/images/C.jpg",
        options: ["C", "O", "S", "A"],
        answer: 0,
        explanation: "This is the ASL letter C! 👀"
    },
    {
        level: "Beginner",
        question: "Guess the letter from the hand shape!",
        image: "/static/images/D.jpg",
        options: ["P", "D", "V", "U"],
        answer: 1,
        explanation: "This is the ASL letter D! 🎉"
    },
    {
        level: "Beginner",
        question: "Which alphabet is shown here?",
        image: "/static/images/F.jpg",
        options: ["G", "E", "F", "O"],
        answer: 2,
        explanation: "This is the ASL letter F! 💖"
    },
    {
        level: "Beginner",
        question: "Identify the sign shown in the picture!",
        image: "/static/images/L.jpg",
        options: ["L", "T", "A", "Y"],
        answer: 0,
        explanation: "This is the ASL letter L! 🤟"
    },
    {
        level: "Intermediate",
        question: "Which ASL letter is represented by this hand?",
        image: "/static/images/V.jpg",
        options: ["U", "V", "W", "N"],
        answer: 1,
        explanation: "This is the ASL letter V! ✌️"
    },
    {
        level: "Intermediate",
        question: "Look carefully! Which letter is this?",
        image: "/static/images/W.jpg",
        options: ["M", "U", "W", "V"],
        answer: 2,
        explanation: "This is the ASL letter W! 🌟"
    },
    {
        level: "Intermediate",
        question: "Guess the ASL alphabet sign!",
        image: "/static/images/Y.jpg",
        options: ["I", "J", "Y", "X"],
        answer: 2,
        explanation: "This is the ASL letter Y! 🤙"
    },
    {
        level: "Intermediate",
        question: "Challenge! Identify this hand sign.",
        image: "/static/images/Z.jpg",
        options: ["S", "Z", "N", "X"],
        answer: 1,
        explanation: "This is the ASL letter Z! ✨"
    }

];


// ==========================================
// GAME VARIABLES
// ==========================================

let currentLevel = "Beginner";
let score = 0;
let totalAnswered = 0;
let selectedAnswer = null;
let currentQuestion = null;
let usedQuestions = [];
let questionLocked = false;


// ==========================================
// ELEMENTS
// ==========================================

const quizQuestionTitle =
    document.querySelector(".quiz-question h2");

const quizQuestionDescription =
    document.querySelector(".quiz-question p");

const quizTop =
    document.querySelector(".quiz-top");

const quizProgress =
    document.querySelector(".quiz-progress div");

const quizFeedback =
    document.getElementById("quizFeedback");

const quizSubmit =
    document.getElementById("quizSubmit");

const quizSignImageBox =
    document.getElementById("quizSignImage");

const quizSignImage =
    document.getElementById("signQuestionImage");


// ==========================================
// RANDOM QUESTION
// ==========================================

function getRandomQuestion() {

    let availableQuestions = questionBank.filter(question =>
        question.level === currentLevel &&
        !usedQuestions.includes(question)
    );

    // Reset questions for this level
    // when all questions have been used

    if (availableQuestions.length === 0) {

        usedQuestions = usedQuestions.filter(question =>
            question.level !== currentLevel
        );

        availableQuestions = questionBank.filter(question =>
            question.level === currentLevel
        );

    }

    if (availableQuestions.length === 0) {
        return null;
    }

    const randomIndex =
        Math.floor(Math.random() * availableQuestions.length);

    currentQuestion =
        availableQuestions[randomIndex];

    usedQuestions.push(currentQuestion);

    return currentQuestion;

}


// ==========================================
// LOAD QUESTION
// ==========================================

function loadQuestion() {

    questionLocked = false;

    selectedAnswer = null;

    currentQuestion = getRandomQuestion();

    if (!currentQuestion) return;


    // QUESTION TEXT

    if (quizQuestionTitle) {

        quizQuestionTitle.textContent =
            currentQuestion.question;

    }

    if (quizQuestionDescription) {

        quizQuestionDescription.textContent =
            "Choose the correct answer below.";

    }


    // QUESTION NUMBER AND LEVEL

    if (quizTop) {

        quizTop.innerHTML = `
            <span>QUESTION ${totalAnswered + 1}</span>
            <span>⭐ ${currentLevel} Level</span>
        `;

    }


    // PROGRESS BAR

    if (quizProgress) {

        const totalLevelQuestions =
            questionBank.filter(q =>
                q.level === currentLevel
            ).length;

        const usedLevelQuestions =
            usedQuestions.filter(q =>
                q.level === currentLevel
            ).length;

        const progress =
            totalLevelQuestions > 0
                ? (usedLevelQuestions / totalLevelQuestions) * 100
                : 0;

        quizProgress.style.width =
            Math.min(progress, 100) + "%";

    }


    // IMAGE QUESTIONS

    if (currentQuestion.image) {

        if (quizSignImageBox) {
            quizSignImageBox.style.display = "block";
        }

        if (quizSignImage) {

            quizSignImage.src =
                currentQuestion.image;

            quizSignImage.alt =
                "ASL sign question image";

        }

    } else {

        if (quizSignImageBox) {
            quizSignImageBox.style.display = "none";
        }

        if (quizSignImage) {
            quizSignImage.src = "";
        }

    }


    // OPTIONS

    document.querySelectorAll(".quiz-option").forEach((button, index) => {

        if (currentQuestion.options[index] !== undefined) {

            button.textContent =
                currentQuestion.options[index];

            button.style.display = "";

        } else {

            button.style.display = "none";

        }

        button.disabled = false;

        button.classList.remove(
            "selected",
            "correct",
            "wrong"
        );

    });


    // FEEDBACK RESET

    if (quizFeedback) {

        quizFeedback.innerHTML = "";

        quizFeedback.className =
            "quiz-feedback";

    }


    // SUBMIT BUTTON

    if (quizSubmit) {

        quizSubmit.textContent =
            "Check Answer →";

        quizSubmit.disabled = false;

        quizSubmit.classList.remove(
            "next-question-btn"
        );

        quizSubmit.onclick =
            checkAnswer;

    }

}


// ==========================================
// SELECT ANSWER
// ==========================================

document.querySelectorAll(".quiz-option").forEach((button, index) => {

    button.addEventListener("click", function () {

        if (questionLocked) return;

        selectedAnswer = index;


        document.querySelectorAll(".quiz-option").forEach(btn => {

            btn.classList.remove(
                "selected",
                "correct",
                "wrong"
            );

        });


        this.classList.add("selected");


        if (quizFeedback) {

            quizFeedback.textContent =
                "Answer selected! 💜";

            quizFeedback.className =
                "quiz-feedback selected-feedback";

        }

    });

});


// ==========================================
// CHECK ANSWER
// ==========================================

function checkAnswer() {

    if (questionLocked) {

        nextQuestion();

        return;

    }


    if (selectedAnswer === null) {

        if (quizFeedback) {

            quizFeedback.textContent =
                "Please select an answer first! 💕";

            quizFeedback.className =
                "quiz-feedback warning-feedback";

        }

        return;

    }


    questionLocked = true;

    totalAnswered++;


    const optionButtons =
        document.querySelectorAll(".quiz-option");

    const correctAnswer =
        currentQuestion.answer;

    const isCorrect =
        selectedAnswer === correctAnswer;


    optionButtons.forEach(button => {

        button.disabled = true;

    });


    // CORRECT

    if (isCorrect) {

        score++;

        optionButtons[selectedAnswer]
            .classList.add("correct");

        if (quizFeedback) {

            quizFeedback.innerHTML = `
                <div class="quiz-result-correct">
                    <div class="quiz-result-icon">🎉</div>
                    <h3>Correct Answer!</h3>
                    <p>${currentQuestion.explanation}</p>
                </div>
            `;

            quizFeedback.className =
                "quiz-feedback correct-feedback";

        }

    }


    // WRONG

    else {

        optionButtons[selectedAnswer]
            .classList.add("wrong");

        optionButtons[correctAnswer]
            .classList.add("correct");

        if (quizFeedback) {

            quizFeedback.innerHTML = `
                <div class="quiz-result-wrong">
                    <div class="quiz-result-icon">💡</div>
                    <h3>Not quite!</h3>

                    <p>
                        Correct answer:
                        <strong>
                            ${currentQuestion.options[correctAnswer]}
                        </strong>
                    </p>

                    <p>${currentQuestion.explanation}</p>
                </div>
            `;

            quizFeedback.className =
                "quiz-feedback wrong-feedback";

        }

    }


    // CHANGE BUTTON

    if (quizSubmit) {

        quizSubmit.textContent =
            "Next Question →";

        quizSubmit.classList.add(
            "next-question-btn"
        );

        quizSubmit.onclick =
            nextQuestion;

    }

}


// ==========================================
// NEXT QUESTION + LEVEL PROGRESSION
// ==========================================

function nextQuestion() {

    if (!questionLocked) return;


    // LEVEL UP EVERY 10 QUESTIONS

    if (totalAnswered > 0 &&
        totalAnswered % 10 === 0) {

        if (currentLevel === "Beginner") {

            currentLevel = "Intermediate";

        } else if (currentLevel === "Intermediate") {

            currentLevel = "Advanced";

        } else {

            currentLevel = "Beginner";

        }


        // Update active level button

        document.querySelectorAll(
            ".quiz-level-btn, .level-btn"
        ).forEach(button => {

            button.classList.remove("active");

            if (button.dataset.level === currentLevel) {

                button.classList.add("active");

            }

        });

    }


    loadQuestion();

}


// ==========================================
// SCORE FUNCTION
// ==========================================

function getQuizScore() {

    return {

        score: score,

        totalAnswered: totalAnswered,

        accuracy: totalAnswered === 0
            ? 0
            : Math.round(
                (score / totalAnswered) * 100
            ),

        currentLevel: currentLevel

    };

}


// ==========================================
// RESET QUIZ
// ==========================================

function resetQuiz() {

    score = 0;

    totalAnswered = 0;

    selectedAnswer = null;

    currentQuestion = null;

    usedQuestions = [];

    questionLocked = false;

    currentLevel = "Beginner";


    document.querySelectorAll(
        ".quiz-level-btn, .level-btn"
    ).forEach(button => {

        button.classList.remove("active");

        if (button.dataset.level === "Beginner") {

            button.classList.add("active");

        }

    });


    loadQuestion();

}


// ==========================================
// START QUIZ
// ==========================================

loadQuestion();
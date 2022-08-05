import face from "../data/face_english.json" assert {type: 'json'};
import hidden from "../data/hidden_english.json" assert {type: 'json'};
import vocab from "../data/vocab_english.json" assert {type: 'json'};


// This isn't fun anymore and I want to be done. Sue me.
let currentLetter = "א";


function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
};

function wrapWord(word) {
    return `<span class="word" onclick="searchHelper('${word}', fromClick=true);">${word}</span>`;
};

export function populateDay(letter) {
    const localLetter = letter || currentLetter;
    currentLetter = localLetter;
    const dayDiv = document.getElementById("day");
    const day = document.getElementById("days").value;
    let words = {}
    try {
        if (document.getElementById("hiddenSelect").checked == true) {
            words = hidden[currentLetter][day];
        } else {
            words = face[currentLetter][day];
        }
        searchHelper(words[0], true);
        const wrappedWords = words.map(wrapWord)
        dayDiv.innerHTML = wrappedWords.join("<br />");
    } catch {
        dayDiv.innerHTML = "";
    };
};

function extractDefinition(definition) {
    return `<span style="padding-left: 1em;">${definition.definition}</span>`;
}

export async function searchHelper(searchTerm, fromClick = false) {
    if(fromClick === true) {
        const searchText = document.getElementById("searchTerm");
        searchText.value = "";
        const searchBox = document.getElementById("hiddenSearch");
        searchBox.checked = false;
    };

    const word = capitalize(searchTerm);
    const defDiv = document.getElementById("definitions");
    const dayText = document.getElementById(`day${vocab[word]["face_mod"]}`).innerText;
    const hiddenDayText = document.getElementById(`day${vocab[word]["hidden_mod"]}`).innerText;
    const line = [];
    line.push(`<strong>${word}</strong>`);
    line.push(`Numeric Value: ${vocab[word]["face_value"].toLocaleString("en-US")}`);
    line.push(`<span style="padding-left: 1em;">${dayText}</span>`);
    line.push(`Hidden Value: ${vocab[word]["hidden_value"].toLocaleString("en-US")}`);
    line.push(`<span style="padding-left: 1em;">${hiddenDayText}</span>`);

    const p = line.join("<br />") + "<br /><br />";

    const response = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${searchTerm}`);
    response.json().then(results => {

        const meanings = results[0].meanings;

        let output = new Array();

        meanings.forEach(meaning => {
                const partOfSpeech = capitalize(meaning.partOfSpeech);
                const definitions = meaning.definitions.map(extractDefinition);
                output.push(`<strong>${partOfSpeech}:</strong><br />${definitions.join("<br />")}`);
            }
        );

        defDiv.innerHTML = p + output.join("<br /><br />");

    })
    .catch(error => {

        defDiv.innerHTML = p + "<strong>dictionaryapi.dev doesn't know that word.</strong>"

    })
};

export async function search() {
    const searchTerm = capitalize(document.getElementById("searchTerm").value);
    if(!(searchTerm in vocab)) {
        window.alert("That word is not in my vocabulary");
        return;
    }
    populateDayFromSearch(searchTerm);
    await searchHelper(searchTerm);
};

function populateDayFromSearch(searchTerm) {
    const dayDiv = document.getElementById("day");
    const daySelect = document.getElementById("days");
    const dayHidden = document.getElementById("hiddenSelect");
    let words = [];
    currentLetter = searchTerm.at(0);
    if (document.getElementById("hiddenSearch").checked == true) {
        const day = vocab[searchTerm]["hidden_mod"];
        words = hidden[currentLetter][day].map(wrapWord);
        dayHidden.checked = true;
    }
    else {
        const day = vocab[searchTerm]["face_mod"];
        words = face[currentLetter][day].map(wrapWord);
        dayHidden.checked = false;
    }
    dayDiv.innerHTML = words.join("<br />");
    daySelect.value = day;
};

function wrapLetter(letter) {
    return `<span class="letter" onclick="populateDay('${letter}');">${letter}</span>`;
};

export async function initialize() {
    populateDay("A");
    const searchTerm = document.getElementById("searchTerm");
    searchTerm.addEventListener("keyup", e => {
        if(e.key === "Enter") {
            search();
        }
    });
    const alefbetDiv = document.getElementById("alefbet");
    const alefbet = [];
    for (let i = 4278124634; i > 4278124608; i--) {
        alefbet.push(String.fromCharCode(i));
    }
    const wrappedAlefbet = alefbet.map(wrapLetter);
    alefbetDiv.innerHTML = wrappedAlefbet.join(" ");
    await initializeSearch();
};

export async function initializeSearch() {
    const searchText = document.getElementById("searchTerm");
    searchText.value = "";
    const dayDiv = document.getElementById("day");
    const wrappedSearchTerm = dayDiv.innerHTML.split("<br>")[0];
    const regex = /.*>(.*)</;
    try {
        const searchTerm = wrappedSearchTerm.match(regex)[1];
        await searchHelper(searchTerm);
    }
    catch {
        const defDiv = document.getElementById("definitions");
        defDiv.innerHTML = "<strong>Try a different day or letter</strong>";
    }
};

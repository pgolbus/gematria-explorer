import env from "../env.json" assert {type: 'json'};
import face from "../data/new/face.json" assert {type: 'json'};
import hidden from "../data/new/hidden.json" assert {type: 'json'};
import words from "../data/new/words.json" assert {type: 'json'};
import diacritics from "../data/new/diacritics.json" assert {type: 'json'};


const SOFITS = ["ך", "ם", "ן", "ף", "ץ"];
const ALEF = "א".charCodeAt(0); // which happens to be 1488


// We are keeping track of the current letter at the module level. Meh.
let currentLetter = "א";


/**
 * Remove the vowels from a "diacritic" turning it into a "word"
 * @param {string} diacritic The diacritic to remove the vowels from
 * @returns {string} the word with the vowels removed
 */
function stripVowels(diacritic) {
    return diacritic.split('').filter(char => char.charCodeAt(0) >= ALEF);
};

/**
 * Wrap a word with a span that makes it searchable
 * @param {string} word The word to wrap
 * @returns {string} The word wrapped in the appropriate span
 */
function wrapWord(word) {
    return `<span class="word hebrew" onclick="searchHelper('${word}', fromClick=true);">${word}</span>`;
};

/**
 * Populate the day div with all of the words corresponding to that day for the specified letter
 * Side effects:
 *   - If letter is provided, overwrites the global currentLetter with the new one
 *   - Overwrites the "day" div w/ the new words
 * @param {string || undefined} letter The letter we're populating with, or the current letter if undefined
 */
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

export async function searchHelper(searchTerm, fromClick = false) {
    if(fromClick === true) {
        const searchText = document.getElementById("searchTerm");
        searchText.value = "";
        const searchBox = document.getElementById("hiddenSearch");
        searchBox.checked = false;
    };

    const defDiv = document.getElementById("definitions");
    const dayText = document.getElementById(`day${vocab[searchTerm]["face_mod"]}`).innerText;
    const hiddenDayText = document.getElementById(`day${vocab[searchTerm]["hidden_mod"]}`).innerText;
    const line = [];
    line.push(`<span class="hebrew">${searchTerm}</span>`);
    line.push(`Numeric Value: ${vocab[searchTerm]["face_value"].toLocaleString("en-US")}`);
    line.push(`<span style="padding-left: 1em;">${dayText}</span>`);
    line.push(`Hidden Value: ${vocab[searchTerm]["hidden_value"].toLocaleString("en-US")}`);
    line.push(`<span style="padding-left: 1em;">${hiddenDayText}</span>`);

    const p = line.join("<br />") + "<br /><br />";

    const url = `https://iq-bible.p.rapidapi.com/GetStrongs?lexiconId=H&id=${vocab[searchTerm]["strongs"]}`;
    const method = "GET";
    const headers = {
        'X-RapidAPI-Key': `${env["X-RapidAPI-Key"]}`,
        'X-RapidAPI-Host': `${env["X-RapidAPI-Host"]}`
    };
    const response = await fetch(url, {
        method: method,
        headers: headers
    });


    response.json().then(result => {

        const entry = result[0];
        const output = new Array();

        output.push(`${entry.glossary}<br />`);
        output.push(`Occurences: ${entry.occurences}<br />`);

        if(!(entry.root) === "") {
            output.push(`Root: ${entry.root}`);
        };
        if(!(entry.root_occurences) === "") {
            output.push(`Root Occurences: ${entry.root_occurence}`);
        };

        output.push("<br />");

        if(!(entry.second_root_hebrew === "")) {
            output.push(`Second Root: ${entry.second_root_hebrew}`);
            if(!(entry.third_root_hebrew === "")) {
                output.push(`Third Root: ${entry.third_root_hebrew}`);
            }
            output.push("<br />");
        };

        if(!(entry.passages === "")) {
            output.push(entry.passages);
        };

        defDiv.innerHTML = p + output.join("<br />")

    })
    .catch(error => {

        console.log(error);
        defDiv.innerHTML = "<strong>Something went wrong.</strong>"

    });
};

export async function search() {
    const searchTerm = document.getElementById("searchTerm").value;
    populateDayFromSearch(searchTerm);
    await searchHelper(searchTerm);
};

function populateDayFromSearch(searchTerm) {
    const dayDiv = document.getElementById("day");
    const daySelect = document.getElementById("days");
    const dayHidden = document.getElementById("hiddenSelect");
    let words = [];
    currentLetter = searchTerm.at(0);
    try {
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
    } catch {
        window.alert("Sorry, I'm broken.");
    };
};

function wrapLetter(letter) {
    if(SOFITS.includes(letter)) {
        return "";
    }
    return `<span class="letter hebrew" onclick="populateDay('${letter}');">${letter}</span>`;
};

export async function initialize() {
    populateDay(currentLetter);
    const searchTerm = document.getElementById("searchTerm");
    searchTerm.addEventListener("keyup", e => {
        if(e.key === "Enter") {
            search();
        }
    });
    const alefbetDiv = document.getElementById("alefbet");
    const alefbet = [];
    for (let i = parseInt("0x05D0", 0); i <= parseInt("0x05EA", 0); i++) {
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

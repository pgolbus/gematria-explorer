import { env } from "../env.js";
import { face } from "../data/face.js";
import { hidden } from "../data/hidden.js";
import { words } from "../data/words.js";
import { diacritics } from "../data/diacritics.js";


const SOFITS = ["ך", "ם", "ן", "ף", "ץ"];
const ALEF = "א".charCodeAt(0); // which happens to be 1488
let LOOKUP = true;

// We are keeping track of the current letter at the module level. Meh.
let currentLetter = "א";


/**
 * Remove the vowels from a "diacritic" turning it into a "word"
 * @param {string} diacritic The diacritic to remove the vowels from
 * @returns {string} the word with the vowels removed
 */
function stripVowels(diacritic) {
    return diacritic.split('').filter(char => char.charCodeAt(0) >= ALEF).join('');
};

/**
 * Wrap a word with a span that makes it searchable
 * @param {string} word The word to wrap
 * @returns {string} The word wrapped in the appropriate span
 */
function wrapWord(word, bold = true) {
    if(bold === true) {
        return `<span class="word" style="font-size: 25pt;" onclick="search('${word}', fromClick=true);">${word}</span>`;
    };
    return `<span class="word" onclick="search('${word}', fromClick=true);">${word}</span>`;
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
            words = hidden[currentLetter][day].map(word => word.word);
        } else {
            words = face[currentLetter][day].map(word => word.word);
        }
        search(words[0], true);
        const wrappedWords = words.map(word => wrapWord(word));
        dayDiv.innerHTML = wrappedWords.join("<br />");
    } catch {
        dayDiv.innerHTML = "";
    };
};

/**
 * Replace all occurences of Strongs numbers w/ their diacritics (and make them clickable)
 *
 * @params{glossary} (string) The glossary from Strongs
 */
function replaceStrongs(glossary) {
    let output = glossary;
    const strongsRegex = /(H\d+)/g;
    const strongsArray = glossary.match(strongsRegex);
    if (strongsArray !== null) {
        strongsArray.shift();
        strongsArray.forEach(strongs => {
            const strongsNumber = strongs.replace("H", "");
            output = output.replaceAll(strongs, wrapWord(diacritics[strongsNumber]["diacritic"], false));
        });
    };
    return output;
};

async function searchHelper(diacritic, defDiv) {
    if (LOOKUP === true) {
        const url = `https://iq-bible.p.rapidapi.com/GetStrongs?lexiconId=H&id=${diacritic["strongs"]}`;
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
            const output = new Array();
            result.forEach(entry => {
                output.push(`<p><span style="font-size: 30px;">${diacritic["diacritic"]}:</span> ${replaceStrongs(entry.glossary)}<br /><strong>Occurences:</strong>${entry.occurences}</p>`);
            })
            defDiv.innerHTML += output.join("");
        })
        .catch(error => {

            console.log(error);
            return "<strong>Something went wrong.</strong>"

        })
    };
};

/**
 * Search for a word and populate results
 *
 * Side-effects
 *   - Update definitions div
 *   - Update current letter
 *   - Update day div
 * @params{searchWord} (Word) The word object we are searching for
 * @params{fromClick} (bool) Indicates whether the term came from clicking rather than searching
 */
export async function search(searchWord, fromClick = false) {
    if(fromClick === true) {
        const searchText = document.getElementById("searchTerm");
        searchText.value = "";
        const searchBox = document.getElementById("hiddenSearch");
        searchBox.checked = false;
    };

    const searchTerm = stripVowels(searchWord);
    const defDiv = document.getElementById("definitions");
    const dayText = document.getElementById(`day${words[searchTerm]["word_numbers"]["face_mod"]}`).innerText;
    const hiddenDayText = document.getElementById(`day${words[searchTerm]["word_numbers"]["hidden_mod"]}`).innerText;
    const line = [];
    line.push(`<span style="font-size: 30px">${searchTerm}</span>`);
    line.push(`Numeric Value: ${words[searchTerm]["word_numbers"]["face_value"].toLocaleString("en-US")}`);
    line.push(`<span style="padding-left: 1em;">${dayText}</span>`);
    line.push(`Hidden Value: ${words[searchTerm]["word_numbers"]["hidden_value"].toLocaleString("en-US")}`);
    line.push(`<span style="padding-left: 1em;">${hiddenDayText}</span>`);

    defDiv.innerHTML = line.join("<br />") + "<br /><br />";

    const results = []
    words[searchTerm]["diacritics"].forEach(diacritic => {
        searchHelper(diacritic, defDiv)
    });
};

export async function searchBox() {
    const searchTerm = stripVowels(document.getElementById("searchTerm").value);
    populateDayFromSearch(searchTerm);
    await search(searchTerm);
};

function populateDayFromSearch(searchTerm) {
    const dayDiv = document.getElementById("day");
    const daySelect = document.getElementById("days");
    const dayHidden = document.getElementById("hiddenSelect");
    let dayWords = [];
    let day = 0
    currentLetter = searchTerm.at(0);
    if (document.getElementById("hiddenSearch").checked == true) {
        day = words[searchTerm]["word_numbers"]["hidden_mod"];
        dayWords = hidden[currentLetter][day].map(word => wrapWord(word.word));
        dayHidden.checked = true;
    }
    else {
        day = words[searchTerm]["word_numbers"]["face_mod"];
        dayWords = face[currentLetter][day].map(word => wrapWord(word.word));
        dayHidden.checked = false;
    }
    dayDiv.innerHTML = dayWords.join("<br />");
    daySelect.value = day;
};

function wrapLetter(letter) {
    if(SOFITS.includes(letter)) {
        return "";
    }
    return `<span class="letter hebrew" onclick="populateDay('${letter}');">${letter}</span>`;
};

export async function initialize(url) {
    const lookup = new URL(url).searchParams.get("lookup");
    if(lookup !== null) {
        LOOKUP = lookup;
    };
    populateDay(currentLetter);
    const searchTerm = document.getElementById("searchTerm");
    searchTerm.addEventListener("keyup", e => {
        if(e.key === "Enter") {
            searchBox();
        }
    });
    const alefbetDiv = document.getElementById("alefbet");
    const alefbet = [];
    for (let i = parseInt("0x05D0", 0); i <= parseInt("0x05EA", 0); i++) {
        alefbet.push(String.fromCharCode(i));
    }
    const wrappedAlefbet = alefbet.map(wrapLetter);
    alefbetDiv.innerHTML = wrappedAlefbet.join(" ");
};

export function clearSearch() {
    const searchBoxDiv = document.getElementById("searchTerm");
    searchBoxDiv.value = "";
};
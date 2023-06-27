import { env } from "../env.js";
import { diacritics } from "../data/diacritics.js";
import { haakhor } from "../data/haakhor.js";
import { hechrechi } from "../data/hechrechi.js";
import { gadol } from "../data/gadol.js";
import { strongs } from "../data/strongs.js";
import { words } from "../data/words.js";


const SOFITS = ["ך", "ם", "ן", "ף", "ץ"];
const ALEF = "א".charCodeAt(0); // which happens to be 1488

// We are keeping track of the current letter at the module level. Meh.
let currentLetter = "א";

// If there is a search in progress, we don't want changing the mispar to blow it away
// Do we need this? I'm not sure it ever gets cleared...
let activeSearch = false;


/**
 * Remove the vowels from a "diacritic" turning it into a "word"
 * @param {string} diacritic The diacritic to remove the vowels from
 * @returns {string} the word with the vowels removed
 */
function stripVowels(diacritic) {
    return diacritic.split('').filter(char => (char.charCodeAt(0) >= ALEF || char === " ")).join('');
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
    let words = {};
    //try {
        if (document.getElementById("misparSelect").value === "hechrechi") {
            words = hechrechi[currentLetter][day].map(word => word.word);
        } else if (document.getElementById("misparSelect").value === "gadol") {
            words = gadol[currentLetter][day].map(word => word.word);
        } else {
            words = haakhor[currentLetter][day].map(word => word.word);
        }
        search(words[0], true);
        const wrappedWords = words.map(word => wrapWord(word));
        dayDiv.innerHTML = wrappedWords.join("<br />");
    /*} catch {
        dayDiv.innerHTML = "";
    };*/
};

/**
 * Replace all occurences of Strongs numbers w/ their diacritics (and make them clickable)
 *
 * @params{glossary} (string) The glossary from Strongs
 */
function replaceStrongs(derivation) {
    let output = derivation;
    const strongsRegex = /(H\d+) (\(.*?\))/g;
    const strongsArray = Array.from(derivation.matchAll(strongsRegex));
    if (strongsArray !== null) {
        strongsArray.forEach(strongs => {
            output = output.replaceAll(strongs[0], wrapWord(diacritics[strongs[1]]["diacritic"], false));
        });
    };
    return output;
};

/**
 * Search for a word and populate results
 *
 * Side-effects
 *   - Update definitions div
 *   - If from click, ends the active search
 * @params{searchWord} (Word) The word object we are searching for
 * @params{fromClick} (bool) Indicates whether the term came from clicking rather than searching
 */
export function search(searchWord, fromClick = false) {
    if(fromClick === true) {
        const searchText = document.getElementById("searchTerm");
        searchText.value = "";
        activeSearch = false;
    };

    const searchTerm = stripVowels(searchWord);
    const defDiv = document.getElementById("definitions");
    const hechrechiText = document.getElementById(`day${words[searchTerm]["hechrechi"]["mod"]}`).innerText;
    const gadolText = document.getElementById(`day${words[searchTerm]["gadol"]["mod"]}`).innerText;
    const haakhorText = document.getElementById(`day${words[searchTerm]["haakhor"]["mod"]}`).innerText;
    const line = [];
    line.push(`<span style="font-size: 30px">${searchTerm}</span>`);
    line.push(`Hechrechi: ${words[searchTerm]["hechrechi"]["value"].toLocaleString("en-US")}<br />&emsp;${hechrechiText}`);
    line.push(`Gadol: ${words[searchTerm]["gadol"]["value"].toLocaleString("en-US")}<br />&emsp;${gadolText}`);
    line.push(`haAkhor: ${words[searchTerm]["haakhor"]["value"].toLocaleString("en-US")}<br />&emsp;${haakhorText}`);

    const results = []
    words[searchTerm]["diacritics"].forEach(diacritic => {
        const strongs_number = diacritic["strongs"];
        const strongs_entry = strongs[strongs_number];
        const entry_output = ["<p>"];
        entry_output.push(`<span class="bold">${strongs_entry["lemma"]}</span>: ${strongs_entry["xlit"]}`);
        entry_output.push(`${replaceStrongs(strongs_entry["derivation"])}`);
        entry_output.push(`Strong's definition: ${strongs_number} ${strongs_entry["strongs_def"]}`);
        entry_output.push(`King James: ${strongs_entry["kjv_def"]}`);
        results.push(`<p>${entry_output.join("<br />")}</p>`)
    });
    defDiv.innerHTML = line.join("<br />") + results.join("");

};

/**
 * Initiate a search from the search box
 *
 * To do a search from the search box, we need to update the day div and do the actual search
 *
 * Side-effects:
 *  - Starts an active search
 */
export function searchBox() {
    activeSearch = true;
    const searchTerm = stripVowels(document.getElementById("searchTerm").value);
    try {
        populateDayFromSearch(searchTerm);
        search(searchTerm);
    } catch {
        window.alert("That word is not in my Strong's dictionary");
    };
};

/**
 * Update the day div from a search
 *
 * Side-effects
 *   - Update day div
 * @params{searchTerm} (string) The hebrew string we are searching for (without vowels)
  */
function populateDayFromSearch(searchTerm) {
    const dayDiv = document.getElementById("day");
    const daySelect = document.getElementById("days");
    const mispar = document.getElementById("misparSelect").value;
    const day = words[searchTerm][mispar]["mod"];
    let dayWords = [];
    if(mispar === "hechrechi") {
        dayWords = hechrechi[currentLetter][day].map(word => wrapWord(word.word));
    } else if(mispar === "gadol") {
        dayWords = gadol[currentLetter][day].map(word => wrapWord(word.word));
    } else {
        dayWords = haakhor[currentLetter][day].map(word => wrapWord(word.word));
    };
    dayDiv.innerHTML = dayWords.join("<br />");
    daySelect.value = day;
};

/**
 * Make a letter clickable
 *
 * @params{letter} (string) The letter to make clickable
  */
function wrapLetter(letter) {
    return `<span class="letter bold" onclick="populateDay('${letter}');">${letter}</span>`;
};


/**
 * Populate the day and alefbet divs, add the enter key event listener
 *
 * @params{letter} (string) The letter to make clickable
  */
export function initialize() {
    populateDay(currentLetter);
    const searchTerm = document.getElementById("searchTerm");
    searchTerm.addEventListener("keyup", e => {
        if(e.key === "Enter") {
            searchBox();
        }
    });
    const alefbetDiv = document.getElementById("alefbet");
    const alefbet = [];
    for (let i = 'א'.charCodeAt(0); i <= 'ת'.charCodeAt(0); i++) {
        const letter = String.fromCharCode(i);
        if(!SOFITS.includes(letter)) {
           alefbet.push(wrapLetter(letter));
        }
    }
    alefbetDiv.innerHTML = alefbet.join(" ");
};

/**
 * Listen for changes to the mispar select and update the day div
 *
 */
export function changeMispar() {
    if(activeSearch) {
        const searchTerm = document.getElementById("searchTerm").value;
        populateDayFromSearch(searchTerm);
    } else {
        populateDay();
    };
};

/**
 * Clear the search box
 *
 * Should we be clearing the activeSearch here?
 */
export function clearSearch() {
    const searchBoxDiv = document.getElementById("searchTerm");
    searchBoxDiv.value = "";
};
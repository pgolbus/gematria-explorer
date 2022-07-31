import face from "../data/face.json" assert {type: 'json'};
import hidden from "../data/hidden.json" assert {type: 'json'};

export function populateDay() {
    const dayDiv = document.getElementById("day");
    const day = document.getElementById("days").value;
    if (document.getElementById("hidden").checked == true) {
        dayDiv.innerHTML = hidden[day].join("<br />");
    } else {
        dayDiv.innerHTML = face[day].join("<br />");
    };
};
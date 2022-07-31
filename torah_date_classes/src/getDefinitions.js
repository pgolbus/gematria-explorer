import face from "../data/face.json" assert {type: 'json'};

export function populateDay() {
    const dayDiv = document.getElementById("day");
    const day = document.getElementById("days").value;
    console.log(day);
    dayDiv.innerHTML = face[day].join("<br />");
};
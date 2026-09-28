const COURSES_EXEMPLE = [
  { id: 1, depart: "Paris", arrivee: "Orly", date: "2026-10-01T08:30:00", prix: 45 },
  { id: 2, depart: "Lyon", arrivee: "Villeurbanne", date: "2026-10-02T14:00:00", prix: 18 },
  { id: 3, depart: "Marseille", arrivee: "Aix-en-Provence", date: "2026-10-03T19:15:00", prix: 60 },
];

function getCourses() {
  return Promise.resolve({ data: COURSES_EXEMPLE });
}

module.exports = {
  getCourses,
};

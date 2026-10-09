const API_METIER_URL = process.env.API_METIER_URL || "http://localhost:8000";

async function requeter(chemin, params = {}, options = {}) {
  const url = new URL(chemin, API_METIER_URL);
  for (const [cle, valeur] of Object.entries(params)) {
    if (valeur !== undefined) url.searchParams.set(cle, valeur);
  }

  const reponse = await fetch(url, options)
  const data = await reponse.json().catch(() => null);

  if (!reponse.ok) {
    const erreur = new Error(`API métier : HTTP ${reponse.status}`);
    erreur.response = { status: reponse.status, data };
    throw erreur;
  }

  return { data };
}

function getCourses({ limit, offset, date } = {}) {
  return requeter("/courses", { limit, offset, date });
}

function getCourse(id) {
  return requeter(`/courses/${encodeURIComponent(id)}`);
}

function predireDuree(corps) {
  return requeter("/predictions/duree", {}, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corps),
  });
}

function reservation(reserv) {
  return requeter("/reservations", {}, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reserv),
  });
}

function listeReservations() {
  return requeter("/reservations", {}, {
    method: "GET",
    headers: { "Content-Type": "application/json" },

  });
}

function updateReservation(uid_reservation,statut) {
  return requeter(`/reservations/${uid_reservation}/statut`, {}, 
      {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(statut),
  });
}

//http://127.0.0.1:8000/reservations/50031/statut

module.exports = {
  getCourses,
  getCourse,
  predireDuree,
  reservation,
  listeReservations,
  updateReservation
};

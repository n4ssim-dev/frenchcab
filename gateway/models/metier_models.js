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

function getCourses({ limit, offset,date } = {}) {
  return requeter("/courses", { limit, offset,date });
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

module.exports = {
  getCourses,
  getCourse,
  predireDuree
};

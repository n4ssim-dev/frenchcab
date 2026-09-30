const API_METIER_URL = process.env.API_METIER_URL || "http://localhost:8000";

async function requeter(chemin, params = {}) {
  const url = new URL(chemin, API_METIER_URL);
  for (const [cle, valeur] of Object.entries(params)) {
    if (valeur !== undefined) url.searchParams.set(cle, valeur);
  }

  const reponse = await fetch(url);
  const data = await reponse.json().catch(() => null);

  if (!reponse.ok) {
    const erreur = new Error(`API métier : HTTP ${reponse.status}`);
    erreur.response = { status: reponse.status, data };
    throw erreur;
  }

  return { data };
}

function getCourses({ limit, offset } = {}) {
  return requeter("/courses", { limit, offset });
}

function getCourse(id) {
  return requeter(`/courses/${encodeURIComponent(id)}`);
}

module.exports = {
  getCourses,
  getCourse,
};

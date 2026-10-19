const { test, beforeEach } = require("node:test");
const assert = require("node:assert");

// variables d'environnement définies AVANT de charger les modules
process.env.GATEWAY_PASSWORD = "secret";
process.env.API_METIER_URL = "http://api-test:8000";

const verifierMotDePasse = require("../middlewares/auth");
const metier_models = require("../models/metier_models");
const metierController = require("../controllers/metier_controllers");

// faux objet res d'Express : garde le statut et le corps envoyés
function fausseReponse() {
  return {
    statusCode: null,
    corps: null,
    status(code) { this.statusCode = code; return this; },
    json(corps) { this.corps = corps; return this; },
  };
}

// faux fetch : enregistre les appels et renvoie la réponse donnée
let appels;
function simulerFetch(status, data) {
  global.fetch = async (url, options) => {
    appels.push({ url: url.toString(), options });
    return { ok: status < 400, status, json: async () => data };
  };
}

beforeEach(() => {
  appels = [];
});

// middleware d'authentification

test("auth : mot de passe valide dans l'en-tête -> next()", () => {
  const req = { get: () => "secret" };
  const res = fausseReponse();
  let suivant = false;
  verifierMotDePasse(req, res, () => { suivant = true; });
  assert.strictEqual(suivant, true);
  assert.strictEqual(res.statusCode, null);
});

test("auth : mot de passe invalide -> 401", () => {
  const req = { get: () => "mauvais" };
  const res = fausseReponse();
  let suivant = false;
  verifierMotDePasse(req, res, () => { suivant = true; });
  assert.strictEqual(suivant, false);
  assert.strictEqual(res.statusCode, 401);
  assert.strictEqual(res.corps.success, false);
});

test("auth : mot de passe absent -> 401", () => {
  const req = { get: () => undefined };
  const res = fausseReponse();
  verifierMotDePasse(req, res, () => {});
  assert.strictEqual(res.statusCode, 401);
});

test("auth : mot de passe accepté dans la query", () => {
  const req = { query: { password: "secret" }, get: () => undefined };
  let suivant = false;
  verifierMotDePasse(req, fausseReponse(), () => { suivant = true; });
  assert.strictEqual(suivant, true);
});

// models : appels vers l'API métier

test("models : getCourses transmet limit/offset/date et ignore les undefined", async () => {
  simulerFetch(200, { total: 0 });
  const reponse = await metier_models.getCourses({ limit: 10, offset: 0 });
  assert.deepStrictEqual(reponse.data, { total: 0 });
  const url = new URL(appels[0].url);
  assert.strictEqual(url.origin, "http://api-test:8000");
  assert.strictEqual(url.pathname, "/courses");
  assert.strictEqual(url.searchParams.get("limit"), "10");
  assert.strictEqual(url.searchParams.get("offset"), "0");
  assert.strictEqual(url.searchParams.has("date"), false);
});

test("models : erreur HTTP de l'API -> exception avec statut et détail", async () => {
  simulerFetch(404, { detail: "Course introuvable" });
  await assert.rejects(metier_models.getCourse(999), (err) => {
    assert.strictEqual(err.response.status, 404);
    assert.strictEqual(err.response.data.detail, "Course introuvable");
    return true;
  });
});

test("models : updateReservation envoie un PATCH avec le statut", async () => {
  simulerFetch(200, { statut_resa: 3 });
  await metier_models.updateReservation(5, 3);
  assert.strictEqual(new URL(appels[0].url).pathname, "/reservations/5/statut");
  assert.strictEqual(appels[0].options.method, "PATCH");
  assert.deepStrictEqual(JSON.parse(appels[0].options.body), { statut: "3" });
});

// controllers

test("controller : getCourses -> 200 avec la réponse de l'API", async () => {
  simulerFetch(200, { total: 1, courses: [] });
  const res = fausseReponse();
  await metierController.getCourses({ query: { limit: "1" } }, res);
  assert.strictEqual(res.statusCode, 200);
  assert.strictEqual(res.corps.success, true);
  assert.deepStrictEqual(res.corps.reponse, { total: 1, courses: [] });
});

test("controller : erreur de l'API -> même statut et message transmis", async () => {
  simulerFetch(409, { detail: "Impossible de passer de 'annulée' à 'confirmée'" });
  const res = fausseReponse();
  await metierController.updateReservation(
    { params: { uid_reservation: "1" }, body: { statut: "1" } },
    res
  );
  assert.strictEqual(res.statusCode, 409);
  assert.strictEqual(res.corps.success, false);
  assert.match(res.corps.message, /Impossible de passer/);
});

test("controller : API injoignable -> 502", async () => {
  global.fetch = async () => { throw new Error("ECONNREFUSED"); };
  const res = fausseReponse();
  await metierController.predireDuree({ body: {} }, res);
  assert.strictEqual(res.statusCode, 502);
  assert.strictEqual(res.corps.message, "Impossible de contacter l'API métier.");
});

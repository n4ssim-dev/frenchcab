const crypto = require("crypto");

const PASSWORD = process.env.GATEWAY_PASSWORD;

if (!PASSWORD) {
  throw new Error("GATEWAY_PASSWORD manquant dans le .env");
}

// Comparaison à temps constant pour ne pas révéler le mot de passe via le temps de réponse
function motDePasseValide(recu) {
  const a = crypto.createHash("sha256").update(recu).digest();
  const b = crypto.createHash("sha256").update(PASSWORD).digest();
  return crypto.timingSafeEqual(a, b);
}

function verifierMotDePasse(req, res, next) {
  const recu = req.get("x-api-password");

  if (!recu || !motDePasseValide(recu)) {
    return res.status(401).json({
      success: false,
      message: "Mot de passe manquant ou invalide.",
    });
  }

  next();
}

module.exports = verifierMotDePasse;

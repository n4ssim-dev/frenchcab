const crypto = require("crypto");

const PASSWORD = process.env.GATEWAY_PASSWORD;

if (!PASSWORD) {
  throw new Error("GATEWAY_PASSWORD manquant dans le .env");
}

function motDePasseValide(recu) {
  const a = crypto.createHash("sha256").update(recu).digest();
  const b = crypto.createHash("sha256").update(PASSWORD).digest();
  return crypto.timingSafeEqual(a, b);
}

function verifierMotDePasse(req, res, next) {
  const recu =
    req.body?.password ?? req.query?.password ?? req.get("x-api-password");

  if (typeof recu !== "string" || !recu || !motDePasseValide(recu)) {
    return res.status(401).json({
      success: false,
      message: "Mot de passe manquant ou invalide.",
    });
  }

  next();
}

module.exports = verifierMotDePasse;

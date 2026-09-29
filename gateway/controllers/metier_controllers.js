const metier_models = require("../models/metier_models");


function repondreErreur(res, error) {
  res.status(error.response?.status || 502).json({
    success: false,
    message:
      error.response?.data?.detail ||
      "Impossible de contacter l'API métier.",
  });
}

async function getCourses(req, res) {
  try {
    const { limit, offset } = req.query;
    const reponse = await metier_models.getCourses({ limit, offset });

    res.status(200).json({
      success: true,
      message: "La demande a été envoyée à l'API métier",
      reponse: reponse.data,
    });
  } catch (error) {
    repondreErreur(res, error);
  }
};

async function getCourse(req, res) {
  try {
    const reponse = await metier_models.getCourse(req.params.id);

    res.status(200).json({
      success: true,
      message: "La demande a été envoyée à l'API métier",
      reponse: reponse.data,
    });
  } catch (error) {
    repondreErreur(res, error);
  }
};

module.exports = {
  getCourses,
  getCourse,
};

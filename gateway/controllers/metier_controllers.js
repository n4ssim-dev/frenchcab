const metier_models = require("../models/metier_models");
const apiURL = process.env.API_METIER_URL


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
    const { limit, offset,date } = req.query;
    const reponse = await metier_models.getCourses({ limit, offset,date });

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

async function predireDuree(req, res) {
  try {
    const reponse = await metier_models.predireDuree(req.body);

    res.status(200).json({
      success: true,
      message: "La demande a été envoyée à l'API métier",
      reponse: reponse.data,
    });
  } catch (error) {
    repondreErreur(res, error);
  }
}

async function reservation(req, res) {
  try {
    const reponse = await metier_models.reservation(req.body);

    res.status(200).json({
      success: true,
      message: "La demande a été envoyée à l'API métier",
      reponse: reponse.data,
    });
  } catch (error) {
    repondreErreur(res, error);
  }
}

async function listeReservations(req, res) {
  try {
    const reponse = await metier_models.listeReservations();

    res.status(200).json({
      success: true,
      message: "La demande a été envoyée à l'API métier",
      reponse: reponse.data,
    });
  } catch (error) {
    repondreErreur(res, error);
  }
}

module.exports = {
  getCourses,
  getCourse,
  predireDuree,
  reservation,
  listeReservations
};
